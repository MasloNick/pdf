"""Data models and SQLite storage for the NPL portfolio platform.

Stores auction listings, portfolio snapshots, individual debtor records,
legal-entity checks and pricing history in a local SQLite database.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "npl.db"


def _get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db(db_path: Optional[Path] = None):
    conn = _get_connection(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS auctions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,          -- setam / prozorro / dgf / bank / private
    external_id     TEXT,                   -- ID on the source platform
    title           TEXT NOT NULL,
    description     TEXT,
    seller          TEXT,                   -- bank / MFO / FC name
    seller_type     TEXT,                   -- bank / mfo / fc / dgf
    portfolio_type  TEXT,                   -- physical / legal / mixed
    debt_type       TEXT,                   -- credit / overdraft / receivables / mixed
    total_debt      REAL,
    total_principal REAL,
    total_interest  REAL,
    total_penalty   REAL,
    num_debtors     INTEGER,
    start_price     REAL,
    guarantee_amount REAL,
    current_price   REAL,
    currency        TEXT DEFAULT 'UAH',
    auction_date    TEXT,                   -- ISO date
    end_date        TEXT,
    status          TEXT DEFAULT 'active',  -- active / completed / cancelled
    url             TEXT,
    passport_url    TEXT,                   -- link to auction passport / lot description
    conditions      TEXT,                   -- JSON with extra conditions
    raw_data        TEXT,                   -- full JSON dump from source
    created_at      REAL DEFAULT (strftime('%%s','now')),
    updated_at      REAL DEFAULT (strftime('%%s','now')),
    UNIQUE(source, external_id)
);

CREATE TABLE IF NOT EXISTS debtors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    auction_id      INTEGER REFERENCES auctions(id) ON DELETE CASCADE,
    debtor_type     TEXT NOT NULL,          -- physical / legal
    name            TEXT,
    edrpou          TEXT,                   -- for legal entities
    debt_total      REAL,
    debt_principal  REAL,
    debt_interest   REAL,
    debt_penalty    REAL,
    contract_number TEXT,
    contract_date   TEXT,
    debt_currency   TEXT DEFAULT 'UAH',
    region          TEXT,
    status          TEXT,                   -- active / bankrupt / liquidated (for legal)
    notes           TEXT,
    created_at      REAL DEFAULT (strftime('%%s','now'))
);

CREATE TABLE IF NOT EXISTS company_checks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    edrpou          TEXT NOT NULL,
    name            TEXT,
    status          TEXT,                   -- active / in_liquidation / bankrupt / terminated
    registration_date TEXT,
    address         TEXT,
    authorized_capital REAL,
    main_activity   TEXT,
    has_tax_debt    INTEGER DEFAULT 0,
    has_court_cases INTEGER DEFAULT 0,
    court_cases_count INTEGER DEFAULT 0,
    has_enforcement INTEGER DEFAULT 0,
    enforcement_count INTEGER DEFAULT 0,
    bankruptcy_case TEXT,
    source_url      TEXT,
    raw_data        TEXT,
    checked_at      REAL DEFAULT (strftime('%%s','now'))
);

CREATE TABLE IF NOT EXISTS court_cases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    debtor_id       INTEGER REFERENCES debtors(id) ON DELETE CASCADE,
    company_check_id INTEGER REFERENCES company_checks(id) ON DELETE CASCADE,
    case_number     TEXT,
    court_name      TEXT,
    case_type       TEXT,                   -- civil / economic / enforcement
    plaintiff       TEXT,
    defendant       TEXT,
    description     TEXT,
    status          TEXT,
    decision_date   TEXT,
    url             TEXT,
    created_at      REAL DEFAULT (strftime('%%s','now'))
);

CREATE TABLE IF NOT EXISTS price_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    auction_id      INTEGER REFERENCES auctions(id) ON DELETE CASCADE,
    price           REAL NOT NULL,
    price_per_debt  REAL,                   -- price / total_debt ratio
    recorded_at     REAL DEFAULT (strftime('%%s','now'))
);

CREATE TABLE IF NOT EXISTS monitoring_targets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type     TEXT NOT NULL,          -- url / keyword / seller
    target_value    TEXT NOT NULL,
    description     TEXT,
    check_interval  INTEGER DEFAULT 3600,   -- seconds
    last_checked    REAL,
    is_active       INTEGER DEFAULT 1,
    created_at      REAL DEFAULT (strftime('%%s','now'))
);

CREATE INDEX IF NOT EXISTS idx_auctions_source ON auctions(source);
CREATE INDEX IF NOT EXISTS idx_auctions_status ON auctions(status);
CREATE INDEX IF NOT EXISTS idx_auctions_seller ON auctions(seller);
CREATE INDEX IF NOT EXISTS idx_debtors_auction ON debtors(auction_id);
CREATE INDEX IF NOT EXISTS idx_debtors_type ON debtors(debtor_type);
CREATE INDEX IF NOT EXISTS idx_company_checks_edrpou ON company_checks(edrpou);
CREATE INDEX IF NOT EXISTS idx_court_cases_debtor ON court_cases(debtor_id);
"""


def init_db(db_path: Optional[Path] = None) -> None:
    with get_db(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


# ---------------------------------------------------------------------------
# Data classes for passing data around
# ---------------------------------------------------------------------------


@dataclass
class AuctionRecord:
    source: str
    title: str
    external_id: Optional[str] = None
    description: Optional[str] = None
    seller: Optional[str] = None
    seller_type: Optional[str] = None
    portfolio_type: Optional[str] = None
    debt_type: Optional[str] = None
    total_debt: Optional[float] = None
    total_principal: Optional[float] = None
    total_interest: Optional[float] = None
    total_penalty: Optional[float] = None
    num_debtors: Optional[int] = None
    start_price: Optional[float] = None
    guarantee_amount: Optional[float] = None
    current_price: Optional[float] = None
    currency: str = "UAH"
    auction_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "active"
    url: Optional[str] = None
    passport_url: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None

    def save(self, conn: sqlite3.Connection) -> int:
        d = asdict(self)
        d["conditions"] = json.dumps(d["conditions"]) if d["conditions"] else None
        d["raw_data"] = json.dumps(d["raw_data"]) if d["raw_data"] else None
        d["updated_at"] = time.time()
        cols = ", ".join(d.keys())
        placeholders = ", ".join(f":{k}" for k in d.keys())
        conn.execute(
            f"INSERT OR REPLACE INTO auctions ({cols}) VALUES ({placeholders})",
            d,
        )
        row = conn.execute(
            "SELECT id FROM auctions WHERE source=:source AND external_id=:external_id",
            {"source": self.source, "external_id": self.external_id},
        ).fetchone()
        return row["id"] if row else 0


@dataclass
class DebtorRecord:
    auction_id: int
    debtor_type: str  # physical / legal
    name: Optional[str] = None
    edrpou: Optional[str] = None
    debt_total: Optional[float] = None
    debt_principal: Optional[float] = None
    debt_interest: Optional[float] = None
    debt_penalty: Optional[float] = None
    contract_number: Optional[str] = None
    contract_date: Optional[str] = None
    debt_currency: str = "UAH"
    region: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    def save(self, conn: sqlite3.Connection) -> int:
        d = asdict(self)
        cols = ", ".join(d.keys())
        placeholders = ", ".join(f":{k}" for k in d.keys())
        cur = conn.execute(
            f"INSERT INTO debtors ({cols}) VALUES ({placeholders})", d
        )
        return cur.lastrowid or 0


@dataclass
class PortfolioStats:
    """Aggregated statistics for a portfolio or group of debtors."""
    total_records: int = 0
    total_debt: float = 0.0
    total_principal: float = 0.0
    total_interest: float = 0.0
    total_penalty: float = 0.0
    avg_debt: float = 0.0
    avg_principal: float = 0.0
    min_debt: float = 0.0
    max_debt: float = 0.0
    median_debt: float = 0.0
    physical_count: int = 0
    legal_count: int = 0
    physical_debt: float = 0.0
    legal_debt: float = 0.0
    regions: Dict[str, int] = field(default_factory=dict)
    debt_types: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Convenience queries
# ---------------------------------------------------------------------------


def get_all_auctions(
    conn: sqlite3.Connection,
    source: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM auctions WHERE 1=1"
    params: Dict[str, Any] = {}
    if source:
        sql += " AND source = :source"
        params["source"] = source
    if status:
        sql += " AND status = :status"
        params["status"] = status
    sql += " ORDER BY created_at DESC LIMIT :limit"
    params["limit"] = limit
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_auction_debtors(
    conn: sqlite3.Connection, auction_id: int
) -> List[Dict[str, Any]]:
    return [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM debtors WHERE auction_id = ?", (auction_id,)
        ).fetchall()
    ]


def get_company_check(
    conn: sqlite3.Connection, edrpou: str
) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT * FROM company_checks WHERE edrpou = ? ORDER BY checked_at DESC LIMIT 1",
        (edrpou,),
    ).fetchone()
    return dict(row) if row else None
