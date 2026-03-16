"""API v1 router that aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import analytics, auth, court_cases, debtors, portfolios

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(portfolios.router)
api_router.include_router(debtors.router)
api_router.include_router(court_cases.router)
api_router.include_router(analytics.router)
