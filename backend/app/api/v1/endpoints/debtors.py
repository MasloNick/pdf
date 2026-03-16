"""Debtor CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.debtor import Debtor
from app.models.user import User
from app.schemas.debtor import DebtorCreate, DebtorListResponse, DebtorResponse, DebtorUpdate

router = APIRouter(prefix="/debtors", tags=["debtors"])


@router.get("/", response_model=DebtorListResponse)
async def list_debtors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    is_bankrupt: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = select(Debtor)
    count_query = select(func.count(Debtor.id))

    if search:
        like = f"%{search}%"
        filter_clause = or_(
            Debtor.last_name.ilike(like),
            Debtor.full_name.ilike(like),
            Debtor.ipn.ilike(like),
            Debtor.edrpou.ilike(like),
        )
        query = query.where(filter_clause)
        count_query = count_query.where(filter_clause)

    if status_filter:
        query = query.where(Debtor.status == status_filter)
        count_query = count_query.where(Debtor.status == status_filter)

    if is_bankrupt is not None:
        query = query.where(Debtor.is_bankrupt == is_bankrupt)
        count_query = count_query.where(Debtor.is_bankrupt == is_bankrupt)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Debtor.id).offset(offset).limit(page_size))
    items = result.scalars().all()

    return DebtorListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{debtor_id}", response_model=DebtorResponse)
async def get_debtor(
    debtor_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Debtor).where(Debtor.id == debtor_id))
    debtor = result.scalar_one_or_none()
    if not debtor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debtor not found")
    return debtor


@router.post("/", response_model=DebtorResponse, status_code=status.HTTP_201_CREATED)
async def create_debtor(
    body: DebtorCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    debtor = Debtor(**body.model_dump())
    db.add(debtor)
    await db.commit()
    await db.refresh(debtor)
    return debtor


@router.patch("/{debtor_id}", response_model=DebtorResponse)
async def update_debtor(
    debtor_id: int,
    body: DebtorUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Debtor).where(Debtor.id == debtor_id))
    debtor = result.scalar_one_or_none()
    if not debtor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debtor not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(debtor, field, value)
    await db.commit()
    await db.refresh(debtor)
    return debtor
