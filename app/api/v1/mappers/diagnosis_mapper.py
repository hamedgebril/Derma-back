"""
Mappers to convert database models to API response formats
Ensures consistent API contract across all diagnosis endpoints
"""
from typing import Dict, List
from app.infrastructure.database.models.diagnosis import Diagnosis


def map_to_create_response(service_result: Dict) -> Dict:
    """
    Map service result to POST /api/v1/diagnosis response format
    
    Args:
        service_result: Result from diagnosis_service.create_diagnosis()
        
    Returns:
        Frontend-friendly normalized response
    """
    return {
        "predicted_label": service_result["top_prediction"]["disease_type"],
        "confidence": service_result["top_prediction"]["probability"],
        "top_k": [
            {
                "label": pred["disease_type"],
                "confidence": pred["probability"]
            }
            for pred in service_result["all_predictions"]
        ],
        "image_quality_score": service_result["image_quality"]["score"],
        "image_quality_label": service_result["image_quality"]["label"],
        "analysis_id": service_result["diagnosis_id"]
    }


def map_to_detail_response(diagnosis_dict: Dict) -> Dict:
    """
    Map database model dict to GET /api/v1/diagnosis/{id} response format
    
    Args:
        diagnosis_dict: Result from diagnosis.to_dict()
        
    Returns:
        Frontend-friendly normalized response with full details
    """
    return {
        "id": diagnosis_dict["id"],
        "predicted_label": diagnosis_dict["top_prediction"]["disease_type"],
        "confidence": diagnosis_dict["top_prediction"]["probability"],
        "all_predictions": diagnosis_dict["all_predictions"],
        "image_quality_score": diagnosis_dict["image_quality"]["score"],
        "image_quality_label": diagnosis_dict["image_quality"]["label"],
        "created_at": diagnosis_dict["created_at"]
    }


def map_to_history_item(diagnosis_dict: Dict) -> Dict:
    """
    Map database model dict to history item format
    
    Args:
        diagnosis_dict: Result from diagnosis.to_dict()
        
    Returns:
        Frontend-friendly normalized history item
    """
    return {
        "id": diagnosis_dict["id"],
        "predicted_label": diagnosis_dict["top_prediction"]["disease_type"],
        "confidence": diagnosis_dict["top_prediction"]["probability"],
        "image_quality_score": diagnosis_dict["image_quality"]["score"],
        "image_quality_label": diagnosis_dict["image_quality"]["label"],
        "created_at": diagnosis_dict["created_at"]
    }


def map_to_history_response(diagnoses: List[Dict], limit: int) -> Dict:
    """
    Map list of diagnosis dicts to GET /api/v1/history response format
    
    Args:
        diagnoses: List of diagnosis.to_dict() results
        limit: Pagination limit
        
    Returns:
        Frontend-friendly normalized history response
    """
    return {
        "analyses": [map_to_history_item(d) for d in diagnoses],
        "total": len(diagnoses),
        "limit": limit
    }
