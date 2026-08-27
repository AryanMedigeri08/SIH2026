import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { 
  Sparkles, Calculator, FileText, Activity, ShieldCheck, 
  LayoutDashboard, Database, Award, CheckCircle2, Menu
} from 'lucide-react';

export function Navbar({ health, onOpenWizard, onOpenCalculator, onToggleMobileSidebar }) {
  const isHealthy = health?.status === 'healthy';

  const navLinks = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/viability', label: 'ML Viability', icon: Activity },
    { to: '/schemes', label: 'Schemes', icon: Award },
    { to: '/calculator', label: 'Calculator', icon: Calculator },
    { to: '/data-sources', label: 'Data Lineage', icon: Database },
  ];

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Left Side: Mobile Menu Button & Brand */}
        <div className="flex items-center gap-3">
          {/* Hamburger button for mobile/drawer */}
          <button
            onClick={onToggleMobileSidebar}
            className="lg:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition"
            title="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Institutional Brand Logo & Tagline */}
          <Link to="/" className="flex items-center gap-2.5 cursor-pointer group">
            <div className="w-9 h-9 rounded-xl bg-sovereign-800 text-white flex items-center justify-center shadow-subtle text-lg font-bold transition-transform group-hover:scale-105">
              🏛️
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-outfit font-extrabold text-base sm:text-lg text-slate-900 tracking-tight">
                  Udyam Saathi
                </span>
                <span className="text-[11px] font-semibold text-sovereign-800 bg-sovereign-50 border border-sovereign-200 px-2 py-0.5 rounded-full font-sans">
                  उद्यम साथी
                </span>
              </div>
              <p className="text-[10px] text-slate-500 hidden sm:block">
                National MSME Credit Feasibility & Bank DPR Portal
              </p>
            </div>
          </Link>
        </div>

        {/* Center Route Navigation Bar (Desktop) */}
        <nav className="hidden lg:flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200">
          {navLinks.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-sovereign-800 text-white shadow-sm font-bold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-white'
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
          <Link 
            to="/data-sources" 
            className={`hidden sm:flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border transition-all ${
              isHealthy 
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800 hover:bg-emerald-100' 
                : 'bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100'
            }`} 
            title="Click to view live database and ML pipeline status"
          >
            <span className={`w-2 h-2 rounded-full animate-pulse ${isHealthy ? 'bg-emerald-600' : 'bg-amber-600'}`} />
            <span className="font-medium">{isHealthy ? 'Live Telemetry Active' : 'Connecting Engine...'}</span>
          </Link>

          {/* Quick Loan Sizing Tool Button */}
          <Link
            to="/calculator"
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-200 px-3 py-1.5 rounded-lg transition-all"
          >
            <Calculator className="w-4 h-4 text-sovereign-700" />
            <span className="hidden md:inline">Quick Sizing</span>
          </Link>

          {/* Launch 6-Step Feasibility Wizard */}
          <Link
            to="/wizard"
            className="flex items-center gap-1.5 text-xs font-bold text-white bg-sovereign-800 hover:bg-sovereign-700 px-3.5 py-1.5 rounded-lg shadow-sm transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span className="hidden sm:inline">New Assessment</span>
          </Link>

        </div>

      </div>
    </header>
  );
}
export default Navbar;
