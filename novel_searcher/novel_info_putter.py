from bs4 import BeautifulSoup


"""Parses a BeautifulSoup object and puts relevant Novel Info"""
class NovelInfoPutter:
    def __init__(self):
        self.novel_info = {}

    def put_info(self, soup: BeautifulSoup):
        self.put_name()
        # If put author fails, then find the reason for it and raise exception. Only two cases:
        # 404 Novel deleted. Or RoyalRoad refusing connection.
        try:
            self.put_author(soup)
        except:
            self.__check_exceptions(soup)
            
        self.put_summary(soup)
        self.put_tags(soup)
        self.put_stats(soup)
        self.put_number_of_chapters(soup)
        self.put_wordcount(soup)
        self.put_patreon_link(soup)

    def put_name(self):
        '''
        Puts novel name in novel_info as 'novel_name'
        '''
        self.novel_info['novel_name'] = self.name if self.name is not None else None

    def put_author(self, soup):
        '''
        Puts author in novel_info
        '''
        container = soup.find('div', class_='row fic-header').find_next('a')    # Author container
        self.novel_info['author'] = container.text.strip()

    def put_summary(self, soup):
        '''
        Puts summary in novel_info
        '''
        container = soup.find('div', class_='description')
        self.novel_info['summary'] = container.text.strip()
        
    def put_tags(self, soup):
        '''
        Puts tags in novel_info
        '''
        container = soup.find('div', class_='fiction-info').find_next('div', class_='margin-bottom-10').text.strip().split('\n')
        unwanted = {'', ' '}
        # Convert tags to lower case in case they change it up later
        self.novel_info['tags'] = [item.strip().lower() for item in container if item.strip() not in unwanted]

    def put_stats(self, soup):
        stats = {}
        # The following stats can be empty for novels which don't have enough reviews
        try:
            stats['overall_score'] = soup.find('span', {'data-original-title': 'Overall Score'})['data-content']
            stats['style_score'] = soup.find('span', {'data-original-title': 'Style Score'}).attrs['data-content']
            stats['story_score'] = soup.find('span', {'data-original-title': 'Story Score'}).attrs['data-content']
            stats['grammar_score'] = soup.find('span', {'data-original-title': 'Grammar Score'}).attrs['data-content']
            stats['character_score'] = soup.find('span', {'data-original-title': 'Character Score'}).attrs['data-content']

            for key, value in stats.items():
                self.novel_info[key] = value
        
        # Relevant info is in the second list element ('li') on the page
        except:
            # If you reach here, then the novel hasn't received enough ratings to have a score
            pass
        # numerical_stats is retrieved as such: ['stat 1', 23, 'stat 2', 3,134]
        try:
            numerical_stats = soup.find_all('div', class_='col-sm-6')[1].find_all('li')
            stat_keys = [x.text.replace(':', ' ').strip().replace(' ', '_').lower() for x in numerical_stats[::2]]
            stat_values = [x.text.strip().replace(',', '') for x in numerical_stats[1::2]]
        except:
            pass
        
        for idx, key in enumerate(stat_keys):
            self.novel_info[key] = stat_values[idx]


    def put_number_of_chapters(self, soup):
        chapter_count = soup.find('div', class_ = 'actions').text.strip()
        chapter_count = int(chapter_count.split()[0])
        self.novel_info['chapter_count'] = chapter_count


    def put_wordcount(self, soup):
        tag = soup.find('i', class_ = 'fal fa-question-circle popovers')
        text = tag.attrs['data-content']
        
        word_count = re.search(r'from (\d{1,3}(?:,\d{3})*|\d+) words', text).group(1)
        word_count = int(word_count.replace(',', ''))
        self.novel_info['word_count'] = word_count


    def put_patreon_link(self, soup):
        self.novel_info['patreon_url'] = None
        try:
            tag = soup.find('i', class_ = 'fa fas fa-money-bill-wave')
            # Sometimes the author doesn't have donation options
            if tag is not None:
                target_tag = tag.find_next('div', class_ = 'dropdown-content')  # This is the tag with the links
                last_link_container = target_tag.find_all('a')[-1]      # In case there is patreon and paypal link, patreon is the last link
                link_href = last_link_container.attrs['href']
                if 'patreon' in link_href:
                    self.novel_info['patreon_url'] = link_href
            else:
                return
        except:
            raise AttributeError("Something wrong with Patreon Link")

    def retrieve_patreon_info(self, link=None):
        pass

    def get_info(self):
        return self.novel_info
