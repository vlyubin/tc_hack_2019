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
        self.custom_info = {'content_element_css_class': 'content-justify'}
        assert 'url_list' in credentials or 'crawling_urls' in credentials,\
            'Credentials must contain URL description'

        self.writeFile = open('humana.csv', 'w')
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

        text = Crawler.get_clean_text(html)


        if '}' in text:
            text = text.split('}')[-1]

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
        raiseException()

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
                'html': str(r.content),
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
      'url_list': ['https://www.humanapharmacy.com/blog.cmd?article=New-live-agent-chat-is-here-to-help', 'https://www.humanapharmacy.com/blog.cmd?article=The-burning-sensation-of-heartburn',
      'https://www.humanapharmacy.com/blog.cmd?article=What-you-might-not-know-about-adult-vaccinations', 'https://www.humanapharmacy.com/blog.cmd?article=Why-prior-authorization,-or-approval,-may-be-needed',
      'https://www.humanapharmacy.com/blog.cmd?article=How-summer-temperatures-may-affect-drugs-',
      'https://www.humanapharmacy.com/blog.cmd?article=Specialty-medicine-explained-',
      'https://www.humanapharmacy.com/blog.cmd?article=What-to-know-about-high-blood-pressure',
      'https://www.humanapharmacy.com/blog.cmd?article=Benefits-of-vitamin-D',
      'https://www.humanapharmacy.com/blog.cmd?article=How-to-avoid-food-and-drug-interactions',
      'https://www.humanapharmacy.com/blog.cmd?article=The-right-dose-of-medicine-at-the-right-time',
      'https://www.humanapharmacy.com/blog.cmd?article=Why-your-prescription-orders-might-get-delayed',
      'https://www.humanapharmacy.com/blog.cmd?article=Sleep-apnea-risks',
      'https://www.humanapharmacy.com/blog.cmd?article=National-Osteoporosis-Awareness-and-Prevention-Month-',
      'https://www.humanapharmacy.com/blog.cmd?article=Take-the-stress-out-of-medication-management',
      'https://www.humanapharmacy.com/blog.cmd?article=How-to-read-your-order-status-messages-',
      'https://www.humanapharmacy.com/blog.cmd?article=Ways-to-help-relieve-seasonal-allergy-symptoms-',
      'https://www.humanapharmacy.com/blog.cmd?article=Know-how-to-detect-and-protect-from-skin-cancer-',
      'https://www.humanapharmacy.com/blog.cmd?article=Safely-spring-clean-your-medicine-cabinets-',
      'https://www.humanapharmacy.com/blog.cmd?article=Colorectal-in-home-screenings-',
      'https://www.humanapharmacy.com/blog.cmd?article=Colorectal-Cancer-Awareness-Month-',
      'https://www.humanapharmacy.com/blog.cmd?article=Medicare-Part-D-just-became-more-donut-and-less-donut-hole-',
      'https://www.humanapharmacy.com/blog.cmd?article=One-click-refill-emails-make-prescription-ordering-simple',
      'https://www.humanapharmacy.com/blog.cmd?article=Important-recall-information-Losartan-and-Losartan-HCTZ',
      'https://www.humanapharmacy.com/blog.cmd?article=How-to-dispose-of-used-needles,-syringes-and-other-sharps-waste',
      'https://www.humanapharmacy.com/blog.cmd?article=Preventing-falls,-fires-and-poisoning-in-your-home',
      'https://www.humanapharmacy.com/blog.cmd?article=Learn-about-heart-disease-and-statins',
      'https://www.humanapharmacy.com/blog.cmd?article=How-to-find-financial-assistance-for-specialty-medicine',
      'https://www.humanapharmacy.com/blog.cmd?article=Prepare-for-unexpected-disasters-with-emergency-readiness-tips',
      'https://www.humanapharmacy.com/blog.cmd?article=Avoid-infection-by-washing-your-hands-regularly-and-correctly',
      'https://www.humanapharmacy.com/blog.cmd?article=FDA-recall-of-Irbesartan-and-Irbesartan/HCTZ-manufactured-by-Prinston',
      'https://www.humanapharmacy.com/blog.cmd?article=Pick-the-right-way-to-refill-for-you',
      'https://www.humanapharmacy.com/blog.cmd?article=Learn-how-to-pay-an-outstanding-balance-online',
      'https://www.humanapharmacy.com/blog.cmd?article=Important-recall-information-for-Losartan-Potassium-100mg-Tablets',
      'https://www.humanapharmacy.com/blog.cmd?article=Pick-the-right-cold-and-flu-medicine',
      'https://www.humanapharmacy.com/blog.cmd?article=Taking-your-medication-on-time,-every-time',
      'https://www.humanapharmacy.com/blog.cmd?article=See-how-easy-it-is-to-make-a-Humana-Pharmacy-online-account',
      'https://www.humanapharmacy.com/blog.cmd?article=Text-message-reminders-make-remembering-to-refill-a-snap',
      'https://www.humanapharmacy.com/blog.cmd?article=Schedule-deliveries-for-your-specialty-medicine-orders',
      'https://www.humanapharmacy.com/blog.cmd?article=Healthy-eating-around-the-holidays',
      'https://www.humanapharmacy.com/blog.cmd?article=Humana-Specialty-Pharmacy-delivers-when-it-counts',
      'https://www.humanapharmacy.com/blog.cmd?article=Track-your-prescription-order,-skip-the-sign-in',
      'https://www.humanapharmacy.com/blog.cmd?article=Transferring-prescriptions-is-a-snap-with-the-Humana-Pharmacy-mobile-app',
      'https://www.humanapharmacy.com/blog.cmd?article=Get-your-preventive-screenings',
      'https://www.humanapharmacy.com/blog.cmd?article=Welcome-to-the-improved-Humana-Pharmacy-dashboard',
      'https://www.humanapharmacy.com/blog.cmd?article=Important-recall-information-for-Valsartan-and-Valsartan-HCTZ',
      'https://www.humanapharmacy.com/blog.cmd?article=Quick-prescription-refill-is-simple,-swift-and-secure-',
      'https://www.humanapharmacy.com/blog.cmd?article=Healthy-bone-habits-for-life',
      'https://www.humanapharmacy.com/blog.cmd?article=What-you-need-to-know-about-over-the-counter-medicine',
      'https://www.humanapharmacy.com/blog.cmd?article=Five-ideas-for-outdoor-fun',
      'https://www.humanapharmacy.com/blog.cmd?article=We-made-the-Humana-Pharmacy-mobile-app-even-better',
      'https://www.humanapharmacy.com/blog.cmd?article=Mobile-tools-for-managing-your-health',
      'https://www.humanapharmacy.com/blog.cmd?article=Vitamin-safety',
      'https://www.humanapharmacy.com/blog.cmd?article=Understanding-drug-formularies',
      'https://www.humanapharmacy.com/blog.cmd?article=Text-notifications-for-refill-reminders-and-order-updates',
      'https://www.humanapharmacy.com/blog.cmd?article=Learn-how-to-identify-and-avoid-email-spoofing-scams',
      'https://www.humanapharmacy.com/blog.cmd?article=Clearing-the-cache-from-your-browser',
      'https://www.humanapharmacy.com/blog.cmd?article=Why-sleep-matters',
      'https://www.humanapharmacy.com/blog.cmd?article=Statins-101',
      'https://www.humanapharmacy.com/blog.cmd?article=How-to-proactively-manage-your-stress-during-the-holidays',
      'https://www.humanapharmacy.com/blog.cmd?article=Flu-shots-can-protect-you-and-others',
      'https://www.humanapharmacy.com/blog.cmd?article=Effects-of-diabetes-on-your-heart',
      'https://www.humanapharmacy.com/blog.cmd?article=Appropriate-use-of-antibiotics',
      'https://www.humanapharmacy.com/blog.cmd?article=.Pharmacy-Verified-Website-Program',
      'https://www.humanapharmacy.com/blog.cmd?article=Humana-Pharmacy-donates-returns-to-nonprofits',
      'https://www.humanapharmacy.com/blog.cmd?article=Tips-on-how-to-travel-safely-with-medicine',
      'https://www.humanapharmacy.com/blog.cmd?article=Keeping-your-mind-sharp',
      'https://www.humanapharmacy.com/blog.cmd?article=Keeping-your-bones-strong',
      'https://www.humanapharmacy.com/blog.cmd?article=New-hepatitis-therapies',
      'https://www.humanapharmacy.com/blog.cmd?article=Treating-your-allergies',
      'https://www.humanapharmacy.com/blog.cmd?article=Staying-on-track-with-your-medications',
      'https://www.humanapharmacy.com/blog.cmd?article=Natural-ways-to-relieve-pain',
      'https://www.humanapharmacy.com/blog.cmd?article=Traveling-with-medicine-during-the-holidays',
      'https://www.humanapharmacy.com/blog.cmd?article=Top-10-health-screenings',
      'https://www.humanapharmacy.com/blog.cmd?article=Top-fitness-trends-in-2017',
      'https://www.humanapharmacy.com/blog.cmd?article=How-sugar-and-salt-affect-the-heart',
      'https://www.humanapharmacy.com/blog.cmd?article=How-to-beat-seasonal-affective-disorder',
      'https://www.humanapharmacy.com/blog.cmd?article=Healthy-holiday-eating-strategies',
      'https://www.humanapharmacy.com/blog.cmd?article=Is-generic-medicine-right-for-you',
      'https://www.humanapharmacy.com/blog.cmd?article=Stay-on-track-with-Humana-Pharmacy-mail-delivery',
      'https://www.humanapharmacy.com/blog.cmd?article=New-look,-same-effectiveness-',
      'https://www.humanapharmacy.com/blog.cmd?article=Patient-financial-assistance',
      'https://www.humanapharmacy.com/blog.cmd?article=Specialty-meds-made-simple',
      ]
    }
    c = Crawler(credentials)
    c.store_all()
