"""Legal entity verification from open Ukrainian data sources.

Checks company status, bankruptcy, court cases, and enforcement
proceedings using publicly available registries.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from scripts.scrapers.base import BaseScraper, extract_links

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Open data sources for verification
# ---------------------------------------------------------------------------

# USR (Unified State Register) — open API for basic company data
USR_SEARCH_URL = "https://data.gov.ua/api/3/action/datastore_search"

# OpenDataBot-like open endpoints
OPENDATABOT_SEARCH = "https://opendatabot.ua/c/"  # + EDRPOU

# Court decision registry
COURT_REGISTRY_URL = "https://reyestr.court.gov.ua/Review/"

# VDVS (enforcement proceedings)
ENFORCEMENT_SEARCH = "https://asvpweb.minjust.gov.ua/search"

# Bankruptcy registry
BANKRUPTCY_REGISTRY = "https://pgr.court.gov.ua/"


@dataclass
class CompanyStatus:
    """Result of a company status check."""
    edrpou: str
    name: str = ""
    status: str = "unknown"        # active / in_liquidation / bankrupt / terminated / unknown
    registration_date: str = ""
    address: str = ""
    authorized_capital: float = 0.0
    main_activity: str = ""
    has_tax_debt: bool = False
    court_cases: List[Dict[str, str]] = field(default_factory=list)
    enforcement_proceedings: List[Dict[str, str]] = field(default_factory=list)
    bankruptcy_info: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    sources_checked: List[str] = field(default_factory=list)

    @property
    def is_problematic(self) -> bool:
        return self.status in ("in_liquidation", "bankrupt", "terminated")

    @property
    def risk_level(self) -> str:
        if self.status in ("bankrupt", "terminated"):
            return "high"
        if self.status == "in_liquidation" or self.bankruptcy_info:
            return "high"
        if self.has_tax_debt or len(self.court_cases) > 5:
            return "medium"
        return "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edrpou": self.edrpou,
            "name": self.name,
            "status": self.status,
            "registration_date": self.registration_date,
            "address": self.address,
            "authorized_capital": self.authorized_capital,
            "main_activity": self.main_activity,
            "has_tax_debt": self.has_tax_debt,
            "court_cases_count": len(self.court_cases),
            "enforcement_count": len(self.enforcement_proceedings),
            "bankruptcy_info": self.bankruptcy_info,
            "risk_level": self.risk_level,
            "is_problematic": self.is_problematic,
            "warnings": self.warnings,
            "sources_checked": self.sources_checked,
        }


class CompanyChecker(BaseScraper):
    """Check legal entity status from open Ukrainian sources."""

    def check_company(self, edrpou: str, name: str = "") -> CompanyStatus:
        """Run all available checks for a company by EDRPOU code."""
        edrpou = edrpou.strip()
        if not edrpou or not edrpou.isdigit():
            result = CompanyStatus(edrpou=edrpou, name=name)
            result.warnings.append("Невалідний код ЄДРПОУ")
            return result

        result = CompanyStatus(edrpou=edrpou, name=name)

        # 1. Check OpenDataBot page for basic status
        self._check_opendatabot(result)

        # 2. Check court decisions registry
        self._check_court_registry(result)

        # 3. Check enforcement proceedings
        self._check_enforcement(result)

        # 4. Check bankruptcy registry
        self._check_bankruptcy(result)

        # Derive warnings
        if result.status == "terminated":
            result.warnings.append("УВАГА: Компанія припинена! Стягнення неможливе.")
        elif result.status == "bankrupt":
            result.warnings.append("УВАГА: Компанія в процедурі банкрутства. Стягнення лише через ліквідатора.")
        elif result.status == "in_liquidation":
            result.warnings.append("УВАГА: Компанія в процесі ліквідації. Потрібно заявляти кредиторські вимоги.")

        if len(result.court_cases) > 10:
            result.warnings.append(f"Багато судових справ ({len(result.court_cases)}). Можливо масові позови.")

        return result

    def _check_opendatabot(self, result: CompanyStatus) -> None:
        """Scrape basic company info from public pages."""
        url = f"{OPENDATABOT_SEARCH}{result.edrpou}"
        html = self.safe_fetch(url)
        if not html:
            result.sources_checked.append(f"opendatabot: помилка завантаження")
            return

        result.sources_checked.append("opendatabot")

        # Extract company name if not provided
        name_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        if name_match and not result.name:
            result.name = re.sub(r'<[^>]+>', '', name_match.group(1)).strip()

        # Detect status from page content
        lower_html = html.lower()
        if "припинено" in lower_html or "terminated" in lower_html:
            result.status = "terminated"
        elif "банкрут" in lower_html or "bankruptcy" in lower_html:
            result.status = "bankrupt"
        elif "ліквідац" in lower_html or "liquidation" in lower_html:
            result.status = "in_liquidation"
        elif "зареєстровано" in lower_html or result.edrpou in html:
            result.status = "active"

        # Extract address
        addr_match = re.search(r'(?:адреса|address)[:\s]*([\w\s,.-]+(?:україна)?)', html, re.IGNORECASE)
        if addr_match:
            result.address = addr_match.group(1).strip()[:200]

    def _check_court_registry(self, result: CompanyStatus) -> None:
        """Search court decision registry for cases involving this company."""
        # The court registry has a search interface
        search_url = "https://reyestr.court.gov.ua/"
        html = self.safe_fetch(search_url + f"?SearchExpression={result.edrpou}")
        if not html:
            result.sources_checked.append("court_registry: помилка завантаження")
            return

        result.sources_checked.append("court_registry")

        # Extract links to court decisions
        links = extract_links(html, search_url, keywords=None)
        court_links = [
            (text, href) for text, href in links
            if "/Review/" in href and len(text) > 10
        ]

        for text, href in court_links[:20]:  # Limit to 20 most relevant
            result.court_cases.append({
                "title": text[:200],
                "url": href,
            })

    def _check_enforcement(self, result: CompanyStatus) -> None:
        """Check enforcement proceedings registry."""
        # ASVP web search
        html = self.safe_fetch(
            f"https://asvpweb.minjust.gov.ua/#/search?query={result.edrpou}"
        )
        if not html:
            result.sources_checked.append("enforcement: помилка завантаження")
            return

        result.sources_checked.append("enforcement")

        if result.edrpou in html and ("виконавче провадження" in html.lower() or "enforcement" in html.lower()):
            # Try to extract enforcement records
            matches = re.findall(
                r'(?:ВП|провадження)\s*[№#]?\s*([\d/]+)',
                html,
            )
            for m in matches[:10]:
                result.enforcement_proceedings.append({"number": m})

    def _check_bankruptcy(self, result: CompanyStatus) -> None:
        """Check bankruptcy proceedings registry."""
        html = self.safe_fetch(f"{BANKRUPTCY_REGISTRY}?code={result.edrpou}")
        if not html:
            result.sources_checked.append("bankruptcy: помилка завантаження")
            return

        result.sources_checked.append("bankruptcy")

        lower = html.lower()
        if "банкрутство" in lower or "ліквідац" in lower:
            if result.status == "active" or result.status == "unknown":
                result.status = "bankrupt"
            case_match = re.search(r'справа[:\s]*([\d/]+)', html)
            if case_match:
                result.bankruptcy_info = f"Справа № {case_match.group(1)}"

    def check_multiple(self, companies: List[Dict[str, str]]) -> List[CompanyStatus]:
        """Check multiple companies. Each dict should have 'edrpou' and optionally 'name'."""
        results = []
        for company in companies:
            edrpou = company.get("edrpou", "")
            name = company.get("name", "")
            if edrpou:
                result = self.check_company(edrpou, name)
                results.append(result)
        return results


class DGFPortfolioChecker(BaseScraper):
    """Check if a financial company that bought DGF portfolio rights
    has actually litigated and enforced those debts."""

    def check_buyer_activity(self, buyer_name: str, buyer_edrpou: str = "") -> Dict[str, Any]:
        """Check court activity for an NPL portfolio buyer."""
        activity: Dict[str, Any] = {
            "buyer": buyer_name,
            "edrpou": buyer_edrpou,
            "court_cases_found": 0,
            "enforcement_found": 0,
            "has_litigation_activity": False,
            "sample_cases": [],
            "sources_checked": [],
        }

        # Search court registry for the buyer as plaintiff
        search_term = buyer_edrpou if buyer_edrpou else buyer_name
        html = self.safe_fetch(
            f"https://reyestr.court.gov.ua/?SearchExpression={search_term}"
        )
        if html:
            activity["sources_checked"].append("court_registry")
            links = extract_links(html, "https://reyestr.court.gov.ua/", keywords=None)
            court_links = [(t, h) for t, h in links if "/Review/" in h]
            activity["court_cases_found"] = len(court_links)
            activity["has_litigation_activity"] = len(court_links) > 0
            for text, href in court_links[:5]:
                activity["sample_cases"].append({"title": text[:200], "url": href})

        return activity
