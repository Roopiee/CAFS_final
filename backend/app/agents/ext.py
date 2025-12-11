"""
ext.py
Extraction agent for OCR and LLM-based certificate data extraction
"""

import pytesseract
from PIL import Image, ImageEnhance
import io
import json
import re
import logging
from mistralai import Mistral

logger = logging.getLogger(__name__)


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
        image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)
        return image

    def _clean_certificate_id(self, cert_id: str) -> str:
        """Clean certificate ID by removing spaces and fixing OCR errors"""
        if not cert_id:
            return cert_id
        
        # Remove ALL whitespace (spaces, newlines, tabs)
        cleaned = ''.join(cert_id.split())
        
        # Fix common OCR mistakes
        replacements = {
            'O1': '01', 'l': '1', '|': '1', 'I': '1',
            'O0': '00', 'o': '0'
        }
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        return cleaned

    def _clean_issuer_url(self, url: str, cert_id: str = None) -> str:
        """Clean and expand issuer URL"""
        if not url:
            return url
        
        url = url.strip()
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Expand short URLs to full verification URLs
        expansions = {
            'ude.my': 'www.udemy.com/certificate',
            'coursera.org/verify': 'www.coursera.org/verify',
        }
        
        for short, full in expansions.items():
            if short in url:
                if cert_id and cert_id in url:
                    url = f'https://{full}/{cert_id}'
                else:
                    parts = url.split('/')
                    if parts:
                        extracted_id = parts[-1]
                        url = f'https://{full}/{extracted_id}'
        
        return url

    def _clean_issuer_name(self, issuer_name: str) -> str:
        """Clean issuer name by removing common phrases"""
        if not issuer_name:
            return issuer_name
        
        phrases_to_remove = [
            'issued by', 'via', 'powered by', 'through', 
            'authorized by', 'offered through', 'from',
            'in partnership with', 'in collaboration with',
            'certificate by'
        ]
        
        issuer_name_lower = issuer_name.lower()
        for phrase in phrases_to_remove:
            if phrase in issuer_name_lower:
                parts = issuer_name.split(phrase, 1)
                if len(parts) > 1:
                    issuer_name = parts[1].strip()
        
        issuer_name = ' '.join(issuer_name.split())
        return issuer_name.strip()

    def extract(self, image_bytes: bytes) -> dict:
        """Extract certificate data from image using OCR and LLM"""
        try:
            logger.info("Starting extraction process...")
            
            # STEP 1: OCR with preprocessing
            image = Image.open(io.BytesIO(image_bytes))
            processed_image = self._preprocess_image(image)
            raw_text = pytesseract.image_to_string(processed_image, lang='eng')
            
            if not raw_text or len(raw_text.strip()) < 20:
                logger.warning("OCR extracted very little text, trying without preprocessing")
                raw_text = pytesseract.image_to_string(image, lang='eng')

            # STEP 2: LLM extraction with Mistral
            logger.info("Processing with Mistral LLM...")
            prompt = f"""
You are an OCR cleanup and certificate extraction agent.

Extract the following information from this certificate text:
1. candidate_name: The person's name who received the certificate
2. certificate_id: The unique certificate ID or number (combine any split lines into ONE continuous string with NO spaces)
3. issuer_name: The platform/organization name ONLY (e.g., "Coursera", "Udemy", "edX", "Google", "LinkedIn")
   - DO NOT include phrases like "issued by", "via", "powered by", "through", "authorized by", "offered through"
   - Extract ONLY the platform name
4. issuer_url: The full verification URL if present
5. cleaned_text: A cleaned version of the certificate text

IMPORTANT for certificate_id:
- Extract the COMPLETE ID with NO spaces or line breaks
- If the ID is split across lines, combine it into one continuous string
- Example: "UC-9ba43c6a-3983-495c-beb2-329801af4557" (no spaces!)
- Example: "ALS76DHQNMVZ" (continuous string)

IMPORTANT for issuer_name:
- Extract ONLY the platform name
- Examples of CORRECT extraction:
  * "issued by Google through Coursera" → "Coursera"
  * "powered by Udemy" → "Udemy"
  * "offered through edX" → "edX"
  * "authorized by Google" → "Google"
  * "certificate by LinkedIn Learning" → "LinkedIn Learning"

OCR TEXT:
---
{raw_text}
---

Return ONLY valid JSON (no markdown, no backticks):
{{
  "candidate_name": "...",
  "certificate_id": "...",
  "issuer_name": "...",
  "issuer_url": "...",
  "cleaned_text": "..."
}}
"""
            
            response = self.client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}]
            )

            cleaned_text = response.choices[0].message.content

            # STEP 3: Parse JSON response
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
                        data = {}

            # STEP 4: Clean and validate extracted data
            
            certificate_id = data.get('certificate_id', '')
            if certificate_id:
                certificate_id = self._clean_certificate_id(certificate_id)
                data['certificate_id'] = certificate_id

            issuer_url = data.get('issuer_url', '')
            if issuer_url:
                issuer_url = self._clean_issuer_url(issuer_url, certificate_id)
                data['issuer_url'] = issuer_url

            issuer_name = data.get('issuer_name', '')
            if issuer_name:
                issuer_name = self._clean_issuer_name(issuer_name)
                data['issuer_name'] = issuer_name

            # STEP 5: Add metadata
            full_text = raw_text.replace('\n', ' ').replace('\r', ' ')
            full_text = re.sub(r'\s+', ' ', full_text)
            data["raw_text_snippet"] = full_text[:300] + "..." if len(full_text) > 300 else full_text

            if "certificate_date" in data:
                del data["certificate_date"]

            logger.info(f"✓ Extraction complete: name={data.get('candidate_name')}, "
                       f"issuer={data.get('issuer_name')}, cert_id={data.get('certificate_id')}")

            return data

        except Exception as e:
            logger.error(f"Extraction error: {e}", exc_info=True)
            return {
                "candidate_name": None,
                "certificate_id": None,
                "issuer_name": None,
                "issuer_url": None,
                "cleaned_text": None,
                "raw_text_snippet": f"Error: {str(e)}"
            }

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