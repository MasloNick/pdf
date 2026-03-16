"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, portfolios, debtors, court_cases, imports, dashboard

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(debtors.router, prefix="/debtors", tags=["debtors"])
api_router.include_router(court_cases.router, prefix="/court-cases", tags=["court-cases"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
