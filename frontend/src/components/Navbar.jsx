import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { 
  Sparkles, Calculator, FileText, Activity, ShieldCheck, 
  LayoutDashboard, Database, Award 
} from 'lucide-react';

export function Navbar({ health, onOpenWizard, onOpenCalculator, activeTab, setActiveTab }) {
  const isHealthy = health?.status === 'healthy';

  const navLinks = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/wizard', label: 'New Assessment', icon: Sparkles },
    { to: '/calculator', label: 'Loan Sizing', icon: Calculator },
    { to: '/schemes', label: 'Scheme Master', icon: Award },
    { to: '/data-sources', label: 'Data Lineage', icon: Database },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#070b14]/85 backdrop-blur-xl border-b border-indigo-500/15 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand & Badge */}
        <Link to="/" className="flex items-center gap-3 cursor-pointer group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-glow text-xl font-bold transition-transform group-hover:scale-105">
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
        </Link>

        {/* Center Route Links */}
        <nav className="hidden lg:flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800">
          {navLinks.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-cyan-500 text-black shadow-glow-cyan font-bold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{link.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Action Controls & Health Indicator */}
        <div className="flex items-center gap-2 sm:gap-3">
          
          {/* Live System Status Pill */}
          <Link to="/data-sources" className={`hidden sm:flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border transition-all ${
            isHealthy 
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20' 
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20'
          }`} title="Click to view live database and ML pipeline status">
            <span className={`w-2 h-2 rounded-full animate-pulse ${isHealthy ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            <span>{isHealthy ? 'Neon DB & ML Active' : 'Connecting Engine...'}</span>
          </Link>

          {/* Quick Loan Sizing Tool Button */}
          <Link
            to="/calculator"
            className="flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 px-3 py-1.5 rounded-lg transition-all"
          >
            <Calculator className="w-4 h-4 text-cyan-400" />
            <span className="hidden md:inline">Quick Calculator</span>
          </Link>

          {/* Launch 6-Step Feasibility Wizard */}
          <Link
            to="/wizard"
            className="flex items-center gap-1.5 text-xs font-semibold text-white bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 px-3.5 py-1.5 rounded-lg shadow-glow hover:shadow-glow-cyan transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span className="hidden sm:inline">New Assessment</span>
          </Link>

        </div>

      </div>
    </header>
  );
}

