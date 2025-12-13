'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { ShieldCheck, Menu, X } from 'lucide-react';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Handle scroll effect for glassmorphism
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav 
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled 
          ? 'bg-slate-900/80 backdrop-blur-md border-b border-slate-700 shadow-lg py-2' 
          : 'bg-transparent py-4'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="bg-orange-600 p-1.5 rounded-lg group-hover:bg-orange-500 transition-colors">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <span className={`text-xl font-bold tracking-tight transition-colors ${
              scrolled ? 'text-white' : 'text-slate-900'
            }`}>
              SKILL<span className="text-orange-600">KENDRA</span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {['Home', 'Verify', 'About'].map((item) => (
              <Link 
                key={item}
                href={item === 'Home' ? '/' : `/#${item.toLowerCase()}`} 
                className={`text-sm font-medium transition-colors hover:text-orange-500 ${
                  scrolled ? 'text-slate-300' : 'text-slate-700'
                }`}
              >
                {item}
              </Link>
            ))}
            
            <Link 
              href="/profile" 
              className="px-5 py-2.5 rounded-full bg-orange-600 text-white text-sm font-semibold hover:bg-orange-700 transition-all shadow-md hover:shadow-orange-500/20"
            >
              Profile
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors"
            aria-label="Toggle menu"
          >
            {isOpen ? (
              <X className={`w-6 h-6 ${scrolled ? 'text-white' : 'text-slate-900'}`} />
            ) : (
              <Menu className={`w-6 h-6 ${scrolled ? 'text-white' : 'text-slate-900'}`} />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden absolute top-full left-0 right-0 bg-slate-900 border-t border-slate-800 shadow-xl p-4 space-y-3">
            {['Home', 'Verify', 'About'].map((item) => (
              <Link 
                key={item}
                href={item === 'Home' ? '/' : `/#${item.toLowerCase()}`}
                className="block px-4 py-3 text-slate-300 hover:bg-slate-800 hover:text-orange-500 rounded-lg transition-colors font-medium"
                onClick={() => setIsOpen(false)}
              >
                {item}
              </Link>
            ))}
             <Link 
              href="/profile" 
              className="block w-full text-center px-4 py-3 bg-orange-600 text-white rounded-lg font-bold hover:bg-orange-700 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              Profile
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
