import sqlite3
from pprint import pprint
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from review_crawler import *
import time
import itertools
import threading


'''
Threadsafe counter. Based on the assumption that itertools relies on GIL lock
so it is threadsafe by default
'''
class WriteCounter(object):
    def __init__(self):
        self._number_of_read = 0
        self._counter = itertools.count()
        self._read_lock = threading.Lock()

    def increment(self, future=None):
        next(self._counter)

    def value(self):
        with self._read_lock:
            value = next(self._counter) - self._number_of_read
            self._number_of_read += 1
        return value
    

'''
Review crawling/scraping has been separated into another component
because of the time it takes. This has been done to make scraping
more lightweight.

How to use:
Given a database with Novel URLs, crawls through the database, extracts
reviews from each and appends to database  
'''
class ReviewCrawler():
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


    '''
    Crawls the database for novels 
    '''
    def crawl(self, batch_size=50, max_workers=5):
        """
        Process novels in the SQLite database, scrape URLs, and store results.
        
        Args:
            batch_size (int): Number of rows to fetch per batch.
            max_workers (int): Number of concurrent threads for scraping.
        """
        # Fetch total number of novels to scrape for reviews
        try:
            # Selects all rows from novels that have no reviews
            self.cursor.execute('''SELECT COUNT(are_reviews_obtained)
                                   WHERE VALUE=0
                                   FROM novels''')
            
            num_novels_no_reviews = self.cursor.fetchone()[0]
            logging.info(f"Total novels to process: {num_novels_no_reviews}")
            countObj = WriteCounter()
            # Start batch processing. Offset set to -1 to allow for first id (0) to be selected as well
            offset = -1
            while offset < num_novels_no_reviews:
                # Fetch a batch of rows from novels that have no reviews
                query = f'''SELECT novel_id, url FROM novels
                            WHERE are_reviews_obtained = 0'''
                # If offset is non-negative, then start pagination
                if offset > -1 :
                    query += f'''WHERE novel_id > {offset}'''
                
                query += f'''ORDER BY novel_id ASC
                             LIMIT {batch_size}'''
                self.cursor.execute(query)
                rows = self.cursor.fetchall()
                # If no more rows, break loop
                if not rows:
                    break

                # Get last novel_id in page
                offset = rows[-1][0]
                # Execute threading on rows
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_id = {}
                    for row in rows:
                        future = executor.submit(scrape_reviews(row[1]))       # Scrape with URL
                        future_to_id[future] = row[0]                          # Store novel_id associated with future
                        future.add_done_callback(countObj.increment)           # Increment progress tracker
                    for future in as_completed(future_to_id):    
                        try:
                            '''
                            Insert novel reviews here one by one. Future.result() is in the form of a tuple of an int and a dict:
                            novel_id, {'author' : review_author, 'review' : review, 'score' : overall_score}
                            '''
                            novel_id, dct = future.result()
                            temp_qry = f"INSERT INTO reviews (novel_id, author, review, score) VALUES (?, ?, ?, ?)"
                            try:
                                self.cursor.execute(temp_qry, [novel_id, dct['author'], dct['review'], dct['score']])
                            except sqlite3.IntegrityError:
                                continue
                        except Exception as e:
                            logging.error(f"Error processing novel_id {novel_id : {e}}")
                        
                logging.info(f"Processed {min(countObj.value, num_novels_no_reviews)} of {num_novels_no_reviews} novels")
        except:
            print("I don't even know how you ended up here. But crawling failed somewhere")
        self.save()

