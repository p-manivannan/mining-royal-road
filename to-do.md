# Immediate To-Do:
This section is for immediate plan of action with the goal of completing the Data Science aspect with the bare minimum data needed.
1. Fix ratings retrieval
2. Re-scrape existing novels in DB
3. Scrape newly updated 
4. Move to DB

# Desirable To-Do:
If more time could be dedicated to this project, these are the features I would modify/tweak/extend.
## Patreon Scraping
- Extend patreon scraping to retrieve all tiers instead of just lower and higher tiers. Involves modifying database schema. 
- Have another field in database that marks the most popular tier if present. Purpose: Can make more accurate guesstimates of author income.
- Some pages like "https://www.patreon.com/cw/Macronomicon" have public income data right in the front page. Scrape that and put it in the database whenever present.