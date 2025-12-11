import io
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pdf2image import convert_from_bytes
from app.config import config

# Import Schemas
from app.schemas import (
    CertificateAnalysisResponse, 
    ForensicsResult, 
    ExtractionResult, 
    VerificationResult
)

# Import Agents
from app.agents.forensics import ForensicsAgent
from app.agents.ext import ExtractionAgent
from app.agents.verification import get_verification_agent

app = FastAPI(title="Multi-Agent Certificate Verifier")

# ← ADD CORS MIDDLEWARE HERE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)

# Initialize Agents
forensics_agent = ForensicsAgent(api_key="nJpjawyHlBoqUrTBSxtOE2oA2KytRL2Y")
extraction_agent = ExtractionAgent(api_key="nJpjawyHlBoqUrTBSxtOE2oA2KytRL2Y")
verification_agent = get_verification_agent()


@app.post("/verify", response_model=CertificateAnalysisResponse)
async def verify_certificate(file: UploadFile = File(...)):
    """
    Orchestrates the workflow:
    1. Forensics (ELA/Photoshop Detection)
    2. Extraction (OCR)
    3. Verification (URL & Domain Check)
    """
    
    # 1. Read the raw file bytes
    file_bytes = await file.read()
    
    image_bytes = None

    # 2. Pre-processing: Handle PDF vs Image
    if file.content_type == "application/pdf":
        try:
            # Convert first page of PDF to Image
            images = convert_from_bytes(file_bytes)
            if not images:
                raise HTTPException(status_code=400, detail="PDF is empty or unreadable.")
            
            # Save the PIL image to a byte stream to mimic a standard image upload
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
        # --- STAGE 1: FORENSICS (Check for Photoshop) ---
        # Run in threadpool to prevent blocking the server
        forensics_data = await run_in_threadpool(forensics_agent.analyze, image_bytes)
        
        # --- STAGE 2: EXTRACTION (OCR) ---
        # extract() is now async, so we call it directly
        extraction_data = await extraction_agent.extract(image_bytes)

        # Convert dict to ExtractionResult object
        extraction_result = ExtractionResult(**extraction_data)

        # --- STAGE 3: VERIFICATION (URL Check) ---
        verification_result = await verification_agent.verify(extraction_result)

        # --- STAGE 4: FINAL VERDICT LOGIC ---
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
        # Validation errors from extraction
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except TimeoutError as e:
        # Timeout errors from extraction or verification
        logger.error(f"Timeout error: {e}")
        raise HTTPException(status_code=504, detail=f"Request timeout: {str(e)}")
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")