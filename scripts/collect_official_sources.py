"""Tools for collecting official derussification-related sources.

This module provides three main building blocks:

``ADMINISTRATIVE_HIERARCHY``
    A nested dictionary that documents the hierarchy of administrative
    units (обласні військові адміністрації, районні/міські/селищні ради
    та територіальні громади) together with links to their official
    websites.  The structure is intentionally compact – it contains a
    representative subset that can be extended in-place without touching
    the rest of the code.

``DecisionRegistry``
    A small data container that keeps the links to decisions on
    дерусифікація, декомунізація, топонімічні зміни тощо.  The registry is
    designed to be easily extendable: new categories can be introduced on
    the fly, and the collected data can be exported either as JSON or CSV.

``OfficialSourceCollector``
    A helper that iterates over the configured official websites,
    attempts to locate hyperlinks that match category-specific keywords
    and stores the results inside ``DecisionRegistry``.  The collector is
    intentionally conservative – in offline environments or when a site
    does not respond it simply records the error instead of failing the
    whole run.

The module keeps the dependencies limited to the Python standard library
so that it can run both as a standalone script and inside the existing
Flask web application without any additional setup.
"""

from __future__ import annotations

import csv
import json
import logging
import time
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import urlopen


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Administrative hierarchy and official sources.


ADMINISTRATIVE_HIERARCHY: Dict[str, object] = {
    "name": "Україна",
    "type": "країна",
    "children": [
        {
            "name": "Київська область",
            "type": "обласна військова адміністрація",
            "website": "https://kyivoda.gov.ua/",
            "children": [
                {
                    "name": "Білоцерківський район",
                    "type": "районна державна адміністрація",
                    "website": "https://bcrda.gov.ua/",
                    "children": [
                        {
                            "name": "Біла Церква",
                            "type": "міська рада",
                            "website": "https://bc-rada.gov.ua/",
                            "communities": [
                                {
                                    "name": "Білоцерківська міська територіальна громада",
                                    "website": "https://bc-rada.gov.ua/",
                                }
                            ],
                        },
                        {
                            "name": "Тараща",
                            "type": "міська рада",
                            "website": "https://tarashcha-rada.gov.ua/",
                            "communities": [
                                {
                                    "name": "Таращанська міська територіальна громада",
                                    "website": "https://tarashcha-rada.gov.ua/",
                                }
                            ],
                        },
                    ],
                },
                {
                    "name": "Бориспільський район",
                    "type": "районна державна адміністрація",
                    "website": "https://borsrda.gov.ua/",
                    "children": [
                        {
                            "name": "Бориспіль",
                            "type": "міська рада",
                            "website": "https://borispol-rada.gov.ua/",
                            "communities": [
                                {
                                    "name": "Бориспільська міська територіальна громада",
                                    "website": "https://borispol-rada.gov.ua/",
                                }
                            ],
                        },
                        {
                            "name": "Переяслав",
                            "type": "міська рада",
                            "website": "https://pereyaslavrada.gov.ua/",
                            "communities": [
                                {
                                    "name": "Переяславська міська територіальна громада",
                                    "website": "https://pereyaslavrada.gov.ua/",
                                }
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "name": "Львівська область",
            "type": "обласна військова адміністрація",
            "website": "https://loda.gov.ua/",
            "children": [
                {
                    "name": "Львівський район",
                    "type": "районна державна адміністрація",
                    "website": "https://lvivska-rda.gov.ua/",
                    "children": [
                        {
                            "name": "Львів",
                            "type": "міська рада",
                            "website": "https://city-adm.lviv.ua/",
                            "communities": [
                                {
                                    "name": "Львівська міська територіальна громада",
                                    "website": "https://city-adm.lviv.ua/",
                                },
                                {
                                    "name": "Рудківська міська територіальна громада",
                                    "website": "https://rudkivska-gromada.gov.ua/",
                                },
                            ],
                        },
                        {
                            "name": "Дрогобич",
                            "type": "міська рада",
                            "website": "https://drohobych-rada.gov.ua/",
                            "communities": [
                                {
                                    "name": "Дрогобицька міська територіальна громада",
                                    "website": "https://drohobych-rada.gov.ua/",
                                }
                            ],
                        },
                    ],
                }
            ],
        },
    ],
}


# Flattened view of official websites that will be iterated by the collector.
OFFICIAL_SOURCES: List[Dict[str, str]] = [
    {
        "name": "Київська ОВА",
        "admin_unit": "Київська область",
        "url": "https://kyivoda.gov.ua/",
    },
    {
        "name": "Київська обласна рада",
        "admin_unit": "Київська область",
        "url": "https://kor.gov.ua/",
    },
    {
        "name": "Біла Церква – міська рада",
        "admin_unit": "Біла Церква",
        "url": "https://bc-rada.gov.ua/",
    },
    {
        "name": "Бориспіль – міська рада",
        "admin_unit": "Бориспіль",
        "url": "https://borispol-rada.gov.ua/",
    },
    {
        "name": "Львівська ОВА",
        "admin_unit": "Львівська область",
        "url": "https://loda.gov.ua/",
    },
    {
        "name": "Львівська міська рада",
        "admin_unit": "Львів",
        "url": "https://city-adm.lviv.ua/",
    },
]


DEFAULT_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "derussification": (
        "дерусифіка",
        "derussification",
        "деколонізац",
    ),
    "decommunisation": (
        "декомунізац",
        "decommunis",
    ),
    "toponymy": (
        "топонім",
        "перейменув",
    ),
}


# ---------------------------------------------------------------------------
# Data containers.


@dataclass
class DecisionLink:
    """A single reference to an official decision."""

    category: str
    admin_unit: str
    title: str
    url: str
    source: str
    fetched_at: float = field(default_factory=time.time)
    note: Optional[str] = None


class DecisionRegistry:
    """Container for collected decision links."""

    def __init__(self, categories: Optional[Iterable[str]] = None) -> None:
        self._categories: Dict[str, List[DecisionLink]] = {
            category: [] for category in (categories or DEFAULT_KEYWORDS.keys())
        }
        self._errors: List[str] = []

    # -- internal helpers -------------------------------------------------

    def _ensure_category(self, category: str) -> None:
        if category not in self._categories:
            self._categories[category] = []

    # -- public API -------------------------------------------------------

    def add_link(
        self,
        category: str,
        admin_unit: str,
        title: str,
        url: str,
        source: str,
        note: Optional[str] = None,
    ) -> None:
        self._ensure_category(category)
        self._categories[category].append(
            DecisionLink(
                category=category,
                admin_unit=admin_unit,
                title=title.strip(),
                url=url,
                source=source,
                note=note,
            )
        )

    def add_error(self, message: str) -> None:
        LOGGER.warning("Collector error: %s", message)
        self._errors.append(message)

    @property
    def errors(self) -> List[str]:
        return self._errors

    def to_dict(self) -> Dict[str, List[Dict[str, object]]]:
        return {
            category: [link.__dict__ for link in links]
            for category, links in self._categories.items()
        }

    def to_csv(self, stream) -> None:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "category",
                "admin_unit",
                "title",
                "url",
                "source",
                "fetched_at",
                "note",
            ],
        )
        writer.writeheader()
        for links in self._categories.values():
            for link in links:
                writer.writerow(link.__dict__)

    def to_json(self, stream, ensure_ascii: bool = False, indent: int = 2) -> None:
        json.dump(self.to_dict(), stream, ensure_ascii=ensure_ascii, indent=indent)


# ---------------------------------------------------------------------------
# Collector implementation.


class _AnchorExtractor(HTMLParser):
    """HTML parser that extracts anchors.

    Accumulates *all* text nodes inside an ``<a>`` element so that nested
    tags (``<a href="…"><span>some</span> text</a>``) produce one entry
    with the full link text instead of separate fragments.
    """

    def __init__(self) -> None:
        super().__init__()
        self.links: List[Tuple[str, str]] = []
        self._current_href: Optional[str] = None
        self._text_parts: List[str] = []

    def _flush(self) -> None:
        if self._current_href is not None:
            text = " ".join("".join(self._text_parts).split()).strip()
            if text:
                self.links.append((text, self._current_href))
        self._current_href = None
        self._text_parts = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        if tag.lower() != "a":
            return
        # Flush any previous unclosed anchor before starting a new one.
        if self._current_href is not None:
            self._flush()
        href = None
        for key, value in attrs:
            if key.lower() == "href":
                href = value
                break
        if href is not None:
            self._current_href = href
            self._text_parts = []

    def handle_endtag(self, tag: str):
        if tag.lower() == "a":
            self._flush()

    def handle_data(self, data: str):
        if self._current_href is not None:
            self._text_parts.append(data)


class OfficialSourceCollector:
    """Iterate over official sources and extract candidate links."""

    def __init__(
        self,
        sources: Iterable[Dict[str, str]],
        keywords: Optional[Dict[str, Tuple[str, ...]]] = None,
    ) -> None:
        self.sources = list(sources)
        self.keywords = keywords or DEFAULT_KEYWORDS

    # -- network ----------------------------------------------------------

    def fetch(self, url: str) -> str:
        LOGGER.info("Fetching %s", url)
        with urlopen(url, timeout=15) as response:  # nosec - trusted domains
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")

    # -- parsing ----------------------------------------------------------

    def extract_anchors(self, html: str) -> List[Tuple[str, str]]:
        parser = _AnchorExtractor()
        parser.feed(html)
        return parser.links

    def match_category(self, text: str) -> Optional[str]:
        lowered = text.lower()
        for category, needles in self.keywords.items():
            if any(needle in lowered for needle in needles):
                return category
        return None

    # -- public API -------------------------------------------------------

    def collect(self, registry: DecisionRegistry) -> DecisionRegistry:
        for source in self.sources:
            url = source.get("url")
            if not url:
                registry.add_error(f"Source without URL: {source}")
                continue
            name = source.get("name", url)
            admin_unit = source.get("admin_unit", name)
            try:
                html = self.fetch(url)
            except URLError as exc:  # pragma: no cover - depends on network
                registry.add_error(f"Не вдалося отримати {url}: {exc}")
                continue
            except Exception as exc:  # pragma: no cover - defensive
                registry.add_error(f"Помилка під час обробки {url}: {exc}")
                continue

            for text, href in self.extract_anchors(html):
                category = self.match_category(text)
                if not category:
                    continue
                absolute_url = urljoin(url, href)
                registry.add_link(
                    category=category,
                    admin_unit=admin_unit,
                    title=text,
                    url=absolute_url,
                    source=name,
                )
        return registry


def collect_official_decisions() -> DecisionRegistry:
    """Convenience helper for one-off collection runs."""

    registry = DecisionRegistry()
    collector = OfficialSourceCollector(OFFICIAL_SOURCES)
    collector.collect(registry)
    return registry


__all__ = [
    "ADMINISTRATIVE_HIERARCHY",
    "OFFICIAL_SOURCES",
    "DEFAULT_KEYWORDS",
    "DecisionLink",
    "DecisionRegistry",
    "OfficialSourceCollector",
    "collect_official_decisions",
]

