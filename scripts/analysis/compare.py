"""Portfolio comparison — side-by-side analysis of two NPL portfolios.

Imports two CSV portfolios, analyses and scores each one, then builds
a structured comparison with per-metric deltas and an overall winner.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from scripts.analysis.portfolio import analyze_portfolio, import_portfolio_csv
from scripts.analysis.scoring import score_portfolio


# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

# Each tuple: (key, label, source, higher_is_better)
#   source: "summary" = PortfolioSummary, "scoring" = PortfolioScore
#   higher_is_better: True  -> bigger value wins
#                     False -> smaller value wins (but only when both > 0)
#                     None  -> informational, no winner logic
METRICS: List[Tuple[str, str, str, Optional[bool]]] = [
    ("total_records",             "Кількість записів",                    "summary", None),
    ("total_debt",                "Загальний борг",                       "summary", True),
    ("total_principal",           "Тіло кредиту",                         "summary", True),
    ("total_interest",            "Відсотки",                             "summary", None),
    ("total_penalty",             "Пеня / штрафи",                        "summary", None),
    ("avg_debt",                  "Середній борг",                        "summary", True),
    ("median_debt",               "Медіанний борг",                       "summary", True),
    ("principal_ratio",           "Частка тіла кредиту",                  "summary", True),
    ("physical_count",            "Фізичні особи",                        "summary", None),
    ("legal_count",               "Юридичні особи",                       "summary", None),
    ("overall_score",             "Загальна оцінка (0-100)",              "scoring", True),
    ("overall_grade",             "Загальна оцінка (літера)",             "scoring", None),
    ("estimated_total_recovery",  "Очікуване стягнення",                  "scoring", True),
    ("avg_recovery_rate",         "Середня ставка стягнення",             "scoring", True),
    ("max_recommended_price",     "Макс. рекомендована ціна",             "scoring", True),
]

# Grade ordering for comparison (higher index = better)
_GRADE_ORDER = {"F": 0, "D": 1, "C": 2, "B": 3, "A": 4}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_metric_value(
    key: str,
    source: str,
    summary_dict: Dict[str, Any],
    scoring_dict: Dict[str, Any],
) -> Any:
    """Retrieve a metric value from the appropriate source dict."""
    pool = summary_dict if source == "summary" else scoring_dict
    return pool.get(key, 0)


def _numeric(val: Any) -> float:
    """Coerce a metric value to float for comparison."""
    if isinstance(val, (int, float)):
        return float(val)
    return 0.0


def _compute_difference(val_a: Any, val_b: Any, key: str) -> Any:
    """Return numeric difference (a - b) or None for non-numeric metrics."""
    if key == "overall_grade":
        return None
    return round(_numeric(val_a) - _numeric(val_b), 6)


def _determine_winner(
    val_a: Any,
    val_b: Any,
    key: str,
    higher_is_better: Optional[bool],
) -> str:
    """Return 'A', 'B', or 'tie'."""
    if higher_is_better is None:
        return "tie"

    # Special handling for letter grade
    if key == "overall_grade":
        oa = _GRADE_ORDER.get(str(val_a), -1)
        ob = _GRADE_ORDER.get(str(val_b), -1)
        if oa > ob:
            return "A"
        elif ob > oa:
            return "B"
        return "tie"

    na, nb = _numeric(val_a), _numeric(val_b)
    if na == nb:
        return "tie"
    if higher_is_better:
        return "A" if na > nb else "B"
    return "A" if na < nb else "B"


def _build_recommendation(
    name_a: str,
    name_b: str,
    score_a: Dict[str, Any],
    score_b: Dict[str, Any],
    summary_a: Dict[str, Any],
    summary_b: Dict[str, Any],
    overall_winner: str,
) -> str:
    """Generate a Ukrainian-language recommendation paragraph."""

    if overall_winner == "tie":
        header = (
            f"Обидва портфелі ({name_a} та {name_b}) мають однакову загальну оцінку."
        )
    else:
        winner_name = name_a if overall_winner == "A" else name_b
        loser_name = name_b if overall_winner == "A" else name_a
        w_score = score_a if overall_winner == "A" else score_b
        l_score = score_b if overall_winner == "A" else score_a
        header = (
            f"{winner_name} є кращим вибором порівняно з {loser_name}."
        )

    parts: List[str] = [header]

    # Score comparison
    sa = score_a.get("overall_score", 0)
    sb = score_b.get("overall_score", 0)
    parts.append(
        f"Загальна оцінка: {name_a} — {sa}/100 ({score_a.get('overall_grade', '?')}), "
        f"{name_b} — {sb}/100 ({score_b.get('overall_grade', '?')})."
    )

    # Recovery comparison
    ra = score_a.get("avg_recovery_rate", 0) * 100
    rb = score_b.get("avg_recovery_rate", 0) * 100
    parts.append(
        f"Очікувана ставка стягнення: {name_a} — {ra:.1f}%, {name_b} — {rb:.1f}%."
    )

    # Principal quality
    pra = summary_a.get("principal_ratio", 0) * 100
    prb = summary_b.get("principal_ratio", 0) * 100
    parts.append(
        f"Частка тіла кредиту: {name_a} — {pra:.1f}%, {name_b} — {prb:.1f}%."
    )

    # Max recommended price
    mpa = score_a.get("max_recommended_price", 0)
    mpb = score_b.get("max_recommended_price", 0)
    parts.append(
        f"Максимальна рекомендована ціна: {name_a} — {mpa:.2f} грн, "
        f"{name_b} — {mpb:.2f} грн."
    )

    # Risk flags
    flags_a = score_a.get("risk_flags", [])
    flags_b = score_b.get("risk_flags", [])
    if flags_a and not flags_b:
        parts.append(f"Увага: {name_a} має ризик-фактори: {'; '.join(flags_a)}.")
    elif flags_b and not flags_a:
        parts.append(f"Увага: {name_b} має ризик-фактори: {'; '.join(flags_b)}.")
    elif flags_a and flags_b:
        parts.append(
            f"Обидва портфелі мають ризик-фактори. "
            f"{name_a}: {'; '.join(flags_a)}. {name_b}: {'; '.join(flags_b)}."
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main comparison function
# ---------------------------------------------------------------------------

def compare_portfolios(
    csv_a: str,
    csv_b: str,
    name_a: str = "Портфель A",
    name_b: str = "Портфель B",
) -> dict:
    """Compare two NPL portfolios side by side.

    Parameters
    ----------
    csv_a : str
        Raw CSV text for the first portfolio.
    csv_b : str
        Raw CSV text for the second portfolio.
    name_a : str
        Display name for the first portfolio.
    name_b : str
        Display name for the second portfolio.

    Returns
    -------
    dict
        Structured comparison result with keys: portfolios, comparison_table,
        overall_winner, recommendation, warnings.
    """
    # --- Import CSVs ---
    records_a, warnings_a = import_portfolio_csv(csv_a)
    records_b, warnings_b = import_portfolio_csv(csv_b)

    # --- Analyse ---
    summary_a = analyze_portfolio(records_a)
    summary_b = analyze_portfolio(records_b)

    # --- Score ---
    scoring_a = score_portfolio(records_a)
    scoring_b = score_portfolio(records_b)

    # Convert to dicts for uniform access
    sum_a = summary_a.to_dict()
    sum_b = summary_b.to_dict()
    scr_a = scoring_a.to_dict()
    scr_b = scoring_b.to_dict()

    # --- Build comparison table ---
    comparison_table: List[Dict[str, Any]] = []
    for key, label, source, higher_is_better in METRICS:
        val_a = _get_metric_value(key, source, sum_a, scr_a)
        val_b = _get_metric_value(key, source, sum_b, scr_b)
        difference = _compute_difference(val_a, val_b, key)
        winner = _determine_winner(val_a, val_b, key, higher_is_better)
        comparison_table.append({
            "metric": label,
            "key": key,
            "value_a": val_a,
            "value_b": val_b,
            "difference": difference,
            "winner": winner,
        })

    # --- Overall winner: based on overall_score ---
    score_val_a = scr_a.get("overall_score", 0)
    score_val_b = scr_b.get("overall_score", 0)
    if score_val_a > score_val_b:
        overall_winner = "A"
    elif score_val_b > score_val_a:
        overall_winner = "B"
    else:
        overall_winner = "tie"

    # --- Recommendation ---
    recommendation = _build_recommendation(
        name_a, name_b, scr_a, scr_b, sum_a, sum_b, overall_winner,
    )

    # --- Aggregate warnings ---
    all_warnings: List[str] = []
    for w in warnings_a:
        all_warnings.append(f"{name_a}: {w}")
    for w in warnings_b:
        all_warnings.append(f"{name_b}: {w}")

    return {
        "portfolios": [
            {
                "name": name_a,
                "summary": sum_a,
                "scoring": scr_a,
            },
            {
                "name": name_b,
                "summary": sum_b,
                "scoring": scr_b,
            },
        ],
        "comparison_table": comparison_table,
        "overall_winner": overall_winner,
        "recommendation": recommendation,
        "warnings": all_warnings,
    }
