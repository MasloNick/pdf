"""Analytics response schemas."""

from decimal import Decimal
from pydantic import BaseModel


class PortfolioStats(BaseModel):
    total_portfolios: int
    total_debtors: int
    total_nominal_debt: Decimal
    total_current_debt: Decimal
    total_recovered: Decimal


class CourtStats(BaseModel):
    court_name: str
    total_cases: int
    satisfied_count: int
    denied_count: int
    satisfaction_rate: float
    avg_awarded_amount: Decimal | None


class JudgeStats(BaseModel):
    judge_name: str
    court_name: str
    total_cases: int
    satisfied_count: int
    denied_count: int
    satisfaction_rate: float


class CaseTypeStats(BaseModel):
    case_type: str
    total_cases: int
    satisfied_count: int
    avg_duration_days: float | None


class DashboardSummary(BaseModel):
    portfolio_stats: PortfolioStats
    cases_by_status: dict[str, int]
    recent_decisions_count: int
    pending_enforcement_count: int
    bankruptcy_alerts_count: int
    needs_review_count: int
