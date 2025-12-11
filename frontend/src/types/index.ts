// Backend Schema Types - Matching app/schemas.py

export interface ForensicsResult {
    manipulation_score: number;
    is_high_risk: boolean;
    status: string;
    details?: string[] | null;
    llm_analysis?: string | null;
    llm_risk_score?: number | null;
    llm_confidence?: number | null;
    llm_reasoning?: string | null;
}

export interface ExtractionResult {
    candidate_name?: string | null;
    certificate_id?: string | null;
    issuer_url?: string | null;
    issuer_name?: string | null;
    issuer_org?: string | null;
    raw_text_snippet?: string | null;
    certificate_date?: string | null;
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
