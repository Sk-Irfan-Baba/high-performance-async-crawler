import argparse
from config import *
from storage.sqlite_store import SQLiteStore
from core.fetcher import Fetcher
from core.parser import Parser
from core.crawler import Crawler
from core.policies import CrawlPolicy
from utils.signals import setup_signal_handlers
from utils.metrics import Metrics
from utils.sitemap import fetch_sitemap_urls

def main():
    parser = argparse.ArgumentParser(
        description="High-performance SQLite-backed web crawler"
    )

    parser.add_argument(
        "--no-policy",
        action="store_true",
        help="Disable crawl policies (experimental mode)",
    )
    parser.add_argument(
    "--use-sitemap",
    action="store_true",
    help="Seed crawler using sitemap.xml",
)

    parser.add_argument(
        "--full-site",
        action="store_true",
        help="Enable full-site crawl mode (uses sitemap + relaxed depth)",
    )


    args = parser.parse_args()

    store = SQLiteStore(DB_PATH)
    fetcher = Fetcher(USER_AGENT)
    parser_ = Parser(DOMAIN)

    policy = None
    if not args.no_policy:
        if args.full_site:
            policy = CrawlPolicy(
                max_depth=8,   # relaxed but still bounded
                allow_path_prefixes=None,
            )
            print("🌐 Full-site crawl mode ENABLED")
        else:
            policy = CrawlPolicy(max_depth=3)
            print("🛡 Crawl policies ENABLED")
    else:
        print("⚠ Crawl policies DISABLED (experimental mode)")

    crawler = Crawler(
    store=store,
    fetcher=fetcher,
    parser=parser_,
    delay=DELAY,
    auto_commit=AUTO_COMMIT_SECONDS,
    policy=policy,
    metrics=metrics,
                    )


    setup_signal_handlers(store.commit)
    if args.use_sitemap:
        sitemap_urls = fetch_sitemap_urls(START_URL)
        if sitemap_urls:
            crawler.seed_from_sitemap(sitemap_urls, depth=1)
    crawler.run(START_URL)
    store.close()

if __name__ == "__main__":
    metrics = Metrics(interval=10)
    main()
