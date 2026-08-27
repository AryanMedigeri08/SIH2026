import React from 'react';
import { Sparkles, Calculator, FileText, Activity, ShieldCheck } from 'lucide-react';

export function Navbar({ health, onOpenWizard, onOpenCalculator, activeTab, setActiveTab }) {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="sticky top-0 z-40 bg-[#070b14]/80 backdrop-blur-xl border-b border-indigo-500/15 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand & Badge */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-glow text-xl font-bold">
            🚀
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-outfit font-extrabold text-lg sm:text-xl text-white tracking-tight">
                Udyam Saathi
              </span>
              <span className="text-xs font-semibold text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 rounded-full font-sans">
                उद्यम साथी
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              AI-Powered MSME Feasibility & Bank DPR Engine • SIH 2026
            </p>
          </div>
        </div>

        {/* Action Controls & Health Indicator */}
        <div className="flex items-center gap-2 sm:gap-4">
          
          {/* Live System Status Pill */}
          <div className={`hidden md:flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border ${
            isHealthy 
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' 
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          }`}>
            <span className={`w-2 h-2 rounded-full animate-pulse ${isHealthy ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            <span>{isHealthy ? 'Neon DB & ML Active' : 'Connecting Engine...'}</span>
          </div>

          {/* Quick Loan Sizing Tool Button */}
          <button
            onClick={onOpenCalculator}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 px-3 py-1.5 rounded-lg transition-all"
          >
            <Calculator className="w-4 h-4 text-cyan-400" />
            <span className="hidden sm:inline">Quick Calculator</span>
          </button>

          {/* Launch 6-Step Feasibility Wizard */}
          <button
            onClick={onOpenWizard}
            className="flex items-center gap-1.5 text-xs font-semibold text-white bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 px-3.5 py-1.5 rounded-lg shadow-glow hover:shadow-glow-cyan transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>New Feasibility Assessment</span>
          </button>

        </div>

      </div>
    </header>
  );
}
