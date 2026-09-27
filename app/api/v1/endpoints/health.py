from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["Health & Monitoring"])
async def health_check():
    """
    Standard readiness probe for DevOps, Docker health checks, and monitoring.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "2.0.0",
    }
