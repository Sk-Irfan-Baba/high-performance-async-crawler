# High-Performance Async Web Crawler

A **production-grade, async web crawler** built in Python.  
This project focuses on **correctness, performance, resume safety, and observability**, not shortcuts.

It is designed to crawl large websites safely while persisting all state to disk and dynamically adapting its concurrency based on runtime conditions.

---

## Key Features

### Crawling Core
- Asynchronous crawling using `asyncio` + `aiohttp`
- Disk-backed queue and visited set using SQLite (WAL mode)
- Resume-safe: crash or Ctrl+C does not lose progress
- Graceful shutdown handling

### Performance
- Adaptive concurrency (AIMD-style tuning)
- Bounded parallelism using semaphores
- Batched SQLite commits for high throughput
- Sustains 8–12 URLs/sec on real-world sites

### Observability
- Periodic metrics reporting:
  - Visited URLs
  - Queue size
  - Error count
  - Crawl rate (URLs/sec)
  - Uptime
- Persistent error logging in SQLite

### Data Pipeline
- Incremental URL batch exporter
- Timestamped, non-overwriting export files
- Resume-safe exporting using cursor-based state
- Enables downstream processing while crawling continues

---

## Project Structure

```
.
├── core/
│   ├── crawler_async.py      # Async crawler engine
│   ├── crawler.py            # Synchronous crawler (baseline)
│   └── fetcher_async.py
├── storage/
│   └── sqlite_store_async.py # SQLite persistence layer
├── utils/
│   ├── metrics.py            # Metrics & observability
│   ├── concurrency.py        # Adaptive concurrency controller
│   └── exporter.py           # URL batch exporter
├── main_async.py             # Async entry point
├── main.py                   # Sync entry point
├── export_urls.py            # Exporter CLI
├── config.py                 # Configuration
└── README.txt
```

---

## Installation

Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

Install dependencies:

```bash
pip install aiohttp aiosqlite beautifulsoup4
```

---

## Configuration

Edit `config.py`:

```python
START_URL = "https://example.com"
DOMAIN = "example.com"

DB_PATH = "crawler.db"
USER_AGENT = "AdaptiveAsyncCrawler/1.0"
```

---

## Running the Crawler

### Asynchronous Crawl (Recommended)

```bash
python main_async.py
```

Features enabled:
- Async crawling
- Adaptive concurrency
- Metrics reporting
- Error logging
- Resume safety

Stop safely anytime using **Ctrl+C**.

---

### Synchronous Crawl (Baseline)

```bash
python main.py
```

Useful for:
- Comparison benchmarking
- Debugging
- Understanding baseline behavior

---

## Adjusting Concurrency & Workers

### Worker Count

In `main_async.py`:

```python
worker_count=25
```

Rule:
```
worker_count >= max_concurrency
```

Workers control task availability.  
Semaphores control actual network concurrency.

---

### Adaptive Concurrency Limits

In `main_async.py`:

```python
ConcurrencyController(
    initial=5,
    min_c=1,
    max_c=20,
    window=20
)
```

Behavior:
- Slowly increases concurrency on success
- Aggressively backs off on errors or high RTT
- Protects target servers automatically

---

## Metrics Output

Example:

```
[METRICS] visited=187 | queue=35020 | errors=0 | rate=8.94 urls/sec | uptime=20s
[TUNER] Adjusted concurrency → 10
```

Metrics are printed by a **single reporter task** to avoid duplication.

---

## Error Logging

Errors are stored persistently in SQLite.

Inspect manually:

```bash
sqlite3 crawler.db
```

```sql
SELECT id, url, error_type, occurred_at
FROM errors
ORDER BY id DESC;
```

---

## URL Exporter

Export discovered URLs incrementally while crawling continues.

### Run exporter

```bash
python export_urls.py
```

### Export behavior
- Writes timestamped batch files
- Never overwrites existing exports
- Maintains progress in `exports/state.json`

Example output:

```
exports/
 ├── 2025-01-03_18-42-10_batch_00001.txt
 ├── 2025-01-03_19-10-55_batch_00001.txt
```

---

## Resume Safety

All crawl state is persisted:
- Queue
- Visited URLs
- Errors
- Export cursor

You can stop and restart the crawler without data loss.

---

## Responsible Usage

- Respect website terms of service
- Use conservative concurrency limits
- Identify yourself via User-Agent
- Avoid crawling sites you do not own or have permission to crawl

---

## Why This Project

This crawler was built to:
- Go beyond toy scripts
- Demonstrate real async system design
- Handle long-running crawls safely
- Show measurable performance improvements

It prioritizes **correctness and architecture** over shortcuts.

---

## Disclaimer

This project is for educational and research purposes only.
The author is not responsible for misuse.
