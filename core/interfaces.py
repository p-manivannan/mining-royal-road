from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

class HTTPClient(ABC):
    @abstractmethod
    def get(self, url: str) -> str:
        """Fetch URL and return text content."""
        pass

class Parser(ABC):
    @abstractmethod
    def parse(self, html: str, **kwargs) -> Any:
        """Parse HTML string and extract domain objects or dictionaries."""
        pass

class Scraper(ABC):
    @abstractmethod
    def scrape(self, url: str) -> Any:
        """Orchestrate downloading and parsing of a single URL."""
        pass

class DatabaseHandler(ABC):
    @abstractmethod
    def insert_name_and_url(self, column: Dict[str, str]) -> None:
        """Insert novel names and URLs."""
        pass

    @abstractmethod
    def get_num_novels_to_scrape(self) -> int:
        """Get the count of novels that haven't been scraped yet."""
        pass

    @abstractmethod
    def get_novels_to_scrape(self, limit: int, offset_id: int) -> List[Tuple[int, str]]:
        """Get a batch of novels to scrape details for."""
        pass

    @abstractmethod
    def insert_data(self, novel_id: int, dct: dict) -> None:
        """Update a novel with scraped details."""
        pass

    @abstractmethod
    def set_novel_as_deleted(self, novel_id: int) -> None:
        """Mark a novel as deleted in the database."""
        pass

    @abstractmethod
    def get_num_novels_no_reviews(self) -> int:
        """Get the count of novels that do not have reviews scraped yet."""
        pass

    @abstractmethod
    def get_novels_no_reviews(self, limit: int, offset_id: int) -> List[Tuple[int, str]]:
        """Get a batch of novels to scrape reviews for."""
        pass

    @abstractmethod
    def insert_reviews(self, novel_id: int, reviews: List[dict]) -> None:
        """Insert reviews for a novel and mark its reviews as obtained."""
        pass

class Crawler(ABC):
    @abstractmethod
    def crawl(self, *args, **kwargs) -> None:
        """Execute the crawling operation."""
        pass
