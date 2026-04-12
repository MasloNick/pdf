"""Court lookup — local xlsx database + court.gov.ua API fallback.

Priority:
1. Local xlsx database (uploaded via web UI) — instant, offline
2. «Суд на долоні» API (api.conp.com.ua) — online fallback

Sources:
- Local: Повна_база_судів_України_2025.xlsx (uploaded by user)
- https://court.gov.ua/sudova-vlada/sudy/
- https://api.conp.com.ua/api/v1.0/court/search
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "courts.db"

# «Суд на долоні» API
CONP_API_BASE = "https://api.conp.com.ua/api/v1.0"
CONP_COURT_SEARCH = f"{CONP_API_BASE}/court/search"

COURT_GOV = "https://court.gov.ua"
COURT_LIST_PAGE = f"{COURT_GOV}/sudova-vlada/sudy/"


# =========================================================================
# Local xlsx import → SQLite
# =========================================================================

COURTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS courts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    court_name      TEXT NOT NULL,
    court_code      TEXT,
    instance_type   TEXT,
    region          TEXT,
    district        TEXT,
    city            TEXT,
    address         TEXT,
    phone           TEXT,
    email           TEXT,
    website         TEXT,
    status          TEXT,
    head_judge      TEXT,
    notes           TEXT
);
CREATE INDEX IF NOT EXISTS idx_courts_region ON courts(region);
CREATE INDEX IF NOT EXISTS idx_courts_city ON courts(city);
CREATE INDEX IF NOT EXISTS idx_courts_name ON courts(court_name);
"""


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(COURTS_SCHEMA)
    return conn


def import_courts_xlsx(file_bytes: bytes) -> Dict[str, Any]:
    """Import courts from an xlsx file into SQLite.

    The function auto-detects column names by scanning the header row
    for known Ukrainian/English names.  It is tolerant to different
    column orders and names.

    Returns {"imported": N, "columns_found": [...], "warnings": [...]}.
    """
    import openpyxl

    wb = openpyxl.load_workbook(filename=_bytes_to_stream(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    if ws is None:
        return {"imported": 0, "columns_found": [], "warnings": ["Файл порожній"]}

    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return {"imported": 0, "columns_found": [], "warnings": ["Файл порожній"]}

    # --- Detect header row (first row with multiple text values) ---
    header_idx = 0
    for i, row in enumerate(rows[:5]):
        text_cells = sum(1 for c in row if c and isinstance(c, str) and len(str(c)) > 1)
        if text_cells >= 3:
            header_idx = i
            break

    raw_headers = [str(c).strip().lower() if c else "" for c in rows[header_idx]]

    # --- Map columns ---
    COLUMN_MAP = {
        "court_name": ["назва суду", "назва", "суд", "найменування", "court_name", "court name", "name"],
        "court_code": ["код суду", "код", "court_code", "code", "ідентифікатор"],
        "instance_type": ["інстанція", "тип інстанції", "instance", "instance_type", "рівень"],
        "region": ["область", "регіон", "region", "oblast"],
        "district": ["район", "district"],
        "city": ["місто", "населений пункт", "city", "locality", "місцезнаходження"],
        "address": ["адреса", "address", "повна адреса", "вулиця", "місцезнаходження суду"],
        "phone": ["телефон", "phone", "тел", "контактний телефон"],
        "email": ["email", "e-mail", "електронна пошта", "пошта"],
        "website": ["сайт", "website", "веб-сайт", "url", "веб"],
        "status": ["статус", "status", "стан"],
        "head_judge": ["голова", "голова суду", "head", "head_judge", "керівник"],
        "notes": ["примітки", "notes", "коментар", "опис"],
    }

    col_index: Dict[str, int] = {}
    for internal, aliases in COLUMN_MAP.items():
        for alias in aliases:
            for i, h in enumerate(raw_headers):
                if alias in h:
                    col_index[internal] = i
                    break
            if internal in col_index:
                break

    columns_found = list(col_index.keys())
    warnings: List[str] = []
    if "court_name" not in col_index:
        # Try to find any column that looks like court names
        for i, h in enumerate(raw_headers):
            if h and any(k in h for k in ("суд", "назв", "name", "найм")):
                col_index["court_name"] = i
                columns_found.append("court_name (auto)")
                break
    if "court_name" not in col_index:
        warnings.append("Не знайдено колонку з назвою суду. Перевірте заголовки файлу.")
        return {"imported": 0, "columns_found": columns_found, "warnings": warnings}

    # --- Import rows ---
    conn = _get_db()
    conn.execute("DELETE FROM courts")  # replace all

    imported = 0
    data_rows = rows[header_idx + 1:]
    for row in data_rows:
        name_val = _cell(row, col_index.get("court_name"))
        if not name_val:
            continue

        conn.execute(
            """INSERT INTO courts (court_name, court_code, instance_type, region,
               district, city, address, phone, email, website, status, head_judge, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                name_val,
                _cell(row, col_index.get("court_code")),
                _cell(row, col_index.get("instance_type")),
                _cell(row, col_index.get("region")),
                _cell(row, col_index.get("district")),
                _cell(row, col_index.get("city")),
                _cell(row, col_index.get("address")),
                _cell(row, col_index.get("phone")),
                _cell(row, col_index.get("email")),
                _cell(row, col_index.get("website")),
                _cell(row, col_index.get("status")),
                _cell(row, col_index.get("head_judge")),
                _cell(row, col_index.get("notes")),
            ),
        )
        imported += 1

    conn.commit()
    conn.close()

    LOGGER.info("Imported %d courts from xlsx", imported)
    return {"imported": imported, "columns_found": columns_found, "warnings": warnings}


def _cell(row: tuple, idx: Optional[int]) -> str:
    if idx is None or idx >= len(row):
        return ""
    val = row[idx]
    if val is None:
        return ""
    return str(val).strip()


def _bytes_to_stream(data: bytes):
    import io
    return io.BytesIO(data)


def get_courts_count() -> int:
    """How many courts are in the local DB."""
    if not DB_PATH.exists():
        return 0
    conn = _get_db()
    count = conn.execute("SELECT COUNT(*) FROM courts").fetchone()[0]
    conn.close()
    return count


# =========================================================================
# Court search — local DB first, then API
# =========================================================================


def find_court_by_address(
    oblast: str,
    district: str = "",
    settlement: str = "",
) -> Dict[str, Any]:
    """Find court by address. Local xlsx DB first, API fallback."""
    oblast = oblast.strip()
    district = district.strip()
    settlement = settlement.strip()

    # 1. Try local DB
    result = _search_local(oblast, district, settlement)
    if result:
        return result

    # 2. Fallback to API
    result = _search_api(oblast, district, settlement)
    if result:
        return result

    return {
        "court_name": f"Не знайдено суд для: {oblast}, {district}, {settlement}",
        "court_code": "",
        "address": "",
        "instance": "",
        "status": "",
        "source": "Завантажте базу судів (xlsx) або перевірте court.gov.ua",
        "url": COURT_LIST_PAGE,
    }


def _search_local(oblast: str, district: str, settlement: str) -> Optional[Dict[str, Any]]:
    """Search local SQLite courts database."""
    if not DB_PATH.exists():
        return None
    conn = _get_db()

    # Count to know if DB has data
    count = conn.execute("SELECT COUNT(*) FROM courts").fetchone()[0]
    if count == 0:
        conn.close()
        return None

    # Try settlement / city match first
    if settlement:
        row = _query_local(conn, "city LIKE ? OR address LIKE ? OR court_name LIKE ?",
                           (f"%{settlement}%", f"%{settlement}%", f"%{settlement}%"))
        if row:
            conn.close()
            return _format_local(row)

    # Try district match
    if district:
        row = _query_local(conn, "district LIKE ? OR court_name LIKE ?",
                           (f"%{district}%", f"%{district}%"))
        if row:
            conn.close()
            return _format_local(row)

    # Try region/oblast match
    if oblast:
        row = _query_local(conn, "region LIKE ? OR court_name LIKE ?",
                           (f"%{oblast}%", f"%{oblast}%"))
        if row:
            conn.close()
            return _format_local(row)

    conn.close()
    return None


def _query_local(conn: sqlite3.Connection, where: str, params: tuple) -> Optional[sqlite3.Row]:
    return conn.execute(f"SELECT * FROM courts WHERE {where} LIMIT 1", params).fetchone()


def _format_local(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "court_name": row["court_name"],
        "court_code": row["court_code"] or "",
        "address": row["address"] or "",
        "instance": row["instance_type"] or "",
        "status": row["status"] or "",
        "phone": row["phone"] or "",
        "email": row["email"] or "",
        "website": row["website"] or "",
        "head_judge": row["head_judge"] or "",
        "source": "Локальна база (xlsx)",
        "url": row["website"] or COURT_LIST_PAGE,
    }


# =========================================================================
# Online API fallback (unchanged)
# =========================================================================


def _search_api(oblast: str, district: str, settlement: str) -> Optional[Dict[str, Any]]:
    """Fallback: search via «Суд на долоні» API."""

    def _api_call(region: str = "", city: str = "", instance: str = "Перша") -> List[Dict]:
        filters: Dict[str, Any] = {}
        if instance:
            filters["instanceType"] = {"list": [instance], "operator": "or"}
        if region:
            filters["address.region"] = {"list": [region], "operator": "or"}
        if city:
            filters["address.locality"] = {"list": [city], "operator": "or"}

        body = json.dumps({
            "query": "", "defaultOperator": "and",
            "filter": filters, "searchIndex": "court",
        }).encode("utf-8")
        req = Request(CONP_COURT_SEARCH, data=body,
                      headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            items = data if isinstance(data, list) else data.get("items", [])
            return items if isinstance(items, list) else []
        except (URLError, OSError, json.JSONDecodeError) as exc:
            LOGGER.warning("Court API error: %s", exc)
            return []

    # Settlement
    if settlement:
        courts = _api_call(city=settlement)
        if not courts and not settlement.startswith("місто"):
            courts = _api_call(city=f"місто {settlement}")
        if courts:
            return _format_api(courts[0])

    # Region
    if oblast:
        region = oblast if oblast.endswith("область") else f"{oblast} область"
        courts = _api_call(region=region)
        if courts:
            if district:
                for c in courts:
                    if district.lower() in c.get("courtName", "").lower():
                        return _format_api(c)
            return _format_api(courts[0])

    return None


def _format_api(court: Dict[str, Any]) -> Dict[str, Any]:
    addr = court.get("address", {})
    if isinstance(addr, dict):
        full = addr.get("fullAddress", "") or ", ".join(filter(None, [
            addr.get("region", ""), addr.get("locality", ""), addr.get("streetAddress", ""),
        ]))
    else:
        full = str(addr)

    code = court.get("courtCode", "")
    return {
        "court_name": court.get("courtName", ""),
        "court_code": code,
        "address": full,
        "instance": court.get("instanceType", ""),
        "status": "",
        "source": "api.conp.com.ua (Суд на долоні)",
        "url": f"{COURT_GOV}/fair/?cs={code}" if code else COURT_LIST_PAGE,
    }
