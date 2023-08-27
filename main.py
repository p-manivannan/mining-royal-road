import requests
import pandas as pd
from bs4 import BeautifulSoup
from functions import *
# import spacy 

# nlp = spacy.load("en_core_web_lg")

'''
TO-DO:
- Find best method of large dictionary storage: Database, pickle, csv, or shelve:
        1. CSV for long-term storage and sharing
        2. Shelve/alternative for loading into application fast
- Implement save/load of novel_collection object
- Convert novel_collection to pandas dataframe
- Pre-process review texts (maybe during retrieval?)
- Perform the analysis
- Implement search function for novels
'''

novel_link = 'https://www.royalroad.com/fiction/21220/mother-of-learning'

page = requests.get(novel_link).text
page = bs_preprocess(page)
soup = BeautifulSoup(page, features='lxml')
title, author, summary = get_title_author_summary(soup)
statistics = get_stats(soup)
genres = get_genres(soup)
reviews = load('raw_reviews', save_flag.pickle)

clean_reviews(reviews)

# novel_collection = {
#                     title : {
#                             'author' : author,
#                             'summary' : summary,
#                             'statistics' : statistics,
#                             'reviews': reviews,
#                             'genres' : genres
#                             }
#                     }
                    

# save(novel_collection, title.lower().replace(' ', '_'), save_flag.pickle)


# Getting all reviews


'''
PIPELINE: 
1. Get all reviews
2. Put reviews in pandas dataframe
3. Pre-process text
4. Perform analysis (topic modelling/GPT/etc.)0
'''


'''
There's something in the review text in the html called '&nbsp;'.
It most likely functions like <br> in the text
'''




