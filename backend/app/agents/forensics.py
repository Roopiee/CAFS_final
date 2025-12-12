"""
forensics.py
Forensics agent using Mistral AI to detect photoshopped certificates
"""

import base64
import io
import logging
from typing import Optional
from PIL import Image
from mistralai import Mistral
from app.schemas import ForensicsResult
from app.config import config

logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)


class ForensicsAgent:
    """
    Digital Forensics Agent using Mistral AI Vision to detect photoshopped certificates.
    
    A certificate is flagged as high-risk (potentially photoshopped) when:
    - The authenticity confidence score is BELOW 0.30
    - This indicates the AI has low confidence the certificate is genuine
    """
    
    def __init__(self, api_key: str = "nJpjawyHlBoqUrTBSxtOE2oA2KytRL2Y"):
        """
        Initialize the forensics agent with Mistral AI
        
        Args:
            api_key: Mistral API key
        """
        self.client = Mistral(api_key=api_key)
        logger.info("✓ Forensics agent initialized with Mistral AI")
    
    def analyze(self, image_bytes: bytes) -> ForensicsResult:
        """
        Analyze a certificate image for signs of digital manipulation
        
        Args:
            image_bytes: Certificate image data
            
        Returns:
            ForensicsResult with manipulation analysis
        """
        try:
            logger.info("Starting Mistral AI forensics analysis...")
            
            # Convert image to base64 for Mistral API
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Validate image size
            image = Image.open(io.BytesIO(image_bytes))
            width, height = image.size
            logger.debug(f"Image dimensions: {width}x{height}")
            
            # Construct the forensics analysis prompt
            prompt = """You are an expert digital forensics analyst specializing in detecting photoshopped or manipulated certificates.

Analyze this certificate image for signs of digital manipulation such as:
1. Photoshopping or image editing
2. Text that appears pasted or overlaid
3. Inconsistent fonts, colors, or styles
4. Compression artifacts suggesting copy-paste manipulation
5. Misaligned elements or irregular spacing
6. Color inconsistencies or unnatural blending
7. Signs of template-based fake certificates

Provide your analysis in this EXACT JSON format:
{
    "authenticity_confidence": <float 0.0-1.0, your confidence that this is a GENUINE certificate>,
    "manipulation_detected": <boolean, true if you detect manipulation>,
    "risk_level": <string: "high", "medium", "low">,
    "evidence": [<list of specific visual evidence you observed>],
    "reasoning": "<brief explanation of your assessment>"
}

IMPORTANT: 
- authenticity_confidence should be HIGH (0.7-1.0) for genuine-looking certificates
- authenticity_confidence should be LOW (0.0-0.3) for suspicious/manipulated certificates
- Be thorough - look for subtle signs of editing
- List specific visual evidence you observe"""

            # Call Mistral Vision API (pixtral-12b model supports images)
            try:
                response = self.client.chat.complete(
                    model="pixtral-12b-2409",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            ]
                        }
                    ]
                )
            except Exception as api_error:
                logger.error(f"Mistral API call failed: {api_error}")
                # Return a safe default instead of crashing
                return ForensicsResult(
                    manipulation_score=0.0,
                    is_high_risk=False,
                    status=f"Error - Forensics analysis unavailable: {str(api_error)}",
                    details=["Mistral API call failed", str(api_error)],
                    llm_analysis="API Error",
                    llm_risk_score=None,
                    llm_confidence=0.0,
                    llm_reasoning="Unable to perform forensics analysis"
                )
            
            # Extract response
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"Mistral response: {response_text[:200]}...")
            
            # Parse JSON from response
            import json
            import re
            
            # Extract JSON from markdown code blocks if present
            if '```json' in response_text:
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
            elif '```' in response_text:
                json_match = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
            else:
                # Try to find JSON in the text
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
            
            try:
                analysis_result = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Mistral response as JSON: {e}")
                logger.error(f"Response text: {response_text}")
                return ForensicsResult(
                    manipulation_score=0.0,
                    is_high_risk=False,
                    status="Error - Could not parse AI response",
                    details=["JSON parsing failed", str(e)],
                    llm_analysis=response_text[:500],
                    llm_risk_score=None,
                    llm_confidence=0.0,
                    llm_reasoning="Failed to parse response"
                )
            
            # Extract values from analysis
            authenticity_confidence = float(analysis_result.get("authenticity_confidence", 0.5))
            manipulation_detected = bool(analysis_result.get("manipulation_detected", False))
            risk_level = str(analysis_result.get("risk_level", "medium")).lower()
            evidence = analysis_result.get("evidence", [])
            reasoning = str(analysis_result.get("reasoning", ""))
            
            # Calculate manipulation score (inverse of authenticity)
            # High authenticity (0.8) → Low manipulation (0.2)
            # Low authenticity (0.2) → High manipulation (0.8)
            manipulation_score = 1.0 - authenticity_confidence
            
            # CRITICAL LOGIC: Flag as high-risk when authenticity confidence is BELOW 0.30
            # This means the AI has low confidence the certificate is genuine
            is_high_risk = authenticity_confidence < 0.30 or manipulation_detected
            
            # Determine status message
            if is_high_risk:
                if authenticity_confidence < 0.30:
                    status = f"⚠️ HIGH RISK - Possible Photoshopped Certificate (Authenticity: {authenticity_confidence:.0%})"
                else:
                    status = f"⚠️ HIGH RISK - Manipulation Detected (Risk: {risk_level})"
            elif manipulation_score > 0.5:
                status = f"⚠️ WARNING - Minor Concerns (Authenticity: {authenticity_confidence:.0%})"
            else:
                status = f"✓ PASS - Certificate Appears Genuine (Authenticity: {authenticity_confidence:.0%})"
            
            # Build detailed evidence list
            details = [
                f"Authenticity Confidence: {authenticity_confidence:.2f} (Below 0.30 = High Risk)",
                f"Manipulation Score: {manipulation_score:.2f}",
                f"Risk Level: {risk_level}",
                f"Manipulation Detected: {manipulation_detected}"
            ]
            
            if evidence:
                details.append("Visual Evidence:")
                details.extend([f"  • {item}" for item in evidence[:10]])  # Limit to 10 items
            
            logger.info(
                f"✓ Forensics complete: authenticity={authenticity_confidence:.2f}, "
                f"is_high_risk={is_high_risk}, manipulation_detected={manipulation_detected}"
            )
            
            return ForensicsResult(
                manipulation_score=float(round(manipulation_score, 2)),
                is_high_risk=is_high_risk,
                status=status,
                details=details,
                llm_analysis=json.dumps(analysis_result, indent=2),
                llm_risk_score=float(round(manipulation_score, 2)),
                llm_confidence=float(round(authenticity_confidence, 2)),
                llm_reasoning=reasoning
            )
        
        except Exception as e:
            logger.error(f"Forensics analysis error: {e}", exc_info=True)
            return ForensicsResult(
                manipulation_score=0.0,
                is_high_risk=False,
                status=f"Error analyzing certificate: {str(e)}",
                details=[f"Error: {str(e)}"],
                llm_analysis=None,
                llm_risk_score=None,
                llm_confidence=0.0,
                llm_reasoning="Analysis failed due to error"
            )