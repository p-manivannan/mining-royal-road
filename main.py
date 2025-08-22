from novel_searcher import SiteCrawler, NovelCrawler


# Get 500 pages of novels from the latest updates section and save to DB
# sitecrawler = SiteCrawler()
# sitecrawler.start('latest', 500)

# Crawl database and add details
novelcrawler = NovelCrawler()
novelcrawler.crawl(batch_size=1, max_workers=1)