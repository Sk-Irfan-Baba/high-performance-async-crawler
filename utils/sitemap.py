import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

VALID_ROOTS = {"urlset", "sitemapindex"}


def is_valid_sitemap(xml_text: str) -> bool:
    try:
        root = ET.fromstring(xml_text)
        tag = root.tag.split("}")[-1]  # remove namespace
        return tag in VALID_ROOTS
    except Exception:
        return False


def fetch_sitemap_urls(base_url, timeout=15):
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    urls = []

    try:
        resp = requests.get(sitemap_url, timeout=timeout)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "").lower()
        if "xml" not in content_type:
            print("[SITEMAP] sitemap.xml is not XML → skipping")
            return []

        if not is_valid_sitemap(resp.text):
            print("[SITEMAP] sitemap.xml is not a valid sitemap → skipping")
            return []

        root = ET.fromstring(resp.text)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        if root.tag.endswith("sitemapindex"):
            for sm in root.findall("sm:sitemap", ns):
                loc = sm.find("sm:loc", ns)
                if loc is not None:
                    urls.extend(fetch_single_sitemap(loc.text))
        else:
            urls.extend(fetch_single_sitemap(sitemap_url))

    except Exception as e:
        print(f"[SITEMAP] sitemap.xml unavailable → {e}")

    return urls


def fetch_single_sitemap(sitemap_url, timeout=15):
    urls = []
    try:
        resp = requests.get(sitemap_url, timeout=timeout)
        resp.raise_for_status()

        if "xml" not in resp.headers.get("Content-Type", "").lower():
            return []

        root = ET.fromstring(resp.text)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        for url in root.findall("sm:url", ns):
            loc = url.find("sm:loc", ns)
            if loc is not None:
                urls.append(loc.text.strip())

    except Exception:
        pass

    return urls
