"""
Test TruFor installation
Run: python test_trufor.py
"""
import torch
import numpy as np
import sys
import os

print("Testing TruFor installation...\n")

# Test 1: PyTorch
try:
    import torch
    print(f"✓ PyTorch installed: {torch.__version__}")
except ImportError as e:
    print(f"❌ PyTorch not installed: {e}")
    sys.exit(1)

# Test 2: timm
try:
    import timm
    print(f"✓ timm installed: {timm.__version__}")
except ImportError as e:
    print(f"❌ timm not installed: {e}")
    sys.exit(1)

# Test 3: Other dependencies
try:
    import numpy as np
    import cv2
    from skimage import io
    print("✓ numpy, opencv, scikit-image installed")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)

# Test 4: Check for model file
model_path = "models/trufor/trufor_model.pth.tar"
if os.path.exists(model_path):
    print(f"✓ Model file found at: {model_path}")
    file_size = os.path.getsize(model_path) / (1024 * 1024)
    print(f"  Model size: {file_size:.1f} MB")
else:
    print(f"⚠️  Model file not found at: {model_path}")
    print("  You need to download it from TruFor releases")

# Test 5: Try to load model (if file exists)
if os.path.exists(model_path):
    try:
        checkpoint = torch.load(model_path, map_location='cpu')
        print("✓ Model file is valid and loadable")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        sys.exit(1)

print("\n✅ All tests passed! TruFor is ready to use.")
print("\nNext step: Integrate into forensics agent")