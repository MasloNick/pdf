"""Scraper for ProZorro.Sale (prozorro.sale/privatization) — Ukrainian public auction system.

ProZorro.Sale is the mandatory platform for selling state-owned assets and
DGF (Deposit Guarantee Fund) lots.  It has a public REST API.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from scripts.scrapers.base import BaseScraper

LOGGER = logging.getLogger(__name__)

# ProZorro.Sale public API endpoints
# Docs: https://procedure-staging.prozorro.sale/api/doc
# Real search: https://procedure.prozorro.sale/api/search/byDateModified/{date}?limit=100
PROZORRO_API = "https://procedure.prozorro.sale/api"
PROZORRO_SEARCH = f"{PROZORRO_API}/search/byDateModified"
PROZORRO_BASE = "https://prozorro.sale"

# DGF-specific search (assets of liquidated banks)
DGF_CATEGORY = "legitimatePropertyLease-english"

NPL_SEARCH_TERMS = [
    "право вимоги",
    "права вимоги",
    "кредитний портфель",
    "портфель прав вимоги",
    "дебіторська заборгованість",
]


class ProzorroScraper(BaseScraper):
    """Scrape ProZorro.Sale for NPL portfolio auctions."""

    def search_npl(
        self,
        limit: int = 100,
        date_from: str = "",
    ) -> List[Dict[str, Any]]:
        """Search ProZorro.Sale for NPL lots.

        The ProZorro.Sale API does NOT support keyword search.  The real
        endpoint is ``/api/search/byDateModified/{iso_date}?limit=N``
        which returns procedures modified since *date_from*.  We fetch a
        batch and then filter locally by NPL keywords.
        """
        if not date_from:
            # Default: look at procedures modified in the last 90 days
            import datetime
            date_from = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()

        url = f"{PROZORRO_SEARCH}/{date_from}"
        data = self.safe_fetch_json(url, {"limit": limit})
        if not data:
            return []

        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not isinstance(items, list):
            return []

        # Filter by NPL-related keywords in title/description
        results: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            text = (
                str(item.get("title", "")) + " " + str(item.get("description", ""))
            ).lower()
            if any(term in text for term in NPL_SEARCH_TERMS):
                ext_id = item.get("id") or item.get("_id")
                if ext_id and not any(r.get("id") == ext_id for r in results):
                    results.append(item)

        LOGGER.info("ProZorro: fetched %d items, %d match NPL keywords", len(items), len(results))
        return results

    def get_procedure_details(self, procedure_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full details for a procedure."""
        return self.safe_fetch_json(f"{PROZORRO_SEARCH}/{procedure_id}")

    def parse_procedure(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a ProZorro procedure dict into our standard format."""
        proc_id = str(raw.get("id", raw.get("_id", "")))
        title = raw.get("title", "")
        description = raw.get("description", "")

        # Extract seller/organizer
        seller_info = raw.get("sellingEntity", raw.get("organizer", {}))
        seller_name = ""
        if isinstance(seller_info, dict):
            seller_name = seller_info.get("name", seller_info.get("identifier", {}).get("legalName", ""))

        # Financial data
        value = raw.get("value", {})
        start_price = value.get("amount") if isinstance(value, dict) else None
        currency = value.get("currency", "UAH") if isinstance(value, dict) else "UAH"

        guarantee = raw.get("guarantee", {})
        guarantee_amount = guarantee.get("amount") if isinstance(guarantee, dict) else None

        # Items / lots analysis
        items = raw.get("items", [])
        num_items = len(items) if isinstance(items, list) else 0

        # Detect portfolio type
        full_text = (title + " " + description).lower()
        portfolio_type = "mixed"
        if "фізичн" in full_text and "юридичн" not in full_text:
            portfolio_type = "physical"
        elif "юридичн" in full_text and "фізичн" not in full_text:
            portfolio_type = "legal"

        return {
            "source": "prozorro",
            "external_id": proc_id,
            "title": title,
            "description": description,
            "seller": seller_name,
            "seller_type": _guess_seller_type_prozorro(seller_name, raw),
            "portfolio_type": portfolio_type,
            "debt_type": _detect_debt_type(full_text),
            "total_debt": _extract_total_debt(description),
            "num_debtors": num_items or _extract_num_debtors(description),
            "start_price": start_price,
            "guarantee_amount": guarantee_amount,
            "current_price": start_price,
            "currency": currency,
            "auction_date": raw.get("auctionPeriod", {}).get("startDate") if isinstance(raw.get("auctionPeriod"), dict) else None,
            "end_date": raw.get("auctionPeriod", {}).get("endDate") if isinstance(raw.get("auctionPeriod"), dict) else None,
            "status": raw.get("status", "active"),
            "url": f"{PROZORRO_BASE}/auction/{proc_id}" if proc_id else None,
            "passport_url": None,
            "raw_data": raw,
        }


class DGFScraper(BaseScraper):
    """Scrape DGF (Deposit Guarantee Fund) specific data.

    The DGF sells assets of liquidated banks, including NPL portfolios,
    primarily through ProZorro.Sale.  This scraper also checks the DGF
    website directly for announcements.
    """

    DGF_SITE = "https://www.fg.gov.ua"
    DGF_ASSETS_URL = f"{DGF_SITE}/asset-management"

    def search_dgf_sales(self) -> List[Dict[str, str]]:
        """Search fg.gov.ua for NPL portfolio sale announcements."""
        from scripts.scrapers.base import extract_links
        results = []
        keywords = [
            "право вимоги", "портфель", "кредитн", "продаж актив",
            "реалізація", "непрацюючі", "дебіторськ",
        ]

        for page_url in [self.DGF_ASSETS_URL, f"{self.DGF_SITE}/news"]:
            html = self.safe_fetch(page_url)
            if not html:
                continue
            links = extract_links(html, self.DGF_SITE, keywords=keywords)
            for text, href in links:
                if not any(r["url"] == href for r in results):
                    results.append({"title": text, "url": href, "source": "dgf"})

        LOGGER.info("DGF site scan: found %d relevant links", len(results))
        return results

    def get_dgf_sold_portfolios(self, year_from: int = 2020) -> List[Dict[str, str]]:
        """Attempt to find DGF sold portfolio records since *year_from*."""
        from scripts.scrapers.base import extract_links
        results = []
        keywords = ["реалізовано", "продано", "переможець", "результат"]

        # Check multiple pages for historical data
        for year in range(year_from, 2027):
            url = f"{self.DGF_SITE}/news?year={year}"
            html = self.safe_fetch(url)
            if not html:
                continue
            links = extract_links(html, self.DGF_SITE, keywords=keywords + ["право вимоги", "портфель"])
            for text, href in links:
                if not any(r["url"] == href for r in results):
                    results.append({
                        "title": text,
                        "url": href,
                        "year": str(year),
                        "source": "dgf",
                    })

        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import re


def _guess_seller_type_prozorro(name: str, raw: Dict[str, Any]) -> str:
    lower = name.lower()
    if "фонд гарантування" in lower:
        return "dgf"
    if any(k in lower for k in ("банк", "bank")):
        return "bank"
    if any(k in lower for k in ("мікрофінанс", "мфо")):
        return "mfo"
    if any(k in lower for k in ("фінансов", "факторинг")):
        return "fc"
    return "other"


def _detect_debt_type(text: str) -> str:
    if "овердрафт" in text:
        return "overdraft"
    if "дебіторськ" in text:
        return "receivables"
    return "credit"


def _extract_total_debt(text: str) -> Optional[float]:
    patterns = [
        r"(?:загальн|сум)[а-яіїє]*\s*(?:борг|заборгован)[а-яіїє]*[:\s]*([\d\s,.]+)",
        r"([\d\s,.]+)\s*(?:грн|UAH|гривень)",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            val = match.group(1).replace(" ", "").replace(",", ".")
            try:
                return float(val)
            except ValueError:
                continue
    return None


def _extract_num_debtors(text: str) -> Optional[int]:
    match = re.search(r"(\d+)\s*(?:боржник|позичальник|договор|кредит)", text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    return None
