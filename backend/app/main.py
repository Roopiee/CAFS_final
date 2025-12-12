"""
app/main.py
Main API application entry point.
"""
import io
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pdf2image import convert_from_bytes

# Import Config
from app.config import config

# Import Schemas
from app.schemas import (
    CertificateAnalysisResponse, 
    ExtractionResult, 
    VerificationResult
)

# Import Agents
# Assumes you have these files for Forensics and Extraction
from app.agents.forensics import ForensicsAgent
from app.agents.ext import ExtractionAgent

# --- KEY CHANGE: Import from the new service architecture ---
from app.agents.verification.service import get_verification_service

# Initialize Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=config.LOG_LEVEL)

app = FastAPI(title="Multi-Agent Certificate Verifier")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents
# (Replace API keys with env variables in production!)
forensics_agent = ForensicsAgent(api_key="nJpjawyHlBoqUrTBSxtOE2oA2KytRL2Y")
extraction_agent = ExtractionAgent(api_key="nJpjawyHlBoqUrTBSxtOE2oA2KytRL2Y")

# Initialize the new Verification Service
verification_service = get_verification_service()


@app.post("/verify", response_model=CertificateAnalysisResponse)
async def verify_certificate(file: UploadFile = File(...)):
    """
    Orchestrates the workflow:
    1. Forensics (ELA/Photoshop Detection)
    2. Extraction (OCR)
    3. Verification (URL & Domain Check via Playwright/Httpx)
    """
    
    # 1. File Pre-processing
    file_bytes = await file.read()
    image_bytes = None

    if file.content_type == "application/pdf":
        try:
            # Convert first page of PDF to Image
            images = convert_from_bytes(file_bytes)
            if not images:
                raise HTTPException(status_code=400, detail="PDF is empty or unreadable.")
            
            img_byte_arr = io.BytesIO()
            images[0].save(img_byte_arr, format='PNG')
            image_bytes = img_byte_arr.getvalue()
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process PDF: {str(e)}")

    elif file.content_type.startswith("image/"):
        image_bytes = file_bytes
    
    else:
        raise HTTPException(status_code=400, detail="File must be an image (JPEG/PNG) or a PDF.")

    try:
        # --- STAGE 1: FORENSICS ---
        # Run CPU-bound task in threadpool
        forensics_data = await run_in_threadpool(forensics_agent.analyze, image_bytes)
        
        # --- STAGE 2: EXTRACTION ---
        extraction_data = await extraction_agent.extract(image_bytes)
        
        # Validate extraction data using Pydantic Schema
        extraction_result = ExtractionResult(**extraction_data)

        # --- STAGE 3: VERIFICATION ---
        # Call the new service's verify method
        verification_result = await verification_service.verify(extraction_result)

        # --- STAGE 4: FINAL VERDICT ---
        final_verdict = "UNVERIFIED"

        if forensics_data.is_high_risk:
            final_verdict = "FLAGGED (High Risk)"
        elif verification_result.is_verified:
            final_verdict = "VERIFIED"
        else:
            final_verdict = "UNVERIFIED"

        return CertificateAnalysisResponse(
            filename=file.filename,
            final_verdict=final_verdict,
            forensics=forensics_data,
            extraction=extraction_result,
            verification=verification_result
        )

    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(e)}")
    except TimeoutError as e:
        logger.error(f"Timeout Error: {e}")
        raise HTTPException(status_code=504, detail="Processing timed out.")
    except Exception as e:
        logger.error(f"System Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")