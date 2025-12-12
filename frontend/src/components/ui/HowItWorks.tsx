"use client";

import { Upload, Shield, CheckCircle } from "lucide-react";
import type React from "react";

interface HowItWorksProps extends React.HTMLAttributes<HTMLElement> {}

interface StepCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  benefits: string[];
}

const StepCard: React.FC<StepCardProps> = ({
  icon,
  title,
  description,
  benefits,
}) => (
  <div className="relative rounded-2xl border border-slate-200 bg-white p-6 transition-all duration-300 ease-in-out hover:scale-105 hover:shadow-xl hover:border-orange-400 hover:bg-slate-50">
    {/* Icon */}
    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-orange-100 text-orange-600">
      {icon}
    </div>
    {/* Title and Description */}
    <h3 className="mb-2 text-xl font-semibold text-slate-900">{title}</h3>
    <p className="mb-6 text-slate-600">{description}</p>
    {/* Benefits List */}
    <ul className="space-y-3">
      {benefits.map((benefit, index) => (
        <li key={index} className="flex items-center gap-3">
          <div className="flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full bg-orange-100">
            <div className="h-2 w-2 rounded-full bg-orange-600"></div>
          </div>
          <span className="text-sm text-slate-600">{benefit}</span>
        </li>
      ))}
    </ul>
  </div>
);

export const HowItWorks: React.FC<HowItWorksProps> = ({
  className = "",
  ...props
}) => {
  const stepsData = [
    {
      icon: <Upload className="h-6 w-6" />,
      title: "Upload Certificate",
      description:
        "Upload your certificate as PDF or image. Our system supports all major certificate formats.",
      benefits: [
        "Drag & drop or click to upload",
        "Supports PDF, PNG, JPG formats",
        "Secure file handling (max 5MB)",
      ],
    },
    {
      icon: <Shield className="h-6 w-6" />,
      title: "AI Analysis",
      description:
        "Advanced AI agents perform forensics detection, OCR extraction, and authenticity verification.",
      benefits: [
        "Multi-engine OCR (Tesseract, PaddleOCR, EasyOCR)",
        "Forgery detection with TruFor model",
        "Automatic issuer verification",
      ],
    },
    {
      icon: <CheckCircle className="h-6 w-6" />,
      title: "Get Results",
      description:
        "Receive instant verification results with detailed analysis and authenticity status.",
      benefits: [
        "Instant results in under 10 seconds",
        "98% accuracy rate",
        "Detailed forensics report",
      ],
    },
  ];

  return (
    <section
      id="how-it-works"
      className={`w-full bg-slate-50 py-16 sm:py-24 ${className}`}
      {...props}
    >
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="mx-auto mb-16 max-w-4xl text-center">
          <h2 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            How It Works
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Our AI-powered system uses advanced technology to verify certificates instantly
          </p>
        </div>

        {/* Step Indicators with Connecting Line */}
        <div className="relative mx-auto mb-8 w-full max-w-4xl">
          <div
            aria-hidden="true"
            className="absolute left-[16.6667%] top-1/2 h-0.5 w-[66.6667%] -translate-y-1/2 bg-slate-300"
          ></div>
          {/* Use grid to align numbers with the card grid below */}
          <div className="relative grid grid-cols-3">
            {stepsData.map((_, index) => (
              <div
                key={index}
                className="flex h-10 w-10 items-center justify-center justify-self-center rounded-full bg-orange-600 text-white font-bold text-lg ring-4 ring-slate-50"
              >
                {index + 1}
              </div>
            ))}
          </div>
        </div>

        {/* Steps Grid */}
        <div className="mx-auto grid max-w-4xl grid-cols-1 gap-8 md:grid-cols-3">
          {stepsData.map((step, index) => (
            <StepCard
              key={index}
              icon={step.icon}
              title={step.title}
              description={step.description}
              benefits={step.benefits}
            />
          ))}
        </div>
      </div>
    </section>
  );
};