# Royal Road Novel Scraper & Crawler - Complete Process Flow

## Project Goal
1. **Crawl** Royal Road website for 1000s of novels
2. **Scrape** detailed information about every novel (including Patreon data) and save to database
3. **Perform data science** on the collected data

This document describes the complete flow through steps 2 (scraping) and 3 (data science preparation).

---

## Architecture Overview

The project follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    CORE LAYER                               │
│  (interfaces.py, base_crawler.py, http_client.py,           │
│   models.py, exceptions.py)                                 │
│  - Defines abstract interfaces                              │
│  - Provides base classes and HTTP client                    │
│  - Custom exceptions (NovelDeleted)                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌─────────────────┐   ┌───────────────┐
│ NOVEL_SEARCHER│    │ REVIEW_CRAWLER  │   │   DATABASE    │
│ (Discovery &  │    │ (Review         │   │   (novels_db) │
│  Detail       │    │  Scraping)      │   │               │
│  Scraping)    │    │                 │   │               │
└───────────────┘    └─────────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │     UTILS       │
                    │ (patreon_scraper│
                    │  custom_exc)    │
                    └─────────────────┘
```

---

## File-by-File Breakdown

### **CORE LAYER** (`/core/`)

#### `interfaces.py`
**Purpose**: Defines abstract base classes that enforce consistent API contracts across the project.

**Key Interfaces**:
- `HTTPClient`: Abstract method `get(url)` → returns HTML string
- `Parser`: Abstract method `parse(html)` → returns structured data
- `Scraper`: Abstract method `scrape(url)` → orchestrates download + parse
- `DatabaseHandler`: CRUD operations for novels, tags, reviews
- `Crawler`: Abstract method `crawl()` → executes batch processing

**Role in Goals**: Ensures all scrapers/crawlers follow the same pattern, making the system extensible and testable.

---

#### `base_crawler.py`
**Purpose**: Provides reusable base class for all crawlers.

**Key Components**:
- `WriteCounter`: Thread-safe counter for tracking progress during concurrent scraping
- `BaseCrawler`: 
  - Initializes logger and database handler
  - Provides `save()` method to commit database changes
  - Enforces implementation of `crawl()` via abstract method

**Role in Goals**: Eliminates code duplication across `NovelCrawler`, `ReviewCrawler`, and `CategoryScraper`.

---

#### `http_client.py`
**Purpose**: Handles all HTTP requests to Royal Road and Patreon.

**Implementation**: `RequestsHTTPClient` implements `HTTPClient` interface
- Uses `requests.Session()` for connection pooling
- Sets realistic browser headers to avoid blocking
- Timeout: 15 seconds per request
- Returns raw HTML text (even for error pages like 404)

**Role in Goals**: Centralized HTTP handling with proper error logging. All scraping flows through this client.

---

#### `models.py`
**Purpose**: Defines data structures and configuration.

**Key Classes**:
- `RoyalRoadConfig`: Base URLs and category endpoints
- `NovelDetailedInfo`: Dataclass with all possible novel fields
- `ScrapingStatus`: Enum for tracking scrape state (PENDING, COMPLETED, etc.)
- `DatabaseParams`, `ScrapingParams`: Parameter containers

**Role in Goals**: Type safety and centralized configuration.

---

#### `exceptions.py` / `custom_exceptions.py`
**Purpose**: Custom exception hierarchy.

**Key Exception**:
- `NovelDeleted`: Raised when a novel page returns "404 Not Found" (Royal Road's custom deleted page)

**Role in Goals**: Enables proper handling of deleted novels throughout the pipeline.

---

### **DATABASE LAYER** (`/database/`)

#### `novels_db.py`
**Purpose**: SQLite database handler implementing `DatabaseHandler` interface.

**Database Schema**:
```sql
novels (
  novel_id, novel_name, novel_url, author, summary,
  overall_score, style_score, story_score, grammar_score, character_score,
  total_views, average_views, favourites, ratings,
  word_count, chapter_count,
  patreon_name, patreon_url, patreon_lowest_tier, patreon_highest_tier, patreon_subs,
  are_reviews_obtained, is_scraped, is_deleted
)

tags (tag_id, tag_name)
novel_tags (novel_id, tag_id)  -- Junction table with CASCADE delete
reviews (review_id, novel_id, author, content, score)  -- CASCADE delete
```

**Key Methods**:

**Discovery Phase**:
- `insert_name_and_url()`: Bulk insert novel names/URLs from category crawling

**Scraping Phase (Step 2)**:
- `get_num_novels_to_scrape()`: Count novels where `is_scraped=0 AND is_deleted=0`
- `get_novels_to_scrape(limit, offset)`: Batch fetch URLs to scrape
- `insert_data(novel_id, dict)`: Update novel with full details + Patreon info
- `set_novel_as_deleted(novel_id)`: Soft-delete flag (`is_deleted=1`)
- `permanently_delete_novel(novel_id)`: Hard delete with CASCADE to tags/reviews
- `cleanup_deleted_novels()`: Verify soft-deleted novels still return 404, then permanently remove

**Review Scraping Phase**:
- `get_num_novels_no_reviews()`: Count where `are_reviews_obtained=0 AND is_deleted=0`
- `get_novels_no_reviews(limit, offset)`: Batch fetch URLs for review scraping
- `insert_reviews(novel_id, list)`: Store reviews and mark as obtained

**Data Science Phase (Step 3)**:
- `print()`: Dump all records (for debugging)
- `get_all_novels()`: Retrieve all novels with deletion status

**Role in Goals**: 
- **Step 2**: Persistent storage with soft-delete mechanism
- **Step 3**: Query interface for data analysis (filtering out deleted novels automatically)

---

### **NOVEL_SEARCHER MODULE** (`/novel_searcher/`)

Handles initial discovery and detailed novel scraping.

#### `categoryscraper.py`
**Purpose**: Discovers novel URLs by crawling Royal Road category pages.

**Categories**: best-rated, trending, active-popular, complete, weekly-popular, latest-updates, new, rising-stars

**Flow**:
1. User calls `crawl(category, pages)`
2. For each page: constructs URL like `https://www.royalroad.com/fictions/latest-updates?page=2`
3. Fetches HTML via `http_client.get()`
4. Parses with `RoyalRoadCategoryParser` → extracts `{novel_name: novel_url}`
5. Calls `db_handler.insert_name_and_url()` to store in database

**Deleted Novel Handling**: Does NOT check for deleted novels (only collects URLs from listing pages).

**Role in Goals**: **Step 1** - Populates database with novel URLs for subsequent scraping.

---

#### `novelscraper.py`
**Purpose**: Scrapes detailed information from individual novel pages.

**Flow**:
1. `scrape(url)` called with novel URL
2. Downloads HTML via `http_client.get(url)`
3. **DELETED CHECK**: Parses `<title>` tag; if "not found" in title → raises `NovelDeleted`
4. Passes HTML to `RoyalRoadNovelParser.parse()` → extracts:
   - Name, author, summary, tags
   - Scores (overall, style, story, grammar, character)
   - Stats (views, favorites, ratings, word count, chapter count)
   - Patreon URL (if exists)
5. **Patreon Scraping**: If Patreon URL exists:
   - Calls `utils.patreon_scraper.scrape_patreon(patreon_url)`
   - Extracts: subscribers, income, tier prices, tier titles
6. Returns consolidated dictionary

**Legacy Methods**: `scrape_novel_info()`, `get_novel_info()` (kept for backward compatibility).

**Role in Goals**: **Step 2** - Primary detail scraper with integrated Patreon data collection.

---

#### `novel_info_putter.py`
**Purpose**: Legacy parser class (largely superseded by `RoyalRoadNovelParser`).

**Current State**: 
- Contains parsing logic duplicated in `parsers.py`
- Has comment acknowledging it should handle 404/deleted detection but doesn't implement it
- Method `put_info(soup)` calls individual `put_*()` methods for each field

**Issue**: This class does NOT check if the page exists before parsing. It assumes the BeautifulSoup object passed to it is valid. The actual deleted-checking happens in `NovelScraper.scrape()` BEFORE calling the parser.

**Recommendation**: This is legacy code that should be deprecated in favor of `RoyalRoadNovelParser` in `parsers.py`.

**Role in Goals**: Historical artifact; not actively used in current flow.

---

#### `novel_crawler.py`
**Purpose**: Orchestrates batch scraping of novel details from database.

**Flow**:
1. `crawl(batch_size=50, max_workers=5)` called
2. Gets count: `db_handler.get_num_novels_to_scrape()` (excludes deleted)
3. Loop until all novels processed:
   - Fetches batch: `db_handler.get_novels_to_scrape(batch_size, offset)`
   - Submits `scraper.scrape(url)` to `ThreadPoolExecutor` (concurrent)
   - For each result:
     - **Success**: `db_handler.insert_data(novel_id, result_dict)`
     - **NovelDeleted**: `db_handler.set_novel_as_deleted(novel_id)` (soft-delete)
     - **AttributeError**: Retry once after 3-second delay
     - **Other errors**: Log and continue
4. Commits changes via `save()`

**Deleted Novel Handling**: ✅ Properly catches `NovelDeleted` and marks novel in database.

**Role in Goals**: **Step 2** - High-throughput detail scraper with concurrency and error handling.

---

#### `parsers.py`
**Purpose**: Contains parser implementations for novel_searcher module.

**Classes**:

**`RoyalRoadCategoryParser`**:
- Input: Category page HTML
- Output: `Dict{novel_name: novel_url}`
- Strategy: Finds `<h2 class="fiction-title">` elements, extracts `<a>` links

**`RoyalRoadNovelParser`**:
- Input: Novel detail page HTML
- Output: Dictionary with all novel fields
- Strategy: Targeted BeautifulSoup searches for each field
  - Author: `.row.fic-header` → next `<a>`
  - Summary: `.description` div
  - Tags: `.fiction-info` → `.margin-bottom-10`
  - Scores: `<span data-original-title="Overall Score">` → `data-content`
  - Stats: `.col-sm-6[1]` → `<li>` pairs
  - Chapter count: `.actions` div
  - Word count: `<i class="fal fa-question-circle popovers">` → regex on `data-content`
  - Patreon: `<i class="fa fas fa-money-bill-wave">` → next `.dropdown-content` → last `<a>`

**Role in Goals**: **Step 2** - Converts raw HTML into structured data for database storage.

---

### **REVIEW_CRAWLER MODULE** (`/review_crawler/`)

Handles scraping user reviews for novels.

#### `review_scraper.py`
**Purpose**: Scrapes all reviews for a single novel.

**Flow**:
1. `scrape(url)` called
2. Downloads first page via `http_client.get(url)`
3. **DELETED CHECK**: Parses `<title>`; if "not found" → raises `NovelDeleted`
4. Parses reviews with `RoyalRoadReviewParser.parse()` → list of review dicts
5. Parses pagination with `RoyalRoadReviewParser.parse_num_pages()`
6. If multiple pages:
   - Constructs URLs: `{url}?sorting=top&reviews={page_num}`
   - Fetches and parses each page
   - Extends review list
7. Returns list of `{author, review, score}` dictionaries

**Deleted Novel Handling**: ✅ Checks title on first page load.

**Role in Goals**: **Step 2** - Collects user-generated review data for sentiment analysis.

---

#### `review_crawler.py`
**Purpose**: Orchestrates batch review scraping.

**Flow**:
1. `crawl(batch_size=50, max_workers=5)` called
2. Gets count: `db_handler.get_num_novels_no_reviews()` (excludes deleted)
3. Loop until all novels processed:
   - Fetches batch: `db_handler.get_novels_no_reviews(batch_size, offset)`
   - Submits `scraper.scrape(url)` to `ThreadPoolExecutor`
   - For each result:
     - **Success**: `db_handler.insert_reviews(novel_id, reviews_list)`
     - **NovelDeleted**: `db_handler.set_novel_as_deleted(novel_id)`
     - **Other errors**: Log and continue
4. Commits changes

**Deleted Novel Handling**: ✅ Catches `NovelDeleted` and marks novel.

**Role in Goals**: **Step 2** - Batch review collector for downstream NLP/sentiment analysis.

---

#### `parsers.py`
**Purpose**: Review-specific parsers.

**Classes**:

**`RoyalRoadReviewParser`**:
- `parse(html)`: 
  - Finds `.portlet.light.reviews` container
  - Iterates through `.review` divs
  - Extracts: reviewer name (`.review-meta` → `<a>`), content (`.review-inner`), score (`aria-label="Overall Score"` sibling)
  - Returns: `List[{author, review, score}]`
  
- `parse_num_pages(html)`:
  - Finds `.pagination` ul
  - Gets last `<a>` → `data-page` attribute
  - Returns: int (default 1)

**Role in Goals**: **Step 2** - Structures review data for storage.

---

### **UTILS MODULE** (`/utils/`)

#### `patreon_scraper.py`
**Purpose**: Scrapes Patreon creator pages for monetization metrics.

**Flow**:
1. `scrape_patreon(url)` called with Patreon URL
2. Downloads HTML with browser headers
3. **Two-pass JSON extraction**:
   - **Pass 1**: Look for `<script id="__NEXT_DATA__">` (Pages Router)
   - **Pass 2**: Look for `self.__next_f.push()` patterns (App Router)
4. Parses nested JSON to extract:
   - Creator name
   - Subscriber count (if public)
   - Monthly income (if public)
   - Tier information (title, price, patron count per tier)
5. Calculates lowest/highest tier prices
6. Returns dictionary with 9 fields

**Deleted Novel Handling**: ❌ Does NOT check if Patreon page exists. Relies on caller to handle exceptions (timeouts, 404s).

**Role in Goals**: **Step 2** - Enriches novel data with creator monetization metrics for correlation analysis.

---

#### `custom_exceptions.py`
**Purpose**: Defines `NovelDeleted` exception.

**Usage**: Imported by `novelscraper.py`, `review_scraper.py`, `novel_crawler.py`, `review_crawler.py`, `novels_db.py`.

**Role in Goals**: Centralized exception for deleted novel handling across entire pipeline.

---

### **UTILITY FILES**

#### `functions.py`
**Purpose**: Data preprocessing utilities for data science phase.

**Functions**:
- `bs_preprocess(html)`: Cleans HTML whitespace
- `tokenizer(text)`: Tokenizes, removes stopwords/punctuation, lemmatizes (NLTK)
- `clean_reviews(reviews)`: Applies tokenizer to review text

**Role in Goals**: **Step 3** - Prepares text data for NLP tasks (sentiment analysis, topic modeling).

---

#### `main.py`
**Purpose**: Example entry point for running crawlers.

**Current Usage**:
```python
novelcrawler = NovelCrawler()
novelcrawler.crawl(batch_size=30, max_workers=30)
```

**Role in Goals**: Quick-start script for **Step 2**.

---

#### `test_scrapers_and_crawlers.py` / `test_patreon_scraper.py`
**Purpose**: Unit and integration tests.

**Coverage**:
- Deleted novel detection in scrapers
- Review crawler handling of deleted novels
- Filtering excludes deleted novels
- Cleanup functionality
- Patreon scraper metric extraction

**Role in Goals**: Ensures reliability of **Steps 1-2**.

---

## Complete Process Flow

### **STEP 1: Discovery (Crawling Royal Road)**

```
User runs CategoryScraper
         │
         ▼
┌────────────────────────┐
│ CategoryScraper.crawl()│
│ - Iterates categories  │
│ - Builds paginated URLs│
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│ HTTPClient.get(url)    │
│ - Fetches category HTML│
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│ RoyalRoadCategoryParser│
│ - Extracts {name: url} │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│ dbHandler.insert_...   │
│ - Stores in 'novels'   │
│ - is_scraped = 0       │
│ - is_deleted = 0       │
└────────────────────────┘
```

**Output**: Database populated with novel names and URLs, ready for detail scraping.

---

### **STEP 2A: Detailed Novel Scraping**

```
User runs NovelCrawler
         │
         ▼
┌─────────────────────────────┐
│ NovelCrawler.crawl()        │
│ - Queries DB for uns scraped│
│   (WHERE is_scraped=0 AND   │
│    is_deleted=0)            │
│ - Batches by 50             │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ ThreadPoolExecutor          │
│ - Spawns 5-30 workers       │
│ - Each calls scraper.scrape │
└─────────────────────────────┘
         │
         ├──────────────────────────────────────┐
         │                                      │
         ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│ NovelScraper.scrape │              │ NovelScraper.scrape │
│ (Worker 1)          │              │ (Worker 2)          │
└─────────────────────┘              └─────────────────────┘
         │                                      │
         ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│ HTTPClient.get(url) │              │ HTTPClient.get(url) │
└─────────────────────┘              └─────────────────────┘
         │                                      │
         ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│ CHECK: <title> tag  │              │ CHECK: <title> tag  │
│ "not found"?        │              │ "not found"?        │
└─────────────────────┘              └─────────────────────┘
         │                                      │
    ┌────┴────┐                            ┌────┴────┐
    │ YES     │                            │ NO      │
    ▼         │                            ▼         │
┌──────────┐  │                    ┌─────────────────┐
│Raise     │  │                    │RoyalRoadNovel   │
│NovelDel. │  │                    │Parser.parse()   │
└──────────┘  │                    └─────────────────┘
    │         │                            │
    │         │                            ▼
    │         │                    ┌─────────────────┐
    │         │                    │Has Patreon URL? │
    │         │                    └─────────────────┘
    │         │                            │
    │         │                    ┌───────┴───────┐
    │         │                    │ YES           │ NO
    │         │                    ▼               │
    │         │            ┌───────────────┐       │
    │         │            │scrape_patreon │       │
    │         │            │(utils module) │       │
    │         │            └───────────────┘       │
    │         │                    │               │
    │         │                    ▼               │
    │         │            ┌───────────────┐       │
    │         │            │Extract: subs, │       │
    │         │            │income, tiers  │       │
    │         │            └───────────────┘       │
    │         │                    │               │
    └─────────┴────────────────────┴───────────────┘
              │
              ▼
    ┌─────────────────┐
    │ NovelCrawler    │
    │ catches result  │
    └─────────────────┘
              │
         ┌────┴────┐
         │Success  │ NovelDeleted
         ▼         ▼
    ┌──────────┐  ┌──────────────────┐
    │insert_data│  │set_novel_as_    │
    │(all fields)│  │deleted()        │
    └──────────┘  │(is_deleted=1)    │
                  └──────────────────┘
```

**Output**: Database enriched with full novel metadata + Patreon metrics. Deleted novels soft-flagged.

---

### **STEP 2B: Review Scraping**

```
User runs ReviewCrawler
         │
         ▼
┌──────────────────────────────┐
│ ReviewCrawler.crawl()        │
│ - Queries DB for no reviews  │
│   (WHERE are_reviews_obtained│
│    =0 AND is_deleted=0)      │
└──────────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ ThreadPoolExecutor           │
│ - Concurrent review scraping │
└──────────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│ ReviewScraper.scrape(url)│
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│ HTTPClient.get(url)      │
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│ CHECK: <title> tag       │
│ "not found"?             │
└──────────────────────────┘
         │
    ┌────┴────┐
    │ YES     │ NO
    ▼         ▼
┌──────────┐ ┌─────────────────────┐
│NovelDel. │ │ReviewParser.parse() │
│exception │ │- Extracts reviews   │
└──────────┘ │- Paginates if needed│
    │        └─────────────────────┘
    │                │
    │                ▼
    │        ┌─────────────────────┐
    │        │Return List[reviews] │
    │        └─────────────────────┘
    │                │
    └────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ ReviewCrawler   │
    │ catches result  │
    └─────────────────┘
             │
        ┌────┴────┐
        │Success  │ NovelDeleted
        ▼         ▼
   ┌──────────┐  ┌──────────────────┐
   │insert_   │  │set_novel_as_     │
   │reviews() │  │deleted()         │
   └──────────┘  └──────────────────┘
```

**Output**: Reviews table populated. Deleted novels flagged.

---

### **STEP 2C: Cleanup (Permanent Deletion)**

```
User runs cleanup_deleted_novels()
         │
         ▼
┌─────────────────────────────┐
│ dbHandler.cleanup_...()     │
│ - Queries WHERE is_deleted=1│
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ For each soft-deleted novel:│
│ - HTTPClient.get(url)       │
│ - Check <title> for         │
│   "not found"               │
└─────────────────────────────┘
         │
    ┌────┴────┐
    │Confirmed│ Still exists
    │404      │ (false positive)
    ▼         ▼
┌──────────┐ ┌─────────────────┐
│permanently│ │Keep in DB      │
│_delete_   │ │(is_deleted=1)  │
│novel()    │ └─────────────────┘
│CASCADE to │
│tags,reviews│
└──────────┘
```

**Output**: Confirmed deleted novels permanently removed from database.

---

### **STEP 3: Data Science Preparation**

```
Data Scientist queries database
         │
         ▼
┌─────────────────────────────┐
│ dbHandler queries           │
│ (automatically exclude      │
│  is_deleted=1)              │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Load into pandas/DataFrame  │
│ - Novel metadata            │
│ - Patreon metrics           │
│ - Reviews (joined)          │
│ - Tags (joined)             │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Preprocessing (functions.py)│
│ - clean_reviews()           │
│ - tokenizer()               │
│ - TF-IDF vectorization      │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Analysis Tasks:             │
│ - Correlation: Patreon $ vs │
│   novel scores              │
│ - Sentiment analysis on     │
│   reviews                   │
│ - Topic modeling on tags    │
│ - Success prediction models │
└─────────────────────────────┘
```

---

## Deleted Novel Handling Summary

| Component | Checks for Deleted? | Action Taken |
|-----------|---------------------|--------------|
| `CategoryScraper` | ❌ No | N/A (only lists URLs) |
| `NovelScraper` | ✅ Yes | Raises `NovelDeleted` if title contains "not found" |
| `NovelCrawler` | ✅ Yes (catches) | Calls `set_novel_as_deleted()` |
| `ReviewScraper` | ✅ Yes | Raises `NovelDeleted` if title contains "not found" |
| `ReviewCrawler` | ✅ Yes (catches) | Calls `set_novel_as_deleted()` |
| `patreon_scraper` | ❌ No | Relies on caller exception handling |
| `NovelInfoPutter` | ❌ No | Legacy; doesn't perform checks |
| `dbHandler.cleanup_deleted_novels()` | ✅ Yes | Permanently removes confirmed 404s |
| All DB queries | ✅ Yes | Filter `WHERE is_deleted=0` |

---

## Identified Issues & Recommendations

### 1. **Patreon Scraper Missing Deleted Check**
**Issue**: `scrape_patreon()` doesn't verify if Patreon page exists before scraping.

**Recommendation**: Add check:
```python
response = requests.get(url, headers=headers, timeout=15)
if response.status_code == 404 or "not found" in response.text.lower():
    raise NovelDeleted(f"Patreon page deleted: {url}")
```

### 2. **NovelInfoPutter is Legacy**
**Issue**: Duplicated parsing logic, no deleted checking, not used in current flow.

**Recommendation**: Deprecate and remove. Use `RoyalRoadNovelParser` exclusively.

### 3. **No Rate Limiting**
**Issue**: Aggressive concurrent scraping could trigger Cloudflare protection.

**Recommendation**: Add rate limiting in `http_client.py`:
```python
import time
from threading import Lock

class RequestsHTTPClient:
    def __init__(self, ...):
        self.rate_limit = 0.5  # seconds between requests
        self.last_request = 0
        self.lock = Lock()
    
    def get(self, url):
        with self.lock:
            elapsed = time.time() - self.last_request
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
            self.last_request = time.time()
        # ... proceed with request
```

### 4. **Retry Logic Could Be Improved**
**Issue**: Only retries on `AttributeError`, not on other transient errors.

**Recommendation**: Implement exponential backoff for all network errors.

---

## Conclusion

The project successfully implements:
- ✅ **Step 1**: Category-based novel discovery
- ✅ **Step 2**: Comprehensive scraping with Patreon integration and deleted novel handling
- ⚠️ **Step 3**: Basic preprocessing utilities provided; analysis scripts not included

**Deleted novel handling is robust** across all scraping components, with soft-delete marking and permanent cleanup capabilities. The only gap is the Patreon scraper, which should be enhanced to detect deleted pages.
