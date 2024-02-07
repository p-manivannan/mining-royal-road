import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer as strainer
from pprint import pprint
import regex as re

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
    def __init__(self):
        self.novel_info = {}

    