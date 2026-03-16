"""Portfolio CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.debtor import Debtor
from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate, PortfolioOut, PortfolioUpdate

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("/", response_model=list[PortfolioOut])
async def list_portfolios(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    offset = (page - 1) * size
    stmt = (
        select(
            Portfolio,
            func.count(Debtor.id).label("debtor_count"),
        )
        .outerjoin(Debtor, Debtor.portfolio_id == Portfolio.id)
        .group_by(Portfolio.id)
        .order_by(Portfolio.purchase_date.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    items = []
    for portfolio, debtor_count in result.all():
        out = PortfolioOut.model_validate(portfolio)
        out.debtor_count = debtor_count
        items.append(out)
    return items


@router.post("/", response_model=PortfolioOut, status_code=201)
async def create_portfolio(
    body: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    portfolio = Portfolio(**body.model_dump())
    db.add(portfolio)
    await db.flush()
    return PortfolioOut.model_validate(portfolio)


@router.get("/{portfolio_id}", response_model=PortfolioOut)
async def get_portfolio(
    portfolio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    portfolio = await db.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Portfolio not found")
    return PortfolioOut.model_validate(portfolio)


@router.patch("/{portfolio_id}", response_model=PortfolioOut)
async def update_portfolio(
    portfolio_id: uuid.UUID,
    body: PortfolioUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    portfolio = await db.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Portfolio not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(portfolio, field, value)
    await db.flush()
    return PortfolioOut.model_validate(portfolio)


@router.delete("/{portfolio_id}", status_code=204)
async def delete_portfolio(
    portfolio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    portfolio = await db.get(Portfolio, portfolio_id)
    if not portfolio:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Portfolio not found")
    await db.delete(portfolio)
