import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer as strainer
from pprint import pprint
import regex as re
from utils.custom_exceptions import NovelDeleted
from lxml import etree

def scrape_novel(url):
    novelscraper = NovelScraper(url=url)
    novelscraper.get_novel_info()
    return novelscraper.novel_info


class NovelScraper():
    def __init__(self, name=None, url=None):
        self.novel_info = {}
        self.name = name
        self.url = url
        self.page = None        # requests.get(URL).text is supposed to be the value\
        self.parser = etree.HTMLParser(recover=True)

    '''
    Check what failed with scraping
    '''
    def __check_exceptions(self, soup):
        # Check if novel deleted
        try:
            check_string = "this fiction has been deleted"
            element = soup.find('div', class_ = 'col-md-12 page-404').text.strip().lower()
            if check_string in element:
                raise NovelDeleted
        except NovelDeleted as e:
            raise NovelDeleted from e
        # If even check string isn't present then retry connection.
        except AttributeError as e:
            raise AttributeError("Page empty") from e

        pass
    '''
    Opens connection to a novel page
    '''
    def init_request(self, link=None):
        # Probably gotta verify link if it's actually a link first
        self.url = link if link is not None else self.url
        if self.url is not None:
            self.page = requests.get(self.url).text
            return

        if self.name is not None:
            self.search_novel(self.name)
            self.page = requests.get(self.url).text
            return

        print(f'Name and link not provided!')
        return None

    '''
    Returns base link of RoyalRoad:
    https://www.royalroad.com
    '''
    def get_royalroad_link(self):
        return 'https://www.royalroad.com'
    
    '''
    Gets information about a novel. If no information present, scrape it.
    '''
    def get_novel_info(self):
        if bool(self.novel_info):         # If dict has something, return it (assuming it's already filled with the right entries)
            return self.novel_info
        
        if self.url is None:
            if self.isName():
                self.search_novel(self.name)        # Search novel if only url is provided
            else:
                raise ValueError("Novel name hasn't been provided")
            
        self.init_request(self.url)
        self.scrape_novel_info()
        return self.novel_info
        

    '''
    The same function from SiteCrawler, but to scrape the name and url of the
    first novel that pops up after search
    '''
    def get_novel_url_and_name(self):
        if self.page is None:
            raise TypeError
        
        fiction_title_element = strainer('h2', attrs={'class': 'fiction-title'})
        soup = BeautifulSoup(self.page, features='lxml', parse_only=fiction_title_element, parser=self.parser)
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

    '''
    Searches a novel by utilizing RoyalRoad's search function.
    '''
    def search_novel(self, name):
        link = self.get_royalroad_link() + '/fictions/search?title='
        link += name.replace(' ', '+')      # Replace the spaces with a '+'
        self.init_request(link)
        self.url, self.name = self.get_novel_url_and_name()

    '''
    Do not call if self.page is None or url or name is None
    should be a private function honestly
    '''
    def scrape_novel_info(self):
        soup = BeautifulSoup(self.page, features='lxml', parser = self.parser)
        self.put_name()             # Bug with this is that if novel searched is not same as novel searched for, then info scraped is mismatched
        # If put author fails, then find the reason for it and raise exception. Only two cases:
        # 404 Novel deleted. Or RoyalRoad refusing connection.
        try:
            self.put_author(soup)
        except:
            ex = self.__check_exceptions(soup)
            
        self.put_summary(soup)
        self.put_tags(soup)
        self.put_stats(soup)
        self.put_number_of_chapters(soup)
        self.put_wordcount(soup)

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
        # The following stats can be empty for novels which don't have enough reviews
        try:
            stats['overall_score'] = soup.find('span', {'data-original-title': 'Overall Score'}).attrs['data-content']
            stats['style_score'] = soup.find('span', {'data-original-title': 'Style Score'}).attrs['data-content']
            stats['story_score'] = soup.find('span', {'data-original-title': 'Story Score'}).attrs['data-content']
            stats['grammar_score'] = soup.find('span', {'data-original-title': 'Grammar Score'}).attrs['data-content']
            stats['character_score'] = soup.find('span', {'data-original-title': 'Character Score'}).attrs['data-content']
        # Relevant info is in the second list element ('li') on the page
        except:
            # If you reach here, then the novel hasn't received enough ratings to have a score
            pass
        # numerical_stats is retrieved as such: ['stat 1', 23, 'stat 2', 3,134]
        try:
            numerical_stats = soup.find_all('div', class_='col-sm-6')[1].find_all('li')
            stat_keys = [x.text.replace(':', ' ').strip().replace(' ', '_').lower() for x in numerical_stats[::2]]
            stat_values = [x.text.strip().replace(',', '') for x in numerical_stats[1::2]]
        except:
            pass
        
        for idx, key in enumerate(stat_keys):
            self.novel_info[key] = stat_values[idx]

    def put_number_of_chapters(self, soup):
        chapter_count = soup.find('div', class_ = 'actions').text.strip()
        chapter_count = int(chapter_count.split()[0])
        self.novel_info['chapter_count'] = chapter_count


    def put_wordcount(self, soup):
        tag = soup.find('i', class_ = 'fal fa-question-circle popovers')
        text = tag.attrs['data-content']
        
        word_count = re.search(r'from (\d{1,3}(?:,\d{3})*|\d+) words', text).group(1)
        word_count = int(word_count.replace(',', ''))
        self.novel_info['word_count'] = word_count


    '''
    Testing it first
    '''
    def get_patreon_link(self, soup):
        tag = soup.find('i', class_ = 'fa fas fa-money-bill-wave')
        # Sometimes the author doesn't have donation options
        if tag is not None:
            target_tag = tag.find_next('div', class_ = 'dropdown-content')  # This is the tag with the links
            last_link_container = target_tag.find_all('a')[-1]      # In case there is patreon and paypal link, patreon is the last link
            link_href = last_link_container.attrs['href']
            if 'patreon' in link_href:
                return link_href
        else:
            return 'None' 

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