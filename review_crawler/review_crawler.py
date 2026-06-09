import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.base_crawler import BaseCrawler, WriteCounter
from core.interfaces import DatabaseHandler, Scraper
from database.novels_db import dbHandler
from review_crawler.review_scraper import RoyalRoadReviewScraper
from utils.custom_exceptions import NovelDeleted

class ReviewCrawler(BaseCrawler):
    def __init__(self, db_handler: DatabaseHandler = None, scraper: Scraper = None):
        db_handler = db_handler or dbHandler()
        super().__init__(db_handler)
        self.scraper = scraper or RoyalRoadReviewScraper()

    def crawl(self, batch_size: int = 50, max_workers: int = 5):
        """
        Process novels in the SQLite database, scrape URLs, and store results.
        
        Args:
            batch_size (int): Number of rows to fetch per batch.
            max_workers (int): Number of concurrent threads for scraping.
        """
        try:
            num_novels_no_reviews = self.db_handler.get_num_novels_no_reviews()
            self.logger.info(f"Total novels to process for reviews: {num_novels_no_reviews}")
            
            if num_novels_no_reviews == 0:
                return

            count_obj = WriteCounter()
            offset = -1
            counter = 0

            while counter < num_novels_no_reviews:
                rows = self.db_handler.get_novels_no_reviews(batch_size, offset)
                if not rows:
                    break

                offset = rows[-1][0]
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_id = {}
                    for novel_id, url in rows:
                        # Correctly submit the function and arguments to executor
                        future = executor.submit(self.scraper.scrape, url)
                        future.add_done_callback(count_obj.increment)
                        future_to_id[future] = novel_id
                        
                    for future in as_completed(future_to_id):    
                        novel_id = future_to_id[future]
                        try:
                            reviews = future.result()
                            self.db_handler.insert_reviews(novel_id, reviews)
                        except NovelDeleted:
                            self.logger.warning(f"Novel {novel_id} ({url}) has been deleted. Marking in DB.")
                            self.db_handler.set_novel_as_deleted(novel_id)
                        except Exception as e:
                            self.logger.error(f"Error processing novel_id {novel_id}: {e}")
                            
                counter += len(rows)
                self.logger.info(f"Processed {min(count_obj.value(), num_novels_no_reviews)} of {num_novels_no_reviews} novels")
        except Exception as e:
            self.logger.error(f"Crawling failed: {e}")
            import traceback
            traceback.print_exc()

        self.save()
