"""Dashboard and analytics endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.portfolio import Portfolio
from app.models.debtor import Debtor
from app.models.court_case import CourtCase
from app.models.enforcement_proceeding import EnforcementProceeding

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Main dashboard statistics."""
    portfolio_count = (await db.execute(select(func.count(Portfolio.id)))).scalar()
    debtor_count = (await db.execute(select(func.count(Debtor.id)))).scalar()
    case_count = (await db.execute(select(func.count(CourtCase.id)))).scalar()
    vp_count = (await db.execute(select(func.count(EnforcementProceeding.id)))).scalar()

    # Cases by outcome
    outcome_query = select(
        CourtCase.decision_outcome, func.count(CourtCase.id)
    ).group_by(CourtCase.decision_outcome)
    outcomes = (await db.execute(outcome_query)).all()

    # Debtors by status
    status_query = select(
        Debtor.collection_status, func.count(Debtor.id)
    ).group_by(Debtor.collection_status)
    statuses = (await db.execute(status_query)).all()

    # Total financials
    total_purchased = (await db.execute(
        select(func.sum(Debtor.purchased_total_uah))
    )).scalar()
    total_awarded = (await db.execute(
        select(func.sum(CourtCase.awarded_total))
    )).scalar()

    return {
        "portfolios": portfolio_count,
        "debtors": debtor_count,
        "court_cases": case_count,
        "enforcement_proceedings": vp_count,
        "cases_by_outcome": {o[0] or "not_yet": o[1] for o in outcomes},
        "debtors_by_status": {s[0] or "unknown": s[1] for s in statuses},
        "total_purchased_uah": float(total_purchased) if total_purchased else 0,
        "total_awarded_uah": float(total_awarded) if total_awarded else 0,
    }


@router.get("/cases-needing-review")
async def get_cases_needing_review(db: AsyncSession = Depends(get_db)):
    """Cases flagged for manual review by AI."""
    result = await db.execute(
        select(CourtCase)
        .where(CourtCase.ai_needs_review.is_(True))
        .order_by(CourtCase.created_at.desc())
        .limit(50)
    )
    cases = result.scalars().all()
    return [
        {
            "id": c.id,
            "case_number": c.case_number,
            "ai_confidence": float(c.ai_confidence) if c.ai_confidence else None,
            "ai_review_reason": c.ai_review_reason,
            "decision_outcome": c.decision_outcome,
        }
        for c in cases
    ]
