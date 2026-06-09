import requests
import logging
from core.interfaces import HTTPClient

class RequestsHTTPClient(HTTPClient):
    def __init__(self, headers: dict = None, timeout: int = 15):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.timeout = timeout
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get(self, url: str) -> str:
        try:
            self.logger.info(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            # Return HTML even for error status codes (like 404 custom pages)
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Error fetching URL {url}: {e}")
            raise e
