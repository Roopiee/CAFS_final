'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ShieldCheck, Menu, X } from 'lucide-react';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <ShieldCheck className="w-8 h-8 text-orange-600 group-hover:text-blue-700 transition-colors" />
            <span className="text-xl font-bold tracking-tight text-slate-800 group-hover:text-orange-600 transition-colors">
              SKILLKENDRA
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link 
              href="/" 
              className="text-slate-600 hover:text-orange-600 font-medium transition-colors"
            >
              Home
            </Link>
            <Link 
              href="/#verify" 
              className="text-slate-600 hover:text-orange-600 font-medium transition-colors"
            >
              Roopakthegreat
            </Link>
            <Link 
              href="/#about" 
              className="text-slate-600 hover:text-orange-600 font-medium transition-colors"
            >
              About
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="Toggle menu"
          >
            {isOpen ? (
              <X className="w-6 h-6 text-slate-600" />
            ) : (
              <Menu className="w-6 h-6 text-slate-600" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden pb-4 space-y-2">
            <Link 
              href="/" 
              className="block px-4 py-2 text-slate-600 hover:bg-blue-50 hover:text-orange-600 rounded-lg transition-colors"
              onClick={() => setIsOpen(false)}
            >
              Home
            </Link>
            <Link 
              href="/#verify" 
              className="block px-4 py-2 text-slate-600 hover:bg-orange-50 hover:text-orange-600 rounded-lg transition-colors"
              onClick={() => setIsOpen(false)}
            >
              Verify
            </Link>
            <Link 
              href="/#about" 
              className="block px-4 py-2 text-slate-600 hover:bg-orange-50 hover:text-orange-600 rounded-lg transition-colors"
              onClick={() => setIsOpen(false)}
            >
              About
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
