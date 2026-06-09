from core.interfaces import Scraper
from utils.custom_exceptions import NovelDeleted

def scrape_novel(url):
    from core.http_client import RequestsHTTPClient
    from novel_searcher.parsers import RoyalRoadNovelParser
    
    client = RequestsHTTPClient()
    parser = RoyalRoadNovelParser()
    scraper = NovelScraper(client, parser)
    return scraper.scrape(url)

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

    def scrape_novel_info(self):
        """Legacy compatibility method."""
        if self.page:
            self.novel_info = self.parser.parse(self.page)
            patreon_url = self.novel_info.get('patreon_url')
            if patreon_url and patreon_url != 'None':
                try:
                    from utils.patreon_scraper import scrape_patreon
                    patreon_info = scrape_patreon(patreon_url)
                    self.novel_info['patreon_lowest_tier'] = patreon_info.get('lowest_tier_price')
                    self.novel_info['patreon_highest_tier'] = patreon_info.get('highest_tier_price')
                    self.novel_info['patreon_subs'] = patreon_info.get('subscribers')
                    self.novel_info['patreon_name'] = patreon_info.get('name')
                except Exception:
                    pass

    def get_novel_info(self):
        """Legacy compatibility method."""
        if bool(self.novel_info):
            return self.novel_info
        if self.url is None:
            raise ValueError("No URL provided!")
        self.page = self.http_client.get(self.url)
        self.scrape_novel_info()
        return self.novel_info

        