"""Scraper for SETAM (setam.net.ua) — the State Enterprise for Auctions.

SETAM publishes auctions of seized property, NPL portfolios, and various
asset lots.  The platform exposes a public JSON search API that this module
queries to locate NPL-related lots.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from scripts.scrapers.base import BaseScraper

LOGGER = logging.getLogger(__name__)

# SETAM public search API
SETAM_SEARCH_URL = "https://setam.net.ua/api/auction/search"
SETAM_LOT_URL = "https://setam.net.ua/api/auction/"
SETAM_BASE = "https://setam.net.ua"

# Keywords that indicate NPL / rights-of-claim portfolios
NPL_KEYWORDS = [
    "право вимоги",
    "права вимоги",
    "портфель",
    "кредитний портфель",
    "кредитні зобов'язання",
    "дебіторська заборгованість",
    "боргові зобов'язання",
    "права вимоги за кредитн",
    "непрацюючі активи",
]


class SetamScraper(BaseScraper):
    """Scrape SETAM for NPL portfolio auctions."""

    def search_npl(
        self,
        page: int = 1,
        per_page: int = 50,
        status: str = "",
    ) -> List[Dict[str, Any]]:
        """Search SETAM for lots matching NPL keywords.

        Returns raw lot dicts from the SETAM API.
        """
        results: List[Dict[str, Any]] = []

        for keyword in NPL_KEYWORDS:
            params = {
                "query": keyword,
                "page": page,
                "perPage": per_page,
            }
            if status:
                params["status"] = status

            data = self.safe_fetch_json(SETAM_SEARCH_URL, params)
            if not data:
                continue

            items = data if isinstance(data, list) else data.get("items", data.get("data", []))
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and item.get("id"):
                        # Avoid duplicates by external_id
                        if not any(r.get("id") == item["id"] for r in results):
                            results.append(item)

            LOGGER.info("SETAM search '%s': found %d items", keyword, len(items) if isinstance(items, list) else 0)

        return results

    def get_lot_details(self, lot_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full details for a specific SETAM lot."""
        return self.safe_fetch_json(f"{SETAM_LOT_URL}{lot_id}")

    def parse_lot(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a SETAM lot dict into our standard auction format."""
        lot_id = str(raw.get("id", ""))
        title = raw.get("title", raw.get("name", ""))
        description = raw.get("description", "")

        # Extract financial data from description
        total_debt = _extract_amount(description, r"(?:загальн|сум)[а-яі]*\s*(?:борг|заборгован)[а-яі]*[:\s]*([\d\s,.]+)")
        start_price = raw.get("startPrice") or raw.get("start_price")
        current_price = raw.get("currentPrice") or raw.get("current_price") or start_price
        guarantee = raw.get("guaranteeAmount") or raw.get("guarantee_amount")

        # Determine portfolio type from description
        portfolio_type = "mixed"
        desc_lower = (title + " " + description).lower()
        if "фіз" in desc_lower and "юр" not in desc_lower:
            portfolio_type = "physical"
        elif "юр" in desc_lower and "фіз" not in desc_lower:
            portfolio_type = "legal"

        # Determine debt type
        debt_type = "credit"
        if "овердрафт" in desc_lower:
            debt_type = "overdraft"
        elif "дебіторськ" in desc_lower:
            debt_type = "receivables"

        num_debtors = _extract_int(description, r"(\d+)\s*(?:боржник|позичальник|договор)")

        return {
            "source": "setam",
            "external_id": lot_id,
            "title": title,
            "description": description,
            "seller": raw.get("organizer", {}).get("name", "") if isinstance(raw.get("organizer"), dict) else raw.get("organizer", ""),
            "seller_type": _guess_seller_type(raw.get("organizer", "")),
            "portfolio_type": portfolio_type,
            "debt_type": debt_type,
            "total_debt": total_debt,
            "num_debtors": num_debtors,
            "start_price": _to_float(start_price),
            "guarantee_amount": _to_float(guarantee),
            "current_price": _to_float(current_price),
            "currency": "UAH",
            "auction_date": raw.get("auctionDate") or raw.get("auction_date"),
            "end_date": raw.get("endDate") or raw.get("end_date"),
            "status": raw.get("status", "active"),
            "url": f"{SETAM_BASE}/auction/{lot_id}" if lot_id else None,
            "passport_url": raw.get("passportUrl") or raw.get("passport_url"),
            "raw_data": raw,
        }


class SetamHTMLScraper(BaseScraper):
    """Fallback HTML-based scraper for SETAM when API is unavailable."""

    def search_npl_html(self) -> List[Dict[str, str]]:
        from scripts.scrapers.base import extract_links
        results = []
        for keyword in NPL_KEYWORDS[:3]:
            url = f"{SETAM_BASE}/search?query={keyword}"
            html = self.safe_fetch(url)
            if not html:
                continue
            links = extract_links(html, SETAM_BASE, keywords=["право вимоги", "портфель", "кредит"])
            for text, href in links:
                results.append({"title": text, "url": href})
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        if isinstance(val, str):
            val = val.replace(" ", "").replace(",", ".")
        return float(val)
    except (ValueError, TypeError):
        return None


def _extract_amount(text: str, pattern: str) -> Optional[float]:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return _to_float(match.group(1))
    return None


def _extract_int(text: str, pattern: str) -> Optional[int]:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1).replace(" ", ""))
        except ValueError:
            pass
    return None


def _guess_seller_type(organizer: Any) -> str:
    if not organizer:
        return "unknown"
    name = str(organizer).lower() if not isinstance(organizer, dict) else str(organizer.get("name", "")).lower()
    if any(k in name for k in ("банк", "bank")):
        return "bank"
    if any(k in name for k in ("мікрофінанс", "мфо", "кредитн")):
        return "mfo"
    if any(k in name for k in ("фінансов", "компанія", "факторинг")):
        return "fc"
    if "фонд гарантування" in name:
        return "dgf"
    return "other"
