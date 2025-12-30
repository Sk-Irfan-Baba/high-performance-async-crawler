import requests

class Fetcher:
    def __init__(self, user_agent):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def fetch(self, url, timeout=10):
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
