import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Sparkles, Menu, Landmark, PlusCircle, LogOut 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useBusiness } from '../context/BusinessContext';
import { BusinessSwitcher } from './BusinessSwitcher';
import { LanguageSelector } from './LanguageSelector';
import { useLanguage } from '../context/LanguageContext';
import { ChatbotNavButton } from './Chat/ChatbotNavButton';

export function Navbar({ health, onToggleMobileSidebar }) {
  const isHealthy = health?.status === 'healthy';
  const { isAuthenticated, userProfile, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleLogout = () => {
    navigate('/login', { replace: true });
    void logout();
  };

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-xs transition-all">
      {/* Sovereign Top Gradient Accent Line */}
      <div className="h-[3px] w-full bg-gradient-to-r from-sovereign-900 via-sky-500 via-indigo-600 to-emerald-500" />
      
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        
        {/* Left: Mobile Toggle & Brand Logo */}
        <div className="flex items-center gap-3 shrink-0">
          {/* Mobile Sidebar Hamburger Toggle */}
          <button
            type="button"
            onClick={onToggleMobileSidebar}
            className="md:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 transition-colors"
            aria-label="Toggle navigation menu"
            title="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Institutional Brand Logo & Tagline */}
          <Link to={isAuthenticated ? "/dashboard" : "/"} className="flex items-center gap-2.5 cursor-pointer group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sovereign-800 via-sovereign-900 to-indigo-950 text-white flex items-center justify-center shadow-md shadow-sovereign-900/20 text-lg font-bold border border-sovereign-700/50 transition-transform group-hover:scale-105">
              <Landmark className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-outfit font-extrabold text-base sm:text-lg text-slate-900 tracking-tight group-hover:text-sovereign-800 transition-colors">
                  Udyam Saathi
                </span>
                <span className="text-[10px] font-bold text-sovereign-800 bg-gradient-to-r from-sovereign-50 to-sky-50 border border-sovereign-200/80 px-2 py-0.5 rounded-full font-sans shadow-subtle hidden sm:inline-block">
                  उद्यम साथी
                </span>
              </div>
              <p className="text-[10px] text-slate-500 hidden md:block font-medium">
                National MSME Credit Feasibility & Bank DPR Portal
              </p>
            </div>
          </Link>
        </div>

        {/* Center: Persistent Multi-Business Switcher with Real Data Status Indicators */}
        <div className="flex-1 max-w-lg mx-2 hidden sm:flex justify-center items-center min-w-0">
          {isAuthenticated && <BusinessSwitcher />}
        </div>

        {/* Right: Action Controls & User Identity */}
        <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
          
          {/* Persistent AI Chatbot Navigation Button (Placed immediately to the left of Live Telemetry) */}
          <ChatbotNavButton />

          {/* Live System Status Pill (Live Telemetry) */}
          <Link 
            to="/data-sources" 
            className={`hidden lg:flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border transition-all ${
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

          {/* + Create New Business / Assessment */}
          <Link
            to="/wizard"
            className="flex items-center gap-1.5 text-xs font-bold text-white bg-gradient-to-r from-sovereign-800 via-sky-700 to-sovereign-800 hover:from-sovereign-700 hover:to-sky-600 px-3.5 py-1.5 rounded-xl shadow-md shadow-sovereign-900/15 border border-sky-400/20 transition-all group"
            title={t('newEnterprise')}
          >
            <PlusCircle className="w-3.5 h-3.5 text-sky-200 group-hover:rotate-90 transition-transform" />
            <span className="hidden sm:inline">{t('newEnterprise')}</span>
          </Link>

          {/* User Auth Section */}
          {isAuthenticated ? (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
              <div className="flex items-center gap-2 px-2.5 py-1 rounded-xl bg-slate-100 border border-slate-200">
                <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-700 text-white flex items-center justify-center text-[10px] font-bold">
                  {userProfile?.name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <span className="text-xs font-bold text-slate-800 hidden md:inline truncate max-w-[120px]">
                  {userProfile?.name || 'User'}
                </span>
              </div>

              <button
                type="button"
                onClick={handleLogout}
                className="p-1.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition-colors cursor-pointer"
                title={t('logout')}
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="text-xs font-bold text-sovereign-800 hover:bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200 transition cursor-pointer"
              >
                {t('login')}
              </Link>
              <Link
                to="/register"
                className="text-xs font-bold text-white bg-sovereign-800 hover:bg-sovereign-700 px-3 py-1.5 rounded-xl transition shadow-sm cursor-pointer"
              >
                {t('register')}
              </Link>
            </div>
          )}

          <div className="hidden md:block">
            <LanguageSelector />
          </div>

        </div>

      </div>
    </header>
  );
}

export default Navbar;
