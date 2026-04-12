"""Deep portfolio scoring — debt quality, recovery estimation, risk grading.

Goes beyond basic totals: scores each debtor, estimates recovery rates,
assigns risk grades, and produces actionable buy/pass recommendations.
"""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Scoring parameters
# ---------------------------------------------------------------------------

# Recovery rate estimates by debt characteristics (% of total debt)
RECOVERY_RATES = {
    # By collateral type
    "mortgage": 0.35,           # іпотека — 35% середнє стягнення
    "vehicle": 0.20,            # авто — 20%
    "other_collateral": 0.12,   # інше забезпечення — 12%
    "unsecured": 0.05,          # без забезпечення — 5%
    # By debtor type
    "physical_active": 0.08,    # фіз. особа працездатна — 8%
    "physical_pension": 0.03,   # пенсіонер — 3%
    "legal_active": 0.15,       # юр. особа діюча — 15%
    "legal_liquidating": 0.03,  # юр. особа в ліквідації — 3%
    "legal_bankrupt": 0.01,     # юр. особа банкрут — 1%
    "legal_terminated": 0.00,   # юр. особа припинена — 0%
}

# Debt aging impact on recovery (multiplier)
AGING_MULTIPLIERS = {
    "0-1y": 1.0,     # свіжий борг
    "1-2y": 0.75,
    "2-3y": 0.55,
    "3-5y": 0.35,
    "5-7y": 0.20,
    "7-10y": 0.10,
    "10y+": 0.05,
}

# Principal ratio impact
PRINCIPAL_QUALITY = {
    "high": {"range": (0.6, 1.0), "label": "високоякісний — переважно тіло", "multiplier": 1.2},
    "medium": {"range": (0.3, 0.6), "label": "середній — тіло + відсотки", "multiplier": 1.0},
    "low": {"range": (0.0, 0.3), "label": "низькоякісний — переважно штрафи/пеня", "multiplier": 0.7},
}


@dataclass
class DebtorScore:
    """Score for an individual debtor."""
    name: str = ""
    debtor_type: str = "physical"
    debt_total: float = 0.0
    debt_principal: float = 0.0
    principal_ratio: float = 0.0
    estimated_recovery: float = 0.0
    recovery_rate: float = 0.0
    risk_grade: str = "C"        # A/B/C/D/F
    score: int = 0               # 0-100
    flags: List[str] = field(default_factory=list)


@dataclass
class PortfolioScore:
    """Deep scoring result for the entire portfolio."""
    # Overall
    total_records: int = 0
    total_debt: float = 0.0
    total_principal: float = 0.0
    overall_score: int = 0              # 0-100
    overall_grade: str = "C"            # A/B/C/D/F
    quality_label: str = ""

    # Recovery
    estimated_total_recovery: float = 0.0
    avg_recovery_rate: float = 0.0
    estimated_profit_at_price: float = 0.0

    # Risk distribution
    grade_distribution: Dict[str, int] = field(default_factory=dict)
    risk_flags: List[str] = field(default_factory=list)

    # Composition analysis
    principal_quality: str = ""
    avg_debt_per_debtor: float = 0.0
    collection_cost_estimate: float = 0.0

    # Recommendation
    max_recommended_price: float = 0.0
    recommendation: str = ""     # "BUY" / "CONSIDER" / "PASS"
    recommendation_reasons: List[str] = field(default_factory=list)

    # Debtor details
    top_debtors: List[Dict[str, Any]] = field(default_factory=list)
    debtor_scores: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def score_debtor(record: Dict[str, Any]) -> DebtorScore:
    """Score a single debtor record."""
    s = DebtorScore()
    s.name = record.get("name", "")
    s.debtor_type = (record.get("debtor_type") or "physical").lower()
    s.debt_total = _f(record.get("debt_total", 0))
    s.debt_principal = _f(record.get("debt_principal", 0))

    if s.debt_total > 0:
        s.principal_ratio = s.debt_principal / s.debt_total
    else:
        s.principal_ratio = 0

    # Base recovery rate
    if s.debtor_type in ("physical", "фіз", "фізична"):
        base_rate = RECOVERY_RATES["physical_active"]
    elif record.get("status") == "bankrupt":
        base_rate = RECOVERY_RATES["legal_bankrupt"]
    elif record.get("status") == "in_liquidation":
        base_rate = RECOVERY_RATES["legal_liquidating"]
    elif record.get("status") == "terminated":
        base_rate = RECOVERY_RATES["legal_terminated"]
    else:
        base_rate = RECOVERY_RATES["legal_active"]

    # Collateral adjustment
    collateral = (record.get("collateral") or record.get("забезпечення") or "").lower()
    if "іпотек" in collateral or "mortgage" in collateral:
        base_rate = max(base_rate, RECOVERY_RATES["mortgage"])
    elif "авто" in collateral or "транспорт" in collateral or "vehicle" in collateral:
        base_rate = max(base_rate, RECOVERY_RATES["vehicle"])
    elif collateral and collateral not in ("ні", "без", "none", ""):
        base_rate = max(base_rate, RECOVERY_RATES["other_collateral"])

    # Principal quality adjustment
    if s.principal_ratio > 0.6:
        base_rate *= 1.15
    elif s.principal_ratio < 0.3:
        base_rate *= 0.75

    # Debt size adjustment — micro debts have higher per-unit collection cost
    if s.debt_total < 5000:
        base_rate *= 0.5   # мікро борг — дорого стягувати
        s.flags.append("мікро-борг (<5000 грн)")
    elif s.debt_total < 20000:
        base_rate *= 0.8

    s.recovery_rate = round(min(base_rate, 0.95), 4)
    s.estimated_recovery = round(s.debt_total * s.recovery_rate, 2)

    # Score (0-100)
    score = 50  # base
    if s.principal_ratio > 0.6:
        score += 15
    elif s.principal_ratio < 0.3:
        score -= 20
    if s.debt_total > 50000:
        score += 10
    elif s.debt_total < 5000:
        score -= 15
    if s.debtor_type in ("physical", "фіз", "фізична"):
        score += 5  # фіз. особи легше стягувати масово
    if record.get("status") in ("bankrupt", "terminated"):
        score -= 30
        s.flags.append("банкрут/припинено")
    elif record.get("status") == "in_liquidation":
        score -= 20
        s.flags.append("ліквідація")

    s.score = max(0, min(100, score))

    # Grade
    if s.score >= 75:
        s.risk_grade = "A"
    elif s.score >= 60:
        s.risk_grade = "B"
    elif s.score >= 40:
        s.risk_grade = "C"
    elif s.score >= 25:
        s.risk_grade = "D"
    else:
        s.risk_grade = "F"

    return s


def score_portfolio(
    records: List[Dict[str, Any]],
    asking_price: float = 0,
) -> PortfolioScore:
    """Deep-score an entire portfolio and produce recommendation."""
    ps = PortfolioScore()
    ps.total_records = len(records)

    if not records:
        ps.recommendation = "PASS"
        ps.recommendation_reasons.append("Порожній портфель")
        return ps

    scored: List[DebtorScore] = []
    for rec in records:
        ds = score_debtor(rec)
        scored.append(ds)
        ps.total_debt += ds.debt_total
        ps.total_principal += ds.debt_principal
        ps.estimated_total_recovery += ds.estimated_recovery

    ps.debtor_scores = [
        {"name": s.name, "debt": s.debt_total, "score": s.score,
         "grade": s.risk_grade, "recovery": s.estimated_recovery, "flags": s.flags}
        for s in scored
    ]

    # Grade distribution
    grades = Counter(s.risk_grade for s in scored)
    ps.grade_distribution = dict(grades.most_common())

    # Overall score = weighted average by debt
    if ps.total_debt > 0:
        ps.overall_score = round(
            sum(s.score * s.debt_total for s in scored) / ps.total_debt
        )
        ps.avg_recovery_rate = round(ps.estimated_total_recovery / ps.total_debt, 4)
    else:
        ps.overall_score = 0

    # Overall grade
    if ps.overall_score >= 75:
        ps.overall_grade = "A"
        ps.quality_label = "Високоякісний портфель"
    elif ps.overall_score >= 60:
        ps.overall_grade = "B"
        ps.quality_label = "Портфель вище середнього"
    elif ps.overall_score >= 40:
        ps.overall_grade = "C"
        ps.quality_label = "Середній портфель"
    elif ps.overall_score >= 25:
        ps.overall_grade = "D"
        ps.quality_label = "Портфель нижче середнього"
    else:
        ps.overall_grade = "F"
        ps.quality_label = "Низькоякісний портфель"

    # Principal quality
    pr = ps.total_principal / ps.total_debt if ps.total_debt > 0 else 0
    for key, info in PRINCIPAL_QUALITY.items():
        lo, hi = info["range"]
        if lo <= pr <= hi:
            ps.principal_quality = info["label"]
            break

    # Average debt
    ps.avg_debt_per_debtor = round(ps.total_debt / len(records), 2)

    # Collection cost estimate (грубо: ~2000 грн на боржника для судового стягнення)
    ps.collection_cost_estimate = round(len(records) * 2000, 2)

    # Top debtors
    top = sorted(scored, key=lambda s: s.debt_total, reverse=True)[:10]
    ps.top_debtors = [
        {"name": s.name, "debt": s.debt_total, "principal": s.debt_principal,
         "score": s.score, "grade": s.risk_grade, "recovery": s.estimated_recovery}
        for s in top
    ]

    # Max recommended price = estimated recovery minus collection costs minus margin
    net_recovery = ps.estimated_total_recovery - ps.collection_cost_estimate
    ps.max_recommended_price = round(max(0, net_recovery * 0.7), 2)  # 30% margin

    # Risk flags
    f_count = grades.get("F", 0)
    d_count = grades.get("D", 0)
    if f_count > len(records) * 0.3:
        ps.risk_flags.append(f"{f_count} боржників ({f_count*100//len(records)}%) з оцінкою F — безнадійні")
    if d_count > len(records) * 0.3:
        ps.risk_flags.append(f"{d_count} боржників з оцінкою D — високий ризик")
    micro = sum(1 for s in scored if s.debt_total < 5000)
    if micro > len(records) * 0.5:
        ps.risk_flags.append(f"{micro} мікро-боргів (<5000 грн) — високі витрати на стягнення")
    if pr < 0.3:
        ps.risk_flags.append("Низька частка тіла кредиту (<30%) — переважно штрафи")

    # Recommendation
    if asking_price > 0:
        if asking_price <= ps.max_recommended_price * 0.7:
            ps.recommendation = "BUY"
            ps.recommendation_reasons.append(f"Ціна {asking_price:,.0f} значно нижче максимальної рекомендованої {ps.max_recommended_price:,.0f}")
        elif asking_price <= ps.max_recommended_price:
            ps.recommendation = "CONSIDER"
            ps.recommendation_reasons.append(f"Ціна {asking_price:,.0f} в межах рекомендованої {ps.max_recommended_price:,.0f}")
        else:
            ps.recommendation = "PASS"
            ps.recommendation_reasons.append(f"Ціна {asking_price:,.0f} перевищує рекомендовану {ps.max_recommended_price:,.0f}")
        ps.estimated_profit_at_price = round(ps.estimated_total_recovery - ps.collection_cost_estimate - asking_price, 2)
    else:
        if ps.overall_score >= 60 and ps.avg_recovery_rate > 0.05:
            ps.recommendation = "CONSIDER"
            ps.recommendation_reasons.append(f"Оцінка {ps.overall_score}/100, очікуване стягнення {ps.avg_recovery_rate*100:.1f}%")
        elif ps.overall_score < 30:
            ps.recommendation = "PASS"
            ps.recommendation_reasons.append(f"Низька оцінка {ps.overall_score}/100")
        else:
            ps.recommendation = "CONSIDER"
            ps.recommendation_reasons.append(f"Середня оцінка {ps.overall_score}/100 — потрібен детальний аналіз")

    ps.recommendation_reasons.append(f"Очікуване стягнення: {ps.estimated_total_recovery:,.0f} грн ({ps.avg_recovery_rate*100:.1f}% від боргу)")
    ps.recommendation_reasons.append(f"Витрати на стягнення: ~{ps.collection_cost_estimate:,.0f} грн ({len(records)} × 2000 грн)")
    ps.recommendation_reasons.append(f"Чистий прибуток при макс. ціні: {net_recovery:,.0f} грн")

    return ps


def _f(val: Any) -> float:
    if val is None or val == "":
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(" ", "").replace(",", ".").replace("грн", "").strip()
        return float(val)
    except (ValueError, TypeError):
        return 0.0
