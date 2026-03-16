"""Debtor CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.core.database import get_db
from app.models.debtor import Debtor
from app.schemas.debtor import (
    DebtorCreate, DebtorUpdate, DebtorResponse, DebtorListResponse,
)

router = APIRouter()


@router.get("/", response_model=DebtorListResponse)
async def list_debtors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    portfolio_id: int | None = Query(None),
    search: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Debtor)
    count_query = select(func.count(Debtor.id))

    if portfolio_id:
        query = query.where(Debtor.portfolio_id == portfolio_id)
        count_query = count_query.where(Debtor.portfolio_id == portfolio_id)
    if status:
        query = query.where(Debtor.collection_status == status)
        count_query = count_query.where(Debtor.collection_status == status)
    if search:
        search_filter = or_(
            Debtor.full_name.ilike(f"%{search}%"),
            Debtor.ipn.ilike(f"%{search}%"),
            Debtor.credit_contract_number.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Debtor.id).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return DebtorListResponse(
        items=[DebtorResponse.model_validate(d) for d in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=DebtorResponse, status_code=201)
async def create_debtor(data: DebtorCreate, db: AsyncSession = Depends(get_db)):
    debtor = Debtor(**data.model_dump())
    db.add(debtor)
    await db.commit()
    await db.refresh(debtor)
    return DebtorResponse.model_validate(debtor)


@router.get("/{debtor_id}", response_model=DebtorResponse)
async def get_debtor(debtor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Debtor).where(Debtor.id == debtor_id))
    debtor = result.scalar_one_or_none()
    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")
    return DebtorResponse.model_validate(debtor)


@router.patch("/{debtor_id}", response_model=DebtorResponse)
async def update_debtor(
    debtor_id: int, data: DebtorUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Debtor).where(Debtor.id == debtor_id))
    debtor = result.scalar_one_or_none()
    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(debtor, field, value)

    await db.commit()
    await db.refresh(debtor)
    return DebtorResponse.model_validate(debtor)


@router.delete("/{debtor_id}", status_code=204)
async def delete_debtor(debtor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Debtor).where(Debtor.id == debtor_id))
    debtor = result.scalar_one_or_none()
    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")
    await db.delete(debtor)
    await db.commit()
