import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer as strainer
from pprint import pprint
import pandas as pd
import regex as re

class NovelCrawler:
    def __init__(self):
        self.novel_info = {}
        self.categories = {'best':'https://www.royalroad.com/fictions/best-rated',
                           'trending':'https://www.royalroad.com/fictions/trending',
                           'ongoing':'https://www.royalroad.com/fictions/active-popular',
                           'complete':'https://www.royalroad.com/fictions/complete',
                           'week':'https://www.royalroad.com/fictions/weekly-popular',
                           'latest':'https://www.royalroad.com/fictions/latest-updates',
                           'new':'https://www.royalroad.com/fictions/new',
                           'rising':'https://www.royalroad.com/fictions/rising-stars'
                           }

    '''
    Returns base link of RoyalRoad:
    https://www.royalroad.com
    '''
    def get_royalroad_link(self):
        return 'https://www.royalroad.com'
    
    '''
    Get link of a given category
    '''
    def get_category_link(self, category_str):
        category_str = category_str.split()[0].strip().lower()  # select the first word and clean.
        return next((key for key in self.categories if category_str in key), None)
        

    def crawl_pages(self, category, pages):
        for n in range(1, pages + 1):
            if n == 1:
                link = self.get_royalroad_link() + category
            else:
                link = self.get_royalroad_link() + category + f'?page={n}'
            
            self.crawl_page(link)
            break
    
    '''
    In a page containing a list of novels, fiction-title is the h2 class
    that is common. By filtering a page for this tag, one can find the 
    title and url of a novel on the page.
    page the text of a link parsed through requests.get()
    '''
    def get_novel_url_and_name(self, page):
        fiction_title_element = strainer('h2', attrs={"class": "fiction-title"})
        soup = BeautifulSoup(page, features='lxml', parse_only=fiction_title_element) 
        novel = soup.find('a')
        novel_name = novel.text.strip()
        novel_link = novel.attrs['href']
        return (novel_name, novel_link)

    '''
    Searches a novel by utilizing RoyalRoad's search function
    and returns a link to it.
    '''
    def search_novel(self, name):
        link = self.get_royalroad_link() + '/fictions/search?title='
        link += name.replace(' ', '%')
        page = requests.get(link).text
        return get_novel_url_and_name(page)

    def crawl_page(self, link):
        '''
        Returns the links and names of all the novels
        in a page
        '''
        page = requests.get(link).text
        fiction_title_element = strainer('h2', attrs={"class": "fiction-title"})
        soup = BeautifulSoup(page, features='lxml', parse_only=fiction_title_element)   # parse only fiction-title to save memory and time. It is a unique name
        for idx, novel in enumerate(soup.find_all('a')):
            novel_name = novel.text.strip()
            if novel.text in self.novel_info:   # Skip duplicates
                return
            self.novel_info[novel_name] = novel.attrs['href']
        pass
    

'''
COMMAND FLOW:
- For each category page (best-rated/latest/rising-stars/etc.):
    - Traverse N pages
    - Check if novel in dict
    - If not, retrieve link and name of novel
'''

'''
TO-DO: 
- Can't have all the novels in RAM while crawling, so must implement saving/loading
  to manage memory usage, though it might slow it down. Maybe I could have a param
  file somewhere that configures the number of pages to crawl before saving so it
  works on systems with different RAM capacity
- Make getting category names neater. Maybe in a function or class or whatever
'''

N_PAGES = 10        # Num pages to traverse
# rising stars doesn't have more than one page
# , '/fictions/rising-stars'
categories = ['/fictions/best-rated']
crawler = NovelCrawler()
for category in categories:
    crawler.crawl_pages(category, N_PAGES)
