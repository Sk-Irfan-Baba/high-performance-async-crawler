from urllib.parse import urlparse

class CrawlPolicy:
    def __init__(
        self,
        max_depth=3,
        deny_extensions=None,
        allow_path_prefixes=None,
    ):
        self.max_depth = max_depth
        self.deny_extensions = deny_extensions or {
            ".pdf", ".jpg", ".png", ".zip", ".exe", ".mp4"
        }
        self.allow_path_prefixes = allow_path_prefixes

    def allowed(self, url, depth):
        if depth > self.max_depth:
            return False

        path = urlparse(url).path.lower()

        for ext in self.deny_extensions:
            if path.endswith(ext):
                return False

        if self.allow_path_prefixes:
            return any(path.startswith(p) for p in self.allow_path_prefixes)

        return True
