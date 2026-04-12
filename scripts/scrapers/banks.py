"""Scrapers for individual bank websites and private auction platforms.

Each bank may publish NPL portfolio sale announcements on their own website
in different formats.  This module provides per-bank scrapers and a registry
that runs them all.

Private platforms and accreditation sources are also tracked here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from scripts.scrapers.base import BaseScraper, extract_links

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Bank / MFO / FC registry
# ---------------------------------------------------------------------------

@dataclass
class BankConfig:
    """Configuration for scraping a specific bank/MFO/FC."""
    name: str
    short_name: str
    bank_type: str              # state_bank / private_bank / mfo / fc
    website: str
    npl_page: Optional[str] = None  # direct link to NPL sales page
    accreditation_page: Optional[str] = None
    news_page: Optional[str] = None
    keywords: List[str] = field(default_factory=lambda: [
        "право вимоги", "портфель", "кредитний портфель",
        "продаж", "аукціон", "торги", "реалізація",
        "непрацюючі активи", "дебіторська",
    ])
    notes: str = ""


# Known banks and financial institutions that sell NPL portfolios
BANK_REGISTRY: List[BankConfig] = [
    # --- State banks ---
    BankConfig(
        name="АТ КБ «ПриватБанк»",
        short_name="ПриватБанк",
        bank_type="state_bank",
        website="https://privatbank.ua",
        npl_page="https://privatbank.ua/about/prodag-aktiviv",
        news_page="https://privatbank.ua/news",
        notes="Найбільший банк, регулярно продає NPL через ProZorro та власні тендери",
    ),
    BankConfig(
        name="АТ «Ощадбанк»",
        short_name="Ощадбанк",
        bank_type="state_bank",
        website="https://oschadbank.ua",
        npl_page="https://oschadbank.ua/sale-of-assets",
        news_page="https://oschadbank.ua/news",
        notes="Державний, продає через ProZorro",
    ),
    BankConfig(
        name="АТ «Укрексімбанк»",
        short_name="Укрексімбанк",
        bank_type="state_bank",
        website="https://eximb.com",
        news_page="https://eximb.com/ua/about/news",
        notes="Державний, продає через ProZorro та внутрішні тендери",
    ),
    BankConfig(
        name="АБ «Укргазбанк»",
        short_name="Укргазбанк",
        bank_type="state_bank",
        website="https://ukrgasbank.com",
        news_page="https://ukrgasbank.com/about/news",
    ),
    # --- Private banks ---
    BankConfig(
        name="АТ «ПУМБ»",
        short_name="ПУМБ",
        bank_type="private_bank",
        website="https://pumb.ua",
        news_page="https://pumb.ua/uk/about/news",
    ),
    BankConfig(
        name="АТ «Альфа-Банк» (Сенс Банк)",
        short_name="Сенс Банк",
        bank_type="private_bank",
        website="https://sensbank.com.ua",
        news_page="https://sensbank.com.ua/about/news",
    ),
    BankConfig(
        name="АТ «Креді Агріколь Банк»",
        short_name="Креді Агріколь",
        bank_type="private_bank",
        website="https://credit-agricole.ua",
        news_page="https://credit-agricole.ua/about/press-center",
        accreditation_page="https://credit-agricole.ua/about",
        notes="Проводить внутрішні аукціони серед акредитованих ФК. "
              "Для акредитації потрібно: 1) ліцензія ФК, "
              "2) досвід роботи з NPL, 3) подати заявку через офіційний сайт або відділ по роботі з проблемними активами",
    ),
    BankConfig(
        name="АТ «Райффайзен Банк»",
        short_name="Райффайзен",
        bank_type="private_bank",
        website="https://raiffeisen.ua",
        news_page="https://raiffeisen.ua/about/press-center",
    ),
    BankConfig(
        name="АТ «ОТП Банк»",
        short_name="ОТП Банк",
        bank_type="private_bank",
        website="https://otpbank.com.ua",
        news_page="https://otpbank.com.ua/about/press-center",
    ),
    BankConfig(
        name="АТ «Укрсиббанк»",
        short_name="Укрсиббанк",
        bank_type="private_bank",
        website="https://ukrsibbank.com",
        news_page="https://ukrsibbank.com/about/news",
    ),
    BankConfig(
        name="АТ «Універсал Банк» (monobank)",
        short_name="Універсал Банк",
        bank_type="private_bank",
        website="https://universalbank.com.ua",
    ),
    BankConfig(
        name="АТ «А-Банк»",
        short_name="А-Банк",
        bank_type="private_bank",
        website="https://a-bank.com.ua",
    ),
    # --- MFOs ---
    BankConfig(
        name="ТОВ «Манівео»",
        short_name="Манівео",
        bank_type="mfo",
        website="https://moneyveo.ua",
        notes="Велика МФО, може продавати портфелі на закритих торгах",
    ),
    BankConfig(
        name="ТОВ «КредитМаркет»",
        short_name="КредитМаркет",
        bank_type="mfo",
        website="https://creditmarket.ua",
    ),
    BankConfig(
        name="ТОВ «CCloan»",
        short_name="CCloan",
        bank_type="mfo",
        website="https://ccloan.ua",
    ),
    BankConfig(
        name="ТОВ «MyCredit»",
        short_name="MyCredit",
        bank_type="mfo",
        website="https://mycredit.ua",
        notes="Одна з найбільших МФО, може мати програми продажу портфелів",
    ),
    # --- FC (Financial Companies) ---
    BankConfig(
        name="ТОВ «ФК Форінт»",
        short_name="Форінт",
        bank_type="fc",
        website="https://forint.com.ua",
        notes="Велика ФК-колектор, може продавати частини портфеля",
    ),
    BankConfig(
        name="ТОВ «Вердикт»",
        short_name="Вердикт",
        bank_type="fc",
        website="https://verdykt.com.ua",
    ),
]


# ---------------------------------------------------------------------------
# Private auction platforms
# ---------------------------------------------------------------------------

PRIVATE_PLATFORMS = [
    {
        "name": "SETAM",
        "url": "https://setam.net.ua",
        "description": "Державне підприємство з проведення аукціонів",
        "type": "state",
    },
    {
        "name": "ProZorro.Продажі",
        "url": "https://prozorro.sale",
        "description": "Державна платформа для продажу активів",
        "type": "state",
    },
    {
        "name": "Закриті банківські тендери",
        "url": "",
        "description": "Внутрішні аукціони банків серед акредитованих ФК (Креді Агріколь, ПУМБ, Райффайзен тощо)",
        "type": "closed",
    },
    {
        "name": "ФГВ — Фонд гарантування вкладів",
        "url": "https://fg.gov.ua",
        "description": "Продаж активів ліквідованих банків",
        "type": "state",
    },
]


# ---------------------------------------------------------------------------
# Bank website scraper
# ---------------------------------------------------------------------------


class BankSiteScraper(BaseScraper):
    """Scan bank websites for NPL sale announcements."""

    def scan_bank(self, config: BankConfig) -> List[Dict[str, Any]]:
        """Scan a single bank's website for NPL-related pages."""
        results: List[Dict[str, Any]] = []
        pages_to_scan = []

        if config.npl_page:
            pages_to_scan.append(("npl_page", config.npl_page))
        if config.news_page:
            pages_to_scan.append(("news", config.news_page))
        if config.accreditation_page:
            pages_to_scan.append(("accreditation", config.accreditation_page))

        # Fallback: scan main website
        if not pages_to_scan:
            pages_to_scan.append(("main", config.website))

        for page_type, url in pages_to_scan:
            html = self.safe_fetch(url)
            if not html:
                continue
            links = extract_links(html, config.website, keywords=config.keywords)
            for text, href in links:
                if not any(r["url"] == href for r in results):
                    results.append({
                        "bank": config.short_name,
                        "bank_type": config.bank_type,
                        "title": text,
                        "url": href,
                        "page_type": page_type,
                        "source_url": url,
                    })

        LOGGER.info("Bank scan %s: found %d relevant links", config.short_name, len(results))
        return results

    def scan_all_banks(self, bank_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Scan all registered banks, optionally filtered by type."""
        all_results: List[Dict[str, Any]] = []
        for config in BANK_REGISTRY:
            if bank_types and config.bank_type not in bank_types:
                continue
            results = self.scan_bank(config)
            all_results.extend(results)
        return all_results


def get_accreditation_info() -> List[Dict[str, str]]:
    """Return known accreditation requirements for banks with internal auctions."""
    info = []
    for config in BANK_REGISTRY:
        if config.accreditation_page or "акредит" in config.notes.lower() or "внутрішн" in config.notes.lower():
            info.append({
                "bank": config.short_name,
                "name": config.name,
                "accreditation_page": config.accreditation_page or "",
                "notes": config.notes,
                "website": config.website,
            })
    return info
