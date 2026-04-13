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
KNOWN_LOTS: List[Dict[str, Any]] = [

    # ===================== АКТУАЛЬНІ / ПІДТВЕРДЖЕНІ =====================

    {
        "category": "active",
        "source": "ProZorro/Комерційний",
        "seller": "—",
        "what": "Пул активів: права вимоги за кредитними та телеком-договорами з фіз. та юр. особами — 14 366 договорів",
        "title": "Пул 14 366 договорів (кредити + телеком) м.Київ",
        "url": "https://prozorro.sale/auction/CSE001-UA-20260317-02812/",
        "num_contracts": 14366,
        "total_debt": None,
        "avg_debt": None,
        "start_price": None,
        "auction_type": "Комерційний продаж (зниження ціни)",
        "guarantee": "",
        "auction_date": "2026-03-17",
        "auction_time": "",
        "status": "активний",
    },
    {
        "category": "history",
        "source": "SETAM/ПриватБанк",
        "seller": "АТ КБ «ПриватБанк»",
        "what": "Права вимоги за беззаставними кредитними договорами з фізичними особами",
        "title": "ПриватБанк — права вимоги фіз.осіб (ВІДБУЛИСЯ)",
        "url": "https://setam.net.ua/auction/576099",
        "num_contracts": None,
        "total_debt": 5203956695.69,
        "avg_debt": None,
        "start_price": 5203956695.69,
        "sold_price": None,
        "sold_pct": None,
        "auction_type": "Редукціон",
        "guarantee": "Згідно з правилами SETAM",
        "auction_date": "",
        "auction_time": "",
        "status": "торги відбулися",
    },
    {
        "category": "watching",
        "source": "SETAM/Укрексімбанк",
        "seller": "АТ «Укрексімбанк»",
        "what": "Права вимоги за кредитними договорами з юридичними особами (РАІЗ-МАКСИМКО, АВАНГАРД, ІМПЕРОВО ФУДЗ, ПАККО ХОЛДІНГ)",
        "title": "Укрексімбанк — права вимоги юр.осіб (НЕ ВІДБУВСЯ)",
        "url": "https://setam.net.ua/auction/564348",
        "num_contracts": None,
        "total_debt": 4984663467.30,
        "avg_debt": None,
        "start_price": 4984663467.30,
        "auction_type": "Редукціон",
        "guarantee": "74 769 952.01 грн",
        "auction_date": "2025-03-07",
        "auction_time": "09:00",
        "status": "торги не відбулися 07.03.2025 — очікується повторний",
        "watch_reason": "Аукціон не відбувся через відсутність заявок. Очікується перевиставлення зі зниженою ціною.",
        "auctions_passed": 1,
        "auctions_expected": 2,
    },

    # ===================== НА СПОСТЕРЕЖЕННІ (хантер) =====================

    {
        "category": "watching",
        "source": "ProZorro/ФГВ",
        "seller": "ФГВ (Фонд гарантування вкладів)",
        "what": "Пул: права вимоги за кредитами фіз.осіб + дебіторка юр.осіб + основні засоби + транспорт",
        "title": "ФГВ — пул активів (кредити + дебіторка + ОЗ)",
        "url": "https://prozorro.sale/auction/GFD001-UA-20260205-03708/",
        "num_contracts": None,
        "total_debt": None,
        "avg_debt": None,
        "start_price": 8457238.13,
        "auction_type": "Голландський аукціон (ФГВ)",
        "guarantee": "~5% від стартової ціни (~422 862 грн)",
        "auction_date": "",
        "auction_time": "",
        "status": "не відбувся — СЛІДКУЄМО за повторним",
        "watch_reason": "Перший аукціон не відбувся — буде перевиставлений зі зниженою ціною. Потенційно вигідна угода.",
        "auctions_passed": 1,
        "auctions_expected": 2,
    },

    # ===================== ІСТОРІЯ (для аналітики цін) =====================

    {
        "category": "history",
        "source": "SETAM/ПриватБанк",
        "seller": "АТ КБ «ПриватБанк»",
        "what": "Права вимоги за портфелем карткових кредитів фіз.осіб — 80 545 договорів",
        "title": "ПриватБанк — 80 545 карткових кредитів (ПРОДАНО)",
        "url": "https://setam.net.ua/auction/541272",
        "num_contracts": 80545,
        "total_debt": 501395467.60,
        "avg_debt": 6225.0,
        "start_price": 501395467.60,
        "sold_price": 13101000.00,
        "sold_pct": 2.6,
        "auction_type": "Редукціон",
        "guarantee": "526 465.24 грн",
        "auction_date": "2024-02-23",
        "auction_time": "09:00",
        "status": "завершено — продано 23.02.2024",
    },
    {
        "category": "history",
        "source": "ProZorro",
        "seller": "Банк",
        "what": "Кредитний портфель — права вимоги за кредитами юр.осіб",
        "title": "Кредитний портфель юр.осіб (завершено)",
        "url": "https://prozorro.sale/auction/CSD001-UA-20250711-29449/",
        "num_contracts": None,
        "total_debt": None,
        "avg_debt": None,
        "start_price": 178110088.04,
        "sold_price": 28497614.09,
        "sold_pct": 16.0,
        "auction_type": "Гібридний голландський",
        "guarantee": "",
        "auction_date": "2025-07-11",
        "auction_time": "",
        "status": "завершено",
    },
]

# КС Фортеця — пакет 12 лотів, квітень 2026 (verified via WebSearch)
# Справа про банкрутство №14 01-10 1523
# Рішення суду: 27.01.2026, чинне з 25.02.2026
# Арбітражний керуючий: Пилипенко Т.В., тел. 067-224-51-17
_FORTETSYA_BASE = "https://ubiz.ua/sale3/auction/"
_FORTETSYA_LOTS = [
    ("BRE001-UA-20260410-57627", "Магай Г.В.", 777625.66),
    ("BRE001-UA-20260410-83171", "Ковтун Ю.О.", 303866.14),
    ("BRE001-UA-20260410-06629", "Степаненко А.П.", 155047.24),
    ("BRE001-UA-20260410-28967", "Пушкаренко С.М.", 82254.59),
    ("BRE001-UA-20260410-84534", "Блізніцов Р.В.", 34035.70),
    ("BRE001-UA-20260410-98084", "Канюка О.М.", 28631.76),
    ("BRE001-UA-20260410-51940", "Семененко О.А.", 23042.34),
    ("BRE001-UA-20260410-52757", "Кобяков С.В.", 15227.46),
    ("BRE001-UA-20260410-86605", "Даценко О.І.", 8844.40),
    ("BRE001-UA-20260410-68351", "Погорелов П.Я.", 6770.44),
    ("BRE001-UA-20260410-68372", "Зарайський В.Ю.", 4688.17),
    ("BRE001-UA-20260410-12395", "Анголюк І.В.", 3144.56),
]
_FORTETSYA_TOTAL = sum(amt for _, _, amt in _FORTETSYA_LOTS)

for lot_id, debtor, amount in _FORTETSYA_LOTS:
    KNOWN_LOTS.append({
        "category": "active",
        "source": "ProZorro/Банкрутство",
        "seller": "КС «Фортеця» (арб.керуючий Пилипенко Т.В.)",
        "what": f"Право вимоги (дебіторська заборгованість) до фіз.особи {debtor}",
        "title": f"Дебіторка {debtor} — {amount:,.2f} грн",
        "url": f"{_FORTETSYA_BASE}{lot_id}",
        "num_contracts": 1,
        "total_debt": amount,
        "avg_debt": amount,
        "start_price": amount,
        "auction_type": "Англійський аукціон (3 раунди)",
        "guarantee": f"5% = {amount * 0.05:,.0f} грн",
        "auction_date": "2026-04-10",
        "auction_time": "",
        "status": "квітень 2026",
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
