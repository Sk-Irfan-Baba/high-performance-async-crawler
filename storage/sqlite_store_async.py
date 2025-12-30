import aiosqlite
import time


class AsyncSQLiteStore:
    def __init__(self, db_path, batch_size=50):
        self.db_path = db_path
        self.batch_size = batch_size
        self.pending = 0
        self.conn = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self._init_pragmas()
        await self._init_tables()

    async def _init_pragmas(self):
        await self.conn.execute("PRAGMA journal_mode=WAL;")
        await self.conn.execute("PRAGMA synchronous=NORMAL;")
        await self.conn.commit()

    async def _init_tables(self):
        # Visited table with stable ordering
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS visited (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                depth INTEGER,
                visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Queue table (FIFO)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                url TEXT PRIMARY KEY,
                depth INTEGER,
                enqueued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                error_type TEXT,
                message TEXT,
                occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


        await self.conn.commit()

    # ---------------- Queue operations ----------------

    async def enqueue(self, url, depth):
        await self.conn.execute(
            "INSERT OR IGNORE INTO queue(url, depth) VALUES (?, ?)",
            (url, depth),
        )
        await self._maybe_commit()

    async def dequeue(self):
        async with self.conn.execute(
            "SELECT url, depth FROM queue ORDER BY rowid LIMIT 1"
        ) as cur:
            row = await cur.fetchone()

        if row:
            await self.conn.execute(
                "DELETE FROM queue WHERE url = ?",
                (row[0],),
            )
            await self._maybe_commit()
            return row

        return None

    async def queue_size(self):
        async with self.conn.execute(
            "SELECT COUNT(*) FROM queue"
        ) as cur:
            row = await cur.fetchone()
            return row[0]

    # ---------------- Visited operations ----------------

    async def mark_visited(self, url, depth):
        await self.conn.execute(
            """
            INSERT OR IGNORE INTO visited(url, depth)
            VALUES (?, ?)
            """,
            (url, depth),
        )
        await self._maybe_commit()

    async def is_visited(self, url):
        async with self.conn.execute(
            "SELECT 1 FROM visited WHERE url = ? LIMIT 1",
            (url,),
        ) as cur:
            return await cur.fetchone() is not None

    # ---------------- Export support ----------------

    async def fetch_visited_since(self, last_id, limit):
        async with self.conn.execute(
            """
            SELECT id, url
            FROM visited
            WHERE id > ?
            ORDER BY id
            LIMIT ?
            """,
            (last_id, limit),
        ) as cur:
            return await cur.fetchall()
    # ---------------- Error logging ----------------
    
    async def log_error(self, url, error_type, message):
        await self.conn.execute(
            """
            INSERT INTO errors(url, error_type, message)
            VALUES (?, ?, ?)
            """,
            (url, error_type, message),
        )
        await self._maybe_commit()


    # ---------------- Commit & shutdown ----------------

    async def _maybe_commit(self):
        self.pending += 1
        if self.pending >= self.batch_size:
            await self.conn.commit()
            self.pending = 0

    async def close(self):
        await self.conn.commit()
        await self.conn.close()
