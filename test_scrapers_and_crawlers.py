import os
import sqlite3
import unittest
from database.novels_db import dbHandler
from novel_searcher.categoryscraper import CategoryScraper
from novel_searcher.novelscraper import NovelScraper
from novel_searcher.novel_crawler import NovelCrawler
from review_crawler.review_scraper import RoyalRoadReviewScraper
from review_crawler.review_crawler import ReviewCrawler

class TestScrapersAndCrawlers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_name = "test_novels.db"
        # Remove if exists
        if os.path.exists(cls.db_name):
            os.remove(cls.db_name)
        cls.db = dbHandler(cls.db_name)

    @classmethod
    def tearDownClass(cls):
        # Clean up database file after test
        if cls.db:
            cls.db.conn.close()
        if os.path.exists(cls.db_name):
            try:
                os.remove(cls.db_name)
            except Exception:
                pass

    def test_1_category_scraper(self):
        print("\n--- Testing CategoryScraper (SiteCrawler) ---")
        # Initialize CategoryScraper with test database
        scraper = CategoryScraper(db_handler=self.db)
        # Rising star category only has 1 page, so crawl it
        scraper.crawl('rising', 1)
        
        # Verify database is populated
        self.db.cursor.execute("SELECT COUNT(*) FROM novels")
        count = self.db.cursor.fetchone()[0]
        print(f"Retrieved {count} novels from Rising Stars category page.")
        self.assertGreater(count, 0, "No novels were crawled.")

    def test_2_novel_scraper_single(self):
        print("\n--- Testing NovelScraper Single Page ---")
        url = "https://www.royalroad.com/fiction/21220/mother-of-learning"
        scraper = NovelScraper()
        info = scraper.scrape(url)
        
        print(f"Scraped Novel Name: {info.get('name')}")
        print(f"Scraped Author: {info.get('author')}")
        print(f"Word Count: {info.get('word_count')}")
        print(f"Chapter Count: {info.get('chapter_count')}")
        print(f"Patreon URL: {info.get('patreon_url')}")
        print(f"Patreon Name: {info.get('patreon_name')}")
        print(f"Patreon Lowest Tier: {info.get('patreon_lowest_tier')}")

        self.assertIsNotNone(info.get('name'))
        self.assertIn("Mother of Learning", info.get('name'))
        self.assertEqual(info.get('author'), "nobody103")
        self.assertGreater(info.get('word_count', 0), 100000)
        self.assertGreater(info.get('chapter_count', 0), 100)

    def test_3_novel_crawler(self):
        print("\n--- Testing NovelCrawler (Details Crawler) ---")
        crawler = NovelCrawler(db_handler=self.db)
        # Crawl details of first 2 novels in db
        crawler.crawl(batch_size=2, max_workers=2)
        
        # Verify that these 2 are marked as scraped
        self.db.cursor.execute("SELECT COUNT(*) FROM novels WHERE is_scraped = 1")
        scraped_count = self.db.cursor.fetchone()[0]
        print(f"Successfully scraped details for {scraped_count} novels via NovelCrawler.")
        self.assertGreater(scraped_count, 0)

    def test_4_review_scraper_single(self):
        print("\n--- Testing ReviewScraper Single Page ---")
        url = "https://www.royalroad.com/fiction/21220/mother-of-learning"
        scraper = RoyalRoadReviewScraper()
        reviews = scraper.scrape(url)
        
        print(f"Scraped {len(reviews)} reviews for Mother of Learning.")
        self.assertGreater(len(reviews), 0)
        first = reviews[0]
        print(f"Sample review - Author: {first.get('author')}, Score: {first.get('score')}")
        self.assertIsNotNone(first.get('author'))
        self.assertIsNotNone(first.get('review'))
        self.assertIsNotNone(first.get('score'))

    def test_5_review_crawler(self):
        print("\n--- Testing ReviewCrawler ---")
        crawler = ReviewCrawler(db_handler=self.db)
        # Process reviews for 1 novel
        crawler.crawl(batch_size=1, max_workers=1)
        
        # Verify reviews are populated in DB
        self.db.cursor.execute("SELECT COUNT(*) FROM reviews")
        reviews_count = self.db.cursor.fetchone()[0]
        print(f"Saved {reviews_count} reviews into the database via ReviewCrawler.")
        self.assertGreater(reviews_count, 0)
        
        self.db.cursor.execute("SELECT COUNT(*) FROM novels WHERE are_reviews_obtained = 1")
        obtained_count = self.db.cursor.fetchone()[0]
        self.assertGreater(obtained_count, 0)

if __name__ == "__main__":
    unittest.main()
