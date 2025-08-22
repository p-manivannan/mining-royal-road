import sqlite3

import logging



class dbHandler:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.db_name = 'novels.db'      # I am aware that this is bad design. Filename should be read from sommewhere common
        self.conn = None
        self.cursor = None
        self.connect_to_db()
        self.create_table()
        


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
    Implement 'if file does not exist' check
    '''
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
            are_reviews_obtained INTEGER,
            is_scraped INTEGER,
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
                            FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
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

    def insert_name_and_url(self, column: dict):
        for item in column.keys():
            sql = f"INSERT INTO novels (novel_name, novel_url) VALUES (?, ?)"
            try:
                self.cursor.execute(sql, [item, column[item]])
            # Skip entries already in db
            except sqlite3.IntegrityError:
                continue
                
        self.save()

    def print(self):
        self.cursor.execute('SELECT * FROM novels')
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)

