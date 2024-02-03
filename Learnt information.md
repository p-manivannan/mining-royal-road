# What I learnt
- Xpath: It is a format used to describe the location of any element on a webpage. Note that the actual HTML isn't coded in the Xpath.
- Python's request library can't handle dynamic webpages. This is why Selenium is used

## BeautifulSoup 4
- When given a link which is then souped and given an element <h2 class="fiction-title"> which has only a single child element <a href="/fiction/21220/mother-of-learning" class="font-red-sunglo bold">Mother of Learning</a> , soup.find('h2', class_='fiction-title') selects only the component and not all of it's children. find_next('a').atrrs.keys() returns 'href' and 'class' which correspond to the link and font-red-sunglo-bold, while the text is accessed by find_next('a').text which gives Mother of Learning