# High-Performance Async Web Crawler

A **production-grade, async web crawler** built in Python with a focus on:
- correctness
- performance
- resume safety
- observability

This project is intentionally designed as a **system**, not a toy script.

---

## Key Features

### Crawling Core
- Asynchronous crawling using `asyncio` + `aiohttp`
- Disk-backed queue and visited set using SQLite (WAL mode)
- Resume-safe (Ctrl+C or crash does not lose progress)
- Graceful shutdown handling

### Performance
- Adaptive concurrency (AIMD-style tuning)
- Bounded parallelism using semaphores
- Batched SQLite commits
- Sustained 8–12 URLs/sec on large real-world sites

### Observability
- Periodic metrics reporting:
  - visited URLs
  - queue size
  - error count
  - crawl rate (URLs/sec)
  - uptime
- Persistent error logging in SQLite

### Data Pipeline
- Incremental URL batch exporter
- Timestamped, non-overwriting export files
- Resume-safe exporting using cursor-based state
- URLs can be processed while crawl continues

---

## Project Structure

```
.
├── core/
│   ├── crawler_async.py
│   ├── crawler.py
│   └── fetcher_async.py
├── storage/
│   └── sqlite_store_async.py
├── utils/
│   ├── metrics.py
│   ├── concurrency.py
│   └── exporter.py
├── main_async.py
├── main.py
├── export_urls.py
├── config.py
└── README.md
```

---

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
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

### Async Crawl (Recommended)

```bash
python main_async.py
```

Enabled by default:
- async crawling
- adaptive concurrency
- metrics reporting
- error logging
- resume safety

Stop safely anytime using **Ctrl+C**.

---

### Sync Crawl (Baseline)

```bash
python main.py
```

Useful for benchmarking and comparison only.

---

## Command-Line Flags

### Disable Crawl Policies (Experimental)

```bash
python main.py --no-policy
python main_async.py --no-policy
```

Effect:
- Disables depth limits and crawl rules
- Useful for experimentation
- NOT recommended for large public sites

---

### Enable Sitemap-Based Crawling

```bash
python main.py --use-sitemap
python main_async.py --use-sitemap
```

Behavior:
- Attempts to discover URLs from `sitemap.xml`
- Falls back to link-based crawling if sitemap is unavailable
- Safe to combine with depth limits

---

### Adjust Worker Count

Edit `main_async.py`:

```python
worker_count = 25
```

Guideline:

```
worker_count >= max_concurrency
```

Workers control task throughput.  
Concurrency controller limits network pressure.

---

### Adjust Concurrency Limits

Edit `main_async.py`:

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
- Quickly backs off on failures or high RTT
- Prevents server overload

---

## Metrics Output

Example:

```
[METRICS] visited=187 | queue=35020 | errors=0 | rate=8.94 urls/sec | uptime=20s
[TUNER] Adjusted concurrency → 10
```

Metrics are printed by a **single reporter task**.

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

Export discovered URLs incrementally.

```bash
python export_urls.py
```

Behavior:
- Writes timestamped batch files
- Never overwrites previous exports
- Maintains progress in `exports/state.json`

Example:

```
exports/
 ├── 2025-01-03_18-42-10_batch_00001.txt
 ├── 2025-01-03_19-10-55_batch_00001.txt
```

---

## Resume Safety

All state is persisted:
- crawl queue
- visited URLs
- errors
- export cursor

Stopping and restarting continues exactly where it left off.

---

## Responsible Usage

- Respect website terms of service
- Use conservative concurrency limits
- Identify yourself via User-Agent
- Do not crawl sites without permission

---

## Why This Project

This crawler demonstrates:
- real async system design
- persistence-first architecture
- adaptive concurrency control
- long-running task safety

It prioritizes **engineering correctness** over shortcuts.

---

## Disclaimer

This project is for educational and research purposes only.
The author is not responsible for misuse.


---

## Colab Quickstart

This project can be run directly on **Google Colab** for demos, testing, and short crawls.

> ⚠️ Colab is not recommended for very long crawls (multi-hour) due to session timeouts.

---

### 1. Open Google Colab

Go to:  
https://colab.research.google.com

Create a **New Notebook**.

---

### 2. Clone the Repository

Run in a Colab cell:

```bash
!git clone https://github.com/Sk-Irfan-Baba/high-performance-async-crawler.git
%cd high-performance-async-crawler
```

---

### 3. Install Dependencies

```bash
!pip install aiohttp aiosqlite beautifulsoup4 lxml
```

(`lxml` is recommended to avoid XML parsing warnings.)

---

### 4. (Recommended) Mount Google Drive

Mounting Drive allows the SQLite database to persist across Colab restarts.

```python
from google.colab import drive
drive.mount('/content/drive')
```

Create a folder for crawler data:

```bash
!mkdir -p /content/drive/MyDrive/crawler
```

Update `config.py`:

```python
DB_PATH = "/content/drive/MyDrive/crawler/crawler.db"
```

---

### 5. Configure Crawl Target

Edit `config.py`:

```python
START_URL = "https://example.com"
DOMAIN = "example.com"
```

For Colab, consider lower resource usage:

```python
# in main_async.py
worker_count = 10
```

---

### 6. Run the Async Crawler

```bash
!python main_async.py
```

You should see output like:

```
[METRICS] visited=120 | queue=5400 | errors=0 | rate=6.8 urls/sec | uptime=20s
```

---

### 7. Stop the Crawl Safely

Use:

**Runtime → Interrupt execution**

The crawler will:
- stop workers
- commit SQLite state
- exit cleanly

---

### 8. Export URLs

After crawling:

```bash
!python export_urls.py
```

Exported URL batches appear in:

```
exports/
```

If using Drive, these files persist across sessions.

---

### Notes on Colab Usage

- Colab already runs an event loop — avoid nested `asyncio.run()` calls
- Sessions may disconnect after inactivity
- Resume is safe as long as the database is stored on Drive

---
