import logging
import time
from concurrent.futures import ThreadPoolExecutor
from core.base_crawler import BaseCrawler, WriteCounter
from core.interfaces import DatabaseHandler, Scraper
from database.novels_db import dbHandler
from novel_searcher.novelscraper import NovelScraper
from utils.custom_exceptions import NovelDeleted

class NovelCrawler(BaseCrawler):
    def __init__(self, db_handler: DatabaseHandler = None, scraper: Scraper = None):
        db_handler = db_handler or dbHandler()
        super().__init__(db_handler)
        self.scraper = scraper or NovelScraper()

    def crawl(self, batch_size: int = 50, max_workers: int = 5):
        """
        Retrieves novel URLs from the database, scrapes detailed metadata concurrently,
        and saves results to the database.
        """
        try:
            num_novels_to_scrape = self.db_handler.get_num_novels_to_scrape()
            self.logger.info(f"Total novels to process: {num_novels_to_scrape}")
            
            if num_novels_to_scrape == 0:
                return

            count_obj = WriteCounter()
            offset = -1
            counter = 0

            while counter < num_novels_to_scrape:
                rows = self.db_handler.get_novels_to_scrape(batch_size, offset)
                if not rows:
                    break

                offset = rows[-1][0]
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_info = []
                    for novel_id, url in rows:
                        # Submit scraping task asynchronously
                        future = executor.submit(self.scraper.scrape, url)
                        future.add_done_callback(count_obj.increment)
                        future_to_info.append((novel_id, future, url))
                    
                    for novel_id, future, url in future_to_info:
                        try:
                            dct = future.result()
                            self.db_handler.insert_data(novel_id, dct)
                        except NovelDeleted:
                            self.logger.warning(f"Novel {novel_id} ({url}) has been deleted. Marking in DB.")
                            self.db_handler.set_novel_as_deleted(novel_id)
                        except AttributeError:
                            # Retry once after brief pause
                            time.sleep(3)
                            try:
                                self.logger.info(f"Retrying scraping for novel {novel_id} ({url})")
                                dct = self.scraper.scrape(url)
                                self.db_handler.insert_data(novel_id, dct)
                            except Exception as ex:
                                self.logger.error(f"Error processing novel {novel_id} on retry: {ex}")
                        except Exception as ex:
                            self.logger.error(f"Unexpected error processing novel {novel_id}: {ex}")

                self.save()
                counter += len(rows)
                self.logger.info(f"Processed {min(count_obj.value(), num_novels_to_scrape)} of {num_novels_to_scrape} novels")
        except Exception as e:
            self.logger.error(f"Crawling failed: {e}")
            import traceback
            traceback.print_exc()
