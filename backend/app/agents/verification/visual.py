"""
app/agents/verification/visual.py
Handles visual fallback: Reading text from screenshots when DOM scraping fails.
"""
import logging
import re
from PIL import Image
import pytesseract
from difflib import SequenceMatcher
from typing import Tuple

logger = logging.getLogger(__name__)

class VisualVerifier:
    def __init__(self):
        # Verify tesseract is available
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            logger.warning("⚠️ Tesseract OCR not found. Visual verification will be disabled.")

    def verify_screenshot(self, image_path: str, candidate_name: str) -> Tuple[bool, float, str]:
        """
        Runs OCR on the screenshot and fuzzy matches the candidate name.
        Returns: (is_match, score, extracted_text)
        """
        if not image_path:
            return False, 0.0, ""

        try:
            # 1. Load Image
            img = Image.open(image_path)
            
            # 2. Run OCR (Extract text from pixels)
            # --psm 6 assumes a block of text, good for documents
            extracted_text = pytesseract.image_to_string(img, config='--psm 6')
            
            # 3. Clean and Normalize
            clean_text = extracted_text.lower()
            clean_name = re.sub(r'[^a-z0-9\s]', '', candidate_name.lower())
            
            # 4. Fuzzy Match
            # We use a slightly looser threshold (0.65) for OCR because of potential typos (e.g., '1' vs 'l')
            if clean_name in clean_text:
                return True, 1.0, extracted_text
            
            # Sequence matching
            match = SequenceMatcher(None, clean_name, clean_text).find_longest_match(0, len(clean_name), 0, len(clean_text))
            found_fragment = clean_text[match.b: match.b + match.size]
            
            ratio = SequenceMatcher(None, clean_name, found_fragment).ratio()
            
            is_match = ratio >= 0.65
            return is_match, ratio, extracted_text

        except Exception as e:
            logger.error(f"Visual verification failed: {e}")
            return False, 0.0, ""