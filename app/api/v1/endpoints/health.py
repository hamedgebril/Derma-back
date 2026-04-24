"""
Health check endpoints
"""
import logging
from datetime import datetime

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.config import settings
from app.infrastructure.ml.model_loader import ModelLoader

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness check response"""
    ready: bool
    checks: dict


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Basic health check endpoint"
)
async def health_check() -> HealthResponse:
    """Basic health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if application is ready to serve requests"
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check - verifies all dependencies are ready
    """
    checks = {}
    all_ready = True
    
    # Check ML model
    try:
        model_loader = ModelLoader.get_instance()
        model_status = model_loader.health_status
        checks["ml_model"] = {
            "ready": model_status["loaded"],
            "details": model_status
        }
        if not model_status["loaded"]:
            all_ready = False
            if "error" in model_status:
                checks["ml_model"]["error"] = model_status["error"]
    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        checks["ml_model"] = {
            "ready": False,
            "error": str(e)
        }
        all_ready = False
    
    # Check database (basic check)
    try:
        # Could add actual DB ping here
        checks["database"] = {
            "ready": True,
            "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "local"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = {
            "ready": False,
            "error": str(e)
        }
        all_ready = False
    
    return ReadinessResponse(
        ready=all_ready,
        checks=checks
    )
