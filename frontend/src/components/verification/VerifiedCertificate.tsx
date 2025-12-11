'use client';

import React from 'react';
import { CheckCircle, Download, User, Hash, Building, Link as LinkIcon, ExternalLink } from 'lucide-react';
import { CertificateAnalysisResponse } from '@/types';

interface VerifiedCertificateProps {
  data: CertificateAnalysisResponse;
}

export default function VerifiedCertificate({ data }: VerifiedCertificateProps) {
  
  const handleViewCertificate = () => {
    // Encode data as Base64 and open in new tab
    const jsonString = JSON.stringify(data);
    const base64Data = btoa(jsonString);
    window.open(`/validation-certificate?data=${base64Data}`, '_blank');
  };

  const handleDownload = () => {
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

    const certificateHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkillKendra Verification Certificate</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; }
        .bg-pattern {
            background-color: #f8fafc;
            background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
            background-size: 20px 20px;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white w-full max-w-5xl shadow-2xl rounded-2xl overflow-hidden flex flex-col md:flex-row">
        <div class="w-full md:w-1/3 bg-slate-900 text-white p-8 flex flex-col items-center text-center relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
                <div class="absolute -top-24 -left-24 w-64 h-64 bg-blue-500 rounded-full blur-3xl"></div>
                <div class="absolute bottom-0 right-0 w-64 h-64 bg-indigo-500 rounded-full blur-3xl"></div>
            </div>
            <div class="relative z-10 flex flex-col items-center w-full h-full">
                <div class="bg-white p-3 rounded-xl shadow-lg mb-6 transform hover:scale-105 transition-transform duration-300">
                    <img src="${qrCodeUrl}" alt="Verification QR Code" class="w-40 h-40 object-contain">
                </div>
                <div class="mb-8">
                    <div class="flex items-center justify-center space-x-2 text-emerald-400 mb-2">
                        <i class="fas fa-check-circle text-xl"></i>
                        <span class="font-bold tracking-wide uppercase text-sm">Official Document</span>
                    </div>
                    <h2 class="text-lg font-semibold text-slate-100 leading-tight">
                        Verified and Authenticated by <span class="text-blue-400">SkillKendra</span>
                    </h2>
                </div>
                <div class="w-full border-t border-slate-700 mb-8"></div>
                <div class="w-full space-y-5 text-left text-sm">
                    <div class="group">
                        <p class="text-slate-400 text-xs uppercase tracking-wider mb-1">Date of Verification</p>
                        <p class="font-medium text-slate-100 flex items-center">
                            <i class="far fa-calendar-check mr-2 text-blue-400"></i> ${verificationDate}
                        </p>
                    </div>
                    <div class="group">
                        <p class="text-slate-400 text-xs uppercase tracking-wider mb-1">Expiry Date</p>
                        <p class="font-medium text-slate-100 flex items-center">
                            <i class="far fa-clock mr-2 text-orange-400"></i> ${expiryDate}
                        </p>
                    </div>
                    ${data.extraction.certificate_id ? `
                    <div class="group">
                        <p class="text-slate-400 text-xs uppercase tracking-wider mb-1">CFT ID</p>
                        <div class="bg-slate-800 p-2 rounded border border-slate-700">
                            <p class="font-mono text-xs text-yellow-400 break-all select-all">
                                #${data.extraction.certificate_id}
                            </p>
                        </div>
                    </div>` : ''}
                    ${data.extraction.issuer_url ? `
                    <div class="group">
                        <p class="text-slate-400 text-xs uppercase tracking-wider mb-1">CFT URL</p>
                        <a href="${data.extraction.issuer_url}" class="text-blue-400 hover:text-blue-300 transition-colors flex items-center truncate">
                            <i class="fas fa-link mr-2 text-xs"></i> ${data.extraction.issuer_url}
                        </a>
                    </div>` : ''}
                    ${data.extraction.issuer_org ? `
                    <div class="group">
                        <p class="text-slate-400 text-xs uppercase tracking-wider mb-1">Organization</p>
                        <p class="text-blue-400 flex items-center truncate">
                            <i class="fas fa-globe mr-2 text-xs"></i> ${data.extraction.issuer_org}
                        </p>
                    </div>` : ''}
                </div>
                <div class="mt-auto pt-8 opacity-50">
                    <p class="text-xs">Secure Verification System v2.0</p>
                </div>
            </div>
        </div>
        <div class="w-full md:w-2/3 bg-pattern p-8 md:p-12 flex flex-col">
            <div class="flex justify-between items-start mb-12">
                <div>
                    <h1 class="text-3xl font-bold text-slate-800 mb-2">Certificate of Verification</h1>
                    <p class="text-slate-500">This document certifies that the credential has been verified and authenticated.</p>
                </div>
                <div class="hidden sm:flex items-center justify-center w-16 h-16 bg-blue-600 text-white rounded-lg shadow-md font-bold text-2xl">SK</div>
            </div>
            <div class="space-y-6 mb-12">
                ${data.extraction.candidate_name ? `
                <div>
                    <label class="block text-sm font-medium text-slate-400 mb-1">Issued To</label>
                    <p class="text-2xl font-serif text-slate-900">${data.extraction.candidate_name}</p>
                </div>` : ''}
                ${data.extraction.issuer_org ? `
                <div>
                    <label class="block text-sm font-medium text-slate-400 mb-1">Issuing Organization</label>
                    <p class="text-xl text-slate-700">${data.extraction.issuer_org}</p>
                </div>` : ''}
                <div>
                    <label class="block text-sm font-medium text-slate-400 mb-1">Verification Status</label>
                    <p class="text-lg text-slate-700">${data.verification.message}</p>
                </div>
            </div>
            <div class="mt-auto border-t border-slate-200 pt-6 flex flex-col sm:flex-row justify-between items-center text-sm text-slate-500">
                <p>Status: <span class="text-emerald-600 font-bold bg-emerald-100 px-2 py-0.5 rounded">${data.final_verdict}</span></p>
                ${data.extraction.certificate_id ? `<p class="mt-2 sm:mt-0">ID: ${data.extraction.certificate_id}</p>` : ''}
            </div>
        </div>
    </div>
</body>
</html>`;

    const blob = new Blob([certificateHTML], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `verification-certificate-${data.extraction.certificate_id || 'certificate'}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Success Header */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 mb-6 border border-green-200">
        <div className="flex items-center gap-3 mb-3">
          <CheckCircle className="w-8 h-8 text-green-600" />
          <h2 className="text-2xl font-bold text-green-800">Certificate Verified!</h2>
        </div>
        <p className="text-green-700">{data.verification.message}</p>
      </div>

      {/* Certificate Details */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 space-y-6">
        
        {/* Candidate Info */}
        {data.extraction.candidate_name && (
          <div className="flex items-start gap-3">
            <User className="w-5 h-5 text-blue-600 mt-1" />
            <div>
              <p className="text-sm text-gray-500 font-medium">Candidate Name</p>
              <p className="text-lg font-semibold text-gray-900">{data.extraction.candidate_name}</p>
            </div>
          </div>
        )}

        {/* Certificate ID */}
        {data.extraction.certificate_id && (
          <div className="flex items-start gap-3">
            <Hash className="w-5 h-5 text-blue-600 mt-1" />
            <div>
              <p className="text-sm text-gray-500 font-medium">Certificate ID</p>
              <p className="text-lg font-mono text-gray-900">{data.extraction.certificate_id}</p>
            </div>
          </div>
        )}

        {/* Issuer Organization */}
        {data.extraction.issuer_org && (
          <div className="flex items-start gap-3">
            <Building className="w-5 h-5 text-blue-600 mt-1" />
            <div>
              <p className="text-sm text-gray-500 font-medium">Issuing Organization</p>
              <p className="text-lg font-semibold text-gray-900">{data.extraction.issuer_org}</p>
            </div>
          </div>
        )}

        {/* Verification URL */}
        {data.extraction.issuer_url && (
          <div className="flex items-start gap-3">
            <LinkIcon className="w-5 h-5 text-blue-600 mt-1" />
            <div className="flex-1">
              <p className="text-sm text-gray-500 font-medium">Verification URL</p>
              <a 
                href={data.extraction.issuer_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700 underline break-all"
              >
                {data.extraction.issuer_url}
              </a>
            </div>
          </div>
        )}

        {/* Divider */}
        <div className="border-t border-gray-200"></div>

        {/* Forensics Info - Removed Manipulation Score */}
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Security Analysis</p>
          <div className="space-y-1 text-sm text-gray-600">
            <p>• Risk Level: <span className={`font-semibold ${data.forensics.is_high_risk ? 'text-red-600' : 'text-green-600'}`}>
              {data.forensics.is_high_risk ? 'High Risk' : 'Low Risk'}
            </span></p>
            <p>• Status: <span className="font-semibold">{data.forensics.status}</span></p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={handleViewCertificate}
            className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-all shadow-md hover:shadow-lg"
          >
            <ExternalLink className="w-5 h-5" />
            View Validation Certificate
          </button>
          
          <button
            onClick={handleDownload}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-all shadow-md hover:shadow-lg"
          >
            <Download className="w-5 h-5" />
            Download Certificate (HTML)
          </button>
        </div>
      </div>
    </div>
  );
}
