const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface CertificateAnalysisResponse {
  filename: string;
  final_verdict: string;
  forensics: {
    manipulation_score: number;
    is_high_risk: boolean;
    status: string;
    details: string[];
    llm_analysis?: string | null;
    llm_risk_score?: number | null;
    llm_confidence?: number | null;
    llm_reasoning?: string | null;
  };
  extraction: {
    candidate_name: string | null;
    certificate_id: string | null;
    issuer_name: string | null;
    issuer_url: string | null;
    issuer_org?: string | null;
    raw_text_snippet?: string | null;
    certificate_date?: string | null;
  };
  verification: {
    is_verified: boolean;
    message: string;
    trusted_domain: boolean;
  };
}

export const verificationService = {
  async uploadCertificate(file: File): Promise<CertificateAnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/verify`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        // Try to get error details from response
        const error = await response.json().catch(() => ({ 
          detail: `Server returned ${response.status}` 
        }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }

      const data: CertificateAnalysisResponse = await response.json();
      return data;
      
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to connect to verification server. Please ensure the backend is running.');
    }
  },

  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/docs`);
      return response.ok;
    } catch {
      return false;
    }
  }
};