"""
Shared API dependencies
"""
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.domain.services.diagnosis_service import DiagnosisService
from app.domain.services.file_service import FileService
from app.infrastructure.database.repositories.diagnosis_repository import DiagnosisRepository
from app.infrastructure.database.session import get_db
from app.infrastructure.ml.predictor import SkinDiseasePredictor

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
) -> int:
    """
    Get current user ID from JWT token
    
    Behavior:
    - If AUTH_REQUIRED=True and no token: returns 401
    - If AUTH_REQUIRED=False and no token: returns default user_id=1 (dev mode)
    - If token provided: validates and returns user_id from token
    """
    from app.core.config import settings
    
    if credentials is None:
        if settings.AUTH_REQUIRED:
            # Production mode: require authentication
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            # Development mode: allow default user
            logger.warning("AUTH_REQUIRED=False: Using default user_id=1")
            return 1
    
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return int(user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Service dependencies
def get_predictor() -> SkinDiseasePredictor:
    """Get ML predictor instance"""
    return SkinDiseasePredictor()


def get_file_service() -> FileService:
    """Get file service instance"""
    return FileService()


def get_diagnosis_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> DiagnosisRepository:
    """Get diagnosis repository"""
    return DiagnosisRepository(db)


def get_diagnosis_service(
    predictor: Annotated[SkinDiseasePredictor, Depends(get_predictor)],
    file_service: Annotated[FileService, Depends(get_file_service)],
    diagnosis_repo: Annotated[DiagnosisRepository, Depends(get_diagnosis_repository)]
) -> DiagnosisService:
    """Get diagnosis service with all dependencies"""
    return DiagnosisService(
        predictor=predictor,
        file_service=file_service,
        diagnosis_repo=diagnosis_repo
    )
