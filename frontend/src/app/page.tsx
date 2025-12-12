import React from 'react';
import UploadForm from '@/components/verification/UploadForm';
import Navbar from '@/components/ui/Navbar';
import { HeroGrid } from '@/components/ui/HeroGrid';
import { HowItWorks } from '@/components/ui/HowItWorks';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white text-slate-900">
      
      {/* Navbar */}
      <Navbar />

      {/* Hero Section with Animated Grid */}
      <HeroGrid />

      {/* Upload Section - Same white background, no grid */}
      <section id="verify" className="bg-white flex flex-col items-center justify-center px-4 py-20">
        
        {/* Section Header */}
        <div className="text-center mb-12 max-w-3xl">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
            Start Verification
          </h2>
          <p className="text-lg text-slate-600">
            Upload your certificate and get instant verification results
          </p>
        </div>

        {/* Centered Upload Card */}
        <div className="w-full max-w-md">
          <UploadForm />
        </div>

      </section>

      {/* How It Works Section - Enhanced */}
      <HowItWorks />
      
    </main>
  );
}