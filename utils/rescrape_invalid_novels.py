"""
Utility to identify and re-scrape novels with invalid/missing data.

Novels with all scores = -1.0 likely indicate:
1. Brand new novels with no ratings yet (valid case)
2. Scraping failures that weren't caught (invalid case - needs re-scraping)

This script identifies such novels and provides options to re-scrape them.
"""

import logging
from database.novels_db import dbHandler
from novel_searcher.novelscraper import NovelScraper
from utils.custom_exceptions import NovelDeleted

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_novels_needing_rescrape(db_handler=None):
    """
    Find novels that are marked as scraped but have all scores = -1.0.
    These likely need to be re-scraped.
    
    Returns list of (novel_id, novel_url, novel_name) tuples.
    """
    db = db_handler or dbHandler()
    cursor = db.cursor
    
    # Find novels marked as scraped, not deleted, with all scores = -1.0
    query = '''SELECT novel_id, novel_name, novel_url 
               FROM novels 
               WHERE is_scraped = 1 
               AND is_deleted = 0
               AND overall_score = -1.0
               AND style_score = -1.0
               AND story_score = -1.0
               AND grammar_score = -1.0
               AND character_score = -1.0'''
    
    cursor.execute(query)
    return cursor.fetchall()


def reset_novel_for_rescrape(db_handler, novel_id):
    """
    Reset a novel's scraped status so it will be picked up again by the crawler.
    """
    query = '''UPDATE novels 
               SET is_scraped = 0,
                   author = NULL,
                   summary = NULL,
                   overall_score = NULL,
                   style_score = NULL,
                   story_score = NULL,
                   grammar_score = NULL,
                   character_score = NULL,
                   total_views = NULL,
                   average_views = NULL,
                   favourites = NULL,
                   ratings = NULL,
                   word_count = NULL,
                   chapter_count = NULL,
                   patreon_url = NULL,
                   patreon_lowest_tier = NULL,
                   patreon_highest_tier = NULL,
                   patreon_subs = NULL,
                   patreon_name = NULL
               WHERE novel_id = ?'''
    
    db.cursor.execute(query, (novel_id,))
    db.save()
    logger.info(f"Reset novel {novel_id} for re-scraping")


def rescrape_novel(db_handler, novel_id, url):
    """
    Attempt to re-scrape a single novel immediately.
    """
    scraper = NovelScraper()
    
    try:
        logger.info(f"Re-scraping novel {novel_id}: {url}")
        data = scraper.scrape(url)
        db_handler.insert_data(novel_id, data)
        logger.info(f"Successfully re-scraped novel {novel_id}")
        return True
        
    except NovelDeleted:
        logger.warning(f"Novel {novel_id} has been deleted. Marking in DB.")
        db_handler.set_novel_as_deleted(novel_id)
        return False
        
    except Exception as e:
        logger.error(f"Failed to re-scrape novel {novel_id}: {e}")
        return False


def main():
    db = dbHandler()
    
    # Find problematic novels
    novels_to_rescrape = find_novels_needing_rescrape(db)
    
    if not novels_to_rescrape:
        print("\n✓ No novels found with all scores = -1.0")
        print("All scraped novels appear to have valid rating data.")
        return
    
    print(f"\nFound {len(novels_to_rescrape)} novel(s) with all scores = -1.0")
    print("These may need to be re-scraped:\n")
    
    for novel_id, name, url in novels_to_rescrape[:20]:  # Show first 20
        print(f"  ID: {novel_id}")
        print(f"  Name: {name}")
        print(f"  URL: {url}")
        print()
    
    if len(novels_to_rescrape) > 20:
        print(f"  ... and {len(novels_to_rescrape) - 20} more\n")
    
    print("\nOptions:")
    print("  1. Reset all these novels for re-scraping (will be picked up by next crawl)")
    print("  2. Re-scrape all these novels immediately")
    print("  3. Exit without changes")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        logger.info("Resetting novels for re-scraping...")
        for novel_id, _, _ in novels_to_rescrape:
            reset_novel_for_rescrape(db, novel_id)
        print(f"\n✓ Reset {len(novels_to_rescrape)} novel(s). They will be scraped on next crawl run.")
        
    elif choice == '2':
        logger.info("Re-scraping novels immediately...")
        success_count = 0
        fail_count = 0
        
        for novel_id, name, url in novels_to_rescrape:
            if rescrape_novel(db, novel_id, url):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\n✓ Completed: {success_count} successful, {fail_count} failed")
        
    elif choice == '3':
        print("\nNo changes made.")
    
    else:
        print("\nInvalid choice. No changes made.")


if __name__ == "__main__":
    main()
