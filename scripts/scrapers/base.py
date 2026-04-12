"""Base scraper class with common HTTP logic and retry handling."""

from __future__ import annotations

import logging
import time
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json",
    "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.5",
}


class ScraperError(Exception):
    """Raised when a scraper encounters an unrecoverable error."""


class BaseScraper:
    """Common HTTP fetch logic with retries and basic parsing helpers."""

    def __init__(
        self,
        timeout: int = 20,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.headers = headers or DEFAULT_HEADERS.copy()
        self.errors: List[str] = []

    def fetch(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        if params:
            url = url + ("&" if "?" in url else "?") + urlencode(params)
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                req = Request(url, headers=self.headers)
                LOGGER.info("Fetch attempt %d: %s", attempt, url)
                with urlopen(req, timeout=self.timeout) as resp:
                    charset = resp.headers.get_content_charset() or "utf-8"
                    return resp.read().decode(charset, errors="replace")
            except (HTTPError, URLError, OSError) as exc:
                last_error = exc
                msg = f"Attempt {attempt}/{self.max_retries} failed for {url}: {exc}"
                LOGGER.warning(msg)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)
        error_msg = f"Failed to fetch {url} after {self.max_retries} attempts: {last_error}"
        self.errors.append(error_msg)
        raise ScraperError(error_msg)

    def fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        import json
        text = self.fetch(url, params)
        return json.loads(text)

    def safe_fetch(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        try:
            return self.fetch(url, params)
        except ScraperError:
            return None

    def safe_fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        try:
            return self.fetch_json(url, params)
        except (ScraperError, ValueError) as exc:
            self.errors.append(f"JSON parse error for {url}: {exc}")
            return None


class LinkExtractor(HTMLParser):
    """Extract all <a> links from HTML, with optional keyword filtering."""

    def __init__(self, keywords: Optional[List[str]] = None) -> None:
        super().__init__()
        self.links: List[Tuple[str, str]] = []
        self.keywords = [k.lower() for k in keywords] if keywords else None
        self._href: Optional[str] = None
        self._parts: List[str] = []

    def _flush(self) -> None:
        if self._href is not None:
            text = " ".join("".join(self._parts).split()).strip()
            if text:
                if self.keywords is None or any(k in text.lower() for k in self.keywords):
                    self.links.append((text, self._href))
        self._href = None
        self._parts = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag.lower() != "a":
            return
        if self._href is not None:
            self._flush()
        href = dict(attrs).get("href")
        if href:
            self._href = href
            self._parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a":
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)


def extract_links(
    html: str,
    base_url: str,
    keywords: Optional[List[str]] = None,
) -> List[Tuple[str, str]]:
    """Return list of (text, absolute_url) from HTML, optionally filtered."""
    parser = LinkExtractor(keywords)
    parser.feed(html)
    return [(text, urljoin(base_url, href)) for text, href in parser.links]
