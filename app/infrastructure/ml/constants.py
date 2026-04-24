"""
ML model constants and configurations
"""
from typing import List

# Disease classes (must match training order from train_model.ipynb)
# Model trained on 6 classes: 5 diseases + healthy
# Order matches dataset.class_names from training (sorted alphabetically)
DISEASE_CLASSES: List[str] = [
    'MF',
    'annular lichen',
    'healty',
    'psoriasis',
    'tinea circinata',
    'urticaria'
]

# Image preprocessing constants (from train_model.ipynb test_tf)
IMAGE_SIZE = (380, 380)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Quality thresholds
MIN_IMAGE_SIZE = 128
RECOMMENDED_IMAGE_SIZE = 512
HIGH_QUALITY_SIZE = 1024

# Confidence thresholds
LOW_CONFIDENCE_THRESHOLD = 0.5
MEDIUM_CONFIDENCE_THRESHOLD = 0.7
HIGH_CONFIDENCE_THRESHOLD = 0.9
