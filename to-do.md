# Desirable To-Do:
If more time could be dedicated to this project, these are the features I would modify/tweak/extend.
## Patreon Scraping
- Extend patreon scraping to retrieve all tiers instead of just lower and higher tiers. Involves modifying database schema. 
- Have another field in database that marks the most popular tier if present. Purpose: Can make more accurate guesstimates of author income.
- Some pages like "https://www.patreon.com/cw/Macronomicon" have public income data right in the front page. Scrape that and put it in the database whenever present.

## General Analysis
- (Highly desirable business usecase) Refocus and extend database to collect daily insights for 6 months for a selected group of random novels (scraped from X pages of recently uploaded).

## Database 
- Include upload schedule
- Include list of first X chapters (including content) and upload time of each
- Include statistics of recent X chapters (exluding content and including upload times, number of chapters, etc.)
- Include whether novel has made it to rising stars or another category page
- Include datetime of scraping. 