"""
ML Model lifecycle management with proper loading and cleanup
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn

from app.core.config import settings
from app.core.exceptions import ModelError
from app.infrastructure.ml.constants import DISEASE_CLASSES

logger = logging.getLogger(__name__)


class ModelLoader:
    """Singleton class to manage ML model lifecycle"""
    
    _instance: Optional['ModelLoader'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.model: Optional[nn.Module] = None
        self.device: torch.device = self._get_device()
        self.is_loaded: bool = False
        self._model_path: Path = Path(settings.MODEL_PATH)
    
    @classmethod
    def get_instance(cls) -> 'ModelLoader':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _get_device(self) -> torch.device:
        """Determine the best available device"""
        if settings.MODEL_DEVICE == "cuda" and torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU device")
        return device
    
    async def load_model(self) -> None:
        """Load model from disk (async to not block startup)"""
        async with self._lock:
            if self.is_loaded:
                logger.info("Model already loaded")
                return
            
            try:
                logger.info(f"Loading model from {self._model_path}")
                
                # Verify model file exists
                if not self._model_path.exists():
                    error_msg = f"Model file not found: {self._model_path}"
                    logger.error(error_msg)
                    raise ModelError(error_msg)
                
                # Run in thread pool to avoid blocking
                await asyncio.to_thread(self._load_model_sync)
                
                self.is_loaded = True
                logger.info(f"Model loaded successfully with {len(DISEASE_CLASSES)} classes")
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}", exc_info=True)
                raise ModelError(f"Model loading failed: {str(e)}")
    
    def _load_model_sync(self) -> None:
        """Synchronous model loading (runs in thread pool)"""
        num_classes = len(DISEASE_CLASSES)
        
        # Create model exactly as in training (train_model.ipynb)
        # timm.create_model("efficientnet_b4", pretrained=True, num_classes=num_classes, drop_rate=0.4)
        try:
            import timm
            
            # Create model with same architecture as training
            self.model = timm.create_model(
                'efficientnet_b4',
                pretrained=False,  # Don't load pretrained weights, we'll load our trained weights
                num_classes=num_classes,
                drop_rate=0.4  # Match training dropout rate
            )
            logger.info(f"Created EfficientNet-B4 using timm with {num_classes} classes and drop_rate=0.4")
            
            # Load trained weights
            checkpoint = torch.load(
                self._model_path,
                map_location=self.device,
                weights_only=False
            )
            
            # Load state dict
            self.model.load_state_dict(checkpoint, strict=True)
            logger.info("Model weights loaded successfully")
            
        except ImportError:
            raise ModelError("timm library required. Install with: pip install timm")
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise ModelError(f"Failed to load model: {str(e)}")
        
        # Move to device and set to eval mode
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"Model moved to {self.device} and set to eval mode")
    
    async def warmup(self, num_iterations: int = 1) -> None:
        """
        Warmup model with dummy inputs to optimize performance
        
        Args:
            num_iterations: Number of warmup iterations
        """
        if not self.is_loaded:
            raise ModelError("Model not loaded. Call load_model() first.")
        
        logger.info(f"Warming up model with {num_iterations} iterations...")
        
        from app.infrastructure.ml.constants import IMAGE_SIZE
        
        def _warmup():
            # Use correct image size from training (380x380)
            dummy_input = torch.randn(1, 3, IMAGE_SIZE[0], IMAGE_SIZE[1]).to(self.device)
            with torch.no_grad():
                for i in range(num_iterations):
                    output = self.model(dummy_input)
                    logger.debug(f"Warmup iteration {i+1}: output shape {output.shape}")
            return output.shape
        
        output_shape = await asyncio.to_thread(_warmup)
        logger.info(f"Model warmup complete. Output shape: {output_shape}")
    
    def get_model(self) -> nn.Module:
        """Get the loaded model"""
        if not self.is_loaded or self.model is None:
            raise ModelError("Model not loaded. Call load_model() first.")
        return self.model
    
    def cleanup(self) -> None:
        """Cleanup model resources"""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.device.type == "cuda":
            torch.cuda.empty_cache()
        
        self.is_loaded = False
        logger.info("Model resources cleaned up")
    
    @property
    def health_status(self) -> dict:
        """Get model health status with detailed verification"""
        status = {
            "loaded": self.is_loaded,
            "device": str(self.device),
            "model_path": str(self._model_path),
            "model_exists": self._model_path.exists(),
            "cuda_available": torch.cuda.is_available(),
            "labels_count": len(DISEASE_CLASSES),
            "labels": DISEASE_CLASSES,
        }
        
        # Add detected num_classes from model if loaded
        if self.is_loaded and self.model is not None:
            try:
                # Get classifier output size
                if hasattr(self.model, 'classifier'):
                    classifier = self.model.classifier
                    if hasattr(classifier, 'out_features'):
                        status["detected_num_classes"] = classifier.out_features
                    elif hasattr(classifier, 'weight'):
                        status["detected_num_classes"] = classifier.weight.shape[0]
                
                # Verify labels match model output
                if "detected_num_classes" in status:
                    if status["detected_num_classes"] != status["labels_count"]:
                        status["warning"] = f"Mismatch: Model has {status['detected_num_classes']} classes but labels list has {status['labels_count']} classes"
            except Exception as e:
                logger.warning(f"Could not detect num_classes from model: {e}")
        
        if not self._model_path.exists():
            status["error"] = f"Model file not found at {self._model_path}"
        elif not self.is_loaded:
            status["error"] = "Model exists but failed to load"
            
        return status
