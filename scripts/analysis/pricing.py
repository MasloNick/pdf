"""Pricing analytics and portfolio valuation recommendations.

Provides price estimation based on portfolio characteristics, market
benchmarks, and historical transaction data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Market benchmarks (Ukrainian NPL market typical ranges)
# ---------------------------------------------------------------------------

# Price as % of total debt, by portfolio type and debt age
BENCHMARK_PRICES: Dict[str, Dict[str, Dict[str, float]]] = {
    "physical": {
        "fresh": {"low": 5.0, "mid": 12.0, "high": 20.0},       # < 1 year past due
        "seasoned": {"low": 2.0, "mid": 7.0, "high": 12.0},     # 1-3 years
        "aged": {"low": 0.5, "mid": 3.0, "high": 6.0},          # 3-5 years
        "very_old": {"low": 0.1, "mid": 1.0, "high": 3.0},      # > 5 years
    },
    "legal": {
        "credit": {"low": 3.0, "mid": 10.0, "high": 25.0},
        "overdraft": {"low": 2.0, "mid": 8.0, "high": 15.0},
        "receivables": {"low": 5.0, "mid": 15.0, "high": 35.0},
    },
    "secured": {
        "mortgage": {"low": 15.0, "mid": 35.0, "high": 60.0},
        "vehicle": {"low": 8.0, "mid": 20.0, "high": 40.0},
        "other_collateral": {"low": 5.0, "mid": 15.0, "high": 30.0},
    },
}

# Adjustment factors
ADJUSTMENTS = {
    "documentation_quality": {
        "complete": 1.2,    # all docs present
        "partial": 1.0,
        "minimal": 0.7,
    },
    "debtor_count": {
        "small": 0.9,       # < 50 debtors — less diversification
        "medium": 1.0,      # 50 – 500
        "large": 1.1,       # > 500 — better diversification
    },
    "avg_debt_size": {
        "micro": 0.8,       # < 5,000 UAH — high cost to collect
        "small": 0.9,       # 5,000 – 20,000
        "medium": 1.0,      # 20,000 – 100,000
        "large": 1.1,       # > 100,000
    },
    "principal_ratio": {
        "high": 1.15,       # > 60% principal — better quality
        "medium": 1.0,      # 30-60%
        "low": 0.85,        # < 30% — mostly penalties/interest
    },
    "seller_type": {
        "state_bank": 1.0,
        "private_bank": 1.05,
        "dgf": 0.95,        # DGF assets often older/lower quality
        "mfo": 0.85,        # MFO portfolios often micro-debts
        "fc": 0.8,          # Already worked portfolio
    },
    "legal_entity_status": {
        "active": 1.2,
        "in_liquidation": 0.3,
        "bankrupt": 0.1,
        "terminated": 0.05,
    },
}


@dataclass
class PriceRecommendation:
    """Computed price recommendation for a portfolio."""

    total_debt: float = 0.0
    recommended_price_low: float = 0.0
    recommended_price_mid: float = 0.0
    recommended_price_high: float = 0.0
    price_pct_low: float = 0.0
    price_pct_mid: float = 0.0
    price_pct_high: float = 0.0
    adjustments_applied: List[str] = field(default_factory=list)
    factors: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


def recommend_price(
    total_debt: float,
    portfolio_type: str = "physical",
    debt_category: str = "seasoned",
    principal_ratio: float = 0.5,
    num_debtors: int = 100,
    avg_debt: float = 30_000,
    seller_type: str = "bank",
    documentation: str = "partial",
    legal_statuses: Optional[Dict[str, int]] = None,
) -> PriceRecommendation:
    """Compute a price recommendation for an NPL portfolio.

    Returns low/mid/high price ranges based on benchmarks and adjustments.
    """
    rec = PriceRecommendation(total_debt=total_debt)

    # 1. Base price range from benchmarks
    type_benchmarks = BENCHMARK_PRICES.get(portfolio_type, BENCHMARK_PRICES["physical"])
    base = type_benchmarks.get(debt_category, type_benchmarks.get("seasoned", {"low": 2, "mid": 7, "high": 12}))
    base_low = base["low"]
    base_mid = base["mid"]
    base_high = base["high"]
    rec.notes.append(f"Базовий діапазон для {portfolio_type}/{debt_category}: {base_low}%-{base_high}%")

    # 2. Apply adjustments
    combined_factor = 1.0

    # Principal ratio
    if principal_ratio > 0.6:
        pr_key = "high"
    elif principal_ratio > 0.3:
        pr_key = "medium"
    else:
        pr_key = "low"
    factor = ADJUSTMENTS["principal_ratio"][pr_key]
    combined_factor *= factor
    rec.adjustments_applied.append(f"Частка тіла кредиту ({pr_key}): x{factor}")
    rec.factors["principal_ratio"] = factor

    # Debtor count
    if num_debtors < 50:
        dc_key = "small"
    elif num_debtors <= 500:
        dc_key = "medium"
    else:
        dc_key = "large"
    factor = ADJUSTMENTS["debtor_count"][dc_key]
    combined_factor *= factor
    rec.adjustments_applied.append(f"Кількість боржників ({dc_key}): x{factor}")
    rec.factors["debtor_count"] = factor

    # Average debt size
    if avg_debt < 5_000:
        ad_key = "micro"
    elif avg_debt < 20_000:
        ad_key = "small"
    elif avg_debt < 100_000:
        ad_key = "medium"
    else:
        ad_key = "large"
    factor = ADJUSTMENTS["avg_debt_size"][ad_key]
    combined_factor *= factor
    rec.adjustments_applied.append(f"Середня сума боргу ({ad_key}): x{factor}")
    rec.factors["avg_debt_size"] = factor

    # Seller type
    factor = ADJUSTMENTS["seller_type"].get(seller_type, 1.0)
    combined_factor *= factor
    rec.adjustments_applied.append(f"Тип продавця ({seller_type}): x{factor}")
    rec.factors["seller_type"] = factor

    # Documentation
    factor = ADJUSTMENTS["documentation_quality"].get(documentation, 1.0)
    combined_factor *= factor
    rec.adjustments_applied.append(f"Документація ({documentation}): x{factor}")
    rec.factors["documentation"] = factor

    # Legal entity status adjustments
    if legal_statuses and portfolio_type == "legal":
        total_entities = sum(legal_statuses.values())
        if total_entities > 0:
            weighted = sum(
                count * ADJUSTMENTS["legal_entity_status"].get(status, 1.0)
                for status, count in legal_statuses.items()
            )
            factor = round(weighted / total_entities, 3)
            combined_factor *= factor
            rec.adjustments_applied.append(f"Статуси юросіб: x{factor}")
            rec.factors["legal_status"] = factor

    # 3. Compute final prices
    rec.price_pct_low = round(base_low * combined_factor, 2)
    rec.price_pct_mid = round(base_mid * combined_factor, 2)
    rec.price_pct_high = round(base_high * combined_factor, 2)

    rec.recommended_price_low = round(total_debt * rec.price_pct_low / 100, 2)
    rec.recommended_price_mid = round(total_debt * rec.price_pct_mid / 100, 2)
    rec.recommended_price_high = round(total_debt * rec.price_pct_high / 100, 2)

    rec.notes.append(f"Сумарний коефіцієнт коригування: x{round(combined_factor, 3)}")
    rec.notes.append(f"Рекомендований діапазон: {rec.price_pct_low}% – {rec.price_pct_high}% від суми боргу")

    return rec


def compare_price_to_market(
    asking_price: float,
    total_debt: float,
    portfolio_type: str = "physical",
    debt_category: str = "seasoned",
) -> Dict[str, Any]:
    """Compare an asking price against market benchmarks.

    Returns verdict: 'cheap', 'fair', 'expensive'.
    """
    if total_debt <= 0:
        return {"verdict": "невизначено", "reason": "Загальний борг не вказано"}

    pct = asking_price / total_debt * 100
    type_benchmarks = BENCHMARK_PRICES.get(portfolio_type, BENCHMARK_PRICES["physical"])
    base = type_benchmarks.get(debt_category, {"low": 2, "mid": 7, "high": 12})

    if pct < base["low"]:
        verdict = "дешево"
        color = "green"
    elif pct <= base["mid"]:
        verdict = "нижче ринку"
        color = "green"
    elif pct <= base["high"]:
        verdict = "ринкова ціна"
        color = "orange"
    else:
        verdict = "дорого"
        color = "red"

    return {
        "asking_price": asking_price,
        "total_debt": total_debt,
        "price_pct": round(pct, 2),
        "market_low_pct": base["low"],
        "market_mid_pct": base["mid"],
        "market_high_pct": base["high"],
        "verdict": verdict,
        "color": color,
    }
