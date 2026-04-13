"""Unified NPL auction scraper.

Instead of hitting SETAM/ProZorro/DGF directly (they use JavaScript
rendering that urllib cannot parse), we use:

1. **ubiz.ua** — accredited ProZorro.Sale marketplace with plain HTML
2. **prozorro.sale/auction/** — individual lot pages (verified working)
3. **fg.gov.ua** — DGF asset sales pages
4. **sale.uub.com.ua** — another accredited marketplace

All URLs verified April 2026.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from scripts.scrapers.base import BaseScraper, extract_links
from scripts.scrapers.lots_data import LOTS as _VERIFIED_LOTS

LOGGER = logging.getLogger(__name__)

# Verified working search/listing URLs
SOURCES = {
    "ubiz": {
        "name": "UBIZ.UA (ProZorro.Sale)",
        "base": "https://ubiz.ua",
        "urls": [
            "https://ubiz.ua/auctions-all/finance",
        ],
        "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ", "заборгован"],
    },
    "uub": {
        "name": "UUB (Українська Універсальна Біржа)",
        "base": "https://sale.uub.com.ua",
        "urls": [
            "https://sale.uub.com.ua/filter/bankrupts-property",
        ],
        "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"],
    },
    "dgf": {
        "name": "ФГВ — Фонд гарантування вкладів",
        "base": "https://www.fg.gov.ua",
        "urls": [
            "https://www.fg.gov.ua/aktivi-bankiv/prodazh-aktiviv",
            "https://bnk.fg.gov.ua/prodazh-aktiviv/prodazh-aktiviv-banku",
        ],
        "keywords": ["право вимоги", "портфель", "кредитн", "реалізація", "продаж актив", "пул актив"],
    },
    "setam": {
        "name": "SETAM",
        "base": "https://setam.net.ua",
        "urls": [
            "https://setam.net.ua/auctions",
        ],
        "keywords": ["право вимоги", "кредитн", "портфель"],
    },
}

# Known lots (verified via WebSearch April 2026)
# category: "active" | "watching" | "history"
# ВАЖЛИВО: статус "active" = ПЕРЕВІРЕНО що лот ще діє
#           статус "check" = потрібно перевірити на сайті
# KNOWN_LOTS — порожній, всі перевірені лоти в lots_data.py
# Скрапер додає нові лоти автоматично при кожному скануванні
KNOWN_LOTS: List[Dict[str, Any]] = []


class AuctionScraper(BaseScraper):
    """Unified scraper that tries multiple sources."""

    def scan_all(self) -> Dict[str, Any]:
        """Scan all sources and return results + errors."""
        results: Dict[str, List[Dict[str, str]]] = {}
        errors: List[str] = []

        for key, src in SOURCES.items():
            found: List[Dict[str, str]] = []
            for url in src["urls"]:
                html = self.safe_fetch(url)
                if not html:
                    continue
                links = extract_links(html, src["base"], keywords=src["keywords"])
                for text, href in links:
                    if not any(f["url"] == href for f in found):
                        found.append({
                            "title": text,
                            "url": href,
                            "source": src["name"],
                        })
            results[key] = found
            errors.extend(self.errors)
            self.errors.clear()
            LOGGER.info("%s: знайдено %d", src["name"], len(found))

        return {"scraped": results, "known": KNOWN_LOTS, "errors": errors}


def get_known_lots() -> List[Dict[str, Any]]:
    """Return list of known/verified NPL lots from lots_data.py + KNOWN_LOTS.

    Automatically moves lots with past auction_date to 'history'.
    """
    import datetime
    today = datetime.date.today()

    combined = list(_VERIFIED_LOTS)
    existing_urls = {l["url"] for l in combined}
    for lot in KNOWN_LOTS:
        if lot["url"] not in existing_urls:
            combined.append(lot)

    # Auto-reclassify: past dates → history
    for lot in combined:
        if lot.get("category") not in ("active", "watching"):
            continue
        date_str = lot.get("auction_date", "")
        if not date_str:
            continue
        try:
            lot_date = datetime.date.fromisoformat(date_str)
            if lot_date < today:
                lot["category"] = "history"
                if "status" not in lot or "продано" not in lot.get("status", "").lower():
                    lot["status"] = f"минув {date_str}"
        except (ValueError, TypeError):
            pass

    # Auto-classify asset_type based on text
    for lot in combined:
        if lot.get("asset_type"):
            continue
        lot["asset_type"] = _classify_asset_type(lot)

    return combined


def _classify_asset_type(lot: Dict[str, Any]) -> str:
    """Determine asset_type from lot text fields."""
    text = " ".join([
        lot.get("what", ""), lot.get("title", ""),
        lot.get("seller", ""), lot.get("source", ""),
    ]).lower()

    # Пул активів (змішане: кредити + дебіторка + ОЗ)
    if "пул актив" in text or ("кредит" in text and "дебіторськ" in text):
        return "asset_pool"

    # Змішане (кредити + телеком)
    if "телеком" in text or ("кредит" in text and "телеком" in text):
        return "mixed"

    # Дебіторська заборгованість (борг контрагента підприємству, НЕ кредит)
    if "дебіторськ" in text or "дебіторка" in text:
        # Перевірка: якщо продавець банк/ФГВ — це скоріше NPL кредит
        if any(w in text for w in ("банк", "фгв", "фонд гарантування", "приватбанк", "ощадбанк", "ексім")):
            return "npl_credit_mixed"
        return "receivable"

    # Права вимоги за кредитами
    if "кредитн" in text or "позичальник" in text or "кредит" in text:
        if "юр" in text or "юридичн" in text:
            return "npl_credit_corporate"
        if "іпотек" in text or "забезпечен" in text or "автокредит" in text or "транспорт" in text:
            return "npl_credit_secured"
        if "беззастав" in text or "картков" in text or "споживч" in text or "фіз" in text:
            return "npl_credit_unsecured"
        return "npl_credit_mixed"

    # Відступлення
    if "відступлення" in text or "факторинг" in text:
        return "assignment"

    # Право вимоги загальне (зобов'язання в банкрутстві)
    if "право вимоги" in text or "зобов'язання" in text:
        return "receivable"

    return "unknown"


# Human-readable labels for asset_type
ASSET_TYPE_LABELS = {
    "npl_credit_unsecured": "Права вимоги за беззаставними кредитами",
    "npl_credit_secured": "Права вимоги за забезпеченими кредитами (іпотека/авто)",
    "npl_credit_corporate": "Права вимоги за кредитами юр.осіб",
    "npl_credit_mixed": "Змішаний кредитний портфель",
    "receivable": "Дебіторська заборгованість",
    "assignment": "Відступлення права вимоги",
    "asset_pool": "Пул активів (кредити + дебіторка + ОЗ)",
    "mixed": "Змішаний (кредити + телеком + інше)",
    "unknown": "Не класифіковано",
}
