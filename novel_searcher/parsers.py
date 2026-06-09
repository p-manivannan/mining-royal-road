import re
from bs4 import BeautifulSoup
from bs4 import SoupStrainer as strainer
from typing import Dict, Any, List
from core.interfaces import Parser

class RoyalRoadCategoryParser(Parser):
    def __init__(self, base_url: str = "https://www.royalroad.com"):
        self.base_url = base_url

    def parse(self, html: str, **kwargs) -> Dict[str, str]:
        """
        Parses a category page and returns a dictionary mapping novel name to novel URL.
        """
        fiction_title_element = strainer('h2', attrs={"class": "fiction-title"})
        soup = BeautifulSoup(html, features='lxml', parse_only=fiction_title_element)
        novel_info = {}
        for novel in soup.find_all('a'):
            name = novel.text.strip()
            href = novel.attrs.get('href', '')
            if href:
                url = href if href.startswith('http') else self.base_url + href
                novel_info[name] = url
        return novel_info

class RoyalRoadNovelParser(Parser):
    def parse(self, html: str, **kwargs) -> dict:
        """
        Parses a single novel's main page to extract details.
        """
        soup = BeautifulSoup(html, features='lxml')
        novel_info = {}

        # Name
        try:
            novel_info['name'] = soup.title.string.strip() if soup.title else None
        except Exception:
            novel_info['name'] = None

        # Author
        try:
            container = soup.find('div', class_='row fic-header')
            if container:
                author_tag = container.find_next('a')
                novel_info['author'] = author_tag.text.strip() if author_tag else None
            else:
                novel_info['author'] = None
        except Exception:
            novel_info['author'] = None

        # Summary
        try:
            container = soup.find('div', class_='description')
            novel_info['summary'] = container.text.strip() if container else None
        except Exception:
            novel_info['summary'] = None

        # Tags
        try:
            container = soup.find('div', class_='fiction-info')
            if container:
                margin_div = container.find_next('div', class_='margin-bottom-10')
                if margin_div:
                    raw_tags = margin_div.text.strip().split('\n')
                    unwanted = {'', ' '}
                    novel_info['tags'] = [item.strip().lower() for item in raw_tags if item.strip() not in unwanted]
                else:
                    novel_info['tags'] = []
            else:
                novel_info['tags'] = []
        except Exception:
            novel_info['tags'] = []

        # Scores
        scores = ['overall_score', 'style_score', 'story_score', 'grammar_score', 'character_score']
        score_titles = ['Overall Score', 'Style Score', 'Story Score', 'Grammar Score', 'Character Score']
        for score_key, title in zip(scores, score_titles):
            try:
                tag = soup.find('span', {'data-original-title': title})
                if tag:
                    novel_info[score_key] = tag.get('data-content') or tag.attrs.get('data-content')
                else:
                    novel_info[score_key] = -1.0
            except Exception:
                novel_info[score_key] = -1.0

        # Numerical stats (views, ratings, favorites, etc.)
        # Usually format in Royal Road is: ['col-sm-6'][1] contains <li> elements with key/values
        try:
            cols = soup.find_all('div', class_='col-sm-6')
            if len(cols) > 1:
                numerical_stats = cols[1].find_all('li')
                stat_keys = [x.text.replace(':', ' ').strip().replace(' ', '_').lower() for x in numerical_stats[::2]]
                stat_values = [x.text.strip().replace(',', '') for x in numerical_stats[1::2]]
                for idx, key in enumerate(stat_keys):
                    # Map followers to favorites or vice-versa if appropriate, but let's keep original mapping
                    novel_info[key] = stat_values[idx]
        except Exception:
            pass

        # Adjust keys if needed (e.g. mapping 'followers' or 'favorites' to DB fields)
        # The DB expects 'favourites' and 'ratings'
        if 'favorites' in novel_info and 'favourites' not in novel_info:
            novel_info['favourites'] = novel_info['favorites']
        elif 'favourites' in novel_info and 'favorites' not in novel_info:
            novel_info['favorites'] = novel_info['favourites']

        # Chapter Count
        try:
            actions_div = soup.find('div', class_='actions')
            if actions_div:
                chapter_count = actions_div.text.strip()
                chapter_count = int(chapter_count.split()[0])
                novel_info['chapter_count'] = chapter_count
            else:
                novel_info['chapter_count'] = 0
        except Exception:
            novel_info['chapter_count'] = 0

        # Word Count
        try:
            tag = soup.find('i', class_='fal fa-question-circle popovers')
            if tag and 'data-content' in tag.attrs:
                text = tag.attrs['data-content']
                word_count_match = re.search(r'from (\d{1,3}(?:,\d{3})*|\d+) words', text)
                if word_count_match:
                    novel_info['word_count'] = int(word_count_match.group(1).replace(',', ''))
                else:
                    novel_info['word_count'] = 0
            else:
                novel_info['word_count'] = 0
        except Exception:
            novel_info['word_count'] = 0

        # Patreon Link
        novel_info['patreon_url'] = None
        try:
            tag = soup.find('i', class_='fa fas fa-money-bill-wave')
            if tag:
                target_tag = tag.find_next('div', class_='dropdown-content')
                if target_tag:
                    last_link_container = target_tag.find_all('a')[-1]
                    link_href = last_link_container.attrs.get('href', '')
                    if 'patreon' in link_href:
                        novel_info['patreon_url'] = link_href
        except Exception:
            pass

        return novel_info
