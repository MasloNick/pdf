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

LOGGER = logging.getLogger(__name__)

# Verified working search/listing URLs
SOURCES = {
    "ubiz": {
        "name": "UBIZ.UA (ProZorro.Sale)",
        "base": "https://ubiz.ua",
        "urls": [
            "https://ubiz.ua/sale3/filter/bankrupts-property?query=%D0%BF%D1%80%D0%B0%D0%B2%D0%BE+%D0%B2%D0%B8%D0%BC%D0%BE%D0%B3%D0%B8",
            "https://ubiz.ua/sale3/filter/bankrupts-property?query=%D0%BA%D1%80%D0%B5%D0%B4%D0%B8%D1%82%D0%BD%D0%B8%D0%B9+%D0%BF%D0%BE%D1%80%D1%82%D1%84%D0%B5%D0%BB%D1%8C",
            "https://ubiz.ua/sale3/filter/bankrupts-property?query=%D0%B4%D0%B5%D0%B1%D1%96%D1%82%D0%BE%D1%80%D1%81%D1%8C%D0%BA%D0%B0+%D0%B7%D0%B0%D0%B1%D0%BE%D1%80%D0%B3%D0%BE%D0%B2%D0%B0%D0%BD%D1%96%D1%81%D1%82%D1%8C",
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

# Known active lots (verified via WebSearch April 2026)
# category: "active" | "upcoming" | "failed" | "history"
KNOWN_LOTS: List[Dict[str, str]] = [

    # ===================== АКТУАЛЬНІ / АКТИВНІ =====================

    {
        "category": "active",
        "source": "ProZorro",
        "title": "Аукціон з продажу права вимоги (комерційний продаж)",
        "url": "https://prozorro.sale/auction/CSE001-UA-20260317-02812/",
        "price": "",
        "auction_type": "Голландський аукціон",
        "guarantee": "",
        "status": "активний",
        "seller": "",
        "date": "березень 2026",
    },
    {
        "category": "active",
        "source": "SETAM/ПриватБанк",
        "title": "Редукціон. Права вимоги за договорами позичальників — фізичних осіб",
        "url": "https://setam.net.ua/auction/576099",
        "price": "5 203 956 695 грн (загальний борг)",
        "auction_type": "Редукціон (зниження ціни)",
        "guarantee": "Згідно з правилами SETAM",
        "status": "активний",
        "seller": "ПриватБанк",
        "date": "діючий",
    },
    {
        "category": "active",
        "source": "SETAM/Укрексімбанк",
        "title": "Редукціон. Права вимоги за кредитними договорами юридичних осіб",
        "url": "https://setam.net.ua/auction/564348",
        "price": "4 984 663 467 грн (загальний борг)",
        "auction_type": "Редукціон (зниження ціни)",
        "guarantee": "Згідно з правилами SETAM",
        "status": "активний",
        "seller": "Укрексімбанк",
        "date": "діючий",
    },
    {
        "category": "active",
        "source": "SETAM/ПриватБанк",
        "title": "Портфель 80 545 договорів фіз.осіб, борг 501 395 467 грн",
        "url": "https://setam.net.ua/auction/541272",
        "price": "10 529 304 грн (2.1% від боргу)",
        "auction_type": "Редукціон (крок 1%)",
        "guarantee": "Згідно з правилами SETAM",
        "status": "редукціон",
        "seller": "ПриватБанк",
        "date": "діючий",
    },

    # ===================== НЕ ВІДБУЛИСЯ (можуть перевиставити) =====================

    {
        "category": "failed",
        "source": "ProZorro/ФГВ",
        "title": "Пул активів: права вимоги за кредитними договорами з фіз.особами + дебіторка юр.осіб + основні засоби",
        "url": "https://prozorro.sale/auction/GFD001-UA-20260205-03708/",
        "price": "8 457 238 грн",
        "auction_type": "Голландський аукціон (ФГВ)",
        "guarantee": "~5% від стартової ціни",
        "status": "не відбувся — очікується повторний",
        "seller": "ФГВ",
        "date": "лютий 2026",
    },

    # ===================== ІСТОРІЯ (завершені продажі для аналітики) =====================

    {
        "category": "history",
        "source": "ProZorro",
        "title": "Кредитний портфель — права вимоги за кредитами юр.осіб",
        "url": "https://prozorro.sale/auction/CSD001-UA-20250711-29449/",
        "price": "178 110 088 грн → продано за 28 497 614 грн (16%)",
        "auction_type": "Гібридний голландський",
        "guarantee": "",
        "status": "завершено",
        "seller": "Банк",
        "date": "липень 2025",
    },
]

# КС Фортеця — пакет лотів квітень 2026 (verified) — АКТУАЛЬНІ
_FORTETSYA_BASE = "https://ubiz.ua/sale3/auction/"
_FORTETSYA_LOTS = [
    ("BRE001-UA-20260410-57627", "Магай Г.В.", "777 625 грн"),
    ("BRE001-UA-20260410-83171", "Ковтун Ю.О.", "303 866 грн"),
    ("BRE001-UA-20260410-06629", "Степаненко А.П.", "155 047 грн"),
    ("BRE001-UA-20260410-28967", "Пушкаренко С.М.", "82 254 грн"),
    ("BRE001-UA-20260410-84534", "Блізніцов Р.В.", "34 035 грн"),
    ("BRE001-UA-20260410-98084", "Канюка О.М.", "28 631 грн"),
    ("BRE001-UA-20260410-51940", "Семененко О.А.", "23 042 грн"),
    ("BRE001-UA-20260410-52757", "Кобяков С.В.", "15 227 грн"),
    ("BRE001-UA-20260410-86605", "Даценко О.І.", "8 844 грн"),
    ("BRE001-UA-20260410-68351", "Погорелов П.Я.", "6 770 грн"),
    ("BRE001-UA-20260410-68372", "Зарайський В.Ю.", "4 688 грн"),
    ("BRE001-UA-20260410-12395", "Анголюк І.В.", "3 144 грн"),
]
for lot_id, debtor, amount in _FORTETSYA_LOTS:
    KNOWN_LOTS.append({
        "category": "active",
        "source": "ProZorro/Банкрутство",
        "title": f"Право вимоги (дебіторка) до {debtor} — {amount}",
        "url": f"{_FORTETSYA_BASE}{lot_id}",
        "price": amount,
        "auction_type": "Англійський аукціон",
        "guarantee": "5% від стартової ціни",
        "status": "квітень 2026",
        "seller": "КС Фортеця (арб.керуючий Пилипенко Т.В.)",
        "date": "10.04.2026",
    })


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


def get_known_lots() -> List[Dict[str, str]]:
    """Return list of known/verified NPL lots without scraping."""
    return KNOWN_LOTS.copy()
