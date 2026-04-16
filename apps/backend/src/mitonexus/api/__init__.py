"""API router package."""

from fastapi import APIRouter

from mitonexus.api.blood_test import router as blood_test_router
from mitonexus.api.report import router as report_router

api_router = APIRouter()
api_router.include_router(blood_test_router)
api_router.include_router(report_router)

__all__ = ["api_router"]
