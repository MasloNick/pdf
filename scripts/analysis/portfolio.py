"""Portfolio analysis — statistics, breakdowns, and summaries.

Works with debtor records from the database or raw dicts/CSV imports to
produce aggregated statistics that help evaluate NPL portfolios.
"""

from __future__ import annotations

import csv
import io
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PortfolioSummary:
    """Full statistical summary of an NPL portfolio."""

    # --- Counts ---
    total_records: int = 0
    physical_count: int = 0
    legal_count: int = 0

    # --- Total amounts ---
    total_debt: float = 0.0
    total_principal: float = 0.0
    total_interest: float = 0.0
    total_penalty: float = 0.0

    # --- Physical persons subtotals ---
    phys_total_debt: float = 0.0
    phys_total_principal: float = 0.0
    phys_total_interest: float = 0.0
    phys_total_penalty: float = 0.0

    # --- Legal entities subtotals ---
    legal_total_debt: float = 0.0
    legal_total_principal: float = 0.0
    legal_total_interest: float = 0.0
    legal_total_penalty: float = 0.0

    # --- Averages ---
    avg_debt: float = 0.0
    avg_principal: float = 0.0
    median_debt: float = 0.0
    min_debt: float = 0.0
    max_debt: float = 0.0

    # --- Breakdowns ---
    by_region: Dict[str, int] = field(default_factory=dict)
    by_debt_type: Dict[str, int] = field(default_factory=dict)
    by_currency: Dict[str, int] = field(default_factory=dict)
    debt_ranges: Dict[str, int] = field(default_factory=dict)

    # --- Composition ratios ---
    principal_ratio: float = 0.0       # principal / total_debt
    interest_ratio: float = 0.0        # interest / total_debt
    penalty_ratio: float = 0.0         # penalty / total_debt

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


# ---------------------------------------------------------------------------
# Debt range classification
# ---------------------------------------------------------------------------

DEBT_RANGES = [
    (0, 1_000, "до 1 000 грн"),
    (1_000, 5_000, "1 000 – 5 000 грн"),
    (5_000, 10_000, "5 000 – 10 000 грн"),
    (10_000, 50_000, "10 000 – 50 000 грн"),
    (50_000, 100_000, "50 000 – 100 000 грн"),
    (100_000, 500_000, "100 000 – 500 000 грн"),
    (500_000, 1_000_000, "500 000 – 1 000 000 грн"),
    (1_000_000, float("inf"), "понад 1 000 000 грн"),
]


def _classify_debt_range(amount: float) -> str:
    for lo, hi, label in DEBT_RANGES:
        if lo <= amount < hi:
            return label
    return "невизначено"


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------


def analyze_portfolio(records: List[Dict[str, Any]]) -> PortfolioSummary:
    """Produce a full statistical summary from a list of debtor records.

    Each record is a dict with optional keys: debtor_type, debt_total,
    debt_principal, debt_interest, debt_penalty, region, debt_currency, etc.
    """
    s = PortfolioSummary()
    s.total_records = len(records)
    if not records:
        return s

    debts: List[float] = []
    region_counter: Counter = Counter()
    debt_type_counter: Counter = Counter()
    currency_counter: Counter = Counter()
    range_counter: Counter = Counter()

    for r in records:
        dtype = (r.get("debtor_type") or "physical").lower()
        total = _float(r.get("debt_total", 0))
        principal = _float(r.get("debt_principal", 0))
        interest = _float(r.get("debt_interest", 0))
        penalty = _float(r.get("debt_penalty", 0))
        region = r.get("region") or "невідомо"
        currency = r.get("debt_currency") or "UAH"

        # Totals
        s.total_debt += total
        s.total_principal += principal
        s.total_interest += interest
        s.total_penalty += penalty

        if dtype in ("physical", "фіз", "фізична"):
            s.physical_count += 1
            s.phys_total_debt += total
            s.phys_total_principal += principal
            s.phys_total_interest += interest
            s.phys_total_penalty += penalty
        else:
            s.legal_count += 1
            s.legal_total_debt += total
            s.legal_total_principal += principal
            s.legal_total_interest += interest
            s.legal_total_penalty += penalty

        if total > 0:
            debts.append(total)
        range_counter[_classify_debt_range(total)] += 1
        region_counter[region] += 1
        currency_counter[currency] += 1

        # Classify debt type from record if present
        dt = r.get("debt_type") or r.get("contract_type") or "кредит"
        debt_type_counter[dt.lower()] += 1

    # Averages
    if debts:
        s.avg_debt = s.total_debt / len(debts)
        s.avg_principal = s.total_principal / len(debts)
        s.median_debt = statistics.median(debts)
        s.min_debt = min(debts)
        s.max_debt = max(debts)

    # Ratios
    if s.total_debt > 0:
        s.principal_ratio = round(s.total_principal / s.total_debt, 4)
        s.interest_ratio = round(s.total_interest / s.total_debt, 4)
        s.penalty_ratio = round(s.total_penalty / s.total_debt, 4)

    # Breakdowns
    s.by_region = dict(region_counter.most_common())
    s.by_debt_type = dict(debt_type_counter.most_common())
    s.by_currency = dict(currency_counter.most_common())
    s.debt_ranges = dict(range_counter)

    return s


def analyze_auction(auction: Dict[str, Any]) -> Dict[str, Any]:
    """Quick analysis of an auction record (without individual debtors).

    Computes key indicators from the auction-level aggregates.
    """
    total_debt = _float(auction.get("total_debt", 0))
    start_price = _float(auction.get("start_price", 0))
    current_price = _float(auction.get("current_price", 0))
    guarantee = _float(auction.get("guarantee_amount", 0))
    num_debtors = auction.get("num_debtors") or 0

    price_to_debt = (start_price / total_debt * 100) if total_debt > 0 else 0
    guarantee_pct = (guarantee / start_price * 100) if start_price > 0 else 0
    avg_debt_per_debtor = (total_debt / num_debtors) if num_debtors > 0 else 0

    return {
        "total_debt": total_debt,
        "start_price": start_price,
        "current_price": current_price,
        "guarantee_amount": guarantee,
        "num_debtors": num_debtors,
        "price_to_debt_pct": round(price_to_debt, 2),
        "guarantee_pct": round(guarantee_pct, 2),
        "avg_debt_per_debtor": round(avg_debt_per_debtor, 2),
        "portfolio_type": auction.get("portfolio_type", "unknown"),
        "debt_type": auction.get("debt_type", "unknown"),
        "seller": auction.get("seller", ""),
        "seller_type": auction.get("seller_type", ""),
    }


# ---------------------------------------------------------------------------
# CSV import helper
# ---------------------------------------------------------------------------

# Expected columns (flexible matching)
COLUMN_MAP = {
    "debtor_type": ["тип", "type", "debtor_type", "тип боржника", "тип_боржника"],
    "name": ["назва", "name", "пiб", "піб", "боржник", "найменування"],
    "edrpou": ["єдрпоу", "edrpou", "код", "код єдрпоу"],
    "debt_total": ["загальна сума", "total", "debt_total", "сума боргу", "борг", "загальний борг"],
    "debt_principal": ["тіло", "principal", "debt_principal", "основний борг", "тіло кредиту"],
    "debt_interest": ["відсотки", "interest", "debt_interest", "проценти", "%"],
    "debt_penalty": ["пеня", "penalty", "debt_penalty", "штраф", "штрафи"],
    "contract_number": ["договір", "contract", "contract_number", "номер договору", "№ договору"],
    "contract_date": ["дата договору", "contract_date", "дата"],
    "region": ["регіон", "region", "область", "місто"],
    "debt_currency": ["валюта", "currency", "debt_currency"],
}


def import_portfolio_csv(csv_text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Parse a CSV string into normalised debtor dicts.

    Returns (records, warnings).  The function maps Ukrainian and English
    column names to internal field names.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        return [], ["CSV файл порожній або не має заголовків."]

    # Build column mapping
    header_map: Dict[str, str] = {}
    lower_fields = {f.strip().lower(): f for f in reader.fieldnames}
    for internal_name, aliases in COLUMN_MAP.items():
        for alias in aliases:
            if alias.lower() in lower_fields:
                header_map[lower_fields[alias.lower()]] = internal_name
                break

    warnings: List[str] = []
    if "debt_total" not in header_map.values():
        warnings.append("Не знайдено колонку із загальною сумою боргу.")

    records: List[Dict[str, Any]] = []
    for i, row in enumerate(reader, start=2):
        rec: Dict[str, Any] = {}
        for csv_col, internal in header_map.items():
            val = row.get(csv_col, "")
            if internal in ("debt_total", "debt_principal", "debt_interest", "debt_penalty"):
                rec[internal] = _float(val)
            else:
                rec[internal] = (val or "").strip()
        # Default debtor type
        if not rec.get("debtor_type"):
            rec["debtor_type"] = "physical"
        records.append(rec)

    return records, warnings


def _float(val: Any) -> float:
    if val is None or val == "":
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(" ", "").replace(",", ".").replace("грн", "").strip()
        return float(val)
    except (ValueError, TypeError):
        return 0.0
