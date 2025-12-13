'use client';

import React, { useState } from 'react';
import { AlertCircle, Loader2, CheckCircle, ArrowRight } from 'lucide-react';
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
    <div className="w-full max-w-xl mx-auto p-4">
      
      {/* Modern Info Header */}
      <div className="bg-amber-50 border-l-4 border-amber-500 rounded-r-lg p-5 mb-8 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="p-2 bg-amber-100 rounded-full shrink-0">
            <AlertCircle className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900 text-lg">Manual Verification Required</h3>
            <p className="text-slate-600 mt-1 leading-relaxed">
              We couldn't automatically verify this certificate. Please enter the details manually below.
            </p>
          </div>
        </div>
      </div>

      {/* Card Form */}
      <form 
        onSubmit={handleSubmit} 
        className="bg-white rounded-2xl shadow-xl shadow-slate-200/60 border border-slate-100 p-8 space-y-6"
      >
        <div className="space-y-6">
          {/* Certificate ID Input */}
          <div className="group">
            <label htmlFor="certificate-id" className="block text-sm font-semibold text-slate-700 mb-2">
              Certificate ID
            </label>
            <div className="relative">
              <input
                type="text"
                id="certificate-id"
                value={certificateId}
                onChange={(e) => setCertificateId(e.target.value)}
                placeholder="e.g., ABC123456789"
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-200 outline-none placeholder:text-slate-400"
                disabled={isVerifying}
              />
            </div>
            <p className="mt-2 text-xs text-slate-500 flex items-center gap-1">
              <ArrowRight className="w-3 h-3" /> The unique ID found on the certificate
            </p>
          </div>

          {/* Issuer URL Input */}
          <div className="group">
            <label htmlFor="issuer-url" className="block text-sm font-semibold text-slate-700 mb-2">
              Issuer Verification URL
            </label>
            <input
              type="url"
              id="issuer-url"
              value={issuerUrl}
              onChange={(e) => setIssuerUrl(e.target.value)}
              placeholder="e.g., https://coursera.org/verify/..."
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-200 outline-none placeholder:text-slate-400"
              disabled={isVerifying}
            />
            <p className="mt-2 text-xs text-slate-500 flex items-center gap-1">
              <ArrowRight className="w-3 h-3" /> The direct link to verify this credential
            </p>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-100 text-red-600 text-sm rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isVerifying || !certificateId.trim() || !issuerUrl.trim()}
          className={`
            w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl font-semibold text-white text-sm tracking-wide transition-all duration-200
            ${isVerifying || !certificateId.trim() || !issuerUrl.trim()
              ? 'bg-slate-300 cursor-not-allowed opacity-70' 
              : 'bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-600/20 hover:shadow-xl hover:shadow-blue-600/30 active:scale-[0.98]'}
          `}
        >
          {isVerifying ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Verifying details...
            </>
          ) : (
            <>
              Verify Certificate
              <CheckCircle className="w-5 h-5" />
            </>
          )}
        </button>
      </form>
    </div>
  );
}