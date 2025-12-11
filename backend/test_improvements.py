import asyncio
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock

import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)

from app.agents.extraction import ExtractionAgent
from app.agents.verification import VerificationAgent
from app.schemas import ExtractionResult

async def test_extraction_verification():
    print("="*70)
    print("TESTING IMPROVEMENTS")
    print("="*70)

    # 1. Test Extraction Agent
    print("\n1. Testing ExtractionAgent...")
    extraction_agent = ExtractionAgent()
    
    # Mock pytesseract to return sample text
    sample_text = """
    CERTIFICATE OF COMPLETION
    This is to certify that
    John Doe
    has successfully completed the course
    Python for Beginners
    on Coursera
    Certificate ID: 1234567890
    https://coursera.org/verify/1234567890
    """
    
    with patch('app.agents.extraction.pytesseract.image_to_string', return_value=sample_text):
        with patch('app.agents.extraction.Image.open', return_value=MagicMock()):
            # Pass dummy bytes
            result = extraction_agent.extract(b"dummy_bytes")
            
            print(f"   Candidate Name: {result.candidate_name}")
            print(f"   Certificate ID: {result.certificate_id}")
            print(f"   Issuer Org: {result.issuer_org}")
            print(f"   Issuer URL: {result.issuer_url}")
            
            if result.candidate_name == "John Doe" and result.certificate_id == "1234567890" and result.issuer_org == "Coursera":
                print("   ✅ Extraction Logic Passed")
            else:
                print("   ❌ Extraction Logic Failed")

    # 2. Test Verification Agent
    print("\n2. Testing VerificationAgent (Async)...")
    verification_agent = VerificationAgent()
    
    # Mock httpx.AsyncClient
    with patch('app.agents.verification.httpx.AsyncClient') as mock_client:
        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_get.text = "John Doe has completed..."
        
        # Setup AsyncMock
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_get
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        
        mock_client.return_value = mock_client_instance
        
        verification_result = await verification_agent.verify(result)
        
        print(f"   Verified: {verification_result.is_verified}")
        print(f"   Message: {verification_result.message}")
        
        if verification_result.is_verified:
            print("   ✅ Verification Logic Passed")
        else:
            print("   ❌ Verification Logic Failed")

if __name__ == "__main__":
    asyncio.run(test_extraction_verification())
