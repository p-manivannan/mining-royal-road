"""
Score Update Module - Updates only the score fields for novels in the database.

This module provides functionality to:
1. Parse score data from Royal Road novel pages
2. Scrape scores from novel URLs
3. Crawl through the database and update only score fields
"""

import logging
from typing import Dict, Any, List, Tuple
from bs4 import BeautifulSoup
from core.interfaces import Parser, Scraper, DatabaseHandler, Crawler
from core.http_client import RequestsHTTPClient
from core.base_crawler import BaseCrawler, WriteCounter
from database.novels_db import dbHandler
from concurrent.futures import ThreadPoolExecutor


class ScoreParser(Parser):
    """Parser that extracts only score values from a novel page."""
    
    def parse(self, html: str, **kwargs) -> Dict[str, Any]:
        """
        Parses a novel page HTML and returns only the score values.
        
        Returns:
            Dictionary with keys: overall_score, style_score, story_score, 
            grammar_score, character_score
        """
        soup = BeautifulSoup(html, features='lxml')
        scores = {}
        
        # Define score mappings
        score_mappings = [
            ('overall_score', 'Overall Score'),
            ('style_score', 'Style Score'),
            ('story_score', 'Story Score'),
            ('grammar_score', 'Grammar Score'),
            ('character_score', 'Character Score')
        ]
        
        for score_key, title in score_mappings:
            try:
                tag = soup.find('span', {'data-original-title': title})
                if tag:
                    value = tag.get('data-content') or tag.attrs.get('data-content')
                    if value is not None:
                        try:
                            scores[score_key] = str(value)
                        except (ValueError, TypeError):
                            scores[score_key] = -1.0
                    else:
                        scores[score_key] = -1.0
                else:
                    scores[score_key] = -1.0
            except Exception:
                scores[score_key] = -1.0
        
        return scores


class ScoreScraper(Scraper):
    """Scraper that fetches and parses only score data from novel pages."""
    
    def __init__(self, http_client=None, parser=None):
        self.http_client = http_client or RequestsHTTPClient()
        self.parser = parser or ScoreParser()
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrapes only the scores from a novel URL.
        
        Args:
            url: The Royal Road novel URL
            
        Returns:
            Dictionary containing only score values
            
        Raises:
            AttributeError: If page is empty or cannot be parsed
        """
        html = self.http_client.get(url)
        if not html:
            raise AttributeError("Page empty")
        
        # Check for deleted/not found title
        soup = BeautifulSoup(html, 'lxml')
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip().lower()
            if "not found" in title_text:
                from core.custom_exceptions import NovelDeleted
                raise NovelDeleted()
        else:
            raise AttributeError("Page empty")
        
        # Parse only scores
        return self.parser.parse(html)


def update_scores_only(novel_url: str) -> Dict[str, Any]:
    """
    Convenience function to scrape scores from a single novel URL.
    
    Args:
        novel_url: The Royal Road novel URL
        
    Returns:
        Dictionary containing score values
    """
    scraper = ScoreScraper()
    return scraper.scrape(novel_url)


class ScoreCrawler(BaseCrawler):
    """
    Crawler that updates only the score fields for novels in the database.
    
    This crawler iterates through all novels in the database (excluding deleted ones),
    scrapes their current scores from Royal Road, and updates only the score columns
    while leaving all other data untouched.
    """
    
    def __init__(self, db_handler: DatabaseHandler = None, scraper: Scraper = None):
        db_handler = db_handler or dbHandler()
        super().__init__(db_handler)
        self.scraper = scraper or ScoreScraper()
    
    def crawl(self, batch_size: int = 50, max_workers: int = 5):
        """
        Crawls through all novels in the database and updates only their scores.
        
        Args:
            batch_size: Number of novels to process per batch
            max_workers: Maximum number of concurrent threads for scraping
        """
        try:
            # Get all non-deleted novels
            all_novels = self._get_all_active_novels()
            total_novels = len(all_novels)
            
            self.logger.info(f"Total novels to process for score update: {total_novels}")
            
            if total_novels == 0:
                self.logger.info("No novels to process.")
                return
            
            count_obj = WriteCounter()
            processed_count = 0
            success_count = 0
            error_count = 0
            deleted_count = 0
            
            # Process in batches
            for i in range(0, total_novels, batch_size):
                batch = all_novels[i:i + batch_size]
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_info = {}
                    
                    for novel_id, url in batch:
                        future = executor.submit(self._scrape_scores_safe, url)
                        future.add_done_callback(count_obj.increment)
                        future_to_info[future] = (novel_id, url)
                    
                    for future in as_completed(future_to_info):
                        novel_id, url = future_to_info[future]
                        try:
                            result = future.result()
                            
                            if result['deleted']:
                                self.logger.warning(f"Novel {novel_id} ({url}) has been deleted. Marking in DB.")
                                self.db_handler.set_novel_as_deleted(novel_id)
                                deleted_count += 1
                            elif result['error']:
                                self.logger.error(f"Error processing novel {novel_id}: {result['error']}")
                                error_count += 1
                            else:
                                # Update only scores
                                self.db_handler.update_scores_only(novel_id, result['scores'])
                                success_count += 1
                                
                        except Exception as e:
                            self.logger.error(f"Unexpected error processing novel {novel_id}: {e}")
                            error_count += 1
                
                processed_count += len(batch)
                self.save()
                self.logger.info(
                    f"Batch complete: {processed_count}/{total_novels} | "
                    f"Success: {success_count}, Errors: {error_count}, Deleted: {deleted_count}"
                )
            
            self.logger.info(
                f"Score update complete! Total: {total_novels}, "
                f"Success: {success_count}, Errors: {error_count}, Deleted: {deleted_count}"
            )
            
        except Exception as e:
            self.logger.error(f"Crawling failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_all_active_novels(self) -> List[Tuple[int, str]]:
        """Get all non-deleted novels from the database."""
        self.db_handler.cursor.execute(
            'SELECT novel_id, novel_url FROM novels WHERE is_deleted = 0'
        )
        return self.db_handler.cursor.fetchall()
    
    def _scrape_scores_safe(self, url: str) -> Dict[str, Any]:
        """
        Safely scrape scores, catching exceptions and returning structured result.
        
        Returns:
            Dictionary with keys: 'scores', 'deleted', 'error'
        """
        from core.custom_exceptions import NovelDeleted
        
        try:
            scores = self.scraper.scrape(url)
            return {'scores': scores, 'deleted': False, 'error': None}
        except NovelDeleted:
            return {'scores': {}, 'deleted': True, 'error': None}
        except Exception as e:
            return {'scores': {}, 'deleted': False, 'error': str(e)}


# Import as_completed here to avoid circular issues at module level
from concurrent.futures import as_completed


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Starting Score Update Crawler...")
    print("=" * 60)
    
    crawler = ScoreCrawler()
    crawler.crawl(batch_size=50, max_workers=5)
    
    print("=" * 60)
    print("Score update completed!")
