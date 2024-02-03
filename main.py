import requests
import pandas as pd
from bs4 import BeautifulSoup
from pprint import pprint
from functions import *
import novel_searcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation



'''
TO-DO:
- Add Star ratings to reviews
- Find best method of large dictionary storage: Database, pickle, csv, or shelve:
        1. CSV for long-term storage and sharing
        2. Shelve/alternative for loading into application fast
- Convert novel_collection to pandas dataframe
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
# reviews = load('raw_reviews', save_flag.pickle)
reviews = get_reviews(soup, novel_link)

# clean_reviews(reviews)

# # TF-IDF Vectorizer
# vect = TfidfVectorizer(max_features=1000)
# vect_text = vect.fit_transform(reviews)

# model = LatentDirichletAllocation(n_components=5, learning_method='online', random_state=42, max_iter=1)
# lda_top = model.fit_transform(vect_text)

# # Topic analysis
# vocab = vect.get_feature_names()
# for i, comp in enumerate(model.components_):
#     vocab_comp = zip(vocab, comp)
#     sorted_words = sorted(vocab_comp, lambda x:x[1], reverse=True)[:10]
#     print("Topic "+str(i)+": ")
#     for t in sorted_words:
#         print(t[0], end=" ")
#         print("n")


novel_collection = {
                    title : {
                            'author' : author,
                            'summary' : summary,
                            'statistics' : statistics,
                            'reviews': reviews,
                            'genres' : genres
                            }
                    }
                    
pprint(novel_collection)

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




