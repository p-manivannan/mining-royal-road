import os
import sqlite3
import unittest
from unittest.mock import Mock, patch
from database.novels_db import dbHandler
from novel_searcher.categoryscraper import CategoryScraper
from novel_searcher.novelscraper import NovelScraper
from novel_searcher.novel_crawler import NovelCrawler
from review_crawler.review_scraper import RoyalRoadReviewScraper
from review_crawler.review_crawler import ReviewCrawler
from utils.custom_exceptions import NovelDeleted

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

    def test_6_deleted_novel_detection_in_scraper(self):
        print("\n--- Testing Deleted Novel Detection in ReviewScraper ---")
        # Test with mocked HTML that simulates a deleted novel page
        deleted_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 Page not found - Royal Road</title>
        </head>
        <body>
            <h1>This fiction has been deleted</h1>
        </body>
        </html>
        """
        
        scraper = RoyalRoadReviewScraper()
        mock_client = Mock()
        mock_client.get.return_value = deleted_html
        scraper.http_client = mock_client
        
        # Should raise NovelDeleted exception
        with self.assertRaises(NovelDeleted):
            scraper.scrape("https://www.royalroad.com/fiction/127411/test")
        print("Correctly detected deleted novel and raised NovelDeleted exception")

    def test_7_review_crawler_handles_deleted_novels(self):
        print("\n--- Testing ReviewCrawler Handles Deleted Novels ---")
        # Insert a test novel into the database
        test_url = "http://example.com/test-novel"
        self.db.cursor.execute(
            "INSERT OR IGNORE INTO novels (novel_name, novel_url, is_scraped, are_reviews_obtained, is_deleted) VALUES (?, ?, 1, 0, 0)",
            ("Test Novel", test_url)
        )
        self.db.save()
        
        # Get the novel_id
        self.db.cursor.execute("SELECT novel_id FROM novels WHERE novel_url = ?", (test_url,))
        result = self.db.cursor.fetchone()
        self.assertIsNotNone(result)
        novel_id = result[0]
        
        # Create a mock scraper that raises NovelDeleted
        mock_scraper = Mock(spec=RoyalRoadReviewScraper)
        mock_scraper.scrape.side_effect = NovelDeleted()
        
        # Run review crawler with mock scraper
        crawler = ReviewCrawler(db_handler=self.db, scraper=mock_scraper)
        crawler.crawl(batch_size=10, max_workers=1)
        
        # Verify the novel is now marked as deleted
        self.db.cursor.execute("SELECT is_deleted FROM novels WHERE novel_id = ?", (novel_id,))
        is_deleted = self.db.cursor.fetchone()[0]
        self.assertEqual(is_deleted, 1, "Novel should be marked as deleted")
        print(f"Successfully marked novel {novel_id} as deleted")

    def test_8_filtering_excludes_deleted_novels(self):
        print("\n--- Testing Filtering Excludes Deleted Novels ---")
        # Insert some test data
        self.db.cursor.execute(
            "INSERT OR IGNORE INTO novels (novel_name, novel_url, is_scraped, is_deleted) VALUES (?, ?, 0, 0)",
            ("Active Novel 1", "http://example.com/active1")
        )
        self.db.cursor.execute(
            "INSERT OR IGNORE INTO novels (novel_name, novel_url, is_scraped, is_deleted) VALUES (?, ?, 0, 1)",
            ("Deleted Novel 1", "http://example.com/deleted1")
        )
        self.db.cursor.execute(
            "INSERT OR IGNORE INTO novels (novel_name, novel_url, is_scraped, is_deleted) VALUES (?, ?, 1, 0)",
            ("Active Novel 2", "http://example.com/active2")
        )
        self.db.cursor.execute(
            "INSERT OR IGNORE INTO novels (novel_name, novel_url, is_scraped, is_deleted) VALUES (?, ?, 1, 1)",
            ("Deleted Novel 2", "http://example.com/deleted2")
        )
        self.db.save()
        
        # Test get_novels_to_scrape - should not include deleted novels
        novels_to_scrape = self.db.get_novels_to_scrape(limit=100, offset_id=-1)
        for novel_id, url in novels_to_scrape:
            self.db.cursor.execute("SELECT is_deleted FROM novels WHERE novel_id = ?", (novel_id,))
            is_deleted = self.db.cursor.fetchone()[0]
            self.assertEqual(is_deleted, 0, f"Novel {novel_id} should not be deleted")
        print(f"get_novels_to_scrape correctly excludes deleted novels (found {len(novels_to_scrape)} active novels)")
        
        # Test get_num_novels_to_scrape
        num_to_scrape = self.db.get_num_novels_to_scrape()
        self.db.cursor.execute("SELECT COUNT(*) FROM novels WHERE is_scraped = 0 AND is_deleted = 0")
        expected_count = self.db.cursor.fetchone()[0]
        self.assertEqual(num_to_scrape, expected_count, "Count should exclude deleted novels")
        print(f"get_num_novels_to_scrape correctly returns {num_to_scrape} (excluding deleted)")
        
        # Test get_novels_no_reviews - should not include deleted novels
        novels_no_reviews = self.db.get_novels_no_reviews(limit=100, offset_id=-1)
        for novel_id, url in novels_no_reviews:
            self.db.cursor.execute("SELECT is_deleted FROM novels WHERE novel_id = ?", (novel_id,))
            is_deleted = self.db.cursor.fetchone()[0]
            self.assertEqual(is_deleted, 0, f"Novel {novel_id} should not be deleted")
        print(f"get_novels_no_reviews correctly excludes deleted novels (found {len(novels_no_reviews)} active novels)")
        
        # Test get_num_novels_no_reviews
        num_no_reviews = self.db.get_num_novels_no_reviews()
        self.db.cursor.execute("SELECT COUNT(*) FROM novels WHERE are_reviews_obtained = 0 AND is_deleted = 0")
        expected_count = self.db.cursor.fetchone()[0]
        self.assertEqual(num_no_reviews, expected_count, "Count should exclude deleted novels")
        print(f"get_num_novels_no_reviews correctly returns {num_no_reviews} (excluding deleted)")

    def test_9_cleanup_deleted_novels(self):
        print("\n--- Testing Cleanup of Deleted Novels ---")
        # Insert a known deleted novel with mock HTML
        deleted_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 Page not found - Royal Road</title>
        </head>
        <body>
            <h1>This fiction has been deleted</h1>
        </body>
        </html>
        """
        
        deleted_url = "http://example.com/deleted-novel"
        self.db.cursor.execute(
            "INSERT OR IGNORE INTO novels (novel_name, novel_url, is_scraped, is_deleted) VALUES (?, ?, 0, 0)",
            ("To Be Cleaned", deleted_url)
        )
        self.db.save()
        
        # Get novel_id before cleanup
        self.db.cursor.execute("SELECT novel_id FROM novels WHERE novel_url = ?", (deleted_url,))
        result = self.db.cursor.fetchone()
        self.assertIsNotNone(result)
        novel_id = result[0]
        
        # Create mock HTTP client that returns deleted page HTML
        mock_client = Mock()
        mock_client.get.return_value = deleted_html
        
        # Run cleanup with mock client
        checked, deleted = self.db.cleanup_deleted_novels(http_client=mock_client)
        
        # Verify the novel was permanently deleted
        self.db.cursor.execute("SELECT COUNT(*) FROM novels WHERE novel_id = ?", (novel_id,))
        count = self.db.cursor.fetchone()[0]
        self.assertEqual(count, 0, "Novel should be permanently deleted")
        print(f"Cleanup successfully permanently deleted novel {novel_id}")
        print(f"Cleanup checked {checked} novels and permanently deleted {deleted}")


if __name__ == "__main__":
    unittest.main()
