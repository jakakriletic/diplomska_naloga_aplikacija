"""Pajek za ZAJEM podatkov iz spletnih virov (web scraping).

Privzeto strga spletno stran FEI UNM (testni primer iz diplome), a je
posplošen: prek argumentov sprejme poljuben začetni URL in globino, zato ga je
mogoče uporabiti na katerikoli spletni strani podjetja/organizacije.

Zagon (orkestrator):
    scrapy crawl fei -a start_url=https://fei.uni-nm.si/ -a max_depth=2 \
        -s CLOSESPIDER_PAGECOUNT=40 -O output/run_<id>.json
"""
from urllib.parse import urlparse

import scrapy
from scrapy.http import TextResponse

from .keywords import KEYWORDS


class FeiSpider(scrapy.Spider):
    name = "fei"

    blocked_domains = [
        "facebook.com", "instagram.com", "linkedin.com", "youtube.com",
        "google.com", "x.com", "twitter.com", "tiktok.com", "pinterest.com",
    ]
    blocked_extensions = (
        ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
        ".zip", ".rar", ".7z", ".doc", ".docx", ".xls", ".xlsx", ".ppt",
        ".pptx", ".mp4", ".mp3", ".avi", ".mov", ".css", ".js", ".xml", ".rss",
    )

    def __init__(self, start_url=None, max_depth="2", *args, **kwargs):
        super().__init__(*args, **kwargs)
        start_url = start_url or "https://fei.uni-nm.si/"
        self.start_urls = [start_url]

        domain = (urlparse(start_url).hostname or "").lower()
        if domain.startswith("www."):
            domain = domain[4:]
        self.allowed_domains = [domain] if domain else []

        try:
            self.max_depth = int(max_depth)
        except (TypeError, ValueError):
            self.max_depth = 2

    # -- glavni vstop (globina 0) --
    def parse(self, response):
        yield from self._handle(response, depth=0)

    # -- nadaljnje strani --
    def parse_detail(self, response):
        yield from self._handle(response, depth=response.meta.get("depth", 1))

    def _handle(self, response, depth):
        # Obdelaj samo besedilne (HTML) odgovore
        if not isinstance(response, TextResponse):
            return

        yield {
            "url": response.url,
            "depth": depth,
            "html": response.text,
        }

        if depth >= self.max_depth:
            return

        for link in response.xpath("//a/@href").getall():
            full_url = response.urljoin(link)
            if self._blocked(full_url):
                continue
            priority = 1 if self._relevant(full_url) else 0
            yield scrapy.Request(
                full_url,
                callback=self.parse_detail,
                meta={"depth": depth + 1},
                priority=priority,
            )

    def _relevant(self, url: str) -> bool:
        u = url.lower()
        return any(keyword in u for keyword in KEYWORDS)

    def _blocked(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return True
        if parsed.path.lower().endswith(self.blocked_extensions):
            return True
        domain = parsed.netloc.lower()
        for blocked in self.blocked_domains:
            if domain == blocked or domain.endswith("." + blocked):
                return True
        return False
