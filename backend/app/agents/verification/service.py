"""
app/agents/verification/service.py
Core verification service with Smart Retry Logic.
"""
import logging
import re
from difflib import SequenceMatcher
from typing import Optional, Tuple

from app.schemas import ExtractionResult, VerificationResult
from app.config import config
from .sources import TrustedSourceRegistry
from .scanner import fetch_page_text
from .visual import VisualVerifier

logger = logging.getLogger(__name__)

class VerificationService:
    def __init__(self):
        self.registry = TrustedSourceRegistry()
        self.visual = VisualVerifier()

    def _fuzzy_match(self, candidate: str, page_text: str, threshold: float = 0.7) -> Tuple[bool, float]:
        if not candidate or not page_text: return False, 0.0
        cand_clean = re.sub(r'[^a-z0-9\s]', '', candidate.lower())
        text_clean = re.sub(r'[^a-z0-9\s]', '', page_text.lower())
        if cand_clean in text_clean: return True, 1.0
        return SequenceMatcher(None, cand_clean, text_clean).ratio() >= threshold, SequenceMatcher(None, cand_clean, text_clean).ratio()

    async def verify(self, data: ExtractionResult) -> VerificationResult:
        # A. Validation
        if not data.candidate_name:
            return VerificationResult(is_verified=False, trusted_domain=False, message="No candidate name.", method="validation_error")

        # B. Get URLs
        org_name_str = data.issuer_name.value if data.issuer_name else (data.issuer_org or "")
        urls = self.registry.generate_urls(data.issuer_url, data.certificate_id, org_name_str)
        if not urls:
            return VerificationResult(is_verified=False, trusted_domain=False, message="No URL generated.", method="url_error")

        # C. Trust Check
        if not self.registry.is_trusted(urls[0]):
            return VerificationResult(is_verified=False, trusted_domain=False, verification_url=urls[0], message="Untrusted domain.", method="security_check")

        # D. Smart Verification Loop
        best_score = 0.0
        best_url = urls[0]
        
        for url in urls[:2]:
            logger.info(f"Scanning: {url}")
            
            # 1. Attempt Standard Scan (Fast)
            page_text, screenshot_path = await fetch_page_text(url, use_browser=True, force_browser=False)
            
            # 2. Check Text Match
            if page_text:
                is_match, score = self._fuzzy_match(data.candidate_name, page_text)
                if score > best_score: best_score = score
                
                if is_match:
                    return VerificationResult(is_verified=True, trusted_domain=True, confidence_score=round(score,2), verification_url=url, method="dom_text_match", message=f"Verified via text. Match: {score:.0%}")
            
            # 3. SMART RETRY: If Text Match Failed AND we don't have a screenshot yet...
            # This handles cases where HTTPX returned "Loading..." text but missed the real content.
            if best_score < 0.7 and not screenshot_path:
                logger.info("Text match failed on fast fetch. Forcing Browser Retry...")
                page_text, screenshot_path = await fetch_page_text(url, force_browser=True)
                
                # Re-check text on the browser version
                if page_text:
                    is_match, score = self._fuzzy_match(data.candidate_name, page_text)
                    if score > best_score: best_score = score
                    if is_match:
                        return VerificationResult(is_verified=True, trusted_domain=True, confidence_score=round(score,2), verification_url=url, method="dom_text_match_retry", message=f"Verified via browser text. Match: {score:.0%}")

            # 4. Visual Fallback (Check the Screenshot pixels)
            if screenshot_path:
                v_match, v_score, _ = self.visual.verify_screenshot(screenshot_path, data.candidate_name)
                if v_score > best_score: best_score = v_score
                
                if v_match:
                    return VerificationResult(is_verified=True, trusted_domain=True, confidence_score=round(v_score,2), verification_url=url, method="visual_ocr", message=f"Verified via visual OCR. Match: {v_score:.0%}")

        return VerificationResult(is_verified=False, trusted_domain=True, confidence_score=round(best_score,2), verification_url=best_url, method="failed", message=f"Verification failed. Best Match: {best_score:.0%}")

# Singleton
_service_instance: Optional[VerificationService] = None
def get_verification_service() -> VerificationService:
    global _service_instance
    if _service_instance is None: _service_instance = VerificationService()
    return _service_instance