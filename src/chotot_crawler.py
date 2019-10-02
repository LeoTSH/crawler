import time, re, requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Chotot_crawler():
    def __init__(self, page_load_timer):
        self.page_load_timer = page_load_timer
        self.chrome_options = Options()
        self.chrome_options.headless = True
        self.driver = webdriver.Chrome('./mac_chromedriver', options=self.chrome_options)

    def _process_details(self, soup):
        process_details = {}
        for details in soup.find_all('div', class_='col-xs-12 col-md-6 _2E8caC-j61im7lRi5lExI9'):
            if len(details.text.split(':')) > 1:
                details = details.text.split(':')        
                process_details[details[0].strip()] = details[1].strip()
            else:
                process_details[details.text] = details.text
        return process_details

    def _process_datetime(self, soup):
        # year, month, day, hour, minute second, yesterday
        result = ''
        dt = soup.find('div', class_='hidden-xs JfuoT2phEEouoxezYbBx4').text
        if re.findall(r'năm', dt):
            result = datetime.timestamp(datetime.now() - timedelta(days=int(''.join(re.findall(r'\d', dt)))*365))
        elif re.findall(r'tháng', dt):
            result = datetime.timestamp(datetime.now() - timedelta(days=int(''.join(re.findall(r'\d', dt)))*30))
        elif re.findall(r'tuần', dt):
            result = datetime.timestamp(datetime.now() - timedelta(days=int(''.join(re.findall(r'\d', dt)))*7))
        elif re.findall(r'ngày', dt):
            result = datetime.timestamp(datetime.now() - timedelta(days=int(''.join(re.findall(r'\d', dt)))))
        elif re.findall(r'giờ', dt):
            result = datetime.timestamp(datetime.now() - timedelta(hours=int(''.join(re.findall(r'\d', dt)))))
        elif re.findall(r'phút', dt):
            result = datetime.timestamp(datetime.now() - timedelta(minutes=int(''.join(re.findall(r'\d', dt)))))
        elif re.findall(r'giây', dt):
            result = datetime.timestamp(datetime.now() - timedelta(seconds=int(''.join(re.findall(r'\d', dt)))))
        elif re.findall(r'hôm qua', dt):
            result = datetime.timestamp(datetime.now() - timedelta(hours=24))
        else:
            print(dt)
        return result

    def get_listings_per_page(self, page_url):
        links = []
        self.driver.get(page_url)
        time.sleep(self.page_load_timer)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        for link in soup.find_all('a', href=re.compile(r'.*.htm')):
            links.append('https://nha.chotot.com'+link.get('href'))
        return links

    def process_data(self, listing_url):
        self.driver.get(listing_url)
        time.sleep(self.page_load_timer)

        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        except:
            print('Error processing url: {}'.format(listing_url))
        else:           
            results = {
                'Link': listing_url,
                'Thread ID': re.sub(r'.htm.*', '', listing_url.split('/')[-1]),
                'Posted Date': self._process_datetime(soup),
                'Seller': soup.find('div', class_='sc-eilVRo hEXVti').text,
                'Seller Type': soup.find('div', class_='sc-fhYwyz fDMLIV').text,
                'Contact': soup.find('a', \
                            class_='H3QBvet3qzdHlB3LVAw-7 btn btn-success hidden-sm hidden-md hidden-lg hidden-xl')\
                            ['href'].split(':')[1],
                'Title': soup.find('h1', class_='_22kG1zbJ4D-6IUEgKvoifC col-xs-12').text,
                'Price': soup.find('span', \
                        class_='oRSYZ0HPb2tHhHjpVp_2o').text.replace(' VND', '').replace('đ', '').replace('.','')
                    }
            details = self._process_details(soup)
            for k, v in details.items():
                results[k] = v
        return results