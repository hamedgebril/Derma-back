"""
Unified diagnosis response schemas for consistent API contract
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TopKPrediction(BaseModel):
    """Single prediction in top-k list"""
    label: str = Field(..., description="Disease type label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")


class DiagnosisCreateResponse(BaseModel):
    """Response for POST /api/v1/diagnosis"""
    predicted_label: str = Field(..., description="Top predicted disease type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    top_k: List[TopKPrediction] = Field(..., description="Top K predictions")
    image_quality_score: int = Field(..., ge=0, le=100, description="Image quality score (0-100)")
    image_quality_label: str = Field(..., description="Image quality label")
    analysis_id: int = Field(..., description="Diagnosis record ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "predicted_label": "psoriasis",
                "confidence": 0.92,
                "top_k": [
                    {"label": "psoriasis", "confidence": 0.92},
                    {"label": "tinea circinata", "confidence": 0.05},
                    {"label": "healty", "confidence": 0.02}
                ],
                "image_quality_score": 85,
                "image_quality_label": "Good",
                "analysis_id": 123
            }
        }


class PredictionDetail(BaseModel):
    """Detailed prediction with rank"""
    disease_type: str = Field(..., description="Disease type")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability (0-1)")
    confidence_percentage: float = Field(..., ge=0.0, le=100.0, description="Confidence percentage")
    rank: int = Field(..., ge=1, description="Prediction rank")


class DiagnosisDetailResponse(BaseModel):
    """Response for GET /api/v1/diagnosis/{analysis_id}"""
    id: int = Field(..., description="Diagnosis ID")
    predicted_label: str = Field(..., description="Top predicted disease type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    all_predictions: List[PredictionDetail] = Field(..., description="All predictions with details")
    image_quality_score: int = Field(..., ge=0, le=100, description="Image quality score")
    image_quality_label: str = Field(..., description="Image quality label")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "predicted_label": "psoriasis",
                "confidence": 0.92,
                "all_predictions": [
                    {
                        "disease_type": "psoriasis",
                        "probability": 0.92,
                        "confidence_percentage": 92.0,
                        "rank": 1
                    },
                    {
                        "disease_type": "tinea circinata",
                        "probability": 0.05,
                        "confidence_percentage": 5.0,
                        "rank": 2
                    }
                ],
                "image_quality_score": 85,
                "image_quality_label": "Good",
                "created_at": "2026-02-22T10:30:00Z"
            }
        }


class DiagnosisHistoryItem(BaseModel):
    """Single item in diagnosis history"""
    id: int = Field(..., description="Diagnosis ID")
    predicted_label: str = Field(..., description="Predicted disease type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    image_quality_score: int = Field(..., ge=0, le=100, description="Image quality score")
    image_quality_label: str = Field(..., description="Image quality label")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "predicted_label": "psoriasis",
                "confidence": 0.92,
                "image_quality_score": 85,
                "image_quality_label": "Good",
                "created_at": "2026-02-22T10:30:00Z"
            }
        }


class DiagnosisHistoryResponse(BaseModel):
    """Response for GET /api/v1/history"""
    analyses: List[DiagnosisHistoryItem] = Field(..., description="List of diagnosis records")
    total: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Limit per page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analyses": [
                    {
                        "id": 123,
                        "predicted_label": "psoriasis",
                        "confidence": 0.92,
                        "image_quality_score": 85,
                        "image_quality_label": "Good",
                        "created_at": "2026-02-22T10:30:00Z"
                    },
                    {
                        "id": 122,
                        "predicted_label": "healty",
                        "confidence": 0.88,
                        "image_quality_score": 90,
                        "image_quality_label": "Excellent",
                        "created_at": "2026-02-21T15:20:00Z"
                    }
                ],
                "total": 2,
                "limit": 20
            }
        }
