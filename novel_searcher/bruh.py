import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer as strainer
from pprint import pprint
import pandas as pd
import regex as re

class NovelCrawler:
    def __init__(self):
        self.novel_info = {}

    def get_royalroad_link(self):
        return 'https://www.royalroad.com'

    def crawl_pages(self, category, pages):
        for n in range(1, pages + 1):
            if n == 1:
                link = self.get_royalroad_link() + category
            else:
                link = self.get_royalroad_link() + category + f'?page={n}'
            
            self.crawl_page(link)
            break

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


