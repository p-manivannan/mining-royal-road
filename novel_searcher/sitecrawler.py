import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer as strainer
from pprint import pprint
import regex as re
from database import db_handler

'''
The following class is used to:
    1) Crawl category pages to get novel names and URLs
    2) Save entry (novel name and URL) to a field in a database 
    3) Search a novel on RoyalRoad by name
'''
class SiteCrawler:
    def __init__(self):
        self.novel_info = {}
        self.categories = {'best':'https://www.royalroad.com/fictions/best-rated',
                           'trending':'https://www.royalroad.com/fictions/trending',
                           'active':'https://www.royalroad.com/fictions/active-popular',
                           'complete':'https://www.royalroad.com/fictions/complete',
                           'weekly':'https://www.royalroad.com/fictions/weekly-popular',
                           'latest':'https://www.royalroad.com/fictions/latest-updates',
                           'new':'https://www.royalroad.com/fictions/new',
                           'rising':'https://www.royalroad.com/fictions/rising-stars'
                           }
        self.session = requests.Session()

    '''
    Returns base link of RoyalRoad:
    https://www.royalroad.com
    '''
    def get_royalroad_link(self):
        return 'https://www.royalroad.com'
    
    '''
    Get link of a given category
    '''
    def get_category_link(self, cat):
        category_str = cat.split()[0].strip().lower()  # select the first word and clean.
        if category_str in self.categories.keys():
            return self.categories[category_str]
        else:
            print(f'Your category, "{cat}" was not found!')
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
        novel_name = novel.text.strip()
        novel_link = novel.attrs['href']
        return novel_name, f'{self.get_royalroad_link() + novel_link}'

    '''
    Searches a novel by utilizing RoyalRoad's search function
    and returns a link to it.
    '''
    def search_novel(self, name):
        link = self.get_royalroad_link() + '/fictions/search?title='
        link += name.replace(' ', '+')
        page = requests.get(link).text
        return self.get_novel_url_and_name(page)


    def start(self, category, pages):
        link = None
        for n in range(1, pages + 1):
            if n == 1:
                link = self.get_category_link(category)
                print(link)
            else:
                link = self.get_category_link(category) + f'?page={n}'
            
            if link != None:
                self.crawl_page(link)

        self.save()

    def crawl_page(self, link):
        page = self.session.get(link).text
        fiction_title_element = strainer('h2', attrs={"class": "fiction-title"})
        soup = BeautifulSoup(page, features='lxml', parse_only=fiction_title_element)   # parse only fiction-title to save memory and time. It is a unique name
        for idx, novel in enumerate(soup.find_all('a')):
            novel_name = novel.text.strip()
            if novel.text in self.novel_info:   # Skip duplicates
                return
            self.novel_info[novel_name] = novel.attrs['href']
        pass

    def save(self):
        handler = db_handler.dbHandler()
        handler.insert_name_and_url(self.novel_info)



