"""Court case endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.court_case import CourtCase
from app.schemas.court_case import CourtCaseCreate, CourtCaseResponse, CourtCaseListResponse

router = APIRouter()


@router.get("/", response_model=CourtCaseListResponse)
async def list_court_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    debtor_id: int | None = Query(None),
    outcome: str | None = Query(None),
    court_name: str | None = Query(None),
    needs_review: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(CourtCase)
    count_query = select(func.count(CourtCase.id))

    if debtor_id:
        query = query.where(CourtCase.debtor_id == debtor_id)
        count_query = count_query.where(CourtCase.debtor_id == debtor_id)
    if outcome:
        query = query.where(CourtCase.decision_outcome == outcome)
        count_query = count_query.where(CourtCase.decision_outcome == outcome)
    if court_name:
        query = query.where(CourtCase.court_name.ilike(f"%{court_name}%"))
        count_query = count_query.where(CourtCase.court_name.ilike(f"%{court_name}%"))
    if needs_review is not None:
        query = query.where(CourtCase.ai_needs_review == needs_review)
        count_query = count_query.where(CourtCase.ai_needs_review == needs_review)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(CourtCase.id.desc()).offset(offset).limit(page_size))
    items = result.scalars().all()

    return CourtCaseListResponse(
        items=[CourtCaseResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=CourtCaseResponse, status_code=201)
async def create_court_case(data: CourtCaseCreate, db: AsyncSession = Depends(get_db)):
    case = CourtCase(**data.model_dump())
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return CourtCaseResponse.model_validate(case)


@router.get("/{case_id}", response_model=CourtCaseResponse)
async def get_court_case(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CourtCase).where(CourtCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Court case not found")
    return CourtCaseResponse.model_validate(case)
