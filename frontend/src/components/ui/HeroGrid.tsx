"use client";
import React, { useRef } from "react";
import { 
  motion, 
  useMotionValue, 
  useMotionTemplate, 
  useAnimationFrame 
} from "framer-motion";

interface HeroGridProps {
  onVerifyClick?: () => void;
}

export const HeroGrid: React.FC<HeroGridProps> = ({ onVerifyClick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const { left, top } = e.currentTarget.getBoundingClientRect();
    mouseX.set(e.clientX - left);
    mouseY.set(e.clientY - top);
  };

  const gridOffsetX = useMotionValue(0);
  const gridOffsetY = useMotionValue(0);

  const speedX = 0.3; 
  const speedY = 0.3;

  useAnimationFrame(() => {
    const currentX = gridOffsetX.get();
    const currentY = gridOffsetY.get();
    gridOffsetX.set((currentX + speedX) % 40);
    gridOffsetY.set((currentY + speedY) % 40);
  });

  const maskImage = useMotionTemplate`radial-gradient(350px circle at ${mouseX}px ${mouseY}px, black, transparent)`;

  const handleScrollToUpload = () => {
    if (onVerifyClick) {
      onVerifyClick();
    } else {
      const uploadSection = document.getElementById('verify');
      if (uploadSection) {
        uploadSection.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className="relative w-full h-screen flex flex-col items-center justify-center overflow-hidden bg-white"
    >
      {/* Base grid layer */}
      <div className="absolute inset-0 z-0 opacity-[0.15]">
        <GridPattern offsetX={gridOffsetX} offsetY={gridOffsetY} />
      </div>

      {/* Interactive grid layer (follows mouse) */}
      <motion.div 
        className="absolute inset-0 z-0 opacity-60"
        style={{ maskImage, WebkitMaskImage: maskImage }}
      >
        <GridPattern offsetX={gridOffsetX} offsetY={gridOffsetY} highlighted />
      </motion.div>

      {/* Single subtle gradient */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute right-[20%] top-[20%] w-[30%] h-[30%] rounded-full bg-orange-500/10 blur-[120px]" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center text-center px-4 max-w-4xl mx-auto space-y-8 pointer-events-none">
        <div className="space-y-4">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-5xl md:text-7xl font-bold tracking-tight text-slate-900"
          >
            Verify Credentials with{" "}
            <span className="text-orange-600">
              Confidence
            </span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-lg md:text-xl text-slate-600 leading-relaxed max-w-2xl mx-auto"
          >
            Advanced AI-powered certificate authentication. Upload your document and get instant verification results.
          </motion.p>
        </div>

        {/* Feature badges - minimal */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="flex flex-wrap gap-3 justify-center"
        >
          <div className="text-sm text-slate-600 bg-slate-50 px-4 py-2 rounded-full border border-slate-200">
            ✓ Instant Analysis
          </div>
          <div className="text-sm text-slate-600 bg-slate-50 px-4 py-2 rounded-full border border-slate-200">
            ✓ Secure Platform
          </div>
          <div className="text-sm text-slate-600 bg-slate-50 px-4 py-2 rounded-full border border-slate-200">
            ✓ AI-Powered
          </div>
        </motion.div>
        
        {/* Buttons - clean */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex gap-4 pointer-events-auto"
        >
          <button 
            onClick={handleScrollToUpload}
            className="px-8 py-4 bg-orange-600 text-white font-semibold rounded-lg hover:bg-orange-700 transition-all shadow-sm hover:shadow-md active:scale-95"
          >
            Verify Certificate
          </button>
          
          <a
            href="#about"
            className="px-8 py-4 bg-white text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition-all border border-slate-300 active:scale-95"
          >
            Learn More
          </a>
        </motion.div>

        {/* Stats - minimal */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="flex flex-wrap gap-12 justify-center text-sm pt-8 text-slate-500"
        >
          <div className="flex flex-col items-center gap-1">
            <div className="text-3xl font-bold text-slate-900">90%</div>
            <div>Accuracy</div>
          </div>
          <div className="flex flex-col items-center gap-1">
            <div className="text-3xl font-bold text-slate-900">&lt;20s</div>
            <div>Processing</div>
          </div>
          <div className="flex flex-col items-center gap-1">
            <div className="text-3xl font-bold text-slate-900">50+</div>
            <div>Platforms</div>
          </div>
        </motion.div>
      </div>

      {/* Scroll indicator - minimal */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.6 }}
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="flex flex-col items-center gap-2 text-slate-400 cursor-pointer hover:text-slate-600 transition-colors"
          onClick={handleScrollToUpload}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </motion.div>
      </motion.div>
    </div>
  );
};

const GridPattern = ({ 
  offsetX, 
  offsetY, 
  highlighted = false 
}: { 
  offsetX: any; 
  offsetY: any; 
  highlighted?: boolean;
}) => {
  return (
    <svg className="w-full h-full">
      <defs>
        <motion.pattern
          id={highlighted ? "grid-highlight" : "grid-base"}
          width="40"
          height="40"
          patternUnits="userSpaceOnUse"
          x={offsetX}
          y={offsetY}
        >
          <path
            d="M 40 0 L 0 0 0 40"
            fill="none"
            stroke="currentColor"
            strokeWidth={highlighted ? "1.5" : "1"}
            className={highlighted ? "text-orange-400" : "text-slate-300"}
          />
        </motion.pattern>
      </defs>
      <rect 
        width="100%" 
        height="100%" 
        fill={`url(#${highlighted ? "grid-highlight" : "grid-base"})`}
      />
    </svg>
  );
};