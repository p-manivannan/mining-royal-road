from novel_searcher import scrape_novel
from utils.custom_exceptions import NovelDeleted
from review_crawler import WriteCounter
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3



'''
Crawls through the pre-existing database of novel names and urls, searches novel,
scrapes information and saves to database
'''

class NovelCrawler():
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.db_name = 'novels.db'      # I am aware that this is bad design. Filename should be read from sommewhere common
        self.conn = None
        self.cursor = None
        self.connect_to_db()


    def connect_to_db(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            logging.info("Connected to Database")
        except sqlite3.Error as e:
            logging.error(f'Error connecting to Database: {e}')
            return


    def save(self):
        self.conn.commit()


    def insert_data(self, novel_id, dct):
        # If novel doesn't have these scores, then set value to a placeholder value to indicate absence (-1)
        if 'overall_score' not in dct.keys():
            dct['overall_score'] = -1
            dct['style_score'] = -1 
            dct['story_score'] = -1 
            dct['grammar_score'] = -1 
            dct['character_score'] = -1
        # Insert most data
        temp_qry = f'''UPDATE novels 
                        SET
                        author = ?, 
                        summary = ?, 
                        overall_score = ?, 
                        style_score = ?, 
                        story_score = ?, 
                        grammar_score = ?, 
                        character_score = ?, 
                        total_views = ?,
                        average_views = ?,
                        favourites = ?,
                        ratings = ?,
                        word_count = ?,
                        chapter_count = ?,
                        are_reviews_obtained = ?,
                        is_scraped = ?
                        WHERE novel_id = {novel_id} '''
        try:
            self.cursor.execute(temp_qry, [dct['author'], dct['summary'], dct['overall_score'], dct['style_score'], dct['story_score'], dct['grammar_score'], dct['character_score'], dct['total_views'], dct['average_views'], dct['favorites'], dct['ratings'], dct['word_count'], dct['chapter_count'], 0, 1])
        except sqlite3.IntegrityError:
            pass

        # Insert tags
        tags = [(item,) for item in dct['tags']]
        query = f'''INSERT OR IGNORE INTO tags 
                    (tag_name) VALUES (?)\n'''
        try:
            self.cursor.executemany(query, tags)
        except sqlite3.IntegrityError:
            pass
        
        prms_list = " ,".join('?' for _ in dct['tags'])
        # Get tag ids of the novel to insert into junction table
        query = f'''SELECT 
                        tag_id 
                    FROM 
                        tags
                    WHERE 
                        tag_name IN ({prms_list})'''
        
        self.cursor.execute(query, dct['tags'])
        rows = self.cursor.fetchall()               # Tag_name, tag_id of novel

        # Insert tag and novel ids into junction table
        query = f'''INSERT OR IGNORE INTO novel_tags (
                    novel_id,
                    tag_id) VALUES (?, ?)\n'''
        # For each tag_id of the novel, insert into junction table
        for tag_id in rows:
            self.cursor.execute(query, [novel_id, tag_id[0]])



    
    '''
    Crawls the database for novels 
    '''
    def crawl(self, batch_size=50, max_workers=5):
        """
        Get novels from SQLite database, scrape and store results.
        
        Args:
            batch_size (int): Number of rows to fetch per batch.
            max_workers (int): Number of concurrent threads for scraping.
        """
        # Fetch total number of novels to scrape for reviews
        try:
            # Selects all rows from novels that have no values
            self.cursor.execute('''SELECT COUNT(novel_id)
                                   FROM novels
                                   WHERE is_scraped IS NULL\n''')
            
            num_novels_no_reviews = self.cursor.fetchone()[0]
            logging.info(f"Total novels to process: {num_novels_no_reviews}")
            countObj = WriteCounter()
            # Start batch processing. Offset set to -1 to allow for first id (0) to be selected as well
            offset = -1
            while offset < num_novels_no_reviews:
                # Fetch a batch of rows from novels that have no reviews
                query = f'''SELECT novel_id, novel_url FROM novels
                            WHERE (is_scraped IS NULL OR is_scraped = 0)\n'''
                # If offset is non-negative, then start pagination
                if offset > -1 :
                    query += f'''AND novel_id > {offset}\n'''
                
                query += f'''ORDER BY novel_id ASC
                             LIMIT {batch_size}\n'''
                self.cursor.execute(query)
                rows = self.cursor.fetchall()
                # If no more rows, break loop
                if not rows:
                    break

                # Get last novel_id in page
                offset = rows[-1][0]
                # Execute threading on rows
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_id = []
                    for row in rows:
                        future = executor.submit(scrape_novel, row[1])         # Scrape with URL
                        future.add_done_callback(countObj.increment)           # Increment progress tracker                        
                        novel_id = row[0]
                        future_to_id.append((novel_id, future))                          # Store future with its associated novel_id                  for future in as_completed(future_to_id.keys()):    
                    for novel_id, future in future_to_id:
                        try:
                            dct = future.result()
                            self.insert_data(novel_id, dct)
                        except NovelDeleted as e:
                            self.set_novel_as_deleted(novel_id)
                        except AttributeError as e:
                            logging.error(f"Error processing novel_id {novel_id}:{e}")


                
                self.save()
                logging.info(f"Processed {min(countObj.value(), num_novels_no_reviews)} of {num_novels_no_reviews} novels")
        except:
            print("I don't even know how you ended up here. But crawling failed somewhere")

    def set_novel_as_deleted(self, novel_id):
        query = f'''UPDATE novels
                    SET is_deleted = ?
                    WHERE novel_id = ?'''
        self.cursor.execute(query, (1, novel_id))
        self.save()
