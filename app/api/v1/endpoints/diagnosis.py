"""
Diagnosis API endpoints
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Query

from app.api.dependencies import get_current_user_id, get_diagnosis_service
from app.api.v1.schemas.diagnosis_response import (
    DiagnosisCreateResponse,
    DiagnosisDetailResponse,
    DiagnosisHistoryResponse
)
from app.api.v1.mappers import (
    map_to_create_response,
    map_to_detail_response,
    map_to_history_response
)
from app.core.config import settings
from app.core.exceptions import AppException
from app.domain.services.diagnosis_service import DiagnosisService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/diagnosis",
    response_model=DiagnosisCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Diagnose skin disease from image",
    description="Upload an image and get AI-powered skin disease diagnosis"
)
async def diagnose_image(
    file: Annotated[UploadFile, File(description="Image file (JPG, PNG, HEIC)")],
    user_id: Annotated[int, Depends(get_current_user_id)],
    diagnosis_service: Annotated[DiagnosisService, Depends(get_diagnosis_service)],
    top_k: int = settings.TOP_K_PREDICTIONS
) -> DiagnosisCreateResponse:
    try:
        logger.info(f"Diagnosis request from user {user_id}, file: {file.filename}")

        file_content = await file.read()

        result = await diagnosis_service.create_diagnosis(
            file_content=file_content,
            filename=file.filename,
            user_id=user_id,
            top_k=top_k
        )

        response_data = map_to_create_response(result)
        return DiagnosisCreateResponse(**response_data)

    except AppException as e:
        logger.error(f"Diagnosis failed: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error during diagnosis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during diagnosis"
        )


@router.get(
    "/history",
    response_model=DiagnosisHistoryResponse,
    summary="Get diagnosis history",
    description="Get user's diagnosis history with pagination"
)
async def get_diagnosis_history(
    user_id: Annotated[int, Depends(get_current_user_id)],
    diagnosis_service: Annotated[DiagnosisService, Depends(get_diagnosis_service)],
    limit: int = Query(20, description="Number of records to return (default: 20)")
) -> DiagnosisHistoryResponse:
    try:
        diagnoses = await diagnosis_service.get_user_history(
            user_id=user_id,
            limit=limit,
            offset=0
        )
        response_data = map_to_history_response(diagnoses, limit)
        return DiagnosisHistoryResponse(**response_data)

    except Exception as e:
        logger.error(f"Error retrieving history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving diagnosis history"
        )


@router.get(
    "/diagnosis/{analysis_id}",
    response_model=DiagnosisDetailResponse,
    summary="Get diagnosis by ID",
    description="Retrieve a specific diagnosis record by analysis ID"
)
async def get_diagnosis_by_id(
    analysis_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    diagnosis_service: Annotated[DiagnosisService, Depends(get_diagnosis_service)]
) -> DiagnosisDetailResponse:
    try:
        result = await diagnosis_service.get_diagnosis(analysis_id, user_id)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagnosis {analysis_id} not found"
            )

        response_data = map_to_detail_response(result)
        return DiagnosisDetailResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving diagnosis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving diagnosis"
        )


# ✅ NEW: Delete diagnosis endpoint
@router.delete(
    "/diagnosis/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete diagnosis",
    description="Delete a specific diagnosis record by ID"
)
async def delete_diagnosis(
    analysis_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    diagnosis_service: Annotated[DiagnosisService, Depends(get_diagnosis_service)]
) -> dict:
    try:
        deleted = await diagnosis_service.delete_diagnosis(analysis_id, user_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagnosis {analysis_id} not found or not authorized"
            )

        logger.info(f"Diagnosis {analysis_id} deleted by user {user_id}")
        return {"success": True, "message": f"Diagnosis {analysis_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting diagnosis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting diagnosis"
        )