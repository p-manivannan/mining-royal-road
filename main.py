from selenium import webdriver
import requests
import pandas as pd
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time

# Download the correct chromedriver (if using chrome. For other browsers, use relevant driver) and place in path
# driver = webdriver.Chrome(r"C:\Users\pithw\Desktop\University\1_PERSONAL PROJECTS\chromedriver")

novel_link = 'https://www.royalroad.com/fiction/21220/mother-of-learning'

# driver.get(novel_link)
# for review_element in driver.find_elements_by_class_name("review-inner"):
#     print(review_element)

page = requests.get(novel_link).text
soup = BeautifulSoup(page, features='lxml')
results = soup.find_all('div', class_='review-inner')
reviews = {}
reviews['review'] = []

for i in results:
    reviews['review'].append(i.text)




'''
BeautifulSoup can't access reviews just be getting the driver 
page source without modifications.

There's something in the review text in the html called '&nbsp;'.
It most likely functions like <br> in the text
'''




