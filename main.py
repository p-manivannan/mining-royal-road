from novel_searcher import CategoryScraper, NovelCrawler


# Get 500 pages of novels from the latest updates section and save to DB
# sitecrawler = SiteCrawler()
# sitecrawler.start('best rated', 500)

# Crawl database and add details
novelcrawler = NovelCrawler()
novelcrawler.crawl(batch_size=30,  max_workers=30)