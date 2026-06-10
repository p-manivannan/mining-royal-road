from core.interfaces import Scraper
from core.custom_exceptions import NovelDeleted


class NovelScraper(Scraper):
    def __init__(self, http_client=None, parser=None, url=None):
        from core.http_client import RequestsHTTPClient
        from novel_searcher.parsers import RoyalRoadNovelParser
        
        self.http_client = http_client or RequestsHTTPClient()
        self.parser = parser or RoyalRoadNovelParser()
        self.url = url
        self.novel_info = {}
        self.page = None

    def scrape(self, url: str) -> dict:
        """
        Orchestrate downloading and parsing of a single novel URL,
        including fallback Patreon retrieval.
        """
        html = self.http_client.get(url)
        if not html:
            raise AttributeError("Page empty")
            
        # Check for deleted/not found title
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip().lower()
            if "not found" in title_text:
                raise NovelDeleted()
        else:
            raise AttributeError("Page empty")

        # Parse novel details from main page
        info = self.parser.parse(html)
        
        # Retrieve Patreon metrics if applicable
        patreon_url = info.get('patreon_url')
        if patreon_url and patreon_url != 'None':
            try:
                from utils.patreon_scraper import scrape_patreon
                patreon_info = scrape_patreon(patreon_url)
                info['patreon_lowest_tier'] = patreon_info.get('lowest_tier_price')
                info['patreon_highest_tier'] = patreon_info.get('highest_tier_price')
                info['patreon_subs'] = patreon_info.get('subscribers')
                info['patreon_name'] = patreon_info.get('name')
            except Exception:
                info['patreon_lowest_tier'] = None
                info['patreon_highest_tier'] = None
                info['patreon_subs'] = None
                info['patreon_name'] = None
        else:
            info['patreon_lowest_tier'] = None
            info['patreon_highest_tier'] = None
            info['patreon_subs'] = None
            info['patreon_name'] = None

        return info


        