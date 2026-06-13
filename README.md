# Mining Royal Road

> **Project status: incomplete / archived**

This project scrapes public novel data from [Royal Road](https://www.royalroad.com/)
and stores it in a SQLite database for analysis. It was originally intended to
support actionable questions such as:

- What factors are associated with a creator becoming successful?
- Can the future popularity or commercial success of a novel be predicted?
- How do readership, ratings, release activity, and monetization change over time?

The current dataset cannot answer those questions reliably. The scraper records a
snapshot of each novel at the time it is run, while predictive analysis requires
the same novels to be observed repeatedly over a long period. For that reason,
development has stopped in its current form.

## What the Project Collects

The program can discover novels from Royal Road category pages, including:

- Best Rated
- Trending
- Active Popular
- Complete
- Popular This Week
- Latest Updates
- Newest Fictions
- Rising Stars

It can then collect and store:

- Novel title, URL, author, and summary
- Ratings and component scores
- Total and average views
- Favorites, word count, and chapter count
- Tags
- Reviews and review scores
- Selected public Patreon information, when available
- Whether a novel has been scraped or appears to have been deleted

Data is stored in `novels.db` using the `novels`, `tags`, `novel_tags`, and
`reviews` tables.

## What the Data Is Useful For

The snapshot dataset is still suitable for exploratory data analysis and
descriptive questions, such as:

- The distribution of ratings, views, chapter counts, or estimated creator income
- The most common genres and tags
- Relationships between word count, ratings, favorites, and views
- Common words or themes in summaries and reviews
- Differences between novels appearing in different ranking categories

These are descriptions of the observed snapshot. They should not be treated as
evidence that a feature causes success, nor as a sound basis for predicting which
authors or novels will succeed.

## Why the Project Was Abandoned

The missing piece is longitudinal data. A useful predictive dataset would need to
record regular observations such as:

- Changes in views, favorites, ratings, and review counts
- Chapter publication dates and posting frequency
- Entry into and movement through discovery lists such as Rising Stars
- Changes in Patreon membership, tiers, or public earnings
- Novel completion, hiatus, deletion, and other status transitions

Collecting this history at the current scale is not responsible or sustainable.
Scraping roughly 10,000 novels can take up to two hours. Repeating a full crawl
every day for months would generate substantial traffic and could lead to rate
limiting, blocking, or an IP ban. More importantly, it could place an unreasonable
load on services that have not agreed to support this research workload.

The current implementation uses concurrent requests and does not provide the
scheduling, caching, backoff, or historical schema required for a responsible
long-running collection system.

## A More Responsible Future Design

If this project is revived, the collection system woudl likely be redesigned before
more data is gathered:

1. **Check permission first.** Review the site's current terms, `robots.txt`, and
   any published rate-limit guidance. Prefer an official API, data export, or
   direct research agreement where possible.
2. **Track a small representative cohort.** Follow hundreds of novels rather than
   repeatedly crawling the entire catalog. Include novels at different ages,
   popularity levels, genres, and publication stages.
3. **Use adaptive collection intervals.** Check active or rapidly changing novels
   more often and completed or inactive novels much less often.
4. **Fetch only what may have changed.** Store the last successful observation
   and avoid re-fetching reviews, chapters, or metadata already collected. Use
   conditional HTTP requests such as `ETag` or `Last-Modified` when the server
   supports them.
5. **Add a global rate limiter.** Use a low request rate, limited concurrency,
   randomized spacing, exponential backoff, and respect for `429` responses and
   `Retry-After` headers.
6. **Make crawls resumable.** Persist a work queue and checkpoints so interrupted
   jobs continue later instead of starting over.
7. **Schedule around change.** Collect index pages first, identify novels whose
   visible metrics or latest chapter changed, and queue detailed pages only for
   those novels.
8. **Stop automatically when asked.** Add circuit breakers for repeated errors,
   blocks, changed page structure, or unexpectedly high response latency.
9. **Identify the research crawler.** Where appropriate, use a truthful user agent
   with project and contact information rather than attempting to disguise or
   rotate traffic.

The database would also need an append-only observation model. Instead of
overwriting a novel's current values, a future schema could include:

```text
novels              Stable identity and metadata
novel_observations  Timestamped views, ratings, favorites, words, and chapters
category_events     When a novel is observed on a category or ranking page
chapter_events      Chapter publication and update history
patreon_observations Timestamped public monetization metrics
crawl_log           Request status, retries, timing, and collection provenance
```

This design would make growth rates, ranking transitions, time-to-success, and
survival-style analysis possible without performing a full-site crawl every day.

## Running the Existing Code

The project was written in Python and uses SQLite. There is currently no pinned
dependency file. The main runtime dependencies are:

```bash
pip install requests beautifulsoup4 lxml regex nltk scikit-learn
```

The examples below show the intended API. Because this is archived research code,
minor repairs may be required before it runs against the current versions of its
dependencies or target websites.

To discover novel URLs from a category:

```python
from novel_searcher import CategoryScraper

scraper = CategoryScraper()
scraper.crawl("latest", pages=5)
```

To populate detailed information for novel URLs already stored in the database:

```python
from novel_searcher import NovelCrawler

crawler = NovelCrawler()
crawler.crawl(batch_size=30, max_workers=5)
```

`main.py` currently runs the detailed novel crawler. Review collection and score
updates are available through `ReviewCrawler` and `ScoreCrawler`.

Tests can be run with:

```bash
pytest
```

Some tests access live Royal Road or Patreon pages. They may be slow or fail when
page structures change, network access is unavailable, or the services limit
requests.

## Disclaimer

This repository is preserved as an exploratory scraping and data-engineering
project. It is not maintained, and its parsers may no longer match the websites
they target. Anyone reusing the code is responsible for confirming that their
collection is permitted, minimizing traffic, protecting collected data, and
complying with applicable terms and laws.
