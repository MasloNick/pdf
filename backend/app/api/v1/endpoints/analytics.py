"""Analytics and dashboard endpoints."""

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.bankruptcy_check import BankruptcyCheck, BankruptcyStatus
from app.models.court_case import CaseStatus, CourtCase
from app.models.court_decision import CourtDecision, DecisionResult
from app.models.debtor import Debtor
from app.models.enforcement import EnforcementProceeding, EnforcementStatus
from app.models.portfolio import Portfolio
from app.schemas.analytics import (
    CourtStats,
    DashboardSummary,
    JudgeStats,
    PortfolioStats,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardSummary)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    # Portfolio stats
    port_q = await db.execute(
        select(
            func.count(Portfolio.id),
            func.coalesce(func.sum(Portfolio.total_nominal_debt), 0),
        )
    )
    port_count, nominal_total = port_q.one()

    debtor_q = await db.execute(
        select(
            func.count(Debtor.id),
            func.coalesce(func.sum(Debtor.current_debt_amount), 0),
        )
    )
    debtor_count, current_total = debtor_q.one()

    recovered_q = await db.execute(
        select(func.coalesce(func.sum(EnforcementProceeding.recovered_amount), 0))
    )
    total_recovered = recovered_q.scalar() or 0

    portfolio_stats = PortfolioStats(
        total_portfolios=port_count,
        total_debtors=debtor_count,
        total_nominal_debt=nominal_total,
        total_current_debt=current_total,
        total_recovered=Decimal(str(total_recovered)),
    )

    # Cases by status
    status_q = await db.execute(
        select(CourtCase.status, func.count(CourtCase.id)).group_by(CourtCase.status)
    )
    cases_by_status = {str(s): c for s, c in status_q.all()}

    # Counts
    decisions_count = (
        await db.execute(select(func.count(CourtDecision.id)))
    ).scalar() or 0

    pending_enforcement = (
        await db.execute(
            select(func.count(EnforcementProceeding.id)).where(
                EnforcementProceeding.status.in_([
                    EnforcementStatus.PENDING_SUBMISSION,
                    EnforcementStatus.SUBMITTED,
                ])
            )
        )
    ).scalar() or 0

    bankruptcy_alerts = (
        await db.execute(
            select(func.count(BankruptcyCheck.id)).where(
                BankruptcyCheck.status.in_([
                    BankruptcyStatus.PROCEEDINGS_OPENED,
                    BankruptcyStatus.BANKRUPT,
                ]),
                BankruptcyCheck.alert_sent == False,  # noqa: E712
            )
        )
    ).scalar() or 0

    needs_review = (
        await db.execute(
            select(func.count(CourtDecision.id)).where(
                CourtDecision.needs_review == True  # noqa: E712
            )
        )
    ).scalar() or 0

    return DashboardSummary(
        portfolio_stats=portfolio_stats,
        cases_by_status=cases_by_status,
        recent_decisions_count=decisions_count,
        pending_enforcement_count=pending_enforcement,
        bankruptcy_alerts_count=bankruptcy_alerts,
        needs_review_count=needs_review,
    )


@router.get("/courts", response_model=list[CourtStats])
async def court_statistics(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    stmt = (
        select(
            CourtCase.court_name,
            func.count(CourtCase.id).label("total_cases"),
            func.sum(
                case(
                    (CourtDecision.result == DecisionResult.SATISFIED, 1),
                    (CourtDecision.result == DecisionResult.PARTIALLY_SATISFIED, 1),
                    else_=0,
                )
            ).label("satisfied_count"),
            func.sum(
                case(
                    (CourtDecision.result == DecisionResult.DENIED, 1),
                    else_=0,
                )
            ).label("denied_count"),
            func.avg(CourtDecision.awarded_total).label("avg_awarded"),
        )
        .outerjoin(CourtDecision, CourtDecision.court_case_id == CourtCase.id)
        .group_by(CourtCase.court_name)
        .order_by(func.count(CourtCase.id).desc())
    )
    result = await db.execute(stmt)
    items = []
    for row in result.all():
        total = row.total_cases or 1
        satisfied = row.satisfied_count or 0
        items.append(
            CourtStats(
                court_name=row.court_name,
                total_cases=row.total_cases,
                satisfied_count=satisfied,
                denied_count=row.denied_count or 0,
                satisfaction_rate=round(satisfied / total * 100, 1),
                avg_awarded_amount=row.avg_awarded,
            )
        )
    return items


@router.get("/judges", response_model=list[JudgeStats])
async def judge_statistics(
    court_name: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    stmt = (
        select(
            CourtCase.judge_name,
            CourtCase.court_name,
            func.count(CourtCase.id).label("total_cases"),
            func.sum(
                case(
                    (CourtDecision.result == DecisionResult.SATISFIED, 1),
                    (CourtDecision.result == DecisionResult.PARTIALLY_SATISFIED, 1),
                    else_=0,
                )
            ).label("satisfied_count"),
            func.sum(
                case(
                    (CourtDecision.result == DecisionResult.DENIED, 1),
                    else_=0,
                )
            ).label("denied_count"),
        )
        .outerjoin(CourtDecision, CourtDecision.court_case_id == CourtCase.id)
        .where(CourtCase.judge_name.isnot(None))
        .group_by(CourtCase.judge_name, CourtCase.court_name)
        .order_by(func.count(CourtCase.id).desc())
    )
    if court_name:
        stmt = stmt.where(CourtCase.court_name.ilike(f"%{court_name}%"))

    result = await db.execute(stmt)
    items = []
    for row in result.all():
        total = row.total_cases or 1
        satisfied = row.satisfied_count or 0
        items.append(
            JudgeStats(
                judge_name=row.judge_name,
                court_name=row.court_name,
                total_cases=row.total_cases,
                satisfied_count=satisfied,
                denied_count=row.denied_count or 0,
                satisfaction_rate=round(satisfied / total * 100, 1),
            )
        )
    return items
