"""
ML inference engine with optimized prediction pipeline
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict, List

import torch
from PIL import Image

from app.core.exceptions import ModelError, FileProcessingError
from app.infrastructure.ml.constants import DISEASE_CLASSES
from app.infrastructure.ml.model_loader import ModelLoader
from app.infrastructure.ml.preprocessing import ImagePreprocessor

logger = logging.getLogger(__name__)


class PredictionResult:
    """Structured prediction result"""
    
    def __init__(
        self,
        disease_type: str,
        probability: float,
        confidence_percentage: float,
        rank: int
    ):
        self.disease_type = disease_type
        self.probability = probability
        self.confidence_percentage = confidence_percentage
        self.rank = rank
    
    def to_dict(self) -> Dict:
        return {
            "disease_type": self.disease_type,
            "probability": self.probability,
            "confidence_percentage": self.confidence_percentage,
            "rank": self.rank
        }


class SkinDiseasePredictor:
    """High-performance skin disease prediction engine"""
    
    def __init__(self):
        self.model_loader = ModelLoader.get_instance()
        self.preprocessor = ImagePreprocessor()
    
    async def predict(
        self,
        image_path: str | Path,
        top_k: int = 3
    ) -> Dict:
        """
        Predict skin disease from image
        
        Args:
            image_path: Path to image file
            top_k: Number of top predictions to return
            
        Returns:
            Dictionary with predictions and metadata
        """
        try:
            image_path = Path(image_path)
            
            # Validate file exists
            if not image_path.exists():
                raise FileProcessingError(
                    f"Image file not found: {image_path}",
                    details={"path": str(image_path)}
                )
            
            # Load and preprocess image
            image = await asyncio.to_thread(Image.open, image_path)
            image = image.convert('RGB')
            
            # Assess image quality
            quality_score, quality_label = self.preprocessor.assess_quality(image)
            
            # Preprocess for model
            input_tensor = self.preprocessor.preprocess(image)
            input_tensor = input_tensor.unsqueeze(0)  # Add batch dimension
            
            # Run inference
            predictions = await self._run_inference(input_tensor, top_k)
            
            return {
                "success": True,
                "top_prediction": predictions[0].to_dict(),
                "all_predictions": [p.to_dict() for p in predictions],
                "image_quality": {
                    "score": quality_score,
                    "label": quality_label
                },
                "affected_area": "Hand",  # Can be improved later
                "metadata": {
                    "image_size": image.size,
                    "image_mode": image.mode,
                    "model_device": str(self.model_loader.device)
                }
            }
            
        except FileProcessingError:
            raise
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            raise ModelError(
                f"Prediction failed: {str(e)}",
                details={"image_path": str(image_path)}
            )
    
    def predict_sync(
        self,
        image_path: str | Path,
        top_k: int = 3
    ) -> Dict:
        """
        Synchronous wrapper for predict (for compatibility with old code)
        
        Args:
            image_path: Path to image file
            top_k: Number of top predictions to return
            
        Returns:
            Dictionary with predictions and metadata
        """
        try:
            # Run async predict in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.predict(image_path, top_k))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Sync prediction error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _run_inference(
        self,
        input_tensor: torch.Tensor,
        top_k: int
    ) -> List[PredictionResult]:
        """
        Run model inference in thread pool
        
        Args:
            input_tensor: Preprocessed image tensor
            top_k: Number of top predictions
            
        Returns:
            List of PredictionResult objects
        """
        model = self.model_loader.get_model()
        device = self.model_loader.device
        
        # Move to device
        input_tensor = input_tensor.to(device)
        
        # Run inference in thread pool
        def _inference():
            with torch.no_grad():
                outputs = model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                probs, indices = torch.topk(probabilities, top_k)
            return probs[0].cpu(), indices[0].cpu()
        
        probs, indices = await asyncio.to_thread(_inference)
        
        # Build results
        predictions = []
        for rank, (prob, idx) in enumerate(zip(probs, indices), start=1):
            predictions.append(
                PredictionResult(
                    disease_type=DISEASE_CLASSES[idx.item()],
                    probability=float(prob.item()),
                    confidence_percentage=round(float(prob.item()) * 100, 2),
                    rank=rank
                )
            )
        
        return predictions
    
    async def batch_predict(
        self,
        image_paths: List[str | Path],
        top_k: int = 3
    ) -> List[Dict]:
        """
        Batch prediction for multiple images
        
        Args:
            image_paths: List of image paths
            top_k: Number of top predictions per image
            
        Returns:
            List of prediction results
        """
        tasks = [self.predict(path, top_k) for path in image_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch prediction failed for image {i}: {result}")
                processed_results.append({
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results


# Singleton instance for compatibility with old code
_predictor_instance = None


def get_predictor() -> SkinDiseasePredictor:
    """
    Get singleton predictor instance (for compatibility with old code)
    
    Returns:
        SkinDiseasePredictor instance
    """
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = SkinDiseasePredictor()
    return _predictor_instance
