"""
ext.py
Extraction agent for OCR and LLM-based certificate data extraction
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
from typing import Optional
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
    Enhanced extraction agent that:
    1. Performs OCR with preprocessing
    2. Uses Mistral LLM for structured extraction
    3. Cleans and validates extracted data
    """

    def __init__(self, api_key: str):
        """
        Initialize the extraction agent
        
        Args:
            api_key: Mistral API key
        """
        self.client = Mistral(api_key=api_key)
        logger.info("✓ Extraction agent initialized with Mistral")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Upscale for better OCR on small text
        width, height = image.size
        if width < 2000 or height < 2000:
            image = image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
            
        image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)
        return image

    def _detect_qr_code(self, image_bytes: bytes) -> Optional[str]:
        """Detect QR code and extract data"""
        try:
            # Convert bytes to numpy array
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
        """Clean certificate ID by removing spaces and fixing OCR errors
        
        Uses context-aware replacements to avoid corrupting legitimate text.
        """
        if not cert_id:
            return cert_id
        
        # Remove ALL whitespace (spaces, newlines, tabs)
        cleaned = ''.join(cert_id.split())
        
        # Fix common OCR mistakes ONLY in certificate ID context
        # Use regex with word boundaries to avoid corrupting legitimate text
        # Only apply to alphanumeric sequences that look like IDs
        
        # Replace pipe character with 1 (common OCR error)
        cleaned = cleaned.replace('|', '1')
        
        # Replace lowercase L with 1 ONLY when surrounded by numbers
        cleaned = re.sub(r'(?<=\d)l(?=\d)', '1', cleaned)
        cleaned = re.sub(r'^l(?=\d)', '1', cleaned)  # At start
        cleaned = re.sub(r'(?<=\d)l$', '1', cleaned)  # At end
        
        # Replace uppercase I with 1 ONLY when surrounded by numbers
        cleaned = re.sub(r'(?<=\d)I(?=\d)', '1', cleaned)
        
        # Replace O with 0 ONLY in specific patterns (e.g., O0, 0O)
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
        
        # Expand short URLs to full verification URLs
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Domain-based expansion (more reliable than substring matching)
            if 'ude.my' in domain:
                if cert_id:
                    url = f'https://www.udemy.com/certificate/{cert_id}'
            elif 'coursera.org' in domain and 'verify' in parsed.path:
                if cert_id:
                    url = f'https://www.coursera.org/verify/{cert_id}'
        except Exception as e:
            logger.warning(f"URL parsing failed: {e}, using original URL")
        
        return url

    def _validate_certificate_id(self, cert_id: Optional[str], issuer_name: Optional[str]) -> Optional[str]:
        """
        Validate certificate ID format based on issuer platform
        
        Args:
            cert_id: Extracted certificate ID
            issuer_name: Platform name
            
        Returns:
            Validated certificate ID or None if invalid
        """
        if not cert_id:
            return None
        
        # Skip validation if issuer unknown
        if not issuer_name:
            return cert_id
        
        issuer_lower = issuer_name.lower()
        
        # Udemy: Must start with "UC-" and be longer than 10 characters
        if 'udemy' in issuer_lower:
            if cert_id.startswith('UC-') and len(cert_id) > 15:
                return cert_id
            else:
                logger.warning(f"Invalid Udemy certificate ID format: '{cert_id}' (expected UC-XXXXXX...)")
                return None
        
        # Coursera: Usually 12+ alphanumeric characters
        if 'coursera' in issuer_lower:
            if len(cert_id) >= 12 and cert_id.replace('-', '').isalnum():
                return cert_id
            elif len(cert_id) < 8:
                logger.warning(f"Certificate ID too short for Coursera: '{cert_id}'")
                return None
        
        # edX: Usually long hex or UUID format
        if 'edx' in issuer_lower:
            if len(cert_id) >= 20:
                return cert_id
            else:
                logger.warning(f"Certificate ID too short for edX: '{cert_id}'")
                return None
        
        # LinkedIn: Usually in URL path
        if 'linkedin' in issuer_lower:
            if len(cert_id) >= 8:
                return cert_id
        
        # Generic validation: Reject very short IDs (likely reference numbers)
        if len(cert_id) <= 6 and cert_id.isdigit():
            logger.warning(f"Certificate ID appears to be a reference number: '{cert_id}' (too short)")
            return None
        
        return cert_id
    
    def _clean_issuer_name(self, issuer_name: Optional[str]) -> str:
        """Clean issuer name by removing common phrases"""
        if not issuer_name:
            return issuer_name
        
        # Normalize whitespace first
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
                # Split on lowercase to find position, then extract from original
                parts = issuer_name_lower.split(phrase, 1)
                if len(parts) > 1:
                    # Find the position and extract from original string
                    pos = issuer_name_lower.index(phrase) + len(phrase)
                    issuer_name = issuer_name[pos:].strip()
                    issuer_name_lower = issuer_name.lower()
        
        return issuer_name.strip()

    def _validate_image_bytes(self, image_bytes: bytes) -> None:
        """Validate image bytes before processing
        
        Raises:
            ValueError: If image data is invalid
        """
        if not image_bytes:
            raise ValueError("Image bytes are empty")
        
        if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
            raise ValueError(f"Image size exceeds maximum allowed size of {MAX_IMAGE_SIZE_BYTES / (1024*1024):.1f}MB")
        
        # Check for valid image format by trying to open it
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Verify it's a valid image by checking format
            if image.format not in ['JPEG', 'PNG', 'JPG', 'WEBP', 'BMP']:
                raise ValueError(f"Unsupported image format: {image.format}")
            image.verify()
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image data: {str(e)}")

    async def _perform_ocr(self, image_bytes: bytes) -> str:
        """Perform OCR in a separate thread to avoid blocking
        
        Returns:
            Extracted text from image
        """
        def _ocr_task():
            image = Image.open(io.BytesIO(image_bytes))
            processed_image = self._preprocess_image(image)
            raw_text = pytesseract.image_to_string(processed_image, lang='eng')
            
            if not raw_text or len(raw_text.strip()) < MIN_OCR_TEXT_LENGTH:
                logger.warning("OCR extracted very little text, trying without preprocessing")
                raw_text = pytesseract.image_to_string(image, lang='eng')
            
            return raw_text
        
        # Run OCR in thread pool to avoid blocking event loop
        try:
            raw_text = await asyncio.wait_for(
                asyncio.to_thread(_ocr_task),
                timeout=OCR_TIMEOUT_SECONDS
            )
            return raw_text
        except asyncio.TimeoutError:
            raise TimeoutError(f"OCR processing exceeded timeout of {OCR_TIMEOUT_SECONDS} seconds")

    async def extract(self, image_bytes: bytes) -> dict:
        """Extract certificate data from image using OCR and LLM
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Dictionary containing extracted certificate data
            
        Raises:
            ValueError: If image validation fails
            TimeoutError: If OCR or Mistral API times out
        """
        try:
            logger.debug("Starting extraction process...")
            
            # STEP 0: Validate input
            self._validate_image_bytes(image_bytes)
            
            # STEP 1: OCR with preprocessing (non-blocking)
            raw_text = await self._perform_ocr(image_bytes)
            
            # STEP 1.5: QR Code Detection
            qr_data = self._detect_qr_code(image_bytes)
            if qr_data:
                raw_text += f"\n\n[QR CODE DATA FOUND]: {qr_data}"
                # If QR code is a URL, it might contain the ID directly
                if "udemy.com" in qr_data and "UC-" in qr_data:
                    raw_text += f"\n[POSSIBLE CERTIFICATE ID]: {qr_data.split('/')[-2] if qr_data.endswith('/') else qr_data.split('/')[-1]}"

            # STEP 2: LLM extraction with Mistral (with timeout)
            logger.debug("Processing with Mistral LLM...")
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
  * Many Udemy PDFs only show reference numbers, NOT the actual certificate ID - if so, leave empty
- **Coursera**: Alphanumeric string (e.g., "ALS76DHQNMVZ", "ABCD1234EFGH")
- **edX**: Long hex string or UUID format
- **LinkedIn**: Contains "learning/certificates/" in URL
- If you see BOTH a reference number (like "0004") AND a longer ID → choose the LONGER one
- If ONLY a reference number exists and no proper certificate ID → return empty string for certificate_id

IMPORTANT for issuer_name:
- Extract ONLY the platform name
- Examples of CORRECT extraction:
  * "issued by Google through Coursera" → "Coursera"
  * "powered by Udemy" → "Udemy"
  * "offered through edX" → "edX"
  * "authorized by Google" → "Google"
  * "certificate by LinkedIn Learning" → "LinkedIn Learning"

IMPORTANT for issuer_url:
- Look for URLs containing: "udemy.com/certificate/", "coursera.org/verify/", "credentials.edx.org"
- If URL is present, extract the FULL URL
- If only domain is shown, extract it

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
                raise TimeoutError(f"Mistral API call exceeded timeout of {MISTRAL_TIMEOUT_SECONDS} seconds")

            cleaned_text = response.choices[0].message.content

            # STEP 3: Parse JSON response
            try:
                data = json.loads(cleaned_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                json_str = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_text, re.S)
                if json_str:
                    data = json.loads(json_str.group(1))
                else:
                    # Last resort: extract any JSON-like structure
                    json_str = re.search(r"\{.*\}", cleaned_text, re.S)
                    if json_str:
                        data = json.loads(json_str.group(0))
                    else:
                        logger.error("Could not parse JSON from Mistral response")
                        raise ValueError("Failed to parse Mistral response as JSON")

            # STEP 4: Clean and validate extracted data
            issuer_name = data.get('issuer_name', '')
            if issuer_name:
                issuer_name = self._clean_issuer_name(issuer_name)
                data['issuer_name'] = issuer_name
            
            certificate_id = data.get('certificate_id', '')
            if certificate_id:
                # First validate the ID format
                certificate_id = self._validate_certificate_id(certificate_id, issuer_name)
                if certificate_id:
                    # Then clean it
                    certificate_id = self._clean_certificate_id(certificate_id)
                data['certificate_id'] = certificate_id

            issuer_url = data.get('issuer_url', '')
            if issuer_url:
                issuer_url = self._clean_issuer_url(issuer_url, certificate_id)
                data['issuer_url'] = issuer_url

            # STEP 5: Add metadata
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
            # Validation errors
            logger.error(f"Validation error: {e}")
            raise
        except TimeoutError as e:
            # Timeout errors
            logger.error(f"Timeout error: {e}")
            raise
        except json.JSONDecodeError as e:
            # JSON parsing errors
            logger.error(f"JSON parsing error: {e}", exc_info=True)
            raise ValueError(f"Failed to parse extraction results: {str(e)}")
        except IOError as e:
            # Image processing errors
            logger.error(f"Image processing error: {e}", exc_info=True)
            raise ValueError(f"Failed to process image: {str(e)}")
        except Exception as e:
            # Unexpected errors
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