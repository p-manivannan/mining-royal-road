# Fix for Novels with -1.0 Ratings

## Problem Analysis

The database had many novels with all rating scores set to `-1.0`. This was caused by two issues:

1. **Parser Issue**: The `RoyalRoadNovelParser` was setting scores to `-1.0` when no rating element was found, instead of `None`. This made it impossible to distinguish between:
   - Brand new novels with no ratings yet (valid case)
   - Failed scrapes that couldn't extract any data (invalid case)

2. **Database Insert Issue**: The `insert_data()` method in `dbHandler` was blindly accepting `-1.0` values and marking novels as `is_scraped=1` even when the scrape clearly failed (no name, no author, all scores -1.0).

## Solution Implemented

### 1. Fixed Parser (`novel_searcher/parsers.py`)

Changed the score extraction logic to return `None` instead of `-1.0` when ratings are not found:

```python
# Before:
novel_info[score_key] = -1.0  # Always set to -1.0

# After:
if value is not None and value != '':
    novel_info[score_key] = float(value)
else:
    novel_info[score_key] = None  # No rating available yet (new novel)
```

This allows distinguishing between:
- `None` = No ratings yet (new novel) or parsing issue
- Valid float = Actual rating value

### 2. Enhanced Database Validation (`database/novels_db.py`)

Added validation in `insert_data()` to detect failed scrapes:

```python
# Check if all scores are -1.0 AND basic info is missing
all_scores_negative = all(
    dct.get(key, -1.0) == -1.0 
    for key in ['overall_score', 'style_score', 'story_score', 'grammar_score', 'character_score']
)

if all_scores_negative:
    has_basic_info = bool(dct.get('name')) and bool(dct.get('author'))
    
    if not has_basic_info:
        # This looks like a failed scrape - don't update the record
        logging.warning(f"Novel {novel_id}: Scraping appears to have failed. Not updating database.")
        return  # Don't mark as scraped
```

This prevents failed scrapes from being marked as successful.

### 3. Created Re-scrape Utility (`utils/rescrape_invalid_novels.py`)

A utility script to identify and fix novels that were incorrectly marked as scraped with invalid data:

```bash
python utils/rescrape_invalid_novels.py
```

Options:
1. Reset novels for re-scraping (will be picked up by next crawl)
2. Re-scrape immediately
3. Exit without changes

## How to Fix Existing -1.0 Records

If you have existing novels with all `-1.0` scores that need to be re-scraped:

```bash
# Run the utility
python utils/rescrape_invalid_novels.py

# Choose option 2 to re-scrape immediately
# OR choose option 1 to reset them for the next crawl run
```

## Future Behavior

Going forward:
- New novels with no ratings will have `NULL` scores in the database (converted to `-1.0` on insert for consistency, but WITH valid name/author)
- Failed scrapes will NOT be marked as `is_scraped=1`, so they'll be automatically retried
- The crawler will properly distinguish between "no ratings yet" and "scraping failed"

## Testing

Tests confirmed:
✓ Parser returns `None` for missing scores (not `-1.0`)
✓ Database rejects completely failed scrapes (no name/author)
✓ Database accepts valid scrapes with no ratings (has name/author but NULL scores)
✓ Failed scrapes remain as `is_scraped=0` for retry
