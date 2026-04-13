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

# Джерела для парсингу — ВСІ доступні платформи
BROWSER_SOURCES = [
    # === ТОРГОВІ ПЛАТФОРМИ ===
    {"name": "ProZorro.Sale — право вимоги",
     "url": "https://prozorro.sale/auction/search?query=%D0%BF%D1%80%D0%B0%D0%B2%D0%BE+%D0%B2%D0%B8%D0%BC%D0%BE%D0%B3%D0%B8",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "ProZorro.Sale — кредитний портфель",
     "url": "https://prozorro.sale/auction/search?query=%D0%BA%D1%80%D0%B5%D0%B4%D0%B8%D1%82%D0%BD%D0%B8%D0%B9+%D0%BF%D0%BE%D1%80%D1%82%D1%84%D0%B5%D0%BB%D1%8C",
     "keywords": ["кредитн", "портфель", "право вимоги"]},
    {"name": "ProZorro.Sale — дебіторська",
     "url": "https://prozorro.sale/auction/search?query=%D0%B4%D0%B5%D0%B1%D1%96%D1%82%D0%BE%D1%80%D1%81%D1%8C%D0%BA%D0%B0+%D0%B7%D0%B0%D0%B1%D0%BE%D1%80%D0%B3%D0%BE%D0%B2%D0%B0%D0%BD%D1%96%D1%81%D1%82%D1%8C",
     "keywords": ["дебіторськ", "заборгован", "право вимоги"]},
    {"name": "ProZorro.Sale — відступлення",
     "url": "https://prozorro.sale/auction/search?query=%D0%B2%D1%96%D0%B4%D1%81%D1%82%D1%83%D0%BF%D0%BB%D0%B5%D0%BD%D0%BD%D1%8F",
     "keywords": ["відступлення", "право вимоги", "кредитн"]},
    {"name": "SETAM — всі торги",
     "url": "https://setam.net.ua/auctions",
     "keywords": ["право вимоги", "кредитн", "портфель"]},
    {"name": "UBIZ.UA — фінанси",
     "url": "https://ubiz.ua/auctions-all/finance",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ", "відступлення"]},
    {"name": "UUB — всі лоти",
     "url": "https://sale.uub.com.ua/PositionList.aspx",
     "keywords": ["право вимоги", "кредитн", "дебіторськ", "портфель"]},
    {"name": "E-Tender — ProZorro.Sale",
     "url": "https://e-tender.ua/prozorro-prodagy",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "SmartTender — торги",
     "url": "https://smarttender.biz/prozorro-prodazhi/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "Центральна універсальна біржа",
     "url": "https://centrex.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ", "аукціон"]},
    {"name": "Українська енергетична біржа",
     "url": "https://sale.ueex.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "PrivatMarket (ПриватБанк)",
     "url": "https://privatmarket.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "продаж актив"]},
    {"name": "IQ-Profi — майданчик",
     "url": "https://iq-profi.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "Держзакупівлі — продажі",
     "url": "https://sale.zakupki.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "Zakupki.Prom.ua",
     "url": "https://zakupki.prom.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "PlayTender",
     "url": "https://playtender.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "DZO — держзакупівлі",
     "url": "https://www.dzo.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "Zakupki.ua — продажі",
     "url": "https://zakupki.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    # --- ТОП акредитовані майданчики ProZorro.Sale ---
    {"name": "Національна Електронна Біржа (NEB)",
     "url": "https://neb.org.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ", "аукціон"]},
    {"name": "Полонекс",
     "url": "https://polonex.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "Публічні Процедури (auction.org.ua)",
     "url": "https://sale.auction.org.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "OpenMarket (SETAM/ProZorro)",
     "url": "https://openmarket.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "Товарна біржа ЕТС",
     "url": "https://tb-ets.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},

    # === ФГВ (Фонд гарантування вкладів) ===
    {"name": "ФГВ — продаж активів",
     "url": "https://www.fg.gov.ua/aktivi-bankiv/prodazh-aktiviv",
     "keywords": ["право вимоги", "портфель", "кредитн", "пул актив", "реалізація"]},
    {"name": "ФГВ — торги",
     "url": "http://torgi.fg.gov.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "пул", "актив"]},
    {"name": "ФГВ — новини",
     "url": "https://www.fg.gov.ua/news",
     "keywords": ["право вимоги", "продаж актив", "реалізація", "портфель", "аукціон"]},

    # === ДЕРЖАВНІ БАНКИ ===
    {"name": "ПриватБанк — продаж активів",
     "url": "https://privatbank.ua/about/prodag-aktiviv",
     "keywords": ["право вимоги", "портфель", "кредитн", "продаж", "актив", "тендер"]},
    {"name": "Ощадбанк — продаж активів",
     "url": "https://www.oschadbank.ua/sell-assets",
     "keywords": ["право вимоги", "портфель", "кредитн", "продаж", "актив", "тендер"]},
    {"name": "Укрексімбанк — непрацюючі активи",
     "url": "https://www.eximb.com/ua/about/non-performing-assets",
     "keywords": ["право вимоги", "портфель", "кредитн", "продаж", "актив", "npl"]},
    {"name": "Укргазбанк — новини",
     "url": "https://www.ukrgasbank.com/about/news/",
     "keywords": ["право вимоги", "продаж", "актив", "портфель", "тендер"]},

    # === ПРИВАТНІ БАНКИ ===
    {"name": "ПУМБ — новини",
     "url": "https://pumb.ua/uk/about/news",
     "keywords": ["право вимоги", "продаж", "актив", "портфель", "тендер", "npl"]},
    {"name": "Сенс Банк — новини",
     "url": "https://sensbank.com.ua/about/news",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Креді Агріколь — прес-центр",
     "url": "https://credit-agricole.ua/about/press-center",
     "keywords": ["право вимоги", "продаж", "актив", "портфель", "тендер", "акредит"]},
    {"name": "Райффайзен — новини",
     "url": "https://raiffeisen.ua/about/news",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "ОТП Банк — новини",
     "url": "https://en.otpbank.com.ua/about/news/",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Укрсиббанк — новини",
     "url": "https://ukrsibbank.com/about/news",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "А-Банк",
     "url": "https://a-bank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Універсал Банк (mono)",
     "url": "https://universalbank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Прокредит Банк",
     "url": "https://procreditbank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Кредит Дніпро",
     "url": "https://creditdnepr.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Таскомбанк",
     "url": "https://tascombank.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Правекс Банк",
     "url": "https://pravex.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Кредобанк",
     "url": "https://kredobank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Банк Восток",
     "url": "https://bankvostok.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Мегабанк",
     "url": "https://megabank.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Форвард Банк",
     "url": "https://forward-bank.com",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Ідея Банк",
     "url": "https://ideabank.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "МТБ Банк",
     "url": "https://mtb.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Банк Альянс",
     "url": "https://bankalliance.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Глобус Банк",
     "url": "https://globusbank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Акордбанк",
     "url": "https://accordbank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    {"name": "Піреус Банк",
     "url": "https://piraeusbank.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"]},
    # === МФО ===
    {"name": "Манівео",
     "url": "https://moneyveo.ua",
     "keywords": ["продаж", "портфель", "право вимоги", "відступлення"]},
    {"name": "MyCredit",
     "url": "https://mycredit.ua",
     "keywords": ["продаж", "портфель", "право вимоги", "відступлення"]},
    {"name": "CreditPlus (Aventus)",
     "url": "https://creditplus.ua",
     "keywords": ["продаж", "портфель", "право вимоги", "відступлення"]},

    # === АНАЛІТИКА / РЕЄСТРИ ===
    {"name": "АМКУ — концентрації",
     "url": "https://amcu.gov.ua/napryami/konkurentne-zakonodavstvo/kontsentratsiyi",
     "keywords": ["відступлення", "право вимоги", "кредитний портфель", "фінансова компанія"]},
    {"name": "НКЦПФР — розкриття інформації",
     "url": "https://stockmarket.gov.ua",
     "keywords": ["відступлення", "право вимоги", "портфель", "факторинг"]},
    {"name": "Clarity Project — ProZorro.Sale",
     "url": "https://clarity-project.info/prozorro-sale",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"]},
    {"name": "OpenDataBot — суди",
     "url": "https://court.opendatabot.ua",
     "keywords": ["відступлення права вимоги", "кредитний портфель"]},
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
