from core.base_crawler import BaseCrawler
from database.novels_db import dbHandler
from core.http_client import RequestsHTTPClient
from novel_searcher.parsers import RoyalRoadCategoryParser

class CategoryScraper(BaseCrawler):
    def __init__(self, db_handler=None, http_client=None, parser=None):
        db_handler = db_handler or dbHandler()
        super().__init__(db_handler)
        
        self.http_client = http_client or RequestsHTTPClient()
        self.parser = parser or RoyalRoadCategoryParser()
        self.novel_info = {}
        
        self.categories = {
            'best': 'https://www.royalroad.com/fictions/best-rated',
            'trending': 'https://www.royalroad.com/fictions/trending',
            'active': 'https://www.royalroad.com/fictions/active-popular',
            'complete': 'https://www.royalroad.com/fictions/complete',
            'weekly': 'https://www.royalroad.com/fictions/weekly-popular',
            'latest': 'https://www.royalroad.com/fictions/latest-updates',
            'new': 'https://www.royalroad.com/fictions/new',
            'rising': 'https://www.royalroad.com/fictions/rising-stars'
        }

    def get_royalroad_link(self):
        return 'https://www.royalroad.com'

    def get_category_link(self, cat):
        category_str = cat.split()[0].strip().lower()
        if category_str in self.categories:
            return self.categories[category_str]
        else:
            self.logger.warning(f'Your category, "{cat}" was not found!')
            return None

    def get_novel_url_and_name(self, page_html):
        """
        Extract name and URL of the first novel in the provided page.
        """
        res = self.parser.parse(page_html)
        if not res:
            print('No results were found matching criteria!')
            return None
        first_name = list(res.keys())[0]
        return first_name, res[first_name]

    def search_novel(self, name):
        """
        Search for a novel on Royal Road by its name.
        """
        link = self.get_royalroad_link() + '/fictions/search?title='
        link += name.replace(' ', '+')
        try:
            page_html = self.http_client.get(link)
            return self.get_novel_url_and_name(page_html)
        except Exception as e:
            self.logger.error(f"Search for '{name}' failed: {e}")
            return None

    def start(self, category, pages):
        """Legacy entrypoint mapping directly to crawl."""
        self.crawl(category, pages)

    def crawl(self, category, pages):
        """
        Crawls pages of a given category and extracts novel URLs.
        """
        self.novel_info = {}
        for n in range(1, pages + 1):
            if n == 1:
                link = self.get_category_link(category)
                if not link:
                    break
                print(link)
                # Rising stars only has 1 page
                if 'rising' in link:
                    self.crawl_page(link)
                    break
            else:
                base_link = self.get_category_link(category)
                if not base_link:
                    break
                link = f"{base_link}?page={n}"

            if link:
                self.crawl_page(link)

        self.save()

    def crawl_page(self, link):
        try:
            page_html = self.http_client.get(link)
            parsed_data = self.parser.parse(page_html)
            self.novel_info.update(parsed_data)
        except Exception as e:
            self.logger.error(f"Failed crawling page {link}: {e}")

    def save(self):
        self.db_handler.insert_name_and_url(self.novel_info)




