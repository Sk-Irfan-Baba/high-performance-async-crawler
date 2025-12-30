from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class Parser:
    def __init__(self, domain):
        self.domain = domain

    def extract_links(self, content, base_url, content_type=None):
        """
        Extract links from HTML or XML safely.
        """
        if content_type and "xml" in content_type.lower():
            soup = BeautifulSoup(content, "xml")
        else:
            soup = BeautifulSoup(content, "html.parser")

        links = set()

        for a in soup.find_all("a", href=True):
            full_url = urljoin(base_url, a["href"]).split("#")[0]
            if urlparse(full_url).netloc == self.domain:
                links.add(full_url)

        return links
