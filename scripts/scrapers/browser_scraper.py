"""Real browser scraper using Playwright.

Парсить JS-сайти (SETAM, ProZorro, ubiz.ua, банки) через справжній
Chromium браузер. Знаходить лоти з правами вимоги автоматично.

Встановлення (один раз):
    pip install playwright
    playwright install chromium
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

LOGGER = logging.getLogger(__name__)

# Джерела для парсингу з реальними URL
BROWSER_SOURCES = [
    {
        "name": "ProZorro.Sale — право вимоги",
        "url": "https://prozorro.sale/auction/search?query=%D0%BF%D1%80%D0%B0%D0%B2%D0%BE+%D0%B2%D0%B8%D0%BC%D0%BE%D0%B3%D0%B8",
        "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"],
    },
    {
        "name": "ProZorro.Sale — кредитний портфель",
        "url": "https://prozorro.sale/auction/search?query=%D0%BA%D1%80%D0%B5%D0%B4%D0%B8%D1%82%D0%BD%D0%B8%D0%B9+%D0%BF%D0%BE%D1%80%D1%82%D1%84%D0%B5%D0%BB%D1%8C",
        "keywords": ["кредитн", "портфель", "право вимоги"],
    },
    {
        "name": "ProZorro.Sale — дебіторська заборгованість",
        "url": "https://prozorro.sale/auction/search?query=%D0%B4%D0%B5%D0%B1%D1%96%D1%82%D0%BE%D1%80%D1%81%D1%8C%D0%BA%D0%B0+%D0%B7%D0%B0%D0%B1%D0%BE%D1%80%D0%B3%D0%BE%D0%B2%D0%B0%D0%BD%D1%96%D1%81%D1%82%D1%8C",
        "keywords": ["дебіторськ", "заборгован", "право вимоги"],
    },
    {
        "name": "SETAM — всі торги",
        "url": "https://setam.net.ua/auctions",
        "keywords": ["право вимоги", "кредитн", "портфель"],
    },
    {
        "name": "UBIZ.UA — фінанси",
        "url": "https://ubiz.ua/auctions-all/finance",
        "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ", "відступлення"],
    },
    {
        "name": "ФГВ — продаж активів",
        "url": "https://www.fg.gov.ua/aktivi-bankiv/prodazh-aktiviv",
        "keywords": ["право вимоги", "портфель", "кредитн", "пул актив", "реалізація"],
    },
    {
        "name": "UUB — банкрутство",
        "url": "https://sale.uub.com.ua/PositionList.aspx",
        "keywords": ["право вимоги", "кредитн", "дебіторськ", "портфель"],
    },
]


def _check_playwright() -> bool:
    """Check if playwright is installed and chromium is available."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


def scan_with_browser(timeout_ms: int = 15000) -> Dict[str, Any]:
    """Scan all sources using real Chromium browser.

    Returns {"lots": [...], "errors": [...], "sources_scanned": N}.
    """
    if not _check_playwright():
        return {
            "lots": [],
            "errors": ["Playwright не встановлено. Виконайте: pip install playwright && playwright install chromium"],
            "sources_scanned": 0,
        }

    from playwright.sync_api import sync_playwright

    all_lots: List[Dict[str, str]] = []
    errors: List[str] = []
    scanned = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                locale="uk-UA",
            )

            for src in BROWSER_SOURCES:
                try:
                    page = context.new_page()
                    LOGGER.info("Browser: loading %s", src["url"])
                    page.goto(src["url"], timeout=timeout_ms, wait_until="networkidle")

                    # Extract all links from the rendered page
                    links = page.evaluate("""() => {
                        const results = [];
                        document.querySelectorAll('a').forEach(a => {
                            const text = (a.textContent || '').trim();
                            const href = a.href || '';
                            if (text.length > 5 && href.startsWith('http')) {
                                results.push({text: text.substring(0, 300), href: href});
                            }
                        });
                        return results;
                    }""")

                    # Filter by NPL keywords
                    for link in links:
                        text_lower = link["text"].lower()
                        if any(kw in text_lower for kw in src["keywords"]):
                            if not any(l["url"] == link["href"] for l in all_lots):
                                all_lots.append({
                                    "source": src["name"],
                                    "title": link["text"],
                                    "url": link["href"],
                                    "category": "active",
                                    "status": "знайдено скрапером",
                                })

                    scanned += 1
                    LOGGER.info("Browser: %s — знайдено %d посилань, %d відповідних",
                                src["name"], len(links), len([l for l in all_lots if l["source"] == src["name"]]))
                    page.close()

                except Exception as exc:
                    errors.append(f"{src['name']}: {exc}")
                    LOGGER.warning("Browser error %s: %s", src["name"], exc)

            browser.close()

    except Exception as exc:
        errors.append(f"Browser launch error: {exc}")

    return {
        "lots": all_lots,
        "errors": errors,
        "sources_scanned": scanned,
    }


def scan_lot_details(lot_url: str, timeout_ms: int = 15000) -> Dict[str, Any]:
    """Fetch full details of a specific lot page using browser.

    Returns parsed lot info: title, price, dates, guarantee, status, etc.
    """
    if not _check_playwright():
        return {"error": "Playwright not installed"}

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(lot_url, timeout=timeout_ms, wait_until="networkidle")

            # Extract all text from the page
            text = page.inner_text("body")
            browser.close()

            # Parse common fields
            result: Dict[str, Any] = {"url": lot_url, "raw_text": text[:3000]}

            patterns = {
                "status": r"(?:Стан аукціон[аи]|Статус)[:\s]*(.*?)(?:\n|$)",
                "lot_number": r"(?:Номер лоту|Лот №)[:\s]*([\d]+)",
                "auction_date": r"(?:Дата проведення|Дата аукціону)[:\s]*([\d]+.*?(?:\d{4}).*?)(?:\n|$)",
                "end_date": r"(?:Дата закінчення)[:\s]*(.*?)(?:\n|$)",
                "start_price": r"(?:Стартова ціна|Початкова ціна)[:\s]*([\d\s,.]+)",
                "guarantee": r"(?:Гарантійний внесок)[:\s]*([\d\s,.]+)",
                "step": r"(?:Крок аукціону)[:\s]*([\d\s,.]+)",
            }
            for key, pat in patterns.items():
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    result[key] = match.group(1).strip()

            return result

    except Exception as exc:
        return {"error": str(exc), "url": lot_url}
