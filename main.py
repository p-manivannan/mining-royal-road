from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# Uncomment if Chrome driver does not exist, or is installed in the wrong path
driver = webdriver.Chrome(ChromeDriverManager().install())

novel_link = 'https://www.royalroad.com/fiction/21220/mother-of-learning'

driver.get(novel_link)
content = driver.page_source
soup = BeautifulSoup(content)
print(soup)

# Returns some install error

