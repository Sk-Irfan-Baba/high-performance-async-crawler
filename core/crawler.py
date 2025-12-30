import time
class Crawler:
    def __init__(
        self,
        store,
        fetcher,
        parser,
        delay,
        auto_commit,
        policy=None,
        metrics=None,
    ):
        self.store = store
        self.fetcher = fetcher
        self.parser = parser
        self.delay = delay
        self.auto_commit = auto_commit
        self.policy = policy
        self.metrics = metrics
        self.last_commit = time.time()
        self.processed = 0

    def run(self, start_url):
        self.store.enqueue(start_url, depth=0)

        while True:
            item = self.store.dequeue()
            if not item:
                print("✅ Queue empty. Crawl complete.")
                break

            url, depth = item

            if self.store.is_visited(url):
                continue

            self.store.mark_visited(url, depth)
            self.processed += 1
            if self.metrics:
                self.metrics.inc_visited()


            try:
                html = self.fetcher.fetch(url)
                links = self.parser.extract_links(html, url)

                for link in links:
                    next_depth = depth + 1

                    if self.policy:
                        if not self.policy.allowed(link, next_depth):
                            continue

                    self.store.enqueue(link, next_depth)

                print(f"[{self.processed}] depth={depth} {url}")

            except Exception as e:
                if self.metrics:
                    self.metrics.inc_error()
                print(f"[FAIL] {url} → {e}")

            if time.time() - self.last_commit >= self.auto_commit:
                self.store.commit()
                print("💾 Auto-commit")
                self.last_commit = time.time()
        
            time.sleep(self.delay)
            if self.metrics and self.metrics.should_report():
                qsize = self.store.queue_size()
                self.metrics.report(qsize)
                
    def seed_from_sitemap(self, urls, depth=1):
        """
        Enqueue sitemap URLs at a controlled depth.
        """
        count = 0
        for url in urls:
            self.store.enqueue(url, depth)
            count += 1

        print(f"[SITEMAP] Seeded {count} URLs into queue at depth={depth}")

