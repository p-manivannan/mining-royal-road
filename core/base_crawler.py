import logging
import itertools
import threading
from abc import abstractmethod
from core.interfaces import Crawler, DatabaseHandler

class WriteCounter:
    """Threadsafe progress counter."""
    def __init__(self):
        self._number_of_read = 0
        self._counter = itertools.count()
        self._read_lock = threading.Lock()

    def increment(self, future=None):
        next(self._counter)

    def value(self):
        with self._read_lock:
            # We subtract the reads to get the current count cleanly
            value = next(self._counter) - self._number_of_read
            self._number_of_read += 1
        return value

class BaseCrawler(Crawler):
    def __init__(self, db_handler: DatabaseHandler, db_name: str = 'novels.db'):
        self.logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        self.db_name = db_name
        self.db_handler = db_handler

    def save(self):
        if hasattr(self.db_handler, 'save'):
            self.db_handler.save()

    @abstractmethod
    def crawl(self, *args, **kwargs) -> None:
        """To be implemented by specific subclasses."""
        pass
