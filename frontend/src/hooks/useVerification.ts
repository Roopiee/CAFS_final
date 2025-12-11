'use client';

import { useState } from 'react';
import { verificationService } from '@/services/api';
import { CertificateAnalysisResponse } from '@/types';

export function useVerification() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const verify = async (file: File): Promise<CertificateAnalysisResponse | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await verificationService.uploadCertificate(file);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Verification failed';
      setError(errorMessage);
      console.error('Verification error:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  return { verify, isLoading, error, clearError };
}