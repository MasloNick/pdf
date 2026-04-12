"""Court lookup via court.gov.ua open data and «Суд на долоні» API.

Sources:
- https://court.gov.ua/sudova-vlada/sudy/ — official court list
- https://api.conp.com.ua/api/v1.0/court/search — structured JSON API
- https://dsa.court.gov.ua/dsa/inshe/oddata/ — open data from DSA
- https://reyestr.court.gov.ua/ — court decisions registry
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)

# «Суд на долоні» API — real, documented, free
CONP_API_BASE = "https://api.conp.com.ua/api/v1.0"
CONP_COURT_SEARCH = f"{CONP_API_BASE}/court/search"

# Official court.gov.ua
COURT_GOV = "https://court.gov.ua"
COURT_LIST_PAGE = f"{COURT_GOV}/sudova-vlada/sudy/"


def search_courts(
    region: str = "",
    city: str = "",
    instance_type: str = "Перша",
    timeout: int = 15,
) -> List[Dict[str, Any]]:
    """Search courts via «Суд на долоні» API.

    Parameters
    ----------
    region : str
        Oblast name, e.g. "Київська область"
    city : str
        City name, e.g. "місто Київ"
    instance_type : str
        "Перша" | "Апеляційна" | "Касаційна"

    Returns list of court dicts with keys:
        courtName, courtCode, instanceType, address.*, currentStatus
    """
    filters: Dict[str, Any] = {}

    if instance_type:
        filters["instanceType"] = {"list": [instance_type], "operator": "or"}
    if region:
        filters["address.region"] = {"list": [region], "operator": "or"}
    if city:
        filters["address.locality"] = {"list": [city], "operator": "or"}

    body = json.dumps({
        "query": "",
        "defaultOperator": "and",
        "filter": filters,
        "searchIndex": "court",
    }).encode("utf-8")

    req = Request(
        CONP_COURT_SEARCH,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )

    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("Court API error: %s", exc)
        return []

    # API returns {"total": N, "items": [...]}
    items = data if isinstance(data, list) else data.get("items", data.get("data", []))
    if not isinstance(items, list):
        return []

    return items


def find_court_by_address(
    oblast: str,
    district: str = "",
    settlement: str = "",
) -> Dict[str, Any]:
    """Find the relevant court for a given address.

    Tries to match by settlement first (most specific), falls back
    to district, then oblast.

    Returns dict with court info or a stub if API is unreachable.
    """
    # Normalize inputs
    oblast = oblast.strip()
    settlement = settlement.strip()
    district = district.strip()

    # Try most specific first: settlement as city
    if settlement:
        courts = search_courts(city=settlement, instance_type="Перша")
        if courts:
            return _pick_best(courts, settlement)

        # Try with "місто" prefix
        if not settlement.startswith("місто"):
            courts = search_courts(city=f"місто {settlement}", instance_type="Перша")
            if courts:
                return _pick_best(courts, settlement)

    # Try by region
    if oblast:
        region = oblast
        if not region.endswith("область") and not region.endswith("місто"):
            region = f"{oblast} область"
        courts = search_courts(region=region, instance_type="Перша")
        if courts:
            # If district is given, try to match
            if district:
                for c in courts:
                    court_name = c.get("courtName", "").lower()
                    if district.lower() in court_name:
                        return _format_result(c)
            return _pick_best(courts, oblast)

    return {
        "court_name": f"Не знайдено суд для: {oblast}, {district}, {settlement}",
        "court_code": "",
        "address": "",
        "instance": "",
        "status": "",
        "source": "court.gov.ua (API недоступний або адресу не знайдено)",
        "url": COURT_LIST_PAGE,
    }


def _pick_best(courts: List[Dict[str, Any]], hint: str) -> Dict[str, Any]:
    """Pick the most relevant court from a list using *hint* for matching."""
    hint_lower = hint.lower()
    # Exact name match
    for c in courts:
        if hint_lower in c.get("courtName", "").lower():
            return _format_result(c)
    # Fallback: first active court
    for c in courts:
        status = c.get("organization", {}).get("currentStatus", "") if isinstance(c.get("organization"), dict) else c.get("currentStatus", "")
        if "ліквідо" not in str(status).lower():
            return _format_result(c)
    return _format_result(courts[0])


def _format_result(court: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize API response into our standard format."""
    addr = court.get("address", {})
    if isinstance(addr, dict):
        full_addr = addr.get("fullAddress", "")
        if not full_addr:
            full_addr = ", ".join(filter(None, [
                addr.get("region", ""),
                addr.get("district", ""),
                addr.get("locality", ""),
                addr.get("streetAddress", ""),
            ]))
    else:
        full_addr = str(addr)

    org = court.get("organization", {})
    status = org.get("currentStatus", "") if isinstance(org, dict) else court.get("currentStatus", "")

    code = court.get("courtCode", "")

    return {
        "court_name": court.get("courtName", ""),
        "court_code": code,
        "address": full_addr,
        "instance": court.get("instanceType", ""),
        "status": status,
        "source": "api.conp.com.ua (Суд на долоні)",
        "url": f"{COURT_GOV}/fair/" if not code else f"{COURT_GOV}/fair/?cs={code}",
    }
