from core.interfaces import Scraper
from typing import List, Dict, Any

def scrape_reviews(url: str) -> List[Dict[str, Any]]:
    from core.http_client import RequestsHTTPClient
    from review_crawler.parsers import RoyalRoadReviewParser
    
    client = RequestsHTTPClient()
    parser = RoyalRoadReviewParser()
    scraper = RoyalRoadReviewScraper(client, parser)
    return scraper.scrape(url)

class RoyalRoadReviewScraper(Scraper):
    def __init__(self, http_client=None, parser=None):
        from core.http_client import RequestsHTTPClient
        from review_crawler.parsers import RoyalRoadReviewParser
        
        self.http_client = http_client or RequestsHTTPClient()
        self.parser = parser or RoyalRoadReviewParser()

    def scrape(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrapes all reviews for a given novel URL page-by-page.
        """
        # First page contains the initial reviews and pagination info
        html = self.http_client.get(url)
        if not html:
            return []
            
        reviews = self.parser.parse(html)
        num_pages = self.parser.parse_num_pages(html)
        
        if num_pages > 1:
            base_review_url = url.rstrip('/') + '?sorting=top&reviews='
            for page in range(2, num_pages + 1):
                try:
                    page_url = f"{base_review_url}{page}"
                    page_html = self.http_client.get(page_url)
                    if page_html:
                        page_reviews = self.parser.parse(page_html)
                        reviews.extend(page_reviews)
                except Exception:
                    # If one page fails, continue scraping the others
                    continue
                    
        return reviews