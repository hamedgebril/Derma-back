from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PredictionResult(BaseModel):
    disease_type: str
    probability: float
    confidence_percentage: float

class DiagnosisResponse(BaseModel):
    success: bool
    diagnosis_id: Optional[int] = None
    session_id: Optional[str] = None
    top_prediction: Optional[PredictionResult] = None
    all_predictions: Optional[List[PredictionResult]] = None
    image_quality: Optional[int] = None
    affected_area: Optional[str] = None
    created_at: Optional[datetime] = None
    error: Optional[str] = None

class ImageUploadResponse(BaseModel):
    success: bool
    filename: Optional[str] = None
    file_path: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
