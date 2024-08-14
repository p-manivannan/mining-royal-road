import sqlite3

class dbHandler:
    def __init__(self):
        self.db_name = 'novels.db'
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def save(self):
        self.conn.commit()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS novels(
            novel_id INTEGER PRIMARY KEY,
            novel_name TEXT UNIQUE NOT NULL,
            novel_url TEXT UNIQUE NOT NULL, 
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
            pages INTEGER,
            number_of_chapters INTEGER,
            patreon_name TEXT,
            patreon_url TEXT,
            patreon_lowest_tier REAL,
            patreon_highest_tier REAL,
            patreon_subs REAL
            )''')
        # Create tags table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tags(
                            tag_id INTEGER UNIQUE NOT NULL,
                            tag_title TEXT
                            )''')
        # Create relation between tags and novels
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS novels_tags(
                            novel_id INTEGER,
                            tag_id INTEGER
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

