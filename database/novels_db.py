import sqlite3
import logging
from typing import Dict, List, Tuple
from core.interfaces import DatabaseHandler

class dbHandler(DatabaseHandler):
    def __init__(self, db_name: str = 'novels.db'):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect_to_db()
        self.create_table()
        
    def connect_to_db(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            logging.info(f"Connected to Database: {self.db_name}")
        except sqlite3.Error as e:
            logging.error(f'Error connecting to Database: {e}')
            raise e

    def save(self):
        if self.conn:
            self.conn.commit()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS novels(
            novel_id INTEGER PRIMARY KEY,
            novel_name TEXT UNIQUE NOT NULL,
            novel_url TEXT UNIQUE NOT NULL, 
            author TEXT,
            summary TEXT,
            overall_score REAL,
            style_score REAL,
            story_score REAL,
            grammar_score REAL,
            character_score REAL,
            total_views INTEGER,
            average_views INTEGER,
            favourites INTEGER,
            ratings INTEGER,
            word_count INTEGER,
            chapter_count INTEGER,
            patreon_name TEXT,
            patreon_url TEXT,
            are_reviews_obtained INTEGER DEFAULT 0,
            is_scraped INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            patreon_lowest_tier REAL,
            patreon_highest_tier REAL,
            patreon_subs REAL
            )''')
        # Create tags table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tags(
                            tag_id INTEGER PRIMARY KEY,
                            tag_name TEXT UNIQUE NOT NULL
                            )''')
        # Create Junction table between tags and novels
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS novel_tags(
                            novel_id INTEGER NOT NULL,
                            tag_id INTEGER NOT NULL,
                            FOREIGN KEY (novel_id) REFERENCES novels(novel_id) ON DELETE CASCADE,
                            FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE,
                            UNIQUE(novel_id, tag_id)
                            )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS reviews(
                            review_id INTEGER PRIMARY KEY,
                            novel_id INTEGER,
                            author TEXT,
                            content TEXT NOT NULL,
                            score REAL,
                            FOREIGN KEY (novel_id) REFERENCES novels(novel_id) ON DELETE CASCADE
                            )''')
        self.save()

    def insert_name_and_url(self, column: Dict[str, str]) -> None:
        for item in column.keys():
            sql = f"INSERT INTO novels (novel_name, novel_url) VALUES (?, ?)"
            try:
                self.cursor.execute(sql, [item, column[item]])
            except sqlite3.IntegrityError:
                continue
        self.save()

    def get_num_novels_to_scrape(self) -> int:
        self.cursor.execute('''SELECT COUNT(novel_id)
                                FROM novels
                                WHERE (is_scraped IS 0 OR is_scraped IS NULL) AND is_deleted = 0''')
        return self.cursor.fetchone()[0]

    def get_novels_to_scrape(self, limit: int, offset_id: int) -> List[Tuple[int, str]]:
        query = '''SELECT novel_id, novel_url FROM novels
                   WHERE (is_scraped IS NULL OR is_scraped = 0) AND is_deleted = 0'''
        if offset_id > -1:
            query += f' AND novel_id > {offset_id}'
        query += f' ORDER BY novel_id ASC LIMIT {limit}'
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    # Helper function created to separate score retrieval. This was done to fix incorrectly saved ratings
    # in the DB as initial run collected 9000 entries with broken scores for all.
    def put_scores(self, dct: dict) -> dict:
        # Validate and set default values
        for key in ['overall_score', 'style_score', 'story_score', 'grammar_score', 'character_score']:
            if key not in dct or dct[key] is None or dct[key] == '':
                dct[key] = -1.0
            else:
                try:
                    dct[key] = str(dct[key])
                except ValueError:
                    dct[key] = -1.0
        
        return dct


    def insert_data(self, novel_id: int, dct: dict) -> None:
        dct = self.put_scores(dct)
        for key in ['total_views', 'average_views', 'favorites', 'ratings', 'word_count', 'chapter_count']:
            if key not in dct or dct[key] is None or dct[key] == '':
                dct[key] = 0
            else:
                try:
                    # Remove potential formatting if any
                    dct[key] = int(str(dct[key]).replace(',', ''))
                except ValueError:
                    dct[key] = 0

        for key in ['author', 'summary', 'patreon_url', 'patreon_name']:
            if key not in dct:
                dct[key] = None
        if dct.get('patreon_url') is None:
            dct['patreon_url'] = 'None'

        for key in ['patreon_lowest_tier', 'patreon_highest_tier', 'patreon_subs']:
            if key not in dct or dct[key] is None or dct[key] == '':
                dct[key] = None
            else:
                try:
                    dct[key] = float(dct[key])
                except ValueError:
                    dct[key] = None

        temp_qry = '''UPDATE novels 
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
                      are_reviews_obtained = 0,
                      is_scraped = 1,
                      patreon_url = ?,
                      patreon_lowest_tier = ?,
                      patreon_highest_tier = ?,
                      patreon_subs = ?,
                      patreon_name = ?
                      WHERE novel_id = ?'''
        
        self.cursor.execute(temp_qry, [
            dct['author'], dct['summary'], dct['overall_score'], dct['style_score'], 
            dct['story_score'], dct['grammar_score'], dct['character_score'], 
            dct['total_views'], dct['average_views'], dct['favorites'], dct['ratings'], 
            dct['word_count'], dct['chapter_count'], dct['patreon_url'],
            dct['patreon_lowest_tier'], dct['patreon_highest_tier'],
            dct['patreon_subs'], dct['patreon_name'], novel_id
        ])

        # Insert tags
        if 'tags' in dct and dct['tags']:
            tags = [(item,) for item in dct['tags']]
            query = 'INSERT OR IGNORE INTO tags (tag_name) VALUES (?)'
            self.cursor.executemany(query, tags)
            
            prms_list = " ,".join('?' for _ in dct['tags'])
            query = f'SELECT tag_id FROM tags WHERE tag_name IN ({prms_list})'
            self.cursor.execute(query, dct['tags'])
            rows = self.cursor.fetchall()

            query = 'INSERT OR IGNORE INTO novel_tags (novel_id, tag_id) VALUES (?, ?)'
            for tag_id in rows:
                self.cursor.execute(query, [novel_id, tag_id[0]])
        
        self.save()

    def set_novel_as_deleted(self, novel_id: int) -> None:
        query = 'UPDATE novels SET is_deleted = 1, is_scraped = 1 WHERE novel_id = ?'
        self.cursor.execute(query, (novel_id,))
        self.save()

    def permanently_delete_novel(self, novel_id: int) -> None:
        """Permanently remove a novel and its associated data from the database."""
        # Due to ON DELETE CASCADE, deleting from novels will remove related tags and reviews
        self.cursor.execute('DELETE FROM novels WHERE novel_id = ?', (novel_id,))
        self.save()

    def get_all_novels(self) -> List[Tuple[int, str, int]]:
        """Get all novels with their id, url, and deleted status."""
        self.cursor.execute('SELECT novel_id, novel_url, is_deleted FROM novels')
        return self.cursor.fetchall()

    def get_deleted_novels(self) -> List[Tuple[int, str]]:
        """Get all novels marked as deleted."""
        self.cursor.execute('SELECT novel_id, novel_url FROM novels WHERE is_deleted = 1')
        return self.cursor.fetchall()

    def cleanup_deleted_novels(self, http_client=None) -> Tuple[int, int]:
        """
        Check all novels marked as deleted to verify if they still exist.
        Permanently removes novels that return a 404 'deleted' page.
        
        Returns:
            Tuple of (number checked, number permanently deleted)
        """
        from core.http_client import RequestsHTTPClient
        from bs4 import BeautifulSoup
        
        client = http_client or RequestsHTTPClient()
        deleted_novels = self.get_deleted_novels()
        
        checked_count = 0
        deleted_count = 0
        
        for novel_id, novel_url in deleted_novels:
            try:
                html = client.get(novel_url)
                if html:
                    soup = BeautifulSoup(html, 'lxml')
                    title_tag = soup.find('title')
                    if title_tag:
                        title_text = title_tag.text.strip().lower()
                        # Only delete if title contains "not found" (Royal Road's custom 404 page)
                        if "not found" in title_text:
                            # Novel is confirmed deleted, permanently remove it
                            self.permanently_delete_novel(novel_id)
                            deleted_count += 1
                            logging.info(f"Permanently deleted novel {novel_id} ({novel_url}) - confirmed 404")
                else:
                    # If no HTML returned, treat as deleted
                    self.permanently_delete_novel(novel_id)
                    deleted_count += 1
                    logging.info(f"Permanently deleted novel {novel_id} ({novel_url}) - no response")
            except Exception as e:
                logging.warning(f"Error checking novel {novel_id} ({novel_url}): {e}")
                # Don't delete on error - might be temporary network issue
            
            checked_count += 1
        
        logging.info(f"Cleanup complete: checked {checked_count} novels, permanently deleted {deleted_count}")
        return (checked_count, deleted_count)

    def get_num_novels_no_reviews(self) -> int:
        self.cursor.execute('''SELECT COUNT(novel_id)
                                FROM novels
                                WHERE (are_reviews_obtained IS 0 OR are_reviews_obtained IS NULL) AND is_deleted = 0''')
        return self.cursor.fetchone()[0]

    def get_novels_no_reviews(self, limit: int, offset_id: int) -> List[Tuple[int, str]]:
        query = '''SELECT novel_id, novel_url FROM novels
                   WHERE (are_reviews_obtained IS NULL OR are_reviews_obtained = 0) AND is_deleted = 0'''
        if offset_id > -1:
            query += f' AND novel_id > {offset_id}'
        query += f' ORDER BY novel_id ASC LIMIT {limit}'
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def insert_reviews(self, novel_id: int, reviews: List[dict]) -> None:
        temp_qry = "INSERT INTO reviews (novel_id, author, content, score) VALUES (?, ?, ?, ?)"
        for r in reviews:
            try:
                self.cursor.execute(temp_qry, [novel_id, r['author'], r['review'], r['score']])
            except sqlite3.IntegrityError:
                continue
        
        # Mark reviews obtained
        self.cursor.execute("UPDATE novels SET are_reviews_obtained = 1 WHERE novel_id = ?", [novel_id])
        self.save()

    def print(self):
        self.cursor.execute('SELECT * FROM novels')
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)


