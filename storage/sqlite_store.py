import sqlite3
import time

class SQLiteStore:
    def __init__(self, db_path, batch_size=50):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.batch_size = batch_size
        self.pending_writes = 0
        self._init_pragmas()
        self._init_tables()

    def _init_pragmas(self):
        cur = self.conn.cursor()

        cur.execute("PRAGMA journal_mode=WAL;")
        mode = cur.fetchone()[0]

        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("PRAGMA temp_store=MEMORY;")

        self.conn.commit()

        print(f"[SQLite] journal_mode={mode}, synchronous=NORMAL")


    def _init_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS visited (
                url TEXT PRIMARY KEY,
                depth INTEGER
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                url TEXT PRIMARY KEY,
                depth INTEGER
            )
        """)

        self.conn.commit()

    def enqueue(self, url, depth):
        self.conn.execute(
            "INSERT OR IGNORE INTO queue(url, depth) VALUES (?, ?)",
            (url, depth),
        )
        self._mark_write()

    def dequeue(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT url, depth FROM queue ORDER BY rowid LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            self.conn.execute(
                "DELETE FROM queue WHERE url = ?", (row[0],)
            )
            return row
        return None


    def mark_visited(self, url, depth):
        self.conn.execute(
            "INSERT OR IGNORE INTO visited(url, depth) VALUES (?, ?)",
            (url, depth),
        )
        self._mark_write()

    def _mark_write(self):
        self.pending_writes += 1
        if self.pending_writes >= self.batch_size:
            self.commit()

    def is_visited(self, url):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT 1 FROM visited WHERE url = ? LIMIT 1", (url,)
        )
        return cur.fetchone() is not None

    def commit(self):
        self.conn.commit()
        self.pending_writes = 0


    def close(self):
        self.conn.close()

    def queue_size(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM queue")
        return cur.fetchone()[0]

