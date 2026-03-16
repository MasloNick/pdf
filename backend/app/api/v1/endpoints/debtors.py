"""Debtor CRUD endpoints with search and pagination."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.debtor import Debtor, DebtorStatus
from app.schemas.debtor import DebtorCreate, DebtorListOut, DebtorOut, DebtorUpdate

router = APIRouter(prefix="/debtors", tags=["debtors"])


@router.get("/", response_model=DebtorListOut)
async def list_debtors(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    portfolio_id: uuid.UUID | None = None,
    status_filter: DebtorStatus | None = Query(None, alias="status"),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    stmt = select(Debtor)
    count_stmt = select(func.count(Debtor.id))

    if portfolio_id:
        stmt = stmt.where(Debtor.portfolio_id == portfolio_id)
        count_stmt = count_stmt.where(Debtor.portfolio_id == portfolio_id)
    if status_filter:
        stmt = stmt.where(Debtor.status == status_filter)
        count_stmt = count_stmt.where(Debtor.status == status_filter)
    if search:
        like = f"%{search}%"
        search_filter = or_(
            Debtor.full_name.ilike(like),
            Debtor.ipn_code.ilike(like),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = (await db.execute(count_stmt)).scalar() or 0
    offset = (page - 1) * size
    stmt = stmt.order_by(Debtor.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    items = [DebtorOut.model_validate(d) for d in result.scalars().all()]
    return DebtorListOut(items=items, total=total, page=page, size=size)


@router.post("/", response_model=DebtorOut, status_code=201)
async def create_debtor(
    body: DebtorCreate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    debtor = Debtor(**body.model_dump())
    db.add(debtor)
    await db.flush()
    return DebtorOut.model_validate(debtor)


@router.get("/{debtor_id}", response_model=DebtorOut)
async def get_debtor(
    debtor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    debtor = await db.get(Debtor, debtor_id)
    if not debtor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Debtor not found")
    return DebtorOut.model_validate(debtor)


@router.patch("/{debtor_id}", response_model=DebtorOut)
async def update_debtor(
    debtor_id: uuid.UUID,
    body: DebtorUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    debtor = await db.get(Debtor, debtor_id)
    if not debtor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Debtor not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(debtor, field, value)
    await db.flush()
    return DebtorOut.model_validate(debtor)
