"""Simple TTL cache for scraped data.

Prevents hammering external sites on every page load.
Default TTL = 30 minutes.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Optional

LOGGER = logging.getLogger(__name__)
CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache"


class ScrapeCache:
    """File-based cache with TTL for scraped results."""

    def __init__(self, ttl: int = 1800, cache_dir: Optional[Path] = None) -> None:
        self.ttl = ttl  # seconds
        self.dir = cache_dir or CACHE_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(":", "_").replace("?", "_")[:120]
        return self.dir / f"{safe}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._key_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - data.get("ts", 0) > self.ttl:
                path.unlink(missing_ok=True)
                return None
            LOGGER.debug("Cache HIT: %s", key)
            return data["value"]
        except (json.JSONDecodeError, KeyError):
            path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any) -> None:
        path = self._key_path(key)
        path.write_text(
            json.dumps({"ts": time.time(), "value": value}, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        LOGGER.debug("Cache SET: %s", key)

    def get_or_fetch(self, key: str, fetch_fn: Callable[[], Any]) -> Any:
        """Return cached value or call *fetch_fn*, cache result, and return it."""
        cached = self.get(key)
        if cached is not None:
            return cached
        value = fetch_fn()
        if value is not None:
            self.set(key, value)
        return value

    def clear(self) -> int:
        """Remove all cache files. Returns count deleted."""
        count = 0
        for f in self.dir.glob("*.json"):
            f.unlink(missing_ok=True)
            count += 1
        return count

    def clear_expired(self) -> int:
        """Remove only expired entries."""
        count = 0
        now = time.time()
        for f in self.dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if now - data.get("ts", 0) > self.ttl:
                    f.unlink(missing_ok=True)
                    count += 1
            except (json.JSONDecodeError, KeyError):
                f.unlink(missing_ok=True)
                count += 1
        return count
