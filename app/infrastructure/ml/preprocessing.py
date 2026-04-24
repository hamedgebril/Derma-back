"""
Image preprocessing for ML model
"""
import logging
from typing import Tuple

import torch
from PIL import Image
from torchvision import transforms

from app.infrastructure.ml.constants import (
    IMAGE_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD
)

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Handle image preprocessing for model inference"""
    
    def __init__(self):
        self.transforms = self._build_transforms()
    
    def _build_transforms(self) -> transforms.Compose:
        """Build transformation pipeline"""
        return transforms.Compose([
            transforms.Resize(IMAGE_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])
    
    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess image for model inference
        
        Args:
            image: PIL Image in RGB format
            
        Returns:
            Preprocessed tensor ready for model
        """
        try:
            # Ensure RGB format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply transforms
            tensor = self.transforms(image)
            
            return tensor
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
    
    def assess_quality(self, image: Image.Image) -> Tuple[int, str]:
        """
        Assess image quality based on resolution and characteristics
        
        Args:
            image: PIL Image
            
        Returns:
            Tuple of (quality_score 0-100, quality_label)
        """
        width, height = image.size
        min_dimension = min(width, height)
        
        # Check for blur (simplified - could use Laplacian variance)
        # Check for proper exposure (simplified - could use histogram analysis)
        
        if min_dimension >= 1024:
            return 95, "Excellent"
        elif min_dimension >= 512:
            return 85, "Good"
        elif min_dimension >= 256:
            return 70, "Fair"
        elif min_dimension >= 128:
            return 50, "Poor"
        else:
            return 30, "Very Poor"
