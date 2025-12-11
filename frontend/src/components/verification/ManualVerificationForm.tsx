'use client';

import React, { useState } from 'react';
import { AlertCircle, Loader2, CheckCircle } from 'lucide-react';
import { verificationService } from '@/services/api';
import { CertificateAnalysisResponse } from '@/types';

interface ManualVerificationFormProps {
  onVerificationComplete?: (data: CertificateAnalysisResponse) => void;
}

export default function ManualVerificationForm({ onVerificationComplete }: ManualVerificationFormProps) {
  const [certificateId, setCertificateId] = useState('');
  const [issuerUrl, setIssuerUrl] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!certificateId.trim() || !issuerUrl.trim()) {
      setError('Both Certificate ID and Issuer URL are required.');
      return;
    }

    setIsVerifying(true);
    setError(null);

    try {
      const result = await verificationService.manualVerify({
        certificate_id: certificateId,
        issuer_url: issuerUrl,
      });
      
      if (onVerificationComplete) {
        onVerificationComplete(result);
      }
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please try again.');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      
      {/* Info Header */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5 mb-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-yellow-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-yellow-900 mb-1">Manual Verification Required</h3>
            <p className="text-sm text-yellow-800">
              We couldn't automatically verify this certificate. Please provide the certificate ID 
              and issuer URL manually to complete verification.
            </p>
          </div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 space-y-5">
        
        {/* Certificate ID Input */}
        <div>
          <label htmlFor="certificate-id" className="block text-sm font-medium text-gray-700 mb-2">
            Certificate ID <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="certificate-id"
            value={certificateId}
            onChange={(e) => setCertificateId(e.target.value)}
            placeholder="e.g., ABC123456789"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            disabled={isVerifying}
          />
          <p className="mt-1 text-xs text-gray-500">Enter the unique certificate identifier</p>
        </div>

        {/* Issuer URL Input */}
        <div>
          <label htmlFor="issuer-url" className="block text-sm font-medium text-gray-700 mb-2">
            Issuer URL <span className="text-red-500">*</span>
          </label>
          <input
            type="url"
            id="issuer-url"
            value={issuerUrl}
            onChange={(e) => setIssuerUrl(e.target.value)}
            placeholder="e.g., https://coursera.org/verify/ABC123456789"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            disabled={isVerifying}
          />
          <p className="mt-1 text-xs text-gray-500">Full verification URL from the certificate issuer</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-red-50 text-red-600 text-sm rounded-md flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isVerifying || !certificateId.trim() || !issuerUrl.trim()}
          className={`
            w-full flex items-center justify-center gap-2 py-3 px-6 rounded-lg font-medium text-white transition-all
            ${isVerifying || !certificateId.trim() || !issuerUrl.trim()
              ? 'bg-gray-300 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'}
          `}
        >
          {isVerifying ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Verifying...
            </>
          ) : (
            <>
              <CheckCircle className="w-5 h-5" />
              Verify Certificate
            </>
          )}
        </button>
      </form>
    </div>
  );
}
