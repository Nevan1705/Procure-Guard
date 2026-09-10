"""Aggregate all API routers."""
from fastapi import APIRouter

from app.api import audit, bids, review, tenders, verification

api_router = APIRouter()
api_router.include_router(tenders.router)
api_router.include_router(bids.router)
api_router.include_router(verification.router)
api_router.include_router(verification.mock_router)
api_router.include_router(review.router)
api_router.include_router(audit.router)
