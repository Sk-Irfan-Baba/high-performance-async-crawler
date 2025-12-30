from urllib.parse import urlparse

START_URL = "https://www.example.com/"
DOMAIN = urlparse(START_URL).netloc

DB_PATH = "crawler.db"
DELAY = 2
AUTO_COMMIT_SECONDS = 300
USER_AGENT = "SQLiteCrawler/1.0"
