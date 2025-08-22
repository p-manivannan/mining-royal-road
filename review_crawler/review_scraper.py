import requests
from bs4 import BeautifulSoup
from pprint import pprint
import time

'''
Methods to scrape a single novel's reviews.
I've made it functional instead of a class
so that I can use Threads 
'''

'''
Opens connection to a novel page
'''
def init_request(link):
    if link is not None:
        return requests.get(link).text
    else:
        ValueError("Link is none!")


'''
Pass this function to ThreadPoolExecutor
'''
def scrape_reviews(url):
    page = init_request(url)
    soup = BeautifulSoup(page, features='lxml')
    return put_reviews(url, soup)

def put_reviews(url, soup):
    temp_url = url + '?sorting=top&reviews='
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
            # Find score
            meta = x.find('div', {'aria-label' : 'Overall Score'})
            target = meta.find_next_sibling('div')
            overall_score = float(target.attrs['aria-label'].split(' ')[0])
            reviews.append({'author' : reviewer, 'review' : review, 'score' : overall_score})

    return reviews