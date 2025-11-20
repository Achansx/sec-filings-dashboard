"""API v1 router."""
from fastapi import APIRouter

from app.api.v1 import companies, filings, alerts, auth

api_router = APIRouter()

# Include route modules
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(filings.router, prefix="/filings", tags=["filings"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
