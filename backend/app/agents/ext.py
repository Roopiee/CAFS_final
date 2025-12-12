"""
ext.py
Enhanced extraction agent with dual OCR cascade (Tesseract → EasyOCR)
"""

import asyncio
import pytesseract
from PIL import Image, ImageEnhance
import io
import json
import re
import logging
import cv2
import numpy as np
import time
from typing import Optional, Tuple
from mistralai import Mistral
from app.config import config

logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)

# Constants
MIN_OCR_TEXT_LENGTH = 20
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_TEXT_SNIPPET_LENGTH = 300
MISTRAL_TIMEOUT_SECONDS = 30
OCR_TIMEOUT_SECONDS = 60


class ExtractionAgent:
    """
    Enhanced extraction agent with dual OCR cascade:
    1. Tesseract (fast, good for clean text) - First attempt
    2. EasyOCR (accurate, good for light/faint text) - Fallback
    """

    def __init__(self, api_key: str):
        """Initialize extraction agent with Mistral and OCR engines"""
        self.client = Mistral(api_key=api_key)
        
        # EasyOCR reader (lazy load - only initialize when needed)
        self.easyocr_reader = None
        
        logger.info("✓ Extraction agent initialized with Mistral")

    def _get_easyocr_reader(self):
        """Lazy load EasyOCR reader (only when needed)"""
        if self.easyocr_reader is None:
            try:
                import easyocr
                logger.info("📚 Initializing EasyOCR (one-time setup, may take 30s)...")
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                logger.info("✓ EasyOCR initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize EasyOCR: {e}")
                self.easyocr_reader = False  # Mark as unavailable
        return self.easyocr_reader if self.easyocr_reader else None

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Upscale for better OCR on small text
        width, height = image.size
        if width < 2000 or height < 2000:
            image = image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
            
        image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)  # Increased for light text
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.2)  # Added for light text
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)  # Increased
        return image

    def _detect_qr_code(self, image_bytes: bytes) -> Optional[str]:
        """Detect QR code and extract data"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return None
                
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(image)
            
            if data:
                logger.info(f"✓ QR Code detected: {data}")
                return data
            return None
        except Exception as e:
            logger.warning(f"QR detection failed: {e}")
            return None

    def _clean_certificate_id(self, cert_id: Optional[str]) -> str:
        """Clean certificate ID by removing spaces and fixing OCR errors"""
        if not cert_id:
            return cert_id
        
        # Remove ALL whitespace
        cleaned = ''.join(cert_id.split())
        
        # Fix common OCR mistakes
        cleaned = cleaned.replace('|', '1')
        cleaned = cleaned.replace('é', '6')  # Common in HubSpot certs
        cleaned = cleaned.replace('ö', 'o')
        cleaned = cleaned.replace('ï', 'i')
        
        # Replace lowercase L with 1 ONLY when surrounded by numbers
        cleaned = re.sub(r'(?<=\d)l(?=\d)', '1', cleaned)
        cleaned = re.sub(r'^l(?=\d)', '1', cleaned)
        cleaned = re.sub(r'(?<=\d)l$', '1', cleaned)
        
        # Replace uppercase I with 1 ONLY when surrounded by numbers
        cleaned = re.sub(r'(?<=\d)I(?=\d)', '1', cleaned)
        
        # Replace O with 0 ONLY in specific patterns
        cleaned = re.sub(r'O(?=0)', '0', cleaned)
        cleaned = re.sub(r'(?<=0)O', '0', cleaned)
        
        return cleaned

    def _clean_issuer_url(self, url: Optional[str], cert_id: Optional[str] = None) -> str:
        """Clean and expand issuer URL"""
        if not url:
            return url
        
        url = url.strip()
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if 'ude.my' in domain and cert_id:
                url = f'https://www.udemy.com/certificate/{cert_id}'
            elif 'coursera.org' in domain and 'verify' in parsed.path and cert_id:
                url = f'https://www.coursera.org/verify/{cert_id}'
        except Exception as e:
            logger.warning(f"URL parsing failed: {e}, using original URL")
        
        return url

    def _validate_certificate_id(self, cert_id: Optional[str], issuer_name: Optional[str]) -> Optional[str]:
        """Validate certificate ID format based on issuer platform"""
        if not cert_id:
            return None
        
        if not issuer_name:
            return cert_id
        
        issuer_lower = issuer_name.lower()
        
        # Udemy: Must start with "UC-"
        if 'udemy' in issuer_lower:
            if cert_id.startswith('UC-') and len(cert_id) > 15:
                return cert_id
            else:
                logger.warning(f"Invalid Udemy certificate ID format: '{cert_id}'")
                return None
        
        # Coursera: 12+ alphanumeric
        if 'coursera' in issuer_lower:
            if len(cert_id) >= 12 and cert_id.replace('-', '').isalnum():
                return cert_id
            elif len(cert_id) < 8:
                logger.warning(f"Certificate ID too short for Coursera: '{cert_id}'")
                return None
        
        # edX: Long hex or UUID
        if 'edx' in issuer_lower:
            if len(cert_id) >= 20:
                return cert_id
            else:
                logger.warning(f"Certificate ID too short for edX: '{cert_id}'")
                return None
        
        # LinkedIn
        if 'linkedin' in issuer_lower:
            if len(cert_id) >= 8:
                return cert_id
        
        # Generic: Reject very short IDs
        if len(cert_id) <= 6 and cert_id.isdigit():
            logger.warning(f"Certificate ID appears to be a reference number: '{cert_id}'")
            return None
        
        return cert_id
    
    def _clean_issuer_name(self, issuer_name: Optional[str]) -> str:
        """Clean issuer name by removing common phrases"""
        if not issuer_name:
            return issuer_name
        
        issuer_name = ' '.join(issuer_name.split())
        
        phrases_to_remove = [
            'issued by', 'via', 'powered by', 'through', 
            'authorized by', 'offered through', 'from',
            'in partnership with', 'in collaboration with',
            'certificate by'
        ]
        
        issuer_name_lower = issuer_name.lower()
        for phrase in phrases_to_remove:
            if phrase in issuer_name_lower:
                parts = issuer_name_lower.split(phrase, 1)
                if len(parts) > 1:
                    pos = issuer_name_lower.index(phrase) + len(phrase)
                    issuer_name = issuer_name[pos:].strip()
                    issuer_name_lower = issuer_name.lower()
        
        return issuer_name.strip()

    def _validate_image_bytes(self, image_bytes: bytes) -> None:
        """Validate image bytes before processing"""
        if not image_bytes:
            raise ValueError("Image bytes are empty")
        
        if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
            raise ValueError(f"Image size exceeds maximum of {MAX_IMAGE_SIZE_BYTES / (1024*1024):.1f}MB")
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.format not in ['JPEG', 'PNG', 'JPG', 'WEBP', 'BMP']:
                raise ValueError(f"Unsupported image format: {image.format}")
            image.verify()
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image data: {str(e)}")

    def _has_critical_data(self, text: str) -> bool:
        """
        Check if OCR text likely contains critical certificate data
        Returns True if we have enough data to skip additional OCR
        """
        text_lower = text.lower()
        
        # Check for certificate indicators
        has_name_indicator = any(word in text_lower for word in 
                                ['certificate', 'certify', 'awarded', 'completed'])
        has_org_indicator = any(word in text_lower for word in 
                               ['udemy', 'coursera', 'hubspot', 'google', 'ibm', 
                                'microsoft', 'edx', 'linkedin'])
        has_id_pattern = bool(re.search(r'[A-Z0-9]{10,}|UC-[a-f0-9\-]{30,}|[a-f0-9]{32}', text))
        
        word_count = len(text.split())
        
        is_complete = has_name_indicator and has_org_indicator and word_count > 30
        
        if is_complete:
            logger.info(f"✓ OCR appears complete ({word_count} words, has indicators)")
        else:
            logger.info(f"⚠️ OCR may be incomplete (words: {word_count}, cert: {has_name_indicator}, org: {has_org_indicator}, id: {has_id_pattern})")
        
        return is_complete

    def _merge_ocr_results(self, text1: str, text2: str) -> str:
        """Intelligently merge two OCR results"""
        if not text1:
            return text2
        if not text2:
            return text1
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        unique_words2 = words2 - words1
        
        if len(unique_words2) > 5:
            logger.info(f"✓ Merging: {len(unique_words2)} unique words from EasyOCR")
            return text1 + "\n" + text2
        else:
            logger.info("✓ Using Tesseract only (minimal new content in EasyOCR)")
            return text1

    async def _perform_tesseract_ocr(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Perform Tesseract OCR with multiple attempts
        Returns: (text, processing_time)
        """
        def _ocr_task():
            start = time.time()
            image = Image.open(io.BytesIO(image_bytes))
            processed_image = self._preprocess_image(image)
            
            # Try standard OCR
            raw_text = pytesseract.image_to_string(processed_image, lang='eng')
            
            # If low text, try PSM mode 6
            if not raw_text or len(raw_text.strip()) < MIN_OCR_TEXT_LENGTH:
                logger.warning("⚠️ Tesseract: Low text, trying PSM mode 6")
                raw_text = pytesseract.image_to_string(processed_image, lang='eng', config='--psm 6')
            
            # Try original image
            if not raw_text or len(raw_text.strip()) < MIN_OCR_TEXT_LENGTH:
                logger.warning("⚠️ Tesseract: Trying original image")
                raw_text = pytesseract.image_to_string(image, lang='eng')
            
            # Try PSM 11 (sparse text)
            if not raw_text or len(raw_text.strip()) < MIN_OCR_TEXT_LENGTH:
                logger.warning("⚠️ Tesseract: Trying PSM 11")
                raw_text = pytesseract.image_to_string(image, lang='eng', config='--psm 11')
            
            # Extract top-right corner (where IDs often are)
            if raw_text:
                width, height = image.size
                top_right = image.crop((width // 2, 0, width, height // 4))
                corner_processed = self._preprocess_image(top_right)
                corner_text = pytesseract.image_to_string(corner_processed, lang='eng', config='--psm 6')
                if corner_text and len(corner_text.strip()) > 5:
                    logger.info(f"✓ Corner OCR found additional text")
                    raw_text = raw_text + "\n" + corner_text
            
            elapsed = time.time() - start
            return raw_text, elapsed
        
        try:
            raw_text, elapsed = await asyncio.wait_for(
                asyncio.to_thread(_ocr_task),
                timeout=OCR_TIMEOUT_SECONDS
            )
            
            if raw_text and len(raw_text.strip()) > MIN_OCR_TEXT_LENGTH:
                logger.info(f"✓ Tesseract: {elapsed:.2f}s, {len(raw_text)} chars")
            else:
                logger.warning(f"⚠️ Tesseract: Low extraction ({len(raw_text) if raw_text else 0} chars)")
            
            return raw_text, elapsed
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tesseract OCR exceeded timeout of {OCR_TIMEOUT_SECONDS}s")

    async def _perform_easyocr(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Perform EasyOCR
        Returns: (text, processing_time)
        """
        def _ocr_task():
            reader = self._get_easyocr_reader()
            if not reader:
                return "", 0.0
            
            start = time.time()
            
            # EasyOCR works with numpy arrays
            image = Image.open(io.BytesIO(image_bytes))
            image_np = np.array(image)
            
            # Run EasyOCR
            results = reader.readtext(image_np)
            
            # Combine detected text
            text_parts = []
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Filter low confidence
                    text_parts.append(text)
            
            combined_text = "\n".join(text_parts)
            elapsed = time.time() - start
            
            return combined_text, elapsed
        
        try:
            combined_text, elapsed = await asyncio.wait_for(
                asyncio.to_thread(_ocr_task),
                timeout=OCR_TIMEOUT_SECONDS
            )
            
            if combined_text and len(combined_text.strip()) > MIN_OCR_TEXT_LENGTH:
                logger.info(f"✓ EasyOCR: {elapsed:.2f}s, {len(combined_text)} chars")
            else:
                logger.warning(f"⚠️ EasyOCR: Low extraction ({len(combined_text) if combined_text else 0} chars)")
            
            return combined_text, elapsed
        except asyncio.TimeoutError:
            raise TimeoutError(f"EasyOCR exceeded timeout of {OCR_TIMEOUT_SECONDS}s")

    async def _perform_ocr_cascade(self, image_bytes: bytes) -> str:
        """
        Perform OCR with cascade: Tesseract → EasyOCR (if needed)
        Returns: Final merged text
        """
        # STEP 1: Try Tesseract first (fast)
        logger.info("📄 Step 1: Tesseract OCR...")
        tesseract_text, tesseract_time = await self._perform_tesseract_ocr(image_bytes)
        
        # Check if Tesseract got enough data
        has_enough_data = self._has_critical_data(tesseract_text)
        
        # STEP 2: If incomplete, try EasyOCR
        final_text = tesseract_text
        
        if not has_enough_data:
            logger.info("📚 Step 2: EasyOCR (fallback for better accuracy)...")
            easyocr_text, easyocr_time = await self._perform_easyocr(image_bytes)
            
            if easyocr_text:
                final_text = self._merge_ocr_results(tesseract_text, easyocr_text)
                logger.info(f"✓ Combined OCR results ({tesseract_time + easyocr_time:.2f}s total)")
            else:
                logger.warning("⚠️ EasyOCR didn't produce additional text")
        else:
            logger.info(f"✓ Tesseract complete, skipping EasyOCR ({tesseract_time:.2f}s)")
        
        return final_text

    async def extract(self, image_bytes: bytes) -> dict:
        """
        Extract certificate data using dual OCR cascade + Mistral LLM
        
        Flow:
        1. Validate image
        2. Try Tesseract OCR (fast)
        3. If incomplete → Try EasyOCR (accurate)
        4. Merge OCR results
        5. QR code detection
        6. Send to Mistral LLM
        7. Clean and validate
        """
        try:
            logger.debug("🔍 Starting extraction process...")
            
            # STEP 0: Validate input
            self._validate_image_bytes(image_bytes)
            
            # STEP 1-2: OCR with cascade (Tesseract → EasyOCR if needed)
            raw_text = await self._perform_ocr_cascade(image_bytes)
            
            # STEP 3: QR Code Detection
            qr_data = self._detect_qr_code(image_bytes)
            if qr_data:
                raw_text += f"\n\n[QR CODE DATA FOUND]: {qr_data}"
                if "udemy.com" in qr_data and "UC-" in qr_data:
                    raw_text += f"\n[POSSIBLE CERTIFICATE ID]: {qr_data.split('/')[-2] if qr_data.endswith('/') else qr_data.split('/')[-1]}"

            # STEP 4: LLM extraction with Mistral
            logger.debug("🤖 Step 3: Mistral LLM extraction...")
            prompt = f"""
You are an OCR cleanup and certificate extraction agent.

Extract the following information from this certificate text:
1. candidate_name: The person's name who RECEIVED the certificate (NOT the instructor/teacher)
   - Look for the recipient's name, often appears after course title or near "Date"
   - For Udemy certificates: The last name after "Instructors" is usually the RECIPIENT, not an instructor
   - Example: "Instructors John Smith Roopak Krishna" → "Roopak Krishna" is the RECIPIENT
2. certificate_id: The unique certificate ID or number (combine any split lines into ONE continuous string with NO spaces)
3. issuer_name: The platform/organization name ONLY (e.g., "Coursera", "Udemy", "edX", "Google", "LinkedIn")
   - DO NOT include phrases like "issued by", "via", "powered by", "through", "authorized by", "offered through"
   - Extract ONLY the platform name
4. issuer_url: The full verification URL if present

CRITICAL for candidate_name:
- The certificate recipient is the LEARNER, not the instructor
- On Udemy certificates, look for the name that appears:
  * After the course title
  * Near the completion date
  * As the LAST name in a list (after "Instructors")
- If you see "Instructors Name1 Name2 Name3", the LAST name is likely the recipient

CRITICAL for certificate_id - Platform-Specific Formats:
- **Udemy**: Starts with "UC-" followed by UUID format (e.g., "UC-9ba43c6a-3983-495c-beb2-329801af4557")
  * DO NOT extract short reference numbers like "0004" or "Ref: 1234"
  * Look for "UC-" prefix or "Certificate:" label
  * Look in corners/headers for light gray text
- **Coursera**: Alphanumeric string (e.g., "ALS76DHQNMVZ", "ABCD1234EFGH")
- **HubSpot**: 32-character hex string (e.g., "93006c20260f4c788fc6c73a73503b84")
  * Often appears as "Certification code:" in light gray
  * Fix OCR errors: é→6, ö→o, ï→i
- **edX**: Long hex string or UUID format
- **LinkedIn**: Contains "learning/certificates/" in URL
- If you see BOTH a reference number (like "0004") AND a longer ID → choose the LONGER one
- If ONLY a reference number exists → return empty string

IMPORTANT for issuer_name:
- Extract ONLY the platform name
- Examples: "issued by Google through Coursera" → "Coursera"
- "powered by Udemy" → "Udemy"
- "HubSpot Academy" → "HubSpot Academy"

IMPORTANT for issuer_url:
- Look for URLs containing: "udemy.com/certificate/", "coursera.org/verify/", "credentials.edx.org"
- Extract the FULL URL if present

OCR TEXT:
---
{raw_text[:2000]}
---

Return ONLY valid JSON (no markdown, no backticks):
{{
  "candidate_name": "...",
  "certificate_id": "...",
  "issuer_name": "...",
  "issuer_url": "..."
}}
"""
            
            # Call Mistral API with timeout
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.complete,
                        model="mistral-large-latest",
                        messages=[{"role": "user", "content": prompt}]
                    ),
                    timeout=MISTRAL_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"Mistral API exceeded timeout of {MISTRAL_TIMEOUT_SECONDS}s")

            cleaned_text = response.choices[0].message.content

            # STEP 5: Parse JSON response
            try:
                data = json.loads(cleaned_text)
            except json.JSONDecodeError:
                json_str = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_text, re.S)
                if json_str:
                    data = json.loads(json_str.group(1))
                else:
                    json_str = re.search(r"\{.*\}", cleaned_text, re.S)
                    if json_str:
                        data = json.loads(json_str.group(0))
                    else:
                        logger.error("Could not parse JSON from Mistral response")
                        raise ValueError("Failed to parse Mistral response as JSON")

            # STEP 6: Clean and validate
            issuer_name = data.get('issuer_name', '')
            if issuer_name:
                issuer_name = self._clean_issuer_name(issuer_name)
                data['issuer_name'] = issuer_name
            
            certificate_id = data.get('certificate_id', '')
            if certificate_id:
                certificate_id = self._validate_certificate_id(certificate_id, issuer_name)
                if certificate_id:
                    certificate_id = self._clean_certificate_id(certificate_id)
                data['certificate_id'] = certificate_id

            issuer_url = data.get('issuer_url', '')
            if issuer_url:
                issuer_url = self._clean_issuer_url(issuer_url, certificate_id)
                data['issuer_url'] = issuer_url

            # STEP 7: Add metadata
            full_text = raw_text.replace('\n', ' ').replace('\r', ' ')
            full_text = re.sub(r'\s+', ' ', full_text)
            data["raw_text_snippet"] = (
                full_text[:MAX_TEXT_SNIPPET_LENGTH] + "..." 
                if len(full_text) > MAX_TEXT_SNIPPET_LENGTH 
                else full_text
            )

            logger.info(f"✓ Extraction complete: name={data.get('candidate_name')}, "
                       f"issuer={data.get('issuer_name')}, cert_id={data.get('certificate_id')}")

            return data

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except TimeoutError as e:
            logger.error(f"Timeout error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}", exc_info=True)
            raise ValueError(f"Failed to parse extraction results: {str(e)}")
        except IOError as e:
            logger.error(f"Image processing error: {e}", exc_info=True)
            raise ValueError(f"Failed to process image: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected extraction error: {e}", exc_info=True)
            raise RuntimeError(f"Extraction failed: {str(e)}")

    def validate_extraction(self, result: dict) -> tuple[bool, list]:
        """Validate extraction results"""
        issues = []
        
        if not result.get('candidate_name'):
            issues.append("Missing candidate name")
        
        if not result.get('certificate_id'):
            issues.append("Missing certificate ID")
        
        if not result.get('issuer_name') and not result.get('issuer_url'):
            issues.append("Missing both issuer name and URL")
        
        is_valid = len(issues) == 0
        return is_valid, issues