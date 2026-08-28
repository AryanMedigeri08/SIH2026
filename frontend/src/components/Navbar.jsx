import React from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { 
  Sparkles, Calculator, Activity, LayoutDashboard, Database, Award, 
  Menu, User, LogOut, LogIn, UserPlus 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Navbar({ health, onToggleMobileSidebar }) {
  const isHealthy = health?.status === 'healthy';
  const { isAuthenticated, userProfile, logout } = useAuth();
  const navigate = useNavigate();

  const navLinks = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/viability', label: 'ML Viability', icon: Activity },
    { to: '/schemes', label: 'Schemes', icon: Award },
    { to: '/calculator', label: 'Calculator', icon: Calculator },
    { to: '/data-sources', label: 'Data Lineage', icon: Database },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-sm transition-all">
      {/* Sovereign Top Gradient Accent Line */}
      <div className="h-[3px] w-full bg-gradient-to-r from-sovereign-900 via-sky-500 via-indigo-600 to-emerald-500" />

      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Left Side: Mobile Menu Button & Brand */}
        <div className="flex items-center gap-3">
          {/* Hamburger button for mobile drawer */}
          <button
            onClick={onToggleMobileSidebar}
            className="lg:hidden p-2 rounded-xl text-slate-600 hover:text-slate-950 hover:bg-slate-100 transition border border-transparent hover:border-slate-200"
            title="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Institutional Brand Logo & Tagline */}
          <Link to="/" className="flex items-center gap-2.5 cursor-pointer group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sovereign-800 via-sovereign-900 to-indigo-950 text-white flex items-center justify-center shadow-md shadow-sovereign-900/20 text-lg font-bold border border-sovereign-700/50 transition-transform group-hover:scale-105">
              🏛️
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-outfit font-extrabold text-base sm:text-lg text-slate-900 tracking-tight group-hover:text-sovereign-800 transition-colors">
                  Udyam Saathi
                </span>
                <span className="text-[10px] font-bold text-sovereign-800 bg-gradient-to-r from-sovereign-50 to-sky-50 border border-sovereign-200/80 px-2 py-0.5 rounded-full font-sans shadow-subtle">
                  उद्यम साथी
                </span>
              </div>
              <p className="text-[10px] text-slate-500 hidden sm:block font-medium">
                National MSME Credit Feasibility & Bank DPR Portal
              </p>
            </div>
          </Link>
        </div>

        {/* Center Route Navigation Bar (Desktop) */}
        <nav className="hidden lg:flex items-center gap-1 bg-slate-100/80 p-1 rounded-xl border border-slate-200/80 shadow-inner">
          {navLinks.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                    isActive
                      ? 'bg-gradient-to-r from-sovereign-800 to-indigo-900 text-white shadow-sm font-bold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-white/80'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{link.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Action Controls & User Identity */}
        <div className="flex items-center gap-2 sm:gap-3">
          
          {/* Live System Status Pill */}
          <Link 
            to="/data-sources" 
            className={`hidden sm:flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border transition-all ${
              isHealthy 
                ? 'bg-emerald-50/90 border-emerald-200 text-emerald-800 hover:bg-emerald-100 shadow-subtle' 
                : 'bg-amber-50/90 border-amber-200 text-amber-800 hover:bg-amber-100 shadow-subtle'
            }`} 
            title="Click to view live database and ML pipeline status"
          >
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isHealthy ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isHealthy ? 'bg-emerald-600' : 'bg-amber-600'}`} />
            </span>
            <span className="font-semibold">{isHealthy ? 'Live Telemetry' : 'Connecting...'}</span>
          </Link>

          {/* Launch 6-Step Feasibility Wizard */}
          <Link
            to="/wizard"
            className="flex items-center gap-1.5 text-xs font-bold text-white bg-gradient-to-r from-sovereign-800 via-sky-700 to-sovereign-800 hover:from-sovereign-700 hover:to-sky-600 px-3.5 py-1.5 rounded-xl shadow-md shadow-sovereign-900/15 border border-sky-400/20 transition-all group"
          >
            <Sparkles className="w-3.5 h-3.5 text-sky-200 group-hover:rotate-12 transition-transform" />
            <span className="hidden sm:inline">New Assessment</span>
          </Link>

          {/* User Auth Section */}
          {isAuthenticated ? (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
              <div className="flex items-center gap-2 px-2.5 py-1 rounded-xl bg-slate-100 border border-slate-200">
                <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-700 text-white flex items-center justify-center text-[10px] font-bold">
                  {userProfile?.name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <span className="text-xs font-semibold text-slate-800 hidden md:inline max-w-[120px] truncate">
                  {userProfile?.name || 'Promoter'}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="p-1.5 rounded-xl text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                title="Sign out of sovereign workspace"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 pl-2 border-l border-slate-200">
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl transition-colors shadow-sm"
              >
                <LogIn className="w-3.5 h-3.5 text-cyan-600" />
                <span>Log In</span>
              </Link>
            </div>
          )}

        </div>

      </div>
    </header>
  );
}
export default Navbar;
