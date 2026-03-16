"""Court case endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.court_case import CaseStatus, CourtCase
from app.schemas.court_case import CourtCaseCreate, CourtCaseOut, CourtCaseUpdate

router = APIRouter(prefix="/court-cases", tags=["court-cases"])


@router.get("/", response_model=list[CourtCaseOut])
async def list_court_cases(
    debtor_id: uuid.UUID | None = None,
    status_filter: CaseStatus | None = Query(None, alias="status"),
    court_name: str | None = None,
    judge_name: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    stmt = select(CourtCase)
    if debtor_id:
        stmt = stmt.where(CourtCase.debtor_id == debtor_id)
    if status_filter:
        stmt = stmt.where(CourtCase.status == status_filter)
    if court_name:
        stmt = stmt.where(CourtCase.court_name.ilike(f"%{court_name}%"))
    if judge_name:
        stmt = stmt.where(CourtCase.judge_name.ilike(f"%{judge_name}%"))
    stmt = stmt.order_by(CourtCase.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return [CourtCaseOut.model_validate(c) for c in result.scalars().all()]


@router.post("/", response_model=CourtCaseOut, status_code=201)
async def create_court_case(
    body: CourtCaseCreate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    case = CourtCase(**body.model_dump())
    db.add(case)
    await db.flush()
    return CourtCaseOut.model_validate(case)


@router.get("/{case_id}", response_model=CourtCaseOut)
async def get_court_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    case = await db.get(CourtCase, case_id)
    if not case:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Court case not found")
    return CourtCaseOut.model_validate(case)


@router.patch("/{case_id}", response_model=CourtCaseOut)
async def update_court_case(
    case_id: uuid.UUID,
    body: CourtCaseUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    case = await db.get(CourtCase, case_id)
    if not case:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Court case not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    await db.flush()
    return CourtCaseOut.model_validate(case)
