"""
app/schemas.py
Pydantic models for data validation and API responses.
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Union
from enum import Enum
from difflib import SequenceMatcher

# --- Enums ---
class IssuerName(str, Enum):
    coursera = "Coursera"
    edx = "edX"
    udemy = "Udemy"
    linkedin_learning = "LinkedIn Learning"
    futurelearn = "FutureLearn"
    udacity = "Udacity"
    alison = "Alison"
    great_learning = "Great Learning"
    simplilearn = "Simplilearn"
    pluralsight = "Pluralsight"
    skillshare = "Skillshare"
    masterclass = "MasterClass"
    codecademy = "Codecademy"
    freecodecamp = "freeCodeCamp"
    swayam = "SWAYAM"
    nptel = "NPTEL"
    openlearn = "OpenLearn"
    khan_academy = "Khan Academy"
    upgrad = "upGrad"
    shaw_academy = "Shaw Academy"
    open_universities_australia = "Open Universities Australia"
    training_360 = "360Training"
    careerfoundry = "CareerFoundry"
    simpliaxis = "Simpliaxis"
    knowledgehut = "Knowledgehut"
    cognitive_class_ibm = "Cognitive Class (IBM)"
    w3schools = "W3Schools"
    google_skillshop = "Google Skillshop"
    ibm = "IBM"
    microsoft = "Microsoft"
    aws = "AWS"
    hubspot_academy = "HubSpot Academy"
    meta = "Meta"
    adobe = "Adobe"
    salesforce_trailhead = "Salesforce Trailhead"
    cisco = "Cisco"
    comptia = "CompTIA"
    oracle = "Oracle"
    sap = "SAP"
    palo_alto_networks = "Palo Alto Networks"
    semrush_academy = "Semrush Academy"
    apple = "Apple"
    intel = "Intel"
    sas = "SAS"
    tableau = "Tableau"
    deeplearning_ai = "DeepLearning.AI"
    pmi = "PMI"
    isaca = "ISACA"
    isc2 = "(ISC)²"
    red_hat = "Red Hat"
    vmware = "VMware"
    who = "WHO"
    linux_foundation = "Linux Foundation"
    british_council = "British Council"
    acca = "ACCA"
    cima = "CIMA"
    unicef = "UNICEF"

# --- Helper Logic ---
def fuzzy_match_issuer(raw_issuer: str):
    """
    Attempts to match a raw string to a known IssuerName enum.
    Returns the Enum member if confidence > 0.6, else None.
    """
    if not raw_issuer:
        return None

    cleaned = raw_issuer.strip().lower()

    def similarity(a, b):
        return SequenceMatcher(None, a, b).ratio()

    best = None
    best_score = 0

    for item in IssuerName:
        score = similarity(cleaned, item.value.lower())
        if score > best_score:
            best_score = score
            best = item

    return best if best_score >= 0.6 else None

# --- Core Models ---

class ForensicsResult(BaseModel):
    manipulation_score: float
    is_high_risk: bool
    status: str
    details: Optional[List[str]] = []
    # LLM Analysis Fields
    llm_analysis: Optional[str] = None
    llm_risk_score: Optional[float] = None
    llm_confidence: Optional[float] = None
    llm_reasoning: Optional[str] = None

class ExtractionResult(BaseModel):
    candidate_name: Optional[str] = None
    certificate_id: Optional[str] = None
    
    # Can be the Enum OR None
    issuer_name: Optional[IssuerName] = None

    @field_validator("issuer_name", mode="before")
    def validate_issuer(cls, value):
        """Auto-converts string input to Enum using fuzzy matching"""
        if isinstance(value, IssuerName):
            return value
        if value is None:
            return None
        return fuzzy_match_issuer(str(value))

    issuer_url: Optional[str] = None
    issuer_org: Optional[str] = None
    raw_text_snippet: Optional[str] = None 
    certificate_date: Optional[str] = None 

class VerificationResult(BaseModel):
    is_verified: bool
    trusted_domain: bool
    confidence_score: float = 0.0      # NEW: 0.0 to 1.0 (How close was the match?)
    verification_url: Optional[str] = None  # NEW: The exact link checked (clickable for user)
    method: str = "none"               # NEW: "exact_match", "fuzzy_match", "domain_only", "failed"
    message: str

class CertificateAnalysisResponse(BaseModel):
    filename: str
    final_verdict: str
    forensics: ForensicsResult
    extraction: ExtractionResult
    verification: VerificationResult

class ManualVerificationRequest(BaseModel):
    certificate_id: str
    issuer_url: str