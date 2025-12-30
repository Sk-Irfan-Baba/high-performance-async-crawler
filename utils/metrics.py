import time
import asyncio


class Metrics:
    def __init__(self, interval=10):
        self.start_time = time.time()
        self.interval = interval

        self.visited = 0
        self.errors = 0

        self._lock = asyncio.Lock()
        self._last_report = 0

    async def inc_visited(self):
        async with self._lock:
            self.visited += 1

    async def inc_error(self):
        async with self._lock:
            self.errors += 1

    async def snapshot(self):
        async with self._lock:
            return self.visited, self.errors

    def uptime(self):
        return int(time.time() - self.start_time)
