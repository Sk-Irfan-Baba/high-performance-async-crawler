import aiohttp
import asyncio
import time


class AsyncFetcher:
    def __init__(self, user_agent, concurrency_controller):
        self.ctrl = concurrency_controller
        self.semaphore = asyncio.Semaphore(self.ctrl.current)
        self.headers = {"User-Agent": user_agent}
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    def _resize_semaphore(self, new_limit):
        diff = new_limit - self.semaphore._value
        if diff > 0:
            for _ in range(diff):
                self.semaphore.release()
        # NOTE: we do NOT shrink semaphore here;
        # shrink happens naturally as permits are acquired

    async def fetch(self, url, timeout=10):
        async with self.semaphore:
            start = time.time()
            try:
                async with self.session.get(url, timeout=timeout) as resp:
                    text = await resp.text()
                    rtt = time.time() - start
                    success = resp.status == 200
                    content_type = resp.headers.get("Content-Type", "")
                    return (
                        text if success else None,
                        rtt,
                        success,
                        content_type,
                    )
            except Exception:
                rtt = time.time() - start
                return None, rtt, False, None
