import asyncio
from config import *
from storage.sqlite_store_async import AsyncSQLiteStore
from core.fetcher_async import AsyncFetcher
from core.parser import Parser
from core.crawler_async import AsyncCrawler
from core.policies import CrawlPolicy
from utils.metrics import Metrics
from utils.concurrency import ConcurrencyController


async def main():
    # Persistent storage
    store = AsyncSQLiteStore(DB_PATH)

    # Dynamic concurrency controller
    ctrl = ConcurrencyController(
        initial=5,
        min_c=1,
        max_c=20,
        window=20,
    )

    # Async fetcher wired to controller
    fetcher = AsyncFetcher(USER_AGENT, ctrl)

    parser = Parser(DOMAIN)
    metrics = Metrics(interval=10)
    policy = CrawlPolicy(max_depth=3)

    # IMPORTANT:
    # worker_count >= max concurrency
    crawler = AsyncCrawler(
        store=store,
        fetcher=fetcher,
        parser=parser,
        policy=policy,
        metrics=metrics,
        worker_count=25,   # >= max_c
    )

    await crawler.run(START_URL)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 KeyboardInterrupt received. Exit complete.")
