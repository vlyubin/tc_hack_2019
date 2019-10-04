import hashlib
import logging
import re
import time
import traceback
import unicodedata
import urllib.error
import urllib.parse
import urllib.parse
import urllib.request
from datetime import datetime

import csv

import html2text
import pymongo
import requests
from bs4 import BeautifulSoup, UnicodeDammit

from storage import *


logger = logging.getLogger(__name__)

def getpars(text):
    pars = text.split('\n')
    newpars = ['']

    idx = 0
    while idx < len(pars):
        if len(newpars[-1]) < 400:
            newpars[-1] += ' ' + pars[idx]
        else:
            newpars.append(pars[idx])
        idx += 1

    return str(newpars)


class Crawler(object):
    # Headers to use for HTTP requests
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
        'Accept-Language': 'en,en-US;q=0,5',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8'
    }

    def __init__(self, credentials):
        self.credentials = credentials
        self.custom_info = {'content_element_css_class': 'content'}
        assert 'url_list' in credentials or 'crawling_urls' in credentials,\
            'Credentials must contain URL description'

        self.writeFile = open('mayo.csv', 'w')
        self.writer = csv.writer(self.writeFile)

    def store_all(self):
        print('store_all!')
        scraped_data = self.scrape_site()
        sleep_time = 1
        for i, item in enumerate(scraped_data):
            self.store_item(
                item,
                'webpage'
            )

    def store_item(self, item, item_type):
        print(item['title'])
        print(item['url'])
        html = unicodedata.normalize('NFKD',
            UnicodeDammit(self.get_clean_html(item['html'],
            custom_info=self.custom_info)).unicode_markup)
        title = item['title']

        html = Crawler.remove_invalid_chars(html)
        title = Crawler.remove_invalid_chars(title)

        html = Crawler.fix_relative_links(html, item['url'])

        html.replace('<h2>Overview</h2>', '')
        html.replace('<h2>Symptoms</h2>', '')
        html.replace('<h2>Causes</h2>', '')
        html.replace('<h2>Risk factors</h2>', '')
        html.replace('<h2>Complications</h2>', '')
        html.replace('<h2>Prevention</h2>', '')

        text = Crawler.get_clean_text(html)

        text = text.split('Print')[1].split('By Mayo Clinic Staff')[0].strip()

        short_text = text[:4000]
        print('Length is ' + str(len(short_text)))


        insert_webpage(item['title'], item['url'], short_text, short_text.split('\n')[0])

        self.writer.writerow([item['title'], item['url'], text.split('\n')[0], getpars(text)])
        self.writeFile.flush()

    def scrape_site(self):
        if 'crawling_urls' in self.credentials:
            return self.crawl_contents(self.credentials['crawling_urls'])
        if 'url_list' in self.credentials:
            urls = self.credentials['url_list']
        else:
            raise Exception('Invalid')
        return self.get_url_contents(urls)

    def crawl_contents(self, crawling_urls_data):
        timestamp_scraped = datetime.utcnow().isoformat() + "Z"
        urls_processed = set()
        urls_to_process = []

        for url in crawling_urls_data['starting_urls']:
            urls_to_process.append(url)

        while len(urls_to_process) > 0:
            url = urls_to_process.pop()
            if url in urls_processed:
                continue
            if url.endswith('pdf') or url.endswith('zip') or url.endswith('xlsx'):
                # We don't handle PDFs yet
                continue
            urls_processed.add(url)

            # Fetch the page - if we get rate limited, try again
            soup = None
            num_attmepts_left = 3
            while num_attmepts_left > 0:
                num_attmepts_left -= 1
                try:
                    r = requests.get(url, headers=self.HEADERS)
                    soup = BeautifulSoup(r.content, 'lxml')
                    break
                except requests.exceptions.ConnectionError:
                    time.sleep(5)

            if soup is None:
                continue
            # Wait to avoid getting rate-limited
            time.sleep(1)

            # The page is considered to be valid for storage, if it matches valid_patterns and doesn't match
            # valid_patterns_no_store
            is_valid = False
            for pattern in crawling_urls_data.get('valid_patterns', []):
                if re.match(pattern, url):
                    is_valid = True
                    break
            for pattern in crawling_urls_data.get('valid_patterns_no_store', []):
                if re.match(pattern, url):
                    is_valid = False
                    break

            if is_valid:
                # Return doc dict for valid pages
                logger.info("Yielding page %s" % url)
                try:
                    page = {
                        'title': html2text.html2text(soup.title.string).strip(),
                        'url': url,
                        'html': str(r.content),
                        'timestamp_scraped': timestamp_scraped
                    }
                    yield page
                except:
                    # Most likely this page returned 404, ignore it
                    continue

            # Add outgoing links to further processing
            url_base = urllib.parse.urljoin(url, '/')
            if url.startswith('https://www.mayoclinic.org/diseases-conditions/index'):
                for link in soup.find_all('a', href=True):
                    new_link = link['href'] if link['href'].startswith('http') else urllib.parse.urljoin(url_base, link['href'])
    
                    if new_link in urls_processed:
                        continue
    
                    should_be_visited = False
                    for pattern in crawling_urls_data.get('valid_patterns', []) + crawling_urls_data.get('valid_patterns_no_store', []):
                        if re.match(pattern, new_link):
                            should_be_visited = True
                            break
    
                    if should_be_visited:
                        urls_to_process.append(new_link)

            logger.info("Processed page %s" % url)

    def get_url_contents(self, urls):
        timestamp_scraped = datetime.utcnow().isoformat() + "Z"
        for i, url in enumerate(urls):
            logger.info('Processing ' + url)
            r = requests.get(url, headers=self.HEADERS, verify=False)
            soup = BeautifulSoup(r.content, 'lxml')
            html = r.content.decode('utf-8') if isinstance(r.content, bytes) else str(r.content)

            page = {
                'title': html2text.html2text(soup.title.string).strip(),
                'url': url,
                'html': html,
                'timestamp_scraped': timestamp_scraped
            }
            yield page

            if i % 10 == 0:
                logger.info("Processed %d page(s)", i + 1)

    def get_clean_html(self, html, custom_info):
        soup = BeautifulSoup(html, 'lxml')

        # Remove useless tags
        for tag in ['script', 'meta', 'footer']:
            tags_to_remove = soup.find_all(tag)
            [tag.extract() for tag in tags_to_remove]

        clean_html = None
        # Check if custom_info_contains details about the element to extract
        if 'content_element_id' in custom_info:
            clean_html = str(soup.find(id=custom_info['content_element_id']))

        if 'content_element_tag' in custom_info:
            clean_html = str(soup.find(custom_info['content_element_tag']))

        if 'content_element_css_class' in custom_info:
            clean_html = str(soup.find('div', {'class': custom_info['content_element_css_class']}))
            return clean_html
            
        if clean_html is not None and clean_html != '' and clean_html != 'None':
            print('here')
            return str(clean_html)

        return str(soup.find('body'))

    @staticmethod
    def get_clean_text(html):
        soup = BeautifulSoup(html, 'lxml')
        return soup.text

    @staticmethod
    def remove_invalid_chars(text):
        text = text.replace('\\n', '\n')
        text = text.replace('\\r', '\n')
        text = text.replace('\r', '\n')
        text = text.replace('\\t', ' ')
        text = text.replace('\t', ' ')
        if '[if lt IE 9]>' in text:
            text = text.split('[if lt IE 9]>')[1]
        if text.startswith("b'"):
            text = text[2:]
        return text.strip()

    @staticmethod
    def fix_relative_links(html, root_url):
        soup = BeautifulSoup(html, 'lxml')
        base_url = urllib.parse.urljoin(root_url, '/')

        for url in soup.find_all('a'):
            link_address = url.get('href', None)
            if link_address is not None and link_address.startswith('/'):
                url['href'] = urllib.parse.urljoin(base_url, link_address)

        for url in soup.find_all('img'):
            link_address = url.get('src', None)
            if link_address is not None and link_address.startswith('/'):
                url['src'] = urllib.parse.urljoin(base_url, link_address)

        return str(soup)

if __name__ == '__main__':
    credentials = {
      'crawling_urls': {
        'starting_urls': ['https://www.mayoclinic.org/diseases-conditions/index?letter=A'],
        'valid_patterns': ['https://www.mayoclinic.org/diseases-conditions/.*'],
        'valid_patterns_no_store': ['https://www.mayoclinic.org/diseases-conditions/index.*']
      }
    }
    c = Crawler(credentials)
    c.store_all()
