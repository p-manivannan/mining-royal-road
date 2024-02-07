import regex as re
import requests
from bs4 import BeautifulSoup
from pprint import pprint
from enum import Enum
import pickle
from string import punctuation
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer  
from sklearn.feature_extraction.text import TfidfVectorizer


stop_words = set(nltk.corpus.stopwords.words('english'))
punctuation = list(punctuation)
'''
the following function was obtained from user svenwildermann on stackoverflow:
https://stackoverflow.com/questions/23241641/how-to-ignore-empty-lines-while-using-next-sibling-in-beautifulsoup4-in-python
'''
def bs_preprocess(html):
    """remove distracting whitespaces and newline characters"""
    pat = re.compile('(^[\s]+)|([\s]+$)', re.MULTILINE)
    html = re.sub(pat, '', html)       # remove leading and trailing whitespaces
    html = re.sub('\n', ' ', html)     # convert newlines to spaces
                                    # this preserves newline delimiters
    html = re.sub('[\s]+<', '<', html) # remove whitespaces before opening tags
    html = re.sub('>[\s]+', '>', html) # remove whitespaces after closing tags
    return html 

'''
Tokenizes text, lemmatises, removes stop words and punctuation
'''
def tokenizer(text):
    l = WordNetLemmatizer()
    words = nltk.word_tokenize(text)
    tokens = [l.lemmatize(w) for w in words if w not in stop_words and w not in punctuation]
    return tokens

def clean_reviews(reviews):
    '''
    1. Tokenize  
    2. Remove punctuation and stop words
    3. Lemmatize
    '''
    for item in reviews:
        review = item['review']
        # Remove \n and &nbsp tags from text
        review = review.replace('\n', '').replace('&nbsp', '')
        # Lowercase
        review = review.lower()
        item['review'] = tokenizer(review)






