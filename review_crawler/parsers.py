from bs4 import BeautifulSoup
from typing import List, Dict, Any
from core.interfaces import Parser

class RoyalRoadReviewParser(Parser):
    def parse(self, html: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses a reviews page HTML and returns a list of dictionaries,
        each containing reviewer name, review content, and overall score.
        """
        soup = BeautifulSoup(html, features='lxml')
        reviews = []
        
        # Find review container
        review_container = soup.find('div', class_='portlet light reviews')
        if not review_container:
            return reviews
            
        for x in review_container.find_all('div', class_='review'):
            try:
                # Find reviewer name
                meta = x.find('div', class_='review-meta')
                reviewer = None
                if meta:
                    a_tag = meta.find_next('a')
                    if a_tag:
                        reviewer = a_tag.text.strip()
                
                # Find review content
                inner = x.find_next('div', class_='review-inner')
                review_content = inner.text.strip() if inner else ""
                
                # Find score
                score_meta = x.find('div', {'aria-label': 'Overall Score'})
                overall_score = 0.0
                if score_meta:
                    target = score_meta.find_next_sibling('div')
                    if target and 'aria-label' in target.attrs:
                        overall_score = float(target.attrs['aria-label'].split(' ')[0])
                
                if reviewer:
                    reviews.append({
                        'author': reviewer,
                        'review': review_content,
                        'score': overall_score
                    })
            except Exception:
                # Skip any malformed single review
                continue
                
        return reviews

    def parse_num_pages(self, html: str) -> int:
        """
        Parses pagination to find total pages. Returns 1 if no pagination is found.
        """
        soup = BeautifulSoup(html, features='lxml')
        try:
            pagination_ul = soup.find('ul', class_='pagination justify-content-center')
            if pagination_ul:
                li_tags = pagination_ul.find_all('li')
                if li_tags:
                    last_a = li_tags[-1].find('a')
                    if last_a and 'data-page' in last_a.attrs:
                        return int(last_a.attrs['data-page'])
            return 1
        except Exception:
            return 1
