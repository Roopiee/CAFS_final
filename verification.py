# """
# verification.py
# Service layer or API endpoint for certificate verification
# """

# import logging
# from typing import Optional
# from fastapi import HTTPException

# from app.agents.verificationagent import VerificationAgent
# from app.schemas import ExtractionResult, VerificationResult
# from app.config import config

# logger = logging.getLogger(__name__)
# logger.setLevel(config.LOG_LEVEL)

# # Global agent instance (initialized once)
# _verification_agent: Optional[VerificationAgent] = None


# def get_verification_agent(use_playwright: bool = True) -> VerificationAgent:
#     """
#     Get or create the verification agent singleton
    
#     Args:
#         use_playwright: Whether to enable Playwright for JS-heavy pages
        
#     Returns:
#         VerificationAgent instance
#     """
#     global _verification_agent
    
#     if _verification_agent is None:
#         logger.info("Initializing verification agent...")
#         _verification_agent = VerificationAgent(
#             csv_path=config.CSV_PATH,
#             use_playwright=use_playwright
#         )
    
#     return _verification_agent


# async def verify_certificate(extraction_data: ExtractionResult) -> VerificationResult:
#     """
#     Main service function to verify a certificate
    
#     Args:
#         extraction_data: Extracted certificate data from OCR/Mistral
        
#     Returns:
#         VerificationResult with verification status
        
#     Raises:
#         HTTPException: If verification fails critically
#     """
#     try:
#         agent = get_verification_agent()
        
#         # Validate input
#         if not extraction_data.candidate_name:
#             logger.warning("No candidate name in extraction data")
#             return VerificationResult(
#                 is_verified=False,
#                 message="Cannot verify: No candidate name extracted from certificate.",
#                 trusted_domain=False
#             )
        
#         # Perform verification
#         result = await agent.verify(extraction_data)
        
#         logger.info(
#             f"Verification result for {extraction_data.candidate_name}: "
#             f"verified={result.is_verified}, trusted={result.trusted_domain}"
#         )
        
#         return result
        
#     except Exception as e:
#         logger.error(f"Critical error during verification: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail=f"Verification service error: {str(e)}"
#         )


# async def batch_verify_certificates(
#     extraction_results: list[ExtractionResult]
# ) -> list[VerificationResult]:
#     """
#     Verify multiple certificates in batch
    
#     Args:
#         extraction_results: List of extraction results to verify
        
#     Returns:
#         List of verification results
#     """
#     results = []
    
#     for extraction in extraction_results:
#         try:
#             result = await verify_certificate(extraction)
#             results.append(result)
#         except Exception as e:
#             logger.error(f"Error verifying certificate: {e}")
#             results.append(
#                 VerificationResult(
#                     is_verified=False,
#                     message=f"Verification error: {str(e)}",
#                     trusted_domain=False
#                 )
#             )
    
#     return results


# def reload_trusted_sources():
#     """
#     Reload trusted sources from CSV (useful after CSV updates)
#     """
#     global _verification_agent
    
#     if _verification_agent:
#         logger.info("Reloading trusted sources...")
#         _verification_agent.org_map, _verification_agent.trusted_domains = (
#             _verification_agent._load_trusted_sources()
#         )
#         logger.info("Trusted sources reloaded successfully")
#     else:
#         logger.warning("Verification agent not initialized yet")


# def add_trusted_organization(org_name: str, verification_url: str):
#     """
#     Dynamically add a trusted organization
    
#     Args:
#         org_name: Organization name
#         verification_url: Base verification URL
#     """
#     agent = get_verification_agent()
#     agent.add_organization(org_name, verification_url)
#     logger.info(f"Added trusted organization: {org_name}")
