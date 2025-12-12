import React from 'react';
import UploadForm from '@/components/verification/UploadForm';
import Navbar from '@/components/ui/Navbar';

export default function LandingPage() {
  return (
    <main className="min-h-screen text-slate-900">
      
      {/* Navbar */}
      <Navbar />

      {/* Hero Section */}
      <section id="verify" className="relative flex flex-col items-center justify-center px-4 py-24 md:py-32 min-h-screen overflow-hidden">
        
        {/* Decorative background blur */}
        <div className="absolute top-0 -z-10 w-full h-full bg-white/50 backdrop-blur-sm"></div>
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-100 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-orange-100 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>

        {/* Header Text */}
        <div className="relative z-10 text-center mb-16 max-w-4xl mx-auto">
          <div className="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium text-blue-600 ring-1 ring-inset ring-blue-600/20 bg-blue-50/50 mb-6">
            AI-Powered Certificate Verification
          </div>
          <h1 className="text-5xl md:text-7xl font-black tracking-tight text-slate-900 leading-[1.1] mb-8">
            Verify Credentials with <br className="hidden md:block"/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-600 to-amber-500">
              Absolute Confidence
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-slate-600 leading-relaxed mb-10 max-w-2xl mx-auto">
            SkillKendra leverages advanced AI agents to instantly authenticate certificates with forensic precision.
          </p>
          
          <div className="flex flex-wrap gap-6 justify-center">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 bg-white/60 px-4 py-2 rounded-full border border-slate-200 shadow-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></span>
              Instant Analysis
            </div>
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 bg-white/60 px-4 py-2 rounded-full border border-slate-200 shadow-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
              Forensic AI
            </div>
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 bg-white/60 px-4 py-2 rounded-full border border-slate-200 shadow-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
              Bank-grade Security
            </div>
          </div>
        </div>

        {/* Centered Upload Card */}
        <div className="relative z-10 w-full max-w-2xl">
          <div className="bg-white/70 backdrop-blur-xl p-1 rounded-3xl shadow-2xl border border-white/50">
            <UploadForm />
          </div>
        </div>

      </section>

      {/* About Section */}
      <section id="about" className="px-4 py-24 bg-white border-t border-slate-100">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-slate-900 mb-6">
              How It Works
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Three simple steps to verify any digital credential with 99.9% accuracy.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-12">
            {[ 
              { step: 1, title: 'Upload', desc: 'Securely upload your certificate as a PDF or image file.', color: 'blue' },
              { step: 2, title: 'Analyze', desc: 'Our AI agents perform OCR and forensic analysis in real-time.', color: 'orange' },
              { step: 3, title: 'Verify', desc: 'Get an instant verification report with a confidence score.', color: 'green' }
            ].map((item) => (
              <div key={item.step} className="group p-8 rounded-3xl bg-slate-50 border border-slate-100 hover:border-blue-100 hover:bg-blue-50/30 hover:shadow-xl transition-all duration-300">
                <div className={`w-16 h-16 bg-${item.color}-100 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  <span className={`text-3xl font-bold text-${item.color}-600`}>{item.step}</span>
                </div>
                <h3 className="font-bold text-2xl mb-4 text-slate-900">{item.title}</h3>
                <p className="text-slate-600 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      
    </main>
  );
}
