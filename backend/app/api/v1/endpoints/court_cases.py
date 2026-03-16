"""Court case endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.court_case import CourtCase, CourtDecision
from app.models.user import User
from app.schemas.court_case import (
    CourtCaseCreate,
    CourtCaseResponse,
    CourtCaseUpdate,
    CourtDecisionResponse,
)

router = APIRouter(prefix="/court-cases", tags=["court_cases"])


@router.get("/", response_model=list[CourtCaseResponse])
async def list_court_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    debtor_id: int | None = None,
    status_filter: str | None = Query(None, alias="status"),
    court_name: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = select(CourtCase)
    if debtor_id:
        query = query.where(CourtCase.debtor_id == debtor_id)
    if status_filter:
        query = query.where(CourtCase.status == status_filter)
    if court_name:
        query = query.where(CourtCase.court_name.ilike(f"%{court_name}%"))

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(CourtCase.created_at.desc()).offset(offset).limit(page_size)
    )
    return result.scalars().all()


@router.get("/{case_id}", response_model=CourtCaseResponse)
async def get_court_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(CourtCase).where(CourtCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court case not found")
    return case


@router.post("/", response_model=CourtCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_court_case(
    body: CourtCaseCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    case = CourtCase(**body.model_dump())
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


@router.patch("/{case_id}", response_model=CourtCaseResponse)
async def update_court_case(
    case_id: int,
    body: CourtCaseUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(CourtCase).where(CourtCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court case not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    await db.commit()
    await db.refresh(case)
    return case


@router.get("/{case_id}/decisions", response_model=list[CourtDecisionResponse])
async def list_decisions(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CourtDecision)
        .where(CourtDecision.court_case_id == case_id)
        .order_by(CourtDecision.decision_date)
    )
    return result.scalars().all()
