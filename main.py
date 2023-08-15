import requests
import pandas as pd
from bs4 import BeautifulSoup
from functions import *
# import spacy 

# nlp = spacy.load("en_core_web_lg")

'''
TO-DO:
1. Get summary
2. Get ALL reviews
3. Convert novel_collection to pandas dataframe
'''

novel_link = 'https://www.royalroad.com/fiction/21220/mother-of-learning'

page = requests.get(novel_link).text
page = bs_preprocess(page)
soup = BeautifulSoup(page, features='lxml')
title, author = get_title_and_author(soup)
statistics = get_stats(soup)
genres = get_genres(soup)

results = soup.find_all('div', class_='review-inner')
novel_collection = {
                    title : {
                            'author' : author,
                            'summary' : '',
                            'statistics' : statistics,
                            'reviews': {},
                            'genres' : genres
                            }
                    }

print(novel_collection)

# Getting all reviews


'''
PIPELINE: 
1. Get all reviews
2. Put reviews in pandas dataframe
3. Pre-process text
4. Perform analysis (topic modelling/GPT/etc.)
'''


'''
There's something in the review text in the html called '&nbsp;'.
It most likely functions like <br> in the text
'''




