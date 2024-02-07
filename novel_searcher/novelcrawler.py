import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer as strainer
from pprint import pprint
import regex as re
from sitecrawler import SiteCrawler

'''
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
    def init_request(self):
        return requests.get(self.url).text

    def get_title_author_summary(self, soup):
        title_and_author_container = soup.find('div', class_='col')
        title = title_and_author_container.text.split('by')[0].strip()
        author = title_and_author_container.text.split('by')[1].strip()
        summary = soup.find('div', class_='hidden-content').text.strip()
        return title, author, summary

    '''
    Returns a dict containing all relevant statistics in the fiction page
    '''
    def get_stats(self, soup):
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

        return stats
        
    '''
    Gets genres
    '''
    def get_genres(self, soup):
        genres = []
        status1 = soup.find('span', 'label label-default label-sm bg-blue-hoki')
        status2 = status1.find_next('span', 'label label-default label-sm bg-blue-hoki')
        tags = soup.find('span', 'tags')
        genres.extend([status1.text.strip().lower(), status2.text.strip().lower()])
        for tag in tags:
            text = tag.text.strip().replace(' ', '_').lower()
            if text != '':
                genres.append(text)
        
        return genres
        

    '''
    very slow T_T, gotta optimize...
    returns a list of dicts containing
    reviewers and their reviews
    Assumes URL is in form:
    https://royalroad.com/fiction/21220/mother-of-learning
    '''
    def get_reviews(self, soup, temp_url):
        m_url = temp_url + '?sorting=top&reviews='
        # RETRIEVE NUMBER OF REVIEW PAGES
        ul = soup.find('ul', class_='pagination justify-content-center').find_all('li')
        a = ul[-1].find('a')
        n_pages = int(a.attrs['data-page'])
        reviews = []

        for n in range(1, n_pages):
            # CREATE LINK TEXT
            review_url = m_url + str(n)
            page = requests.get(review_url).text
            soup = BeautifulSoup(page, features='lxml')
            # FIND THE REVIEW CONTAINER
            review_container = soup.find('div', class_='portlet light reviews')
            # LOOP THROUGH ALL REVIEWS
            for x in review_container.find_all('div', class_='review'):
                meta = x.find('div', class_ = 'review-meta')
                reviewer = meta.find_next('a').text.strip()
                review = x.find_next('div', class_='review-inner').text.strip()
                reviews.append({'author' : reviewer, 'review' : review})

        return reviews


    

    

# Testing
site_crawler = SiteCrawler()
name, url = site_crawler.search_novel('mother of learning')
novel_crawler = NovelCrawler(name, url)
    