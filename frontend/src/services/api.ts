import type { CertificateAnalysisResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

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