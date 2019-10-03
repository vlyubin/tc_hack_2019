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

import html2text
import pymongo
import requests
from bs4 import BeautifulSoup, UnicodeDammit


logger = logging.getLogger(__name__)


class Crawler(object):
    # Headers to use for HTTP requests
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
        'Accept-Language': 'en,en-US;q=0,5',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8'
    }

    def __init__(self, credentials):
        self.credentials = credentials
        assert 'url_list' in credentials or 'crawling_urls' in credentials,\
            'Credentials must contain URL description'

    def store_all(self):
        scraped_data = self.scrape_site()
        sleep_time = 1
        for i, item in enumerate(scraped_data):
            while True:
                try:
                    self.store_item(
                        item,
                        'webpage'
                    )
                except Exception:
                    print('Some error!')

    def store_item(self, item, item_type):
        raise Exception("Not Implamanted!")
        html = unicodedata.normalize('NFKD',
            UnicodeDammit(self.get_clean_html(item['original_item']['html'],
            self.get_origin(item['link'], default_origin=item.get('origin', None)), item.get('custom_info', {}))).unicode_markup)
        title = item['original_item']['title']

        html = SitemapConnector.remove_invalid_chars(html)
        title = SitemapConnector.remove_invalid_chars(title)

        html = SitemapConnector.fix_relative_links(html, item['link'])

        raise Execption("Implement storage mechanism!")
        '''
        get_mongo_client()[str(self.org_id)].update_one(
            {'id': 'webpage_%s' % hashlib.sha1(str(item['url']).encode('utf-8')).hexdigest()[:16]},
            {'$set': {
                'doc_type': item_type,
                'original_item': item,
                'is_deleted': False,
                'updated_at': item['timestamp_scraped'],
                'link': item['url'],
                'custom_info': self.custom_info,
                'origin': self.get_origin(item['url'])
            }},
            upsert=True)
        '''

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
                    r = requests.get(url, headers=self.HEADERS, verify=False)
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

    def get_clean_html(self, html, origin, custom_info={}):
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

        if clean_html is not None and clean_html != '' and clean_html != 'None':
            return str(clean_html)

        # Return content inside the tag that holds relevant content - defalts to body
        tag = org_feature_instances.SITEMAP_CONNECTOR_ORIGIN_TO_TAG_WITH_CONTENT.apply_to_org(self.org_id)
        if tag:
            tag_result = soup.find(tag.get(origin, 'body'))
            return str(tag_result) if tag_result is not None else str(soup.find('body'))

        # Class
        css_class = org_feature_instances.CSS_CONTENT_CLASS.apply_to_org(self.org_id)
        if css_class:
            return str(soup.find('div', {'class': css_class}))

        return str(soup.find('body'))

    def get_clean_text(self, html):
        soup = BeautifulSoup(html, 'lxml')

        invalid_html_tags = org_feature_instances.INVALID_HTML_TAGS.apply_to_org(self.org_id)
        if invalid_html_tags is not None:
            for args in invalid_html_tags:
                tags_to_remove = soup.find_all(**args)
                [tag.extract() for tag in tags_to_remove]

        text_tags = []

        valid_html_tags = org_feature_instances.VALID_HTML_TAGS.apply_to_org(self.org_id)
        for args in valid_html_tags:
            text_tags += soup.find_all(**args)
            if text_tags:
                break

        stripped_text = [' '.join(item.text.split()) for item in text_tags]
        text = "\n\n".join(stripped_text)

        # Gusto specific filters - if there are more of these, make these an org feature
        if 'Free tools\n\nCustomer stories\n\nContact us\n\n' in text:
            text = ' '.join(text.split('Free tools\n\nCustomer stories\n\nContact us\n\n')[1:])
        if 'Gusto\u2019s mission is to create a world' in text:
            text = ' '.join(text.split('Gusto\u2019s mission is to create a world')[:-1])

        return SitemapConnector.remove_invalid_chars(text)

    @staticmethod
    def remove_invalid_chars(text):
        text = text.replace('\\n', '')
        text = text.replace('\\r', '')
        text = text.replace('\r', '\n')
        text = text.replace('\\t', '')
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
