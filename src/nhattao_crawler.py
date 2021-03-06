import time, re, requests
from bs4 import BeautifulSoup
from datetime import datetime

class Nhattao_crawler():
    def __init__(self, url):
        '''
            Creates a Nhattao crawler object to extract and process data from the provided url.

            Args:
                url (str): Url address of category to extract data from.

            Attributes:
                headers (dict:str): Contains header information, to be sent when making requests.
                type (str): Query parameter used to generate full url for requests, retrieves latest data.
                search_id (str): Query parameter used to generate full url for requests, unique ID for each query.
                order (str): Query parameter used to generate full url for requests, default ordering for listings.
                direction (str): Query parameter used to generate full url for requests, default ordering for listings.
                r (:obj:requests): Requests session object to manage requests.
        '''
        self.url = url
        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) \
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
        self.type = 'recent'
        self.search_id = ''
        self.order = 'up_time'
        self.direction = 'desc'
        self.r = requests.Session()
    
    def _set_search_id(self):
        '''
            Retrieves the Search ID from a request using BeautifulSoup and uses it for remaining requests (Changes for each page).
        '''
        page = self.r.get(self.url, headers=self.headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        search_id = soup.find('div', class_='PageNav')['data-baseurl'].split('/')[2]
        self.search_id = ''.join(re.findall(r'\d', search_id))

    def _process_datetime(self, soup, class_):
        '''
            Retrieves the datetime string using BeautifulSoup and parses it into timestamp format.

            Args:
                soup (:obj:BeautifulSoup): BeautifulSoup object containing the HTML information of a listing.
                class_ (str): HTML div --> class containing the datetime string.

            Returns:
                Datetime in timestamp format.
        '''
        for dt in soup.find('li', class_=class_):
            dt_str = dt.text
            if 'at' in dt_str:
                dt_str = dt_str.replace('at', '')
            dt_str = dt_str.split()
            return datetime.timestamp(datetime.strptime(dt_str[0], '%d/%m/%y'))
    
    def _get_seller_info(self, soup):
        '''
            Processes infromation regarding the seller and stores them in a list.

            Args:
                soup (:obj:BeautifulSoup): BeautifulSoup object containing the HTML information of the seller.

            Returns:
                List of results.
        '''
        tmp = []
        for info in soup.find('div', class_='threadview-header--seller'):
            tmp.append(info)

        tmp[1] = tmp[1].span.text
        if tmp[3].span:
            tmp[3] = datetime.timestamp(datetime.strptime(tmp[3].span.text, '%d/%m/%y'))
        else:
            tmp[3] = tmp[3].abbr['data-time']
        tmp[5] = tmp[5].dd.text
        tmp[7] = tmp[7].dd.text
        return tmp
    
    def _check_details(self, soup):
        '''
            Verifies if any information from the listing is empty and replaces them with N/A otherwise, the value is used.
            Results are stored in a list.

            Args:
                soup (:obj:BeautifulSoup): BeautifulSoup object containing the HTML information of a listing.

            Returns:
                List of results.
        '''
        checked = []
        if soup.find('li', class_='threadview-header--classifiedStatus'):
            condition = soup.find('li', class_='threadview-header--classifiedStatus').text
        else:
            condition = 'N/A'
        checked.append(condition)
            
        if soup.find('li', class_='threadview-header--classifiedLoc'):
            location = soup.find('li', class_='threadview-header--classifiedLoc').text.strip()
        else:
            location = 'N/A'
        checked.append(location)
        
        if soup.find('li', class_='threadview-header--viewCount'):
            seen = int(soup.find('li', class_='threadview-header--viewCount').text.split()[1].replace('.',''))
        else:
            seen = 'N/A'
        checked.append(seen)

        if soup.find('p', class_='threadview-header--classifiedPrice'):
            price = float(soup.find('p', class_='threadview-header--classifiedPrice').text.strip().replace(' đ', '').replace('.',''))
        else:
            price = 0
        checked.append(price)

        if soup.find('span', class_='address'):
            addr = soup.find('span', class_='address').text.strip()
        else:
            addr = 'N/A'
        checked.append(addr)
            
        if soup.find('a', class_='threadview-header--contactPhone'):
            contact = soup.find('a', class_='threadview-header--contactPhone').text.strip().replace(' ','')
        else:
            contact = 'N/A'
        checked.append(contact)
        return checked
        
    def get_no_pages(self):
        '''
            Retrieves the last page number from the webpage.

            Returns:
                Integer value of last page.
        '''
        # Determine maximum number of webpages in a category        
        category_page = self.r.get(self.url, headers=self.headers)
        page_content = BeautifulSoup(category_page.text, 'html.parser')
        return int(page_content.find('div', class_='PageNav')['data-last'])

    def get_listings_per_page(self, i):
        listing_links = []
        self._set_search_id()
        url = self.url+'page-{}?type={}&search_id={}&order={}&direction={}'.format(i, self.type, self.search_id, self.order, self.direction)
        print('URL: {}'.format(url))
        page_listings = self.r.get(url, headers=self.headers)
        listings = BeautifulSoup(page_listings.text, 'html.parser')
    
        # Grab all listing links from each page
        for link in listings.find_all('a', attrs={'href': re.compile(r'threads/.*'), 'class': 'Nhattao-CardItem--image'}):
            listing_links.append('https://nhattao.com/'+link.get('href'))
        return listing_links
    
    def process_data(self, listing_url):
        info = self.r.get(listing_url, headers=self.headers)
        data = BeautifulSoup(info.text, 'html.parser')                
        seller_info = self._get_seller_info(data)
        details = self._check_details(data)
        results = {
            'Thread Link': listing_url,
            'Thread ID': listing_url.split('.')[-1].replace('/',''),
            'Title': data.find('h2').text,
            'Condition': details[0],
            'Location': details[1],
            'Posted Date': self._process_datetime(data, 'threadview-header--postDate'),
            'Seen': details[2],
            'Price': details[3],
            'Address': details[4],
            'Contact': details[5],
            'Seller': seller_info[1],
            'Date Joined': seller_info[3],
            'No Products': seller_info[5],
            'Likes': seller_info[7]
                 }
        return results