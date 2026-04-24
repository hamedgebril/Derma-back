"""
Diagnosis request/response schemas
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PredictionResult(BaseModel):
    """Single prediction result"""
    disease_type: str = Field(..., description="Predicted disease type")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability score")
    confidence_percentage: float = Field(..., ge=0.0, le=100.0, description="Confidence percentage")
    rank: int = Field(..., ge=1, description="Prediction rank")


class ImageQuality(BaseModel):
    """Image quality assessment"""
    score: int = Field(..., ge=0, le=100, description="Quality score (0-100)")
    label: str = Field(..., description="Quality label (Excellent, Good, Fair, Poor)")


class DiagnosisResponse(BaseModel):
    """Diagnosis response"""
    success: bool = True
    diagnosis_id: Optional[int] = Field(None, description="Diagnosis record ID")
    session_id: Optional[str] = Field(None, description="Unique session identifier")
    top_prediction: Optional[PredictionResult] = Field(None, description="Top prediction")
    all_predictions: Optional[List[PredictionResult]] = Field(None, description="All predictions")
    image_quality: Optional[ImageQuality] = Field(None, description="Image quality assessment")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "diagnosis_id": 123,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "top_prediction": {
                    "disease_type": "Acne and Rosacea",
                    "probability": 0.92,
                    "confidence_percentage": 92.0,
                    "rank": 1
                },
                "all_predictions": [
                    {
                        "disease_type": "Acne and Rosacea",
                        "probability": 0.92,
                        "confidence_percentage": 92.0,
                        "rank": 1
                    },
                    {
                        "disease_type": "Eczema",
                        "probability": 0.05,
                        "confidence_percentage": 5.0,
                        "rank": 2
                    }
                ],
                "image_quality": {
                    "score": 85,
                    "label": "Good"
                },
                "created_at": "2024-01-15T10:30:00"
            }
        }


class DiagnosisHistoryResponse(BaseModel):
    """Diagnosis history response"""
    diagnoses: List[dict] = Field(..., description="List of diagnosis records")
    total: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Limit per page")
    offset: int = Field(..., description="Offset for pagination")
