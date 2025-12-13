import React from 'react';
import { XCircle, ArrowLeft, Home } from 'lucide-react';
import Link from 'next/link';

export default function CertificateNotFound() {
  return (
    <div className="bg-white rounded-xl shadow-lg border border-red-100 p-8 md:p-12 text-center max-w-2xl mx-auto">
      <div className="mb-6 inline-flex p-4 bg-red-50 rounded-full">
        <XCircle className="w-16 h-16 text-red-500" />
      </div>
      
      <h2 className="text-3xl font-bold text-slate-900 mb-4">
        Sorry, we could not find your certificate
      </h2>
      
      <p className="text-slate-600 text-lg mb-8 leading-relaxed">
        We were unable to verify the certificate details you provided. This could be because the 
        Certificate ID or URL is incorrect, or the certificate is not publicly accessible.
      </p>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <button 
          onClick={() => window.location.reload()}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Try Again
        </button>
        
        <Link 
          href="/"
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors shadow-md hover:shadow-lg"
        >
          <Home className="w-5 h-5" />
          Back to Home
        </Link>
      </div>
    </div>
  );
}
