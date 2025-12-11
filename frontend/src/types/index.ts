// Backend Schema Types - Matching app/schemas.py

export interface ForensicsResult {
    manipulation_score: number;
    is_high_risk: boolean;
    status: string;
    details?: string[];
    llm_analysis?: string;
    llm_risk_score?: number;
    llm_confidence?: number;
    llm_reasoning?: string;
}

export interface ExtractionResult {
    candidate_name?: string;
    certificate_id?: string;
    issuer_url?: string;
    issuer_org?: string;
    raw_text_snippet?: string;
}

export interface VerificationResult {
    is_verified: boolean;
    message: string;
    trusted_domain: boolean;
}

export interface CertificateAnalysisResponse {
    filename: string;
    final_verdict: string;
    forensics: ForensicsResult;
    extraction: ExtractionResult;
    verification: VerificationResult;
}

// Manual Verification Types
export interface ManualVerificationRequest {
    certificate_id: string;
    issuer_url: string;
}

export interface ApiError {
    detail: string;
}
