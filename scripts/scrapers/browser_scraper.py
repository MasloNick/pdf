"""Browser scraper sources — 70+ verified sources for NPL hunting.

Based on verified source map as of 13.04.2026.
Priority: 1) Prozorro + platforms, 2) ФГВФО + НБУ,
3) Bank NPL pages, 4) Court/bankruptcy/analytics registries.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

LOGGER = logging.getLogger(__name__)

# =====================================================================
# ALL SOURCES — verified URLs only
# =====================================================================

BROWSER_SOURCES = [

    # === ПРІОРИТЕТ 1: Prozorro.Продажі — пошук ===
    {"name": "ProZorro — право вимоги",
     "url": "https://prozorro.sale/auction/search?query=%D0%BF%D1%80%D0%B0%D0%B2%D0%BE+%D0%B2%D0%B8%D0%BC%D0%BE%D0%B3%D0%B8",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 1},
    {"name": "ProZorro — кредитний портфель",
     "url": "https://prozorro.sale/auction/search?query=%D0%BA%D1%80%D0%B5%D0%B4%D0%B8%D1%82%D0%BD%D0%B8%D0%B9+%D0%BF%D0%BE%D1%80%D1%82%D1%84%D0%B5%D0%BB%D1%8C",
     "keywords": ["кредитн", "портфель", "право вимоги"], "priority": 1},
    {"name": "ProZorro — дебіторська",
     "url": "https://prozorro.sale/auction/search?query=%D0%B4%D0%B5%D0%B1%D1%96%D1%82%D0%BE%D1%80%D1%81%D1%8C%D0%BA%D0%B0",
     "keywords": ["дебіторськ", "заборгован", "право вимоги"], "priority": 1},
    {"name": "ProZorro — відступлення",
     "url": "https://prozorro.sale/auction/search?query=%D0%B2%D1%96%D0%B4%D1%81%D1%82%D1%83%D0%BF%D0%BB%D0%B5%D0%BD%D0%BD%D1%8F",
     "keywords": ["відступлення", "право вимоги", "кредитн"], "priority": 1},
    {"name": "ProZorro — NPL",
     "url": "https://prozorro.sale/auction/search?query=NPL",
     "keywords": ["npl", "право вимоги", "кредитн", "портфель"], "priority": 1},
    {"name": "ProZorro — факторинг",
     "url": "https://prozorro.sale/auction/search?query=%D1%84%D0%B0%D0%BA%D1%82%D0%BE%D1%80%D0%B8%D0%BD%D0%B3",
     "keywords": ["факторинг", "відступлення", "право вимоги"], "priority": 1},
    {"name": "ProZorro — активи банків",
     "url": "https://prozorro.sale/prodazh-majna-derzhavnih-kompanij/",
     "keywords": ["право вимоги", "кредитн", "портфель", "банк", "актив"], "priority": 1},

    # === ПРІОРИТЕТ 1: ФГВФО ===
    {"name": "ФГВФО — продаж активів банків",
     "url": "https://www.fg.gov.ua/aktivi-bankiv/prodazh-aktiviv",
     "keywords": ["право вимоги", "портфель", "кредитн", "пул актив", "реалізація"], "priority": 1},
    {"name": "ФГВФО — торги",
     "url": "http://torgi.fg.gov.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "пул", "актив"], "priority": 1},
    {"name": "ФГВФО — новини (щотижневі продажі)",
     "url": "https://www.fg.gov.ua/news",
     "keywords": ["продаж актив", "реалізація", "право вимоги", "портфель", "аукціон"], "priority": 1},
    {"name": "НБУ — ліквідація банків",
     "url": "https://bank.gov.ua/ua/supervision/reorganization",
     "keywords": ["ліквідац", "реорганізац", "тимчасова адміністрація"], "priority": 1},

    # === ПРІОРИТЕТ 2: SETAM ===
    {"name": "SETAM / OpenMarket",
     "url": "https://setam.net.ua/auctions",
     "keywords": ["право вимоги", "кредитн", "портфель"], "priority": 2},

    # === АВТОРИЗОВАНІ МАЙДАНЧИКИ ProZorro.Продажі ===
    {"name": "UBIZ.UA", "url": "https://ubiz.ua/auctions-all/finance",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ", "відступлення"], "priority": 2},
    {"name": "UUB (Українська Універсальна Біржа)", "url": "https://sale.uub.com.ua/PositionList.aspx",
     "keywords": ["право вимоги", "кредитн", "дебіторськ", "портфель"], "priority": 2},
    {"name": "E-Tender", "url": "https://e-tender.ua/prozorro-prodagy",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "SmartTender", "url": "https://smarttender.biz/prozorro-prodazhi/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "Українська енергетична біржа (UEEX)", "url": "https://sale.ueex.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "Національна Електронна Біржа (NEB)", "url": "https://neb.org.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "Полонекс", "url": "https://polonex.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "Публічні Процедури", "url": "https://sale.auction.org.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "OpenMarket (SETAM/ProZorro)", "url": "https://openmarket.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "Товарна біржа ЕТС", "url": "https://tb-ets.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "EAuction (Open Tender)", "url": "https://eauction.open-tender.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "Tender-Online", "url": "https://tender-online.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "Закупівлі.Про (Zakupki.Prom)", "url": "https://zakupki.prom.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "DZO (Держзакупівлі.Онлайн)", "url": "https://www.dzo.com.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 2},
    {"name": "Invest.UA — ProZorro", "url": "https://invest.ua/prozorro-prodazhi/",
     "keywords": ["право вимоги", "кредитн", "портфель", "приватизація"], "priority": 2},
    {"name": "PrivatMarket (ПриватБанк)", "url": "https://privatmarket.ua/",
     "keywords": ["право вимоги", "кредитн", "портфель", "продаж актив"], "priority": 3},

    # === ПРІОРИТЕТ 3: ДЕРЖБАНКИ — спеціальні сторінки NPL ===
    {"name": "ПриватБанк — продаж майна",
     "url": "https://privatbank.ua/about/prodag-aktiviv",
     "keywords": ["право вимоги", "портфель", "кредитн", "продаж", "актив", "тендер"], "priority": 3},
    {"name": "Ощадбанк — продаж майна та прав вимоги",
     "url": "https://www.oschadbank.ua/sell-assets",
     "keywords": ["право вимоги", "портфель", "кредитн", "продаж", "актив", "тендер"], "priority": 3},
    {"name": "Укрексімбанк — право вимоги",
     "url": "https://www.eximb.com/ua/about/non-performing-assets",
     "keywords": ["право вимоги", "портфель", "кредитн", "продаж", "актив", "npl"], "priority": 3},
    {"name": "Укргазбанк — реалізація майна та NPL",
     "url": "https://www.ukrgasbank.com/about/news/",
     "keywords": ["право вимоги", "продаж", "актив", "портфель", "npl", "реалізація"], "priority": 3},

    # === ПРІОРИТЕТ 3: ПРИВАТНІ БАНКИ з окремими сторінками продажів ===
    {"name": "Райффайзен — заставне майно",
     "url": "https://zalog.raiffeisen.ua",
     "keywords": ["право вимоги", "заставн", "продаж", "актив", "відступлення"], "priority": 3},
    {"name": "Універсал Банк — заставне майно",
     "url": "https://universalbank.com.ua",
     "keywords": ["право вимоги", "заставн", "майно банку", "продаж"], "priority": 3},
    {"name": "МТБ Банк — реалізація заставного майна",
     "url": "https://mtb.ua",
     "keywords": ["право вимоги", "заставн", "реалізація", "продаж"], "priority": 3},

    # === ПРІОРИТЕТ 3: РЕШТА БАНКІВ — моніторинг новин ===
    {"name": "ПУМБ", "url": "https://pumb.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель", "тендер", "npl"], "priority": 3},
    {"name": "Сенс Банк", "url": "https://sensbank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Креді Агріколь", "url": "https://credit-agricole.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель", "тендер", "акредит"], "priority": 3},
    {"name": "ОТП Банк", "url": "https://en.otpbank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Укрсиббанк", "url": "https://ukrsibbank.com",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "А-Банк", "url": "https://a-bank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Прокредит Банк", "url": "https://procreditbank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Кредит Дніпро", "url": "https://creditdnepr.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Таскомбанк", "url": "https://tascombank.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Правекс Банк", "url": "https://pravex.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Кредобанк", "url": "https://kredobank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "ВСТ Банк (колишній Банк Восток)", "url": "https://vstbank.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Ідея Банк", "url": "https://ideabank.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Банк Альянс", "url": "https://alb.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Глобус Банк", "url": "https://globusbank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Акордбанк", "url": "https://accordbank.com.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},
    {"name": "Піреус Банк", "url": "https://piraeusbank.ua",
     "keywords": ["право вимоги", "продаж", "актив", "портфель"], "priority": 3},

    # === МФО ===
    {"name": "Манівео", "url": "https://moneyveo.ua",
     "keywords": ["продаж", "портфель", "право вимоги", "відступлення"], "priority": 3},
    {"name": "MyCredit", "url": "https://mycredit.ua",
     "keywords": ["продаж", "портфель", "право вимоги", "відступлення"], "priority": 3},
    {"name": "CreditPlus (Aventus)", "url": "https://creditplus.ua",
     "keywords": ["продаж", "портфель", "право вимоги", "відступлення"], "priority": 3},

    # === ФК / Колектори ===
    {"name": "УкрБорг", "url": "https://ukrborg.ua/",
     "keywords": ["продаж", "портфель", "право вимоги", "відступлення", "факторинг"], "priority": 3},
    {"name": "ФК Форінт", "url": "https://forint.com.ua/",
     "keywords": ["продаж", "портфель", "право вимоги", "відступлення"], "priority": 3},

    # === ПРІОРИТЕТ 4: АНАЛІТИКА / РЕЄСТРИ / ПЕРЕВІРКА ===
    {"name": "ЄДРСР — судові рішення",
     "url": "https://reyestr.court.gov.ua",
     "keywords": ["відступлення права вимоги", "кредитний портфель", "звернення стягнення"], "priority": 4},
    {"name": "Банкрутство — інфосистема",
     "url": "https://info.bankrut.gov.ua",
     "keywords": ["банкрутство", "ліквідатор", "право вимоги", "дебіторськ"], "priority": 4},
    {"name": "АМКУ — концентрації",
     "url": "https://amcu.gov.ua/napryami/konkurentne-zakonodavstvo/kontsentratsiyi",
     "keywords": ["відступлення", "право вимоги", "кредитний портфель", "фінансова компанія"], "priority": 4},
    {"name": "НКЦПФР / stockmarket.gov.ua",
     "url": "https://stockmarket.gov.ua",
     "keywords": ["відступлення", "право вимоги", "портфель", "факторинг"], "priority": 4},
    {"name": "Clarity Project",
     "url": "https://clarity-project.info/prozorro-sale",
     "keywords": ["право вимоги", "кредитн", "портфель", "дебіторськ"], "priority": 4},
    {"name": "OpenDataBot",
     "url": "https://opendatabot.ua",
     "keywords": ["відступлення", "право вимоги", "кредитний"], "priority": 4},
    {"name": "YouControl",
     "url": "https://youcontrol.com.ua",
     "keywords": ["право вимоги", "відступлення", "борг"], "priority": 4},
    {"name": "LIGA360",
     "url": "https://liga360.com",
     "keywords": ["право вимоги", "відступлення", "кредитний"], "priority": 4},
    {"name": "НБУ — реєстр небанківських установ",
     "url": "https://bank.gov.ua/ua/supervision/registry/nonbank",
     "keywords": ["фінансова компанія", "факторинг", "кредитн"], "priority": 4},
    {"name": "Відкриті дані Prozorro.Sale",
     "url": "https://prozorro.sale/opendata/",
     "keywords": ["право вимоги", "кредитн", "портфель"], "priority": 4},

    # === З ДОКУМЕНТА: додаткові джерела зі звіту 13.04.2026 ===

    # --- Базова інфраструктура ---
    {"name": "ProZorro.Sale — фінансові активи",
     "url": "https://prozorro.sale/auction/search?query=%D1%84%D1%96%D0%BD%D0%B0%D0%BD%D1%81%D0%BE%D0%B2%D1%96+%D0%B0%D0%BA%D1%82%D0%B8%D0%B2%D0%B8",
     "keywords": ["фінансов", "актив", "право вимоги", "портфель"], "priority": 1},
    {"name": "ProZorro.Sale — майнові права",
     "url": "https://prozorro.sale/auction/search?query=%D0%BC%D0%B0%D0%B9%D0%BD%D0%BE%D0%B2%D1%96+%D0%BF%D1%80%D0%B0%D0%B2%D0%B0",
     "keywords": ["майнові права", "право вимоги", "кредитн"], "priority": 1},
    {"name": "ProZorro.Sale — пул активів",
     "url": "https://prozorro.sale/auction/search?query=%D0%BF%D1%83%D0%BB+%D0%B0%D0%BA%D1%82%D0%B8%D0%B2%D1%96%D0%B2",
     "keywords": ["пул", "актив", "право вимоги", "кредитн"], "priority": 1},

    # --- ФГВФО: сторінки ліквідованих банків ---
    {"name": "ФГВФО — МР Банк",
     "url": "https://mrb.fg.gov.ua/prodazh-aktiviv/prodazh-aktiviv-banku",
     "keywords": ["право вимоги", "кредитн", "портфель", "актив"], "priority": 1},
    {"name": "ФГВФО — Мегабанк",
     "url": "https://megabank.fg.gov.ua/prodazh-aktiviv/prodazh-aktiviv-banku",
     "keywords": ["право вимоги", "кредитн", "портфель", "актив"], "priority": 1},
    {"name": "ФГВФО — Промінвестбанк",
     "url": "https://pib.fg.gov.ua/prodazh-aktiviv/prodazh-aktiviv-banku",
     "keywords": ["право вимоги", "кредитн", "портфель", "актив"], "priority": 1},
    {"name": "ФГВФО — Банк Січ",
     "url": "https://sich.fg.gov.ua/prodazh-aktiviv/prodazh-aktiviv-banku",
     "keywords": ["право вимоги", "кредитн", "портфель", "актив"], "priority": 1},
    {"name": "ФГВФО — Форвард Банк",
     "url": "https://forward.fg.gov.ua/prodazh-aktiviv/prodazh-aktiviv-banku",
     "keywords": ["право вимоги", "кредитн", "портфель", "актив"], "priority": 1},
    {"name": "ФГВФО — Родовід Банк",
     "url": "https://rodovid.fg.gov.ua/prodazh-aktiviv/prodazh-aktiviv-banku",
     "keywords": ["право вимоги", "кредитн", "портфель", "актив"], "priority": 1},
    {"name": "ФГВФО — загальна сторінка банків",
     "url": "https://bnk.fg.gov.ua/prodazh-aktiviv/prodazh-aktiviv-banku",
     "keywords": ["право вимоги", "кредитн", "портфель", "актив"], "priority": 1},

    # --- Приватні банки: додаткові сторінки зі звіту ---
    {"name": "ОТП Банк — заставне майно",
     "url": "https://en.otpbank.com.ua/privatnim/krediti/zastavne-mayno/",
     "keywords": ["заставн", "майно", "продаж", "право вимоги"], "priority": 3},
    {"name": "Укрсиббанк — врегулювання заборгованості",
     "url": "https://ukrsibbank.com/debtsettlement",
     "keywords": ["заборгован", "врегулюван", "продаж", "право вимоги"], "priority": 3},
    {"name": "ПроКредит Банк — прозорість",
     "url": "https://procreditbank.com.ua/about/prozorrist/",
     "keywords": ["звіт", "портфель", "актив"], "priority": 3},
    {"name": "Кредит Дніпро — реалізація",
     "url": "https://creditdnepr.com.ua/realizacia",
     "keywords": ["реалізац", "заставн", "продаж", "майно"], "priority": 3},
    {"name": "Таскомбанк — реалізація",
     "url": "https://tascombank.ua/sale",
     "keywords": ["реалізац", "продаж", "майно", "заставн"], "priority": 3},
    {"name": "Кредобанк — реалізація майна",
     "url": "https://kredobank.com.ua/business/realizacia-majna",
     "keywords": ["реалізац", "продаж", "майно", "заставн"], "priority": 3},
    {"name": "Глобус Банк — продаж майна",
     "url": "https://globusbank.com.ua/prodazh-majna",
     "keywords": ["продаж", "майно", "заставн", "право вимоги"], "priority": 3},

    # --- Перевірка та due diligence ---
    {"name": "Єдиний реєстр боржників",
     "url": "https://erb.minjust.gov.ua",
     "keywords": ["боржник", "виконавче провадження"], "priority": 4},
    {"name": "Реєстр обтяжень рухомого майна",
     "url": "https://orm.minjust.gov.ua",
     "keywords": ["обтяження", "застава", "рухоме майно"], "priority": 4},
    {"name": "Реєстр речових прав на нерухомість",
     "url": "https://kap.minjust.gov.ua",
     "keywords": ["нерухомість", "іпотека", "обтяження", "право власності"], "priority": 4},
    {"name": "ЄДР юридичних осіб (Мін'юст)",
     "url": "https://usr.minjust.gov.ua",
     "keywords": ["юридична особа", "статус", "засновник", "ліквідац"], "priority": 4},
    {"name": "ДПС — податковий борг",
     "url": "https://tax.gov.ua",
     "keywords": ["податковий борг", "заборгован"], "priority": 4},
    {"name": "Дія.Відкриті дані",
     "url": "https://diia.data.gov.ua",
     "keywords": ["відкриті дані", "реєстр"], "priority": 4},
    {"name": "Data.gov.ua",
     "url": "https://data.gov.ua",
     "keywords": ["відкриті дані", "судов", "реєстр"], "priority": 4},
    {"name": "НБУ — статистика наглядової діяльності",
     "url": "https://bank.gov.ua/ua/statistic/supervision-statist",
     "keywords": ["npl", "непрацюючі", "кредитний портфель"], "priority": 4},
    {"name": "ФГВФО — щотижневі пресрелізи",
     "url": "https://www.fg.gov.ua/articles",
     "keywords": ["продаж актив", "право вимоги", "тиждень", "аукціон"], "priority": 1},
]


def _check_playwright() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


# =====================================================================
# EXTRACTION HELPERS — pull structured data from link text
# =====================================================================

# Matches Ukrainian currency amounts like "123 456 789,00 грн" or "1234567.89 грн"
# Also matches plain large numbers (>= 10 000) that likely represent money.
_RE_PRICE = re.compile(
    r'(\d[\d\s]{2,}[\d](?:[,\.]\d{1,2})?)\s*(?:грн|UAH|₴)',
    re.IGNORECASE,
)
_RE_LARGE_NUMBER = re.compile(
    r'(\d[\d\s]{4,}\d(?:[,\.]\d{1,2})?)',
)

# Matches contract/credit counts like "15 договорів", "3 кредитних"
_RE_CONTRACTS = re.compile(
    r'(\d+)\s*(?:договор|кредитн|позик)',
    re.IGNORECASE,
)

# Auction type keywords
_AUCTION_KEYWORDS = {
    'англійський': 'англійський',
    'english': 'англійський',
    'голландський': 'голландський',
    'dutch': 'голландський',
    'редукціон': 'редукціон',
}


def _extract_total_debt(text: str) -> str | None:
    """Extract the largest price/amount from text (likely total debt)."""
    # First try explicit currency amounts
    matches = _RE_PRICE.findall(text)
    if not matches:
        # Fall back to large numbers (>=10 000)
        matches = _RE_LARGE_NUMBER.findall(text)

    if not matches:
        return None

    # Parse each match to a numeric value, pick the largest
    best_raw = None
    best_val = 0.0
    for raw in matches:
        cleaned = raw.replace(' ', '').replace(',', '.')
        try:
            val = float(cleaned)
        except ValueError:
            continue
        if val >= 10_000 and val > best_val:
            best_val = val
            best_raw = raw.strip()

    return best_raw


def _extract_num_contracts(text: str) -> int | None:
    """Extract number of contracts/credits from text."""
    m = _RE_CONTRACTS.search(text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None


def _extract_auction_type(text: str) -> str | None:
    """Detect auction type keyword in text."""
    lower = text.lower()
    for keyword, canonical in _AUCTION_KEYWORDS.items():
        if keyword in lower:
            return canonical
    return None


def _is_auction_url(url: str) -> bool:
    """Check if URL looks like an actual auction lot, not a news article."""
    lot_patterns = [
        "/auction/", "/sale3/auction/", "/lot/", "/PositionList",
        "prozorro.sale/auction/", "setam.net.ua/auction/",
        "ubiz.ua/sale3/", "uub.com.ua/auction/",
        "e-tender.ua/", "smarttender.biz/",
        "neb.org.ua/", "polonex.com.ua/",
        "auction.org.ua/", "torgi.fg.gov.ua/",
    ]
    news_patterns = [
        "/news/", "/blog/", "/article/", "/press/",
        "/about/", "/info/", "/faq/", "/rules/",
        "/contacts/", "/login/", "/register/",
        "/poryadok", "/pravila", "/instruk",
        "wikipedia.org", "facebook.com", "instagram.com",
        "telegram.me", "t.me/", "youtube.com",
    ]
    url_lower = url.lower()
    # Reject news/info pages
    if any(p in url_lower for p in news_patterns):
        return False
    # Accept known auction patterns
    if any(p in url_lower for p in lot_patterns):
        return True
    # Accept if URL has auction-like ID pattern
    if re.search(r'[A-Z]{2,3}\d{3}-UA-\d{8}', url):
        return True
    return False


def _enrich_lot_with_details(page, lot: Dict[str, Any], timeout_ms: int = 10000) -> Dict[str, Any]:
    """Navigate to lot page and extract details: price, date, status, guarantee."""
    import datetime
    url = lot.get("url", "")
    if not url:
        return lot

    try:
        page.goto(url, timeout=timeout_ms, wait_until="networkidle")
        text = page.inner_text("body")[:5000]
    except Exception:
        return lot

    # Extract fields
    patterns = {
        "lot_status": r"(?:Стан аукціон[аи]|Статус)[:\s]*(.*?)(?:\n|$)",
        "auction_date_raw": r"(?:Дата проведення|Дата аукціону)[:\s]*([\d]+[.\s/\-]+[\d]+[.\s/\-]+[\d]{4}(?:\s*\d{1,2}:\d{2})?)",
        "end_reg_date": r"(?:Дата закінчення подання заявок|закінчення реєстрації)[:\s]*([\d]+[.\s/\-]+[\d]+[.\s/\-]+[\d]{4})",
        "start_price_raw": r"(?:Стартова ціна|Початкова ціна)[:\s]*([\d\s,.]+)",
        "guarantee_raw": r"(?:Гарантійний внесок)[:\s]*([\d\s,.]+)",
        "num_contracts_raw": r"(\d[\d\s]*)\s*(?:договор|кредитн|позик|актив)",
    }
    for key, pat in patterns.items():
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            lot[key] = match.group(1).strip()

    # Parse status
    status = lot.get("lot_status", "").lower()
    if "відбулися" in status or "завершен" in status or "продано" in status:
        lot["category"] = "history"
        lot["status"] = "торги відбулися"
    elif "не відбу" in status:
        lot["category"] = "watching"
        lot["status"] = "не відбувся"
        lot["watch_reason"] = "Аукціон не відбувся — можливе перевиставлення зі зниженою ціною."
    elif "прийом заявок" in status or "очікується" in status:
        lot["status"] = "прийом заявок"

    # Parse auction date and check if past
    date_raw = lot.get("auction_date_raw", "")
    if date_raw:
        # Try parsing DD.MM.YYYY or DD/MM/YYYY
        for fmt in ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d %m %Y"]:
            try:
                dt = datetime.datetime.strptime(date_raw[:10].replace("/", ".").replace("-", "."), "%d.%m.%Y")
                lot["auction_date"] = dt.strftime("%Y-%m-%d")
                if dt.date() <= datetime.date.today():
                    lot["category"] = "history"
                    if "status" not in lot or lot["status"] == "знайдено скрапером":
                        lot["status"] = f"минув {lot['auction_date']}"
                break
            except ValueError:
                continue

    # Parse start price
    price_raw = lot.get("start_price_raw", "")
    if price_raw:
        try:
            lot["start_price"] = float(price_raw.replace(" ", "").replace(",", "."))
        except ValueError:
            lot["start_price_text"] = price_raw

    # Parse guarantee
    guarantee_raw = lot.get("guarantee_raw", "")
    if guarantee_raw:
        lot["guarantee"] = guarantee_raw + " грн"

    # Parse num contracts
    nc = lot.get("num_contracts_raw", "")
    if nc and not lot.get("num_contracts"):
        try:
            lot["num_contracts"] = int(nc.replace(" ", ""))
        except ValueError:
            pass

    return lot


def scan_with_browser(timeout_ms: int = 15000, enrich: bool = True) -> Dict[str, Any]:
    """Scan all sources using real Chromium browser.

    If enrich=True, navigates to each found lot to extract details.
    """
    if not _check_playwright():
        return {
            "lots": [],
            "errors": ["Playwright не встановлено. Виконайте: pip install playwright && python -m playwright install chromium"],
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

                    for link in links:
                        text_lower = link["text"].lower()
                        href = link["href"]
                        if not any(kw in text_lower for kw in src["keywords"]):
                            continue
                        if any(l["url"] == href for l in all_lots):
                            continue
                        # Filter: only auction URLs, not news/articles
                        if not _is_auction_url(href):
                            continue
                        lot: Dict[str, Any] = {
                            "source": src["name"],
                            "title": link["text"],
                            "url": href,
                            "category": "active",
                            "status": "знайдено скрапером",
                            "priority": src.get("priority", 3),
                            "total_debt": _extract_total_debt(link["text"]),
                            "num_contracts": _extract_num_contracts(link["text"]),
                            "auction_type": _extract_auction_type(link["text"]),
                        }
                        all_lots.append(lot)

                    scanned += 1
                    LOGGER.info("Browser: %s — %d посилань, %d лотів",
                                src["name"], len(links), len([l for l in all_lots if l["source"] == src["name"]]))
                    page.close()

                except Exception as exc:
                    errors.append(f"{src['name']}: {exc}")
                    LOGGER.warning("Browser error %s: %s", src["name"], exc)

            # Phase 2: Enrich each lot by visiting its page
            if enrich and all_lots:
                LOGGER.info("Збагачення: заходимо на %d лотів для отримання деталей...", len(all_lots))
                enrich_page = context.new_page()
                for i, lot in enumerate(all_lots):
                    try:
                        LOGGER.info("  [%d/%d] %s", i + 1, len(all_lots), lot["url"][:60])
                        _enrich_lot_with_details(enrich_page, lot, timeout_ms=10000)
                    except Exception as exc:
                        LOGGER.warning("  Збагачення помилка %s: %s", lot["url"][:40], exc)
                enrich_page.close()

            browser.close()

    except Exception as exc:
        errors.append(f"Browser launch error: {exc}")

    return {"lots": all_lots, "errors": errors, "sources_scanned": scanned}


def scan_lot_details(lot_url: str, timeout_ms: int = 15000) -> Dict[str, Any]:
    """Fetch full details of a specific lot page using browser."""
    if not _check_playwright():
        return {"error": "Playwright not installed"}

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(lot_url, timeout=timeout_ms, wait_until="networkidle")
            text = page.inner_text("body")
            browser.close()

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


def scan_priority_only(timeout_ms: int = 15000) -> Dict[str, Any]:
    """Scan only priority 1 and 2 sources for a faster scan cycle.

    Uses the same extraction logic as *scan_with_browser* but skips
    lower-priority sources (banks, MFIs, registries, analytics) so the
    scan completes much faster.
    """
    if not _check_playwright():
        return {
            "lots": [],
            "errors": ["Playwright не встановлено. Виконайте: pip install playwright && python -m playwright install chromium"],
            "sources_scanned": 0,
        }

    from playwright.sync_api import sync_playwright

    priority_sources = [s for s in BROWSER_SOURCES if s.get("priority", 99) <= 2]
    all_lots: List[Dict[str, Any]] = []
    errors: List[str] = []
    scanned = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                locale="uk-UA",
            )

            for src in priority_sources:
                try:
                    page = context.new_page()
                    LOGGER.info("Priority scan: loading %s", src["url"])
                    page.goto(src["url"], timeout=timeout_ms, wait_until="networkidle")

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

                    for link in links:
                        text_lower = link["text"].lower()
                        if any(kw in text_lower for kw in src["keywords"]):
                            if not any(l["url"] == link["href"] for l in all_lots):
                                lot: Dict[str, Any] = {
                                    "source": src["name"],
                                    "title": link["text"],
                                    "url": link["href"],
                                    "category": "active",
                                    "status": "знайдено скрапером",
                                    "priority": src.get("priority", 3),
                                    "total_debt": _extract_total_debt(link["text"]),
                                    "num_contracts": _extract_num_contracts(link["text"]),
                                    "auction_type": _extract_auction_type(link["text"]),
                                }
                                all_lots.append(lot)

                    scanned += 1
                    LOGGER.info("Priority scan: %s — %d посилань, %d відповідних",
                                src["name"], len(links), len([l for l in all_lots if l["source"] == src["name"]]))
                    page.close()

                except Exception as exc:
                    errors.append(f"{src['name']}: {exc}")
                    LOGGER.warning("Priority scan error %s: %s", src["name"], exc)

            browser.close()

    except Exception as exc:
        errors.append(f"Browser launch error: {exc}")

    return {"lots": all_lots, "errors": errors, "sources_scanned": scanned}
