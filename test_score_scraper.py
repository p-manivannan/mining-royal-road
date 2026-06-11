"""
Unit Tests for Score Updater Module.

These tests ensure that the score updater functionality works correctly
and does not damage the database. They use a separate test database file
that is created and destroyed during testing.
"""

import os
import sqlite3
import unittest
from unittest.mock import Mock, patch, MagicMock
from database.novels_db import dbHandler
from score_updater import ScoreParser, ScoreScraper, ScoreCrawler, update_scores_only
from core.custom_exceptions import NovelDeleted


class TestScoreUpdater(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database before all tests."""
        cls.db_name = "test_score_update.db"
        # Remove if exists from previous runs
        if os.path.exists(cls.db_name):
            os.remove(cls.db_name)
        cls.db = dbHandler(cls.db_name)

    @classmethod
    def tearDownClass(cls):
        """Clean up test database after all tests."""
        if cls.db:
            cls.db.conn.close()
        if os.path.exists(cls.db_name):
            try:
                os.remove(cls.db_name)
            except Exception:
                pass

    def setUp(self):
        """Clear tables before each test to ensure isolation."""
        self.db.cursor.execute("DELETE FROM novels")
        self.db.cursor.execute("DELETE FROM reviews")
        self.db.cursor.execute("DELETE FROM tags")
        self.db.cursor.execute("DELETE FROM novel_tags")
        self.db.save()

    def test_1_score_parser_extracts_all_scores(self):
        """Test that ScoreParser correctly extracts all five scores from HTML."""
        print("\n--- Testing ScoreParser ---")

        # Sample HTML with all scores in "X.X / 5" format
        html = """
        <html>
        <body>
            <span data-original-title="Overall Score" data-content="4.5 / 5"></span>
            <span data-original-title="Style Score" data-content="4.2 / 5"></span>
            <span data-original-title="Story Score" data-content="4.8 / 5"></span>
            <span data-original-title="Grammar Score" data-content="4.6 / 5"></span>
            <span data-original-title="Character Score" data-content="4.4 / 5"></span>
        </body>
        </html>
        """

        parser = ScoreParser()
        scores = parser.parse(html)

        self.assertEqual(scores['overall_score'], "4.5 / 5")
        self.assertEqual(scores['style_score'], "4.2 / 5")
        self.assertEqual(scores['story_score'], "4.8 / 5")
        self.assertEqual(scores['grammar_score'], "4.6 / 5")
        self.assertEqual(scores['character_score'], "4.4 / 5")
        print("ScoreParser correctly extracted all scores as strings")

    def test_2_score_parser_handles_missing_scores(self):
        """Test that ScoreParser returns "-1" string for missing scores."""
        print("\n--- Testing ScoreParser with Missing Scores ---")

        # HTML with no scores
        html = "<html><body><h1>No scores here</h1></body></html>"

        parser = ScoreParser()
        scores = parser.parse(html)

        # All scores should default to "-1" string
        for key in ['overall_score', 'style_score', 'story_score', 'grammar_score', 'character_score']:
            self.assertEqual(scores[key], "-1", f"{key} should be \"-1\" when missing")

        print("ScoreParser correctly defaults missing scores to \"-1\" string")

    def test_3_score_scraper_detects_deleted_novel(self):
        """Test that ScoreScraper raises NovelDeleted for deleted novels."""
        print("\n--- Testing ScoreScraper Deleted Novel Detection ---")

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

        scraper = ScoreScraper()
        mock_client = Mock()
        mock_client.get.return_value = deleted_html
        scraper.http_client = mock_client

        with self.assertRaises(NovelDeleted):
            scraper.scrape("https://www.royalroad.com/fiction/127411/test")

        print("ScoreScraper correctly detects deleted novels")

    def test_4_score_scraper_extracts_scores(self):
        """Test that ScoreScraper correctly extracts scores from HTML."""
        print("\n--- Testing ScoreScraper Score Extraction ---")

        # html = """
        # <html>
        # <head>
        #     <title>Test Novel - Royal Road</title>
        # </head>
        # <body>
        #     <span data-original-title="Overall Score" data-content="4.5 / 5"></span>
        #     <span data-original-title="Style Score" data-content="4.2 / 5"></span>
        #     <span data-original-title="Story Score" data-content="4.8 / 5"></span>
        #     <span data-original-title="Grammar Score" data-content="4.6 / 5"></span>
        #     <span data-original-title="Character Score" data-content="4.4 / 5"></span>
        # </body>
        # </html>
        # """

        scraper = ScoreScraper()
        # mock_client = Mock()
        # mock_client.get.return_value = html
        # scraper.http_client = mock_client

        scores = scraper.scrape("https://www.royalroad.com/fiction/21220/mother-of-learning")

        self.assertEqual(scores['overall_score'], "4.83 / 5")
        self.assertEqual(scores['style_score'], "4.69 / 5")
        self.assertEqual(scores['story_score'], "4.81 / 5")
        self.assertEqual(scores['grammar_score'], "4.79 / 5")
        self.assertEqual(scores['character_score'], "4.72 / 5")

        print("ScoreScraper correctly extracts scores as strings")

    def test_5_update_scores_only_method_updates_only_scores(self):
        """Test that update_scores_only updates ONLY score fields, leaving others untouched."""
        print("\n--- Testing dbHandler.update_scores_only ---")

        # Insert a test novel with known values (scores as strings)
        test_data = {
            'novel_name': 'Test Novel',
            'novel_url': 'http://example.com/test',
            'author': 'Original Author',
            'summary': 'Original Summary',
            'overall_score': '3.0 / 5',
            'style_score': '3.0 / 5',
            'story_score': '3.0 / 5',
            'grammar_score': '3.0 / 5',
            'character_score': '3.0 / 5',
            'total_views': 1000,
            'favourites': 50,
            'ratings': 20,
            'word_count': 50000,
            'chapter_count': 10
        }

        # Insert using raw SQL to avoid insert_data's transformations
        self.db.cursor.execute("""
            INSERT INTO novels (
                novel_name, novel_url, author, summary,
                overall_score, style_score, story_score, grammar_score, character_score,
                total_views, favourites, ratings, word_count, chapter_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_data['novel_name'], test_data['novel_url'], test_data['author'], test_data['summary'],
            test_data['overall_score'], test_data['style_score'], test_data['story_score'],
            test_data['grammar_score'], test_data['character_score'],
            test_data['total_views'], test_data['favourites'], test_data['ratings'],
            test_data['word_count'], test_data['chapter_count']
        ))
        self.db.save()

        # Get the novel_id
        self.db.cursor.execute("SELECT novel_id FROM novels WHERE novel_url = ?", (test_data['novel_url'],))
        novel_id = self.db.cursor.fetchone()[0]

        # New scores to update (as strings in "X.X / 5" format)
        new_scores = {
            'overall_score': '4.5 / 5',
            'style_score': '4.2 / 5',
            'story_score': '4.8 / 5',
            'grammar_score': '4.6 / 5',
            'character_score': '4.4 / 5'
        }

        # Update only scores
        self.db.update_scores_only(novel_id, new_scores)

        # Verify scores were updated
        self.db.cursor.execute("""
            SELECT overall_score, style_score, story_score, grammar_score, character_score
            FROM novels WHERE novel_id = ?
        """, (novel_id,))
        scores = self.db.cursor.fetchone()
        self.assertEqual(scores[0], '4.5 / 5')
        self.assertEqual(scores[1], '4.2 / 5')
        self.assertEqual(scores[2], '4.8 / 5')
        self.assertEqual(scores[3], '4.6 / 5')
        self.assertEqual(scores[4], '4.4 / 5')

        # Verify other fields remain unchanged
        self.db.cursor.execute("""
            SELECT author, summary, total_views, favourites, ratings, word_count, chapter_count
            FROM novels WHERE novel_id = ?
        """, (novel_id,))
        other_fields = self.db.cursor.fetchone()
        self.assertEqual(other_fields[0], 'Original Author')
        self.assertEqual(other_fields[1], 'Original Summary')
        self.assertEqual(other_fields[2], 1000)
        self.assertEqual(other_fields[3], 50)
        self.assertEqual(other_fields[4], 20)
        self.assertEqual(other_fields[5], 50000)
        self.assertEqual(other_fields[6], 10)

        print("update_scores_only correctly updates ONLY score fields")

    def test_6_update_scores_only_handles_invalid_values(self):
        """Test that update_scores_only handles invalid score values gracefully."""
        print("\n--- Testing update_scores_only with Invalid Values ---")

        # Insert a test novel (scores as floats since DB schema uses REAL type)
        self.db.cursor.execute("""
            INSERT INTO novels (novel_name, novel_url, overall_score, style_score, story_score, grammar_score, character_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Test Novel 2', 'http://example.com/test2', 3.0, 3.0, 3.0, 3.0, 3.0))
        self.db.save()

        self.db.cursor.execute("SELECT novel_id FROM novels WHERE novel_url = ?", ('http://example.com/test2',))
        novel_id = self.db.cursor.fetchone()[0]

        # Scores with invalid values - None and empty become -1.0 (float due to REAL column type)
        invalid_scores = {
            'overall_score': None,
            'style_score': '',
            'story_score': 'invalid',
            'grammar_score': '4.5 / 5',
            'character_score': '-1'
        }

        self.db.update_scores_only(novel_id, invalid_scores)

        # Verify invalid values become -1.0 (float), valid string values are stored as-is
        # Note: SQLite REAL columns convert numeric strings to floats automatically
        self.db.cursor.execute("""
            SELECT overall_score, style_score, story_score, grammar_score, character_score
            FROM novels WHERE novel_id = ?
        """, (novel_id,))
        scores = self.db.cursor.fetchone()
        self.assertEqual(scores[0], -1.0)  # None -> "-1" -> -1.0 (SQLite conversion)
        self.assertEqual(scores[1], -1.0)  # '' -> "-1" -> -1.0 (SQLite conversion)
        self.assertEqual(scores[2], 'invalid')  # Non-numeric string stays as text
        self.assertEqual(scores[3], '4.5 / 5')   # Valid string preserved as text
        self.assertEqual(scores[4], -1.0)  # "-1" -> -1.0 (SQLite conversion)

        print("update_scores_only correctly handles invalid values")

    def test_7_score_crawler_integration(self):
        """Integration test for ScoreCrawler with mocked HTTP client."""
        print("\n--- Testing ScoreCrawler Integration ---")

        # Insert test novels (scores as strings)
        test_novels = [
            ('Novel 1', 'http://example.com/novel1'),
            ('Novel 2', 'http://example.com/novel2'),
            ('Novel 3', 'http://example.com/novel3')
        ]

        for name, url in test_novels:
            self.db.cursor.execute("""
                INSERT INTO novels (novel_name, novel_url, overall_score, style_score, story_score, grammar_score, character_score)
                VALUES (?, ?, '', '', '', '', '')
            """, (name, url))
        self.db.save()

        # Create mock scraper
        mock_scraper = Mock(spec=ScoreScraper)

        def mock_scrape(url):
            if 'novel1' in url:
                return {'overall_score': '4.0 / 5', 'style_score': '4.1 / 5', 'story_score': '4.2 / 5', 'grammar_score': '4.3 / 5', 'character_score': '4.4 / 5'}
            elif 'novel2' in url:
                return {'overall_score': '3.5 / 5', 'style_score': '3.6 / 5', 'story_score': '3.7 / 5', 'grammar_score': '3.8 / 5', 'character_score': '3.9 / 5'}
            elif 'novel3' in url:
                raise NovelDeleted()
            return {}

        mock_scraper.scrape.side_effect = mock_scrape

        # Run crawler
        crawler = ScoreCrawler(db_handler=self.db, scraper=mock_scraper)
        crawler.crawl(batch_size=10, max_workers=1)

        # Verify results
        self.db.cursor.execute("SELECT COUNT(*) FROM novels WHERE is_deleted = 1")
        deleted_count = self.db.cursor.fetchone()[0]
        self.assertEqual(deleted_count, 1, "One novel should be marked as deleted")

        # Check that scores were updated for non-deleted novels
        self.db.cursor.execute("""
            SELECT novel_name, overall_score, style_score
            FROM novels WHERE is_deleted = 0
            ORDER BY novel_name
        """)
        results = self.db.cursor.fetchall()

        # Novel 1
        self.assertEqual(results[0][1], '4.0 / 5')  # overall_score
        self.assertEqual(results[0][2], '4.1 / 5')  # style_score

        # Novel 2
        self.assertEqual(results[1][1], '3.5 / 5')
        self.assertEqual(results[1][2], '3.6 / 5')

        print("ScoreCrawler integration test passed")

    def test_8_no_database_damage_on_error(self):
        """Test that database remains intact even when errors occur during crawling."""
        print("\n--- Testing Database Integrity on Errors ---")

        # Insert a novel with specific data
        self.db.cursor.execute("""
            INSERT INTO novels (novel_name, novel_url, author, summary, overall_score, total_views, word_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Integrity Test', 'http://example.com/integrity', 'Author X', 'Summary Y', 3.5, 5000, 100000))
        self.db.save()

        self.db.cursor.execute("SELECT novel_id FROM novels WHERE novel_url = ?", ('http://example.com/integrity',))
        novel_id = self.db.cursor.fetchone()[0]

        # Store original values
        self.db.cursor.execute("SELECT * FROM novels WHERE novel_id = ?", (novel_id,))
        original_row = self.db.cursor.fetchone()

        # Create mock scraper that always fails
        mock_scraper = Mock(spec=ScoreScraper)
        mock_scraper.scrape.side_effect = Exception("Network error")

        # Run crawler
        crawler = ScoreCrawler(db_handler=self.db, scraper=mock_scraper)
        try:
            crawler.crawl(batch_size=10, max_workers=1)
        except Exception:
            pass  # Expected to have errors

        # Verify the row still exists and non-score fields are unchanged
        self.db.cursor.execute("SELECT * FROM novels WHERE novel_id = ?", (novel_id,))
        current_row = self.db.cursor.fetchone()

        self.assertIsNotNone(current_row, "Row should still exist")

        # Check that non-score fields are unchanged (author, summary, total_views, word_count)
        # Indices: 3=author, 4=summary, 9=total_views, 14=word_count
        self.assertEqual(current_row[3], original_row[3], "Author should be unchanged")
        self.assertEqual(current_row[4], original_row[4], "Summary should be unchanged")
        self.assertEqual(current_row[9], original_row[9], "Total views should be unchanged")
        self.assertEqual(current_row[14], original_row[14], "Word count should be unchanged")

        print("Database integrity maintained despite errors")

    def test_9_concurrent_score_updates(self):
        """Test that concurrent score updates work correctly."""
        print("\n--- Testing Concurrent Score Updates ---")

        # Insert multiple novels (scores as strings)
        for i in range(5):
            self.db.cursor.execute("""
                INSERT INTO novels (novel_name, novel_url, overall_score)
                VALUES (?, ?, '')
            """, (f'Concurrent Novel {i}', f'http://example.com/concurrent{i}'))
        self.db.save()

        # Create mock scraper returning different scores as strings
        mock_scraper = Mock(spec=ScoreScraper)

        def mock_scrape(url):
            # Extract number from URL
            num = int(url[-1])
            return {
                'overall_score': f'{num * 1.0} / 5',
                'style_score': f'{num * 1.1} / 5',
                'story_score': f'{num * 1.2} / 5',
                'grammar_score': f'{num * 1.3} / 5',
                'character_score': f'{num * 1.4} / 5'
            }

        mock_scraper.scrape.side_effect = mock_scrape

        # Run crawler with multiple workers
        crawler = ScoreCrawler(db_handler=self.db, scraper=mock_scraper)
        crawler.crawl(batch_size=10, max_workers=3)

        # Verify all novels got correct scores
        self.db.cursor.execute("""
            SELECT novel_name, overall_score, style_score
            FROM novels
            WHERE novel_name LIKE 'Concurrent%'
            ORDER BY novel_name
        """)
        results = self.db.cursor.fetchall()

        for i, row in enumerate(results):
            expected_overall = f'{i * 1.0} / 5'
            expected_style = f'{i * 1.1} / 5'
            self.assertEqual(row[1], expected_overall)
            self.assertEqual(row[2], expected_style)

        print("Concurrent score updates work correctly")

    def test_10_empty_database_handling(self):
        """Test that crawler handles empty database gracefully."""
        print("\n--- Testing Empty Database Handling ---")

        # Ensure database is empty
        self.db.cursor.execute("DELETE FROM novels")
        self.db.save()

        mock_scraper = Mock(spec=ScoreScraper)
        crawler = ScoreCrawler(db_handler=self.db, scraper=mock_scraper)

        # Should not raise any exceptions
        crawler.crawl(batch_size=10, max_workers=1)

        print("Empty database handled gracefully")


if __name__ == "__main__":
    unittest.main(verbosity=2)