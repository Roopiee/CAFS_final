'use client';

import React from 'react';
import { useSearchParams } from 'next/navigation';
import { CertificateAnalysisResponse } from '@/types';

export default function ValidationCertificatePage() {
  const searchParams = useSearchParams();
  const dataParam = searchParams.get('data');
  
  let data: CertificateAnalysisResponse | null = null;
  
  if (dataParam) {
    try {
      // Decode from Base64
      const decodedString = atob(dataParam);
      data = JSON.parse(decodedString);
    } catch (error) {
      console.error('Error decoding certificate data:', error);
    }
  }

  // Alternative: Try to get from sessionStorage if not in URL
  if (!data) {
    try {
      const storedResult = sessionStorage.getItem('verificationResult');
      if (storedResult) {
        data = JSON.parse(storedResult);
      }
    } catch (error) {
      console.error('Error reading from sessionStorage:', error);
    }
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <p className="text-gray-600 mb-4">No certificate data available</p>
          <a href="/" className="text-blue-600 hover:underline">
            Go back to upload
          </a>
        </div>
      </div>
    );
  }

  const verificationDate = new Date().toLocaleDateString('en-US', { 
    day: 'numeric', 
    month: 'long', 
    year: 'numeric' 
  });
  
  const expiryDate = new Date(Date.now() + 3 * 365 * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { 
    day: 'numeric', 
    month: 'long', 
    year: 'numeric' 
  });

  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(data.extraction.issuer_url || 'https://skillkendra.com')}`;

  // Determine status color
  const getStatusColor = () => {
    if (data.final_verdict === 'VERIFIED') return 'text-emerald-600 bg-emerald-100';
    if (data.final_verdict === 'UNVERIFIED') return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <html lang="en">
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>SkillKendra Verification Certificate</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet" />
        <style dangerouslySetInnerHTML={{ __html: `
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
          body {
            font-family: 'Inter', sans-serif;
          }
          .bg-pattern {
            background-color: #f8fafc;
            background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
            background-size: 20px 20px;
          }
          @media print {
            .no-print { display: none; }
          }
        `}} />
      </head>
      <body className="bg-gray-100 min-h-screen flex items-center justify-center p-4">
        <div className="bg-white w-full max-w-5xl shadow-2xl rounded-2xl overflow-hidden flex flex-col md:flex-row">
          
          {/* LEFT SIDE: Verification Sidebar */}
          <div className="w-full md:w-1/3 bg-slate-900 text-white p-8 flex flex-col items-center text-center relative overflow-hidden">
            
            {/* Decorative circles */}
            <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
              <div className="absolute -top-24 -left-24 w-64 h-64 bg-blue-500 rounded-full blur-3xl"></div>
              <div className="absolute bottom-0 right-0 w-64 h-64 bg-indigo-500 rounded-full blur-3xl"></div>
            </div>

            <div className="relative z-10 flex flex-col items-center w-full h-full">
              
              {/* QR Code */}
              <div className="bg-white p-3 rounded-xl shadow-lg mb-6 transform hover:scale-105 transition-transform duration-300">
                <img 
                  src={qrCodeUrl}
                  alt="Verification QR Code" 
                  className="w-40 h-40 object-contain"
                />
              </div>

              {/* Tagline */}
              <div className="mb-8">
                <div className="flex items-center justify-center space-x-2 text-emerald-400 mb-2">
                  <i className="fas fa-check-circle text-xl"></i>
                  <span className="font-bold tracking-wide uppercase text-sm">Official Document</span>
                </div>
                <h2 className="text-lg font-semibold text-slate-100 leading-tight">
                  Verified and Authenticated by <span className="text-blue-400">SkillKendra</span>
                </h2>
              </div>

              <div className="w-full border-t border-slate-700 mb-8"></div>

              {/* Verification Details */}
              <div className="w-full space-y-5 text-left text-sm">
                
                <div className="group">
                  <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Date of Verification</p>
                  <p className="font-medium text-slate-100 flex items-center">
                    <i className="far fa-calendar-check mr-2 text-blue-400"></i> {verificationDate}
                  </p>
                </div>

                <div className="group">
                  <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Expiry Date</p>
                  <p className="font-medium text-slate-100 flex items-center">
                    <i className="far fa-clock mr-2 text-orange-400"></i> {expiryDate}
                  </p>
                </div>

                {data.extraction.certificate_id && (
                  <div className="group">
                    <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Certificate ID</p>
                    <div className="bg-slate-800 p-2 rounded border border-slate-700">
                      <p className="font-mono text-xs text-yellow-400 break-all select-all">
                        {data.extraction.certificate_id}
                      </p>
                    </div>
                  </div>
                )}

                {data.extraction.issuer_url && (
                  <div className="group">
                    <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Verification URL</p>
                    <a 
                      href={data.extraction.issuer_url} 
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 transition-colors flex items-center text-xs break-all"
                    >
                      <i className="fas fa-link mr-2 flex-shrink-0"></i> 
                      <span className="break-all">{data.extraction.issuer_url}</span>
                    </a>
                  </div>
                )}

                {(data.extraction.issuer_name || data.extraction.issuer_org) && (
                  <div className="group">
                    <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Issuing Organization</p>
                    <p className="text-blue-400 flex items-center">
                      <i className="fas fa-building mr-2 text-xs"></i> 
                      {data.extraction.issuer_name || data.extraction.issuer_org}
                    </p>
                  </div>
                )}

                {/* Forensics Summary */}
                <div className="group">
                  <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Forensics Analysis</p>
                  <div className="bg-slate-800 p-2 rounded border border-slate-700">
                    <p className={`text-xs font-medium ${data.forensics.is_high_risk ? 'text-red-400' : 'text-green-400'}`}>
                      {data.forensics.status}
                    </p>
                    <p className="text-slate-300 text-xs mt-1">
                      Manipulation Score: {(data.forensics.manipulation_score * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="mt-auto pt-8 opacity-50">
                <p className="text-xs">Secure Verification System v2.0</p>
              </div>
            </div>
          </div>

          {/* RIGHT SIDE: Certificate Context */}
          <div className="w-full md:w-2/3 bg-pattern p-8 md:p-12 flex flex-col">
            
            {/* Header */}
            <div className="flex justify-between items-start mb-12">
              <div>
                <h1 className="text-3xl font-bold text-slate-800 mb-2">Certificate of Verification</h1>
                <p className="text-slate-500">
                  This document certifies that the credential has been {data.final_verdict.toLowerCase()}.
                </p>
              </div>
              <div className="hidden sm:flex items-center justify-center w-16 h-16 bg-blue-600 text-white rounded-lg shadow-md font-bold text-2xl">
                SK
              </div>
            </div>

            {/* Certificate Details */}
            <div className="space-y-6 mb-12">
              {data.extraction.candidate_name && (
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">Issued To</label>
                  <p className="text-2xl font-serif text-slate-900">{data.extraction.candidate_name}</p>
                </div>
              )}
              
              {(data.extraction.issuer_name || data.extraction.issuer_org) && (
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">Issuing Organization</label>
                  <p className="text-xl text-slate-700">
                    {data.extraction.issuer_name || data.extraction.issuer_org}
                  </p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Verification Status</label>
                <p className="text-base text-slate-700 leading-relaxed">{data.verification.message}</p>
              </div>

              {/* Domain Trust Badge */}
              {data.verification.trusted_domain && (
                <div className="flex items-center gap-2 text-sm">
                  <div className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full">
                    <i className="fas fa-shield-alt"></i>
                    <span className="font-medium">Trusted Domain</span>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="mt-auto border-t border-slate-200 pt-6 flex flex-col sm:flex-row justify-between items-center text-sm text-slate-500 gap-4">
              <p>
                Status: <span className={`font-bold px-2 py-0.5 rounded ${getStatusColor()}`}>
                  {data.final_verdict}
                </span>
              </p>
              {data.extraction.certificate_id && (
                <p className="font-mono text-xs">ID: {data.extraction.certificate_id}</p>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 mt-6 no-print">
              <button 
                onClick={() => window.print()}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors text-sm font-medium"
              >
                <i className="fas fa-print mr-2"></i>
                Print Certificate
              </button>
              <a 
                href="/"
                className="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-700 py-2 px-4 rounded-lg transition-colors text-sm font-medium text-center"
              >
                <i className="fas fa-home mr-2"></i>
                Back to Home
              </a>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}