import os
import json
import aiosqlite
from datetime import datetime


class URLBatchExporter:
    def __init__(
        self,
        db_path,
        out_dir="exports",
        batch_size=1000,
        state_file="exports/state.json",
    ):
        self.db_path = db_path
        self.batch_size = batch_size
        self.out_dir = out_dir
        self.state_file = state_file

        os.makedirs(out_dir, exist_ok=True)

        self.last_id = self._load_state()

        # NEW: export session identifier (stable per run)
        self.session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.batch_counter = 0

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                return json.load(f).get("last_id", 0)
        return 0

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump({"last_id": self.last_id}, f)

    async def export_next_batch(self):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, url
                FROM visited
                WHERE id > ?
                ORDER BY id
                LIMIT ?
                """,
                (self.last_id, self.batch_size),
            )
            rows = await cursor.fetchall()

        if not rows:
            return False

        self.batch_counter += 1
        filename = f"{self.session_id}_batch_{self.batch_counter:05d}.txt"
        path = os.path.join(self.out_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            for row_id, url in rows:
                f.write(url + "\n")
                self.last_id = row_id

        self._save_state()
        print(f"[EXPORT] Wrote {len(rows)} URLs → {path}")
        return True
