import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer as strainer
from pprint import pprint
import regex as re
from . import SiteCrawler
import time

'''
Handles information about a single novel.
Given a novel (either name or URL), NovelCrawler handles
retrieval and saving to a Mongo database of the following:
    1) Author
    2) Tags
    3) Summary
    4) Statistics:
        - Overall score
        - Style score
        - Story score
        - Grammar score
        - Character score
        - Total views
        - Average views
        - Favourites
        - Ratings
        - Pages
        - Number of chapters
    5) Reviews:
        - Reviewer
        - Review time
        - Reviewed at chapter
        - Review content
        - Review score
'''
class NovelCrawler():
    def __init__(self, name=None, url=None):
        self.novel_info = {}
        self.name = name
        self.url = url

    '''
    Opens request and returns page as unicode
    '''
    def init_request(self, link=None):
        # Probably gotta verify link if it's actually a link first
        self.url = link if link is not None else self.url
        if self.url is not None:
            return requests.get(self.url).text
        
        if self.name is not None:
            self.search_novel(self.name)
            return requests.get(self.url).text

        print(f'Name and link not provided!')
        return None

    '''
    Returns base link of RoyalRoad:
    https://www.royalroad.com
    '''
    def get_royalroad_link(self):
        return 'https://www.royalroad.com'
    
    '''
    Gets information about a novel after having provided
    a name/URL
    '''
    def get_novel_info(self):
        if self.novel_info:         # If dict has something, return it (assuming it's already filled with the right entries)
            return self.novel_info

        if not self.novel_info and (self.isName() or self.url is None):
            print(f"You haven't provided the following: {'a name' if self.name is None else ''}, {'a URL' if self.url is None else ''}")
            return None

        if not self.novel_info and (self.name is not None and self.url is None):    # If nothing is in dict, but we have a name, search it up and get url
            self.search_novel(self.name)
        
        if not self.novel_info and self.isURL():     # If nothing in dict and there is a URL, retrieve novel info and return it
            self.retrieve_novel_info()
            return self.novel_info
        
        print(f'Failed to get novel info: {self.name}, {self.url}, {self.novel_info.keys() if self.novel_info is not None else None}')
        return None

    '''
    In a page containing a list of novels, fiction-title is the h2 class
    that is common. By filtering a page for this tag, one can find the 
    title and url of a novel on the page.
    page the text of a link parsed through requests.get()
    '''
    def get_novel_url_and_name(self, page):
        fiction_title_element = strainer('h2', attrs={'class': 'fiction-title'})
        soup = BeautifulSoup(page, features='lxml', parse_only=fiction_title_element)
        novel = soup.find('a')
        if novel == None:
            print('No results were found matching criteria!')
            return None
        self.name = novel.text.strip()
        self.url = novel.attrs['href']

        return f'{self.get_royalroad_link() + self.url}', self.name, 

    def isName(self):
        return True if self.name is not None else False

    def isURL(self):
        if self.url is None:
            print('No URL provided!')
            return False
        try:
            page = requests.get(self.url)
            print(page.status_code)
            return True
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
            print(f'Error reaching page: {self.url}')
        
        return False

    def get_patreon_link(self):
        soup = BeautifulSoup(page, features='lxml')
        container = soup.find('div', class_='dropdown-content')
        link_container = container.find_all('a')      # In case there is patreon and paypal link, patreon is the last link
        # Only return if link is patreon
        for link in link_container:
            if 'patreon' in link.attrs['href']:
                return link.attrs['href']
        
        return None

    def retrieve_patreon_info(self, link=None):
        if link is None:
            print('No patreon link provided')
            return None
        # First check if income is already stated
        # If not, check if there is number of subs
        # If there is, and there are tiers, get highest and lowest tier
        # Return None
        #
        # tag span, data-tag = patron-count (find first)/creation-count/earnings-count
        pass

    '''
    Searches a novel by utilizing RoyalRoad's search function
    and returns a link to it.
    '''
    def search_novel(self, name):
        link = self.get_royalroad_link() + '/fictions/search?title='
        link += name.replace(' ', '+')
        page = self.init_request(link)
        self.url, self.name = self.get_novel_url_and_name(page)

    def retrieve_novel_info(self):
        page = self.init_request()
        soup = BeautifulSoup(page, features='lxml')
        self.put_name()
        self.put_author(soup)
        self.put_summary(soup)
        self.put_tags(soup)
        self.put_stats(soup)
        self.put_reviews(soup)
        return None
        # return self.get_novel_info()        # Danger of endless recursion

    def put_name(self):
        '''
        Puts novel name in novel_info as 'novel_name'
        '''
        self.novel_info['novel_name'] = self.name if self.name is not None else None

    def put_author(self, soup):
        '''
        Puts author in novel_info
        '''
        container = soup.find('div', class_='row fic-header').find_next('a')    # Author container
        self.novel_info['author'] = container.text.strip()

    def put_summary(self, soup):
        '''
        Puts summary in novel_info
        '''
        container = soup.find('div', class_='description')
        self.novel_info['summary'] = container.text.strip()
        
    def put_tags(self, soup):
        '''
        Puts tags in novel_info
        '''
        container = soup.find('div', class_='fiction-info').find_next('div', class_='margin-bottom-10').text.strip().split('\n')
        unwanted = {'', ' '}
        # Convert tags to lower case in case they change it up later
        self.novel_info['tags'] = [item.strip().lower() for item in container if item.strip() not in unwanted]

    def put_stats(self, soup):
        stats = {}
        stats['overall_score'] = soup.find('span', {'data-original-title': 'Overall Score'}).attrs['data-content']
        stats['style_score'] = soup.find('span', {'data-original-title': 'Style Score'}).attrs['data-content']
        stats['story_score'] = soup.find('span', {'data-original-title': 'Story Score'}).attrs['data-content']
        stats['grammar_score'] = soup.find('span', {'data-original-title': 'Grammar Score'}).attrs['data-content']
        stats['character_score'] = soup.find('span', {'data-original-title': 'Character Score'}).attrs['data-content']
        # Relevant info is in the second list element ('li') on the page
        # numerical_stats is retrieved as such: ['stat 1', 23, 'stat 2', 3,134]
        numerical_stats = soup.find_all('div', class_='col-sm-6')[1].find_all('li')
        stat_keys = [x.text.replace(':', ' ').strip().replace(' ', '_').lower() for x in numerical_stats[::2]]
        stat_values = [x.text.strip().replace(',', '') for x in numerical_stats[1::2]]
        for idx, key in enumerate(stat_keys):
            stats[key] = stat_values[idx]
        self.novel_info['stats'] = stats
    
        

    '''
    very slow T_T, gotta optimize...
    returns a list of dicts containing
    reviewers and their reviews
    Assumes URL is in form:
    https://royalroad.com/fiction/21220/mother-of-learning
    '''
    def put_reviews(self, soup):
        temp_url = self.url + '?sorting=top&reviews='
        # RETRIEVE NUMBER OF REVIEW PAGES
        ul = soup.find('ul', class_='pagination justify-content-center').find_all('li')
        a = ul[-1].find('a')
        n_pages = int(a.attrs['data-page'])
        reviews = []

        for n in range(1, n_pages):
            # CREATE LINK TEXT
            review_url = temp_url + str(n)
            page = requests.get(review_url).text
            soup = BeautifulSoup(page, features='lxml')
            # FIND THE REVIEW CONTAINER
            review_container = soup.find('div', class_='portlet light reviews')
            # LOOP THROUGH ALL REVIEWS1
            for x in review_container.find_all('div', class_='review'):
                meta = x.find('div', class_ = 'review-meta')
                reviewer = meta.find_next('a').text.strip()
                review = x.find_next('div', class_='review-inner').text.strip()
                reviews.append({'author' : reviewer, 'review' : review})

        self.novel_info['reviews'] = reviews



# # Testing
# site_crawler = SiteCrawler()
# novel_crawler = NovelCrawler(name='Mother of Learning')
# page = novel_crawler.init_request()
# novel_crawler.get_patreon_link()

# novel_crawler.retrieve_novel_info()
    