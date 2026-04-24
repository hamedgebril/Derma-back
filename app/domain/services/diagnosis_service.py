"""
Business logic for diagnosis operations
"""
import logging
from typing import Dict, Optional
from uuid import uuid4

from app.core.exceptions import ValidationError
from app.domain.services.file_service import FileService
from app.infrastructure.database.repositories.diagnosis_repository import DiagnosisRepository
from app.infrastructure.ml.predictor import SkinDiseasePredictor

logger = logging.getLogger(__name__)


class DiagnosisService:
    """Service layer for diagnosis business logic"""

    def __init__(
        self,
        predictor: SkinDiseasePredictor,
        file_service: FileService,
        diagnosis_repo: DiagnosisRepository
    ):
        self.predictor = predictor
        self.file_service = file_service
        self.diagnosis_repo = diagnosis_repo

    async def create_diagnosis(
        self,
        file_content: bytes,
        filename: str,
        user_id: int,
        top_k: int = 3
    ) -> Dict:
        session_id = str(uuid4())

        try:
            file_path = await self.file_service.save_upload(
                file_content=file_content,
                filename=filename,
                session_id=session_id
            )

            logger.info(f"Processing diagnosis for session {session_id}")

            prediction_result = await self.predictor.predict(
                image_path=file_path,
                top_k=top_k
            )

            if not prediction_result.get("success"):
                raise ValidationError("Prediction failed", details=prediction_result)

            diagnosis_data = {
                "user_id": user_id,
                "session_id": session_id,
                "image_path": str(file_path),
                "image_quality_score": prediction_result["image_quality"]["score"],
                "image_quality_label": prediction_result["image_quality"]["label"],
                "disease_type": prediction_result["top_prediction"]["disease_type"],
                "probability": prediction_result["top_prediction"]["probability"],
                "confidence_percentage": prediction_result["top_prediction"]["confidence_percentage"],
                "all_predictions": prediction_result["all_predictions"],
                "metadata": prediction_result.get("metadata", {})
            }

            diagnosis = await self.diagnosis_repo.create(diagnosis_data)

            logger.info(
                f"Diagnosis created: ID={diagnosis.id}, "
                f"Disease={diagnosis.disease_type}, "
                f"Confidence={diagnosis.confidence_percentage}%"
            )

            return {
                "success": True,
                "diagnosis_id": diagnosis.id,
                "session_id": session_id,
                "top_prediction": prediction_result["top_prediction"],
                "all_predictions": prediction_result["all_predictions"],
                "image_quality": prediction_result["image_quality"],
                "created_at": diagnosis.created_at
            }

        except Exception as e:
            logger.error(f"Diagnosis creation failed: {e}", exc_info=True)
            if 'file_path' in locals():
                await self.file_service.delete_file(file_path)
            raise

    async def get_diagnosis(self, diagnosis_id: int, user_id: int) -> Optional[Dict]:
        diagnosis = await self.diagnosis_repo.get_by_id(diagnosis_id)
        if diagnosis and diagnosis.user_id == user_id:
            return diagnosis.to_dict()
        return None

    async def get_user_history(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> list[Dict]:
        diagnoses = await self.diagnosis_repo.get_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return [d.to_dict() for d in diagnoses]

    # ✅ NEW: Delete diagnosis
    async def delete_diagnosis(self, diagnosis_id: int, user_id: int) -> bool:
        """
        Delete diagnosis by ID - بيتأكد إن الـ record بتاع الـ user ده فعلاً
        """
        # ✅ تأكد إن الـ diagnosis بتاع الـ user ده
        diagnosis = await self.diagnosis_repo.get_by_id(diagnosis_id)

        if not diagnosis:
            return False

        if diagnosis.user_id != user_id:
            logger.warning(
                f"User {user_id} tried to delete diagnosis {diagnosis_id} "
                f"owned by user {diagnosis.user_id}"
            )
            return False

        # ✅ احذف الـ file من الـ storage
        try:
            from pathlib import Path
            if diagnosis.image_path:
                await self.file_service.delete_file(Path(diagnosis.image_path))
        except Exception as e:
            logger.warning(f"Could not delete image file: {e}")

        # ✅ احذف من الـ database
        deleted = await self.diagnosis_repo.delete(diagnosis_id)

        if deleted:
            logger.info(f"Diagnosis {diagnosis_id} deleted by user {user_id}")

        return deleted