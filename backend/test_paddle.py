"""
Test PaddleOCR installation
Run: python test_paddleocr.py
"""

import sys

print("Testing PaddleOCR installation...")

try:
    from paddleocr import PaddleOCR
    print("✓ PaddleOCR imported successfully")
    
    # Initialize reader
    print("Initializing PaddleOCR reader (first run downloads models ~300MB)...")
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    print("✓ PaddleOCR reader initialized successfully")
    
    print("\n✅ All tests passed! PaddleOCR is working.")
    print("Note: First actual OCR will be slow (loading models)")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: pip install paddlepaddle paddleocr")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)