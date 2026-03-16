"""Analytics / dashboard endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.court_case import CourtCase
from app.models.debtor import Debtor
from app.models.enforcement import EnforcementProceeding
from app.models.portfolio import Portfolio
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    portfolios_count = (await db.execute(select(func.count(Portfolio.id)))).scalar() or 0
    debtors_count = (await db.execute(select(func.count(Debtor.id)))).scalar() or 0
    cases_count = (await db.execute(select(func.count(CourtCase.id)))).scalar() or 0
    active_enforcements = (
        await db.execute(
            select(func.count(EnforcementProceeding.id)).where(
                EnforcementProceeding.status == "active"
            )
        )
    ).scalar() or 0

    bankrupt_count = (
        await db.execute(select(func.count(Debtor.id)).where(Debtor.is_bankrupt.is_(True)))
    ).scalar() or 0

    cases_by_status = dict(
        (
            await db.execute(
                select(CourtCase.status, func.count(CourtCase.id)).group_by(CourtCase.status)
            )
        ).all()
    )

    return {
        "portfolios": portfolios_count,
        "debtors": debtors_count,
        "court_cases": cases_count,
        "active_enforcements": active_enforcements,
        "bankrupt_debtors": bankrupt_count,
        "cases_by_status": cases_by_status,
    }


@router.get("/courts")
async def court_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Stats grouped by court name."""
    result = await db.execute(
        select(
            CourtCase.court_name,
            func.count(CourtCase.id).label("total_cases"),
            func.sum(CourtCase.awarded_amount).label("total_awarded"),
        )
        .group_by(CourtCase.court_name)
        .order_by(func.count(CourtCase.id).desc())
        .limit(50)
    )
    rows = result.all()
    return [
        {"court_name": r.court_name, "total_cases": r.total_cases, "total_awarded": r.total_awarded}
        for r in rows
    ]


@router.get("/judges")
async def judge_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Stats grouped by judge."""
    result = await db.execute(
        select(
            CourtCase.judge_name,
            func.count(CourtCase.id).label("total_cases"),
            func.sum(CourtCase.awarded_amount).label("total_awarded"),
        )
        .where(CourtCase.judge_name.isnot(None))
        .group_by(CourtCase.judge_name)
        .order_by(func.count(CourtCase.id).desc())
        .limit(50)
    )
    rows = result.all()
    return [
        {"judge_name": r.judge_name, "total_cases": r.total_cases, "total_awarded": r.total_awarded}
        for r in rows
    ]
