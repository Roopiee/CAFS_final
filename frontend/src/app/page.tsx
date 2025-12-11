import React from 'react';
import UploadForm from '@/components/verification/UploadForm';
import Navbar from '@/components/ui/Navbar';
import { ShieldCheck } from 'lucide-react';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 text-slate-900">
      
      {/* Navbar */}
      <Navbar />

      {/* Hero Section */}
      <section id="verify" className="flex flex-col items-center justify-center px-4 py-12 md:py-20 min-h-[calc(100vh-4rem)]">
        
        {/* Header Text */}
        <div className="text-center mb-12 max-w-3xl">
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-tight mb-6">
            Verify Credentials with <span className="text-orange-600">Confidence</span>
          </h1>
          <p className="text-lg text-slate-600 leading-relaxed mb-8">
            SkillKendra uses advanced AI agents to authenticate certificates instantly. 
            Upload your document, and let our secure platform handle the verification process for you.
          </p>
          
          <div className="flex flex-wrap gap-4 justify-center">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              Instant Analysis
            </div>
            <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              Bank-grade Security
            </div>
            <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              AI-Powered Forensics
            </div>
          </div>
        </div>

        {/* Centered Upload Card */}
        <div className="w-full max-w-md">
          <UploadForm />
        </div>

      </section>

      {/* About Section */}
      <section id="about" className="px-4 py-16 md:py-24 bg-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-6">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8 mt-12">
            <div className="p-6">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-blue-600">1</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Upload</h3>
              <p className="text-slate-600 text-sm">Upload your certificate as PDF or image</p>
            </div>
            <div className="p-6">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-blue-600">2</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Analyze</h3>
              <p className="text-slate-600 text-sm">AI agents perform forensics and extraction</p>
            </div>
            <div className="p-6">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-blue-600">3</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Verify</h3>
              <p className="text-slate-600 text-sm">Get instant verification results</p>
            </div>
          </div>
        </div>
      </section>
      
    </main>
  );
}
