import asyncio


class AsyncCrawler:
    def __init__(
        self,
        store,
        fetcher,
        parser,
        policy,
        metrics,
        worker_count=25,
    ):
        self.store = store
        self.fetcher = fetcher        # fetcher owns concurrency controller
        self.parser = parser
        self.policy = policy
        self.metrics = metrics
        self.worker_count = worker_count

        self.workers = []
        self.metrics_task = None
        self._stopping = False

    async def run(self, start_url):
        await self.store.connect()
        await self.store.enqueue(start_url, depth=0)

        async with self.fetcher:
            # start metrics reporter ONCE
            self.metrics_task = asyncio.create_task(self.metrics_reporter())

            # start workers
            self.workers = [
                asyncio.create_task(self.worker(i))
                for i in range(self.worker_count)
            ]

            try:
                await asyncio.gather(*self.workers)
            except asyncio.CancelledError:
                await self.shutdown()
                raise

    async def shutdown(self):
        if self._stopping:
            return

        self._stopping = True
        print("\n🛑 Async shutdown initiated...")

        # stop workers
        for task in self.workers:
            task.cancel()

        # stop metrics reporter
        if self.metrics_task:
            self.metrics_task.cancel()

        await asyncio.gather(*self.workers, return_exceptions=True)

        if self.metrics_task:
            await asyncio.gather(self.metrics_task, return_exceptions=True)

        await self.store.close()
        print("✅ Async crawler exited safely")

    # -------------------------------------------------
    # METRICS (single reporter task)
    # -------------------------------------------------
    async def metrics_reporter(self):
        try:
            while not self._stopping:
                await asyncio.sleep(self.metrics.interval)

                visited, errors = await self.metrics.snapshot()
                qsize = await self.store.queue_size()
                uptime = self.metrics.uptime()
                rate = visited / uptime if uptime > 0 else 0

                print(
                    f"[METRICS] visited={visited} | queue={qsize} | "
                    f"errors={errors} | rate={rate:.2f} urls/sec | uptime={uptime}s"
                )
        except asyncio.CancelledError:
            pass

    # -------------------------------------------------
    # WORKERS
    # -------------------------------------------------
    async def worker(self, wid):
        try:
            while not self._stopping:
                item = await self.store.dequeue()
                if not item:
                    await asyncio.sleep(0.5)
                    continue

                url, depth = item

                if await self.store.is_visited(url):
                    continue

                await self.store.mark_visited(url, depth)
                await self.metrics.inc_visited()

                # ---- ASYNC FETCH ----
                html, rtt, success, content_type = await self.fetcher.fetch(url)

                # ---- DYNAMIC CONCURRENCY FEEDBACK ----
                self.fetcher.ctrl.record(success, rtt)

                if self.fetcher.ctrl.should_adjust():
                    new_c = self.fetcher.ctrl.adjust()
                    self.fetcher._resize_semaphore(new_c)
                    print(f"[TUNER] Adjusted concurrency → {new_c}")
                # ------------------------------------

                if not html:
                    await self.metrics.inc_error()
                    await self.store.log_error(
                        url,
                        error_type="fetch_failed",
                        message="HTTP error / timeout / non-200",
                    )
                    continue

                links = self.parser.extract_links(html, url, content_type)

                for link in links:
                    next_depth = depth + 1
                    if self.policy and not self.policy.allowed(link, next_depth):
                        continue
                    await self.store.enqueue(link, next_depth)

        except asyncio.CancelledError:
            # normal shutdown path
            pass
