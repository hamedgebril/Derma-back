"""
Test script to verify ML model inference works correctly
Matches training notebook preprocessing and model architecture
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from PIL import Image
import timm

from app.infrastructure.ml.constants import DISEASE_CLASSES, IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD
from app.infrastructure.ml.preprocessing import ImagePreprocessor


def load_model(model_path: str, device: str = "cpu"):
    """Load model exactly as in training"""
    num_classes = len(DISEASE_CLASSES)
    
    # Create model with same architecture as training
    model = timm.create_model(
        'efficientnet_b4',
        pretrained=False,
        num_classes=num_classes,
        drop_rate=0.4
    )
    
    # Load trained weights
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint, strict=True)
    
    # Set to eval mode
    model.eval()
    
    return model


def predict_image(model, image_path: str, device: str = "cpu"):
    """Run inference on a single image"""
    # Load and preprocess image
    image = Image.open(image_path).convert("RGB")
    preprocessor = ImagePreprocessor()
    tensor = preprocessor.preprocess(image)
    
    # Add batch dimension
    tensor = tensor.unsqueeze(0).to(device)
    
    # Run inference
    with torch.no_grad():
        output = model(tensor)
        probabilities = torch.nn.functional.softmax(output, dim=1)
    
    # Get top-3 predictions
    top3_prob, top3_idx = torch.topk(probabilities, 3, dim=1)
    
    return top3_prob[0], top3_idx[0]


def main():
    print("=" * 60)
    print("ML Model Inference Test")
    print("=" * 60)
    
    # Configuration
    model_path = "app/infrastructure/ml/weights/skin_efficientnet_b4_9.pth"
    test_image = "uploads/c616000c-6b47-43df-8e15-712ae9ad9a7a.png"  # Use existing test image
    device = "cpu"
    
    print(f"\nConfiguration:")
    print(f"  Model path: {model_path}")
    print(f"  Test image: {test_image}")
    print(f"  Device: {device}")
    print(f"  Image size: {IMAGE_SIZE}")
    print(f"  Normalization: mean={IMAGENET_MEAN}, std={IMAGENET_STD}")
    print(f"  Number of classes: {len(DISEASE_CLASSES)}")
    
    # Verify files exist
    if not os.path.exists(model_path):
        print(f"\n❌ ERROR: Model file not found at {model_path}")
        return
    
    if not os.path.exists(test_image):
        print(f"\n⚠️  WARNING: Test image not found at {test_image}")
        print("Please provide a test image path as argument")
        if len(sys.argv) > 1:
            test_image = sys.argv[1]
        else:
            return
    
    print("\n" + "-" * 60)
    print("Loading model...")
    try:
        model = load_model(model_path, device)
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"❌ ERROR loading model: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "-" * 60)
    print("Running inference...")
    try:
        top3_prob, top3_idx = predict_image(model, test_image, device)
        print("✓ Inference completed successfully")
    except Exception as e:
        print(f"❌ ERROR during inference: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "-" * 60)
    print("Results:")
    print("\nTop-3 Predictions:")
    for i in range(3):
        class_name = DISEASE_CLASSES[top3_idx[i]]
        probability = top3_prob[i].item() * 100
        print(f"  {i+1}. {class_name:20s} - {probability:5.2f}%")
    
    print("\n" + "-" * 60)
    print("Class Labels (in order):")
    for i, class_name in enumerate(DISEASE_CLASSES):
        print(f"  {i}: {class_name}")
    
    print("\n" + "=" * 60)
    print("✓ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
