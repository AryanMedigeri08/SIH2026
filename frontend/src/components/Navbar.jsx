import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Menu, Landmark, PlusCircle, LogOut 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { BusinessSwitcher } from './BusinessSwitcher';
import { LanguageSelector } from './LanguageSelector';
import { useLanguage } from '../context/LanguageContext';
import { ChatbotNavButton } from './Chat/ChatbotNavButton';
import { PersonaSwitcher } from './PersonaSwitcher';

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
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-xs transition-all w-full">
      {/* Sovereign Top Gradient Accent Line */}
      <div className="h-[3px] w-full bg-gradient-to-r from-sovereign-900 via-sky-500 via-indigo-600 to-emerald-500" />
      
      <div className="w-full px-3 sm:px-4 lg:px-6 h-14 sm:h-16 flex items-center justify-between gap-2 lg:gap-3 min-w-0">
        
        {/* Left: Mobile Toggle, Brand Logo & Enterprise Switcher */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0 min-w-0">
          {/* Mobile Sidebar Hamburger Toggle */}
          <button
            type="button"
            onClick={onToggleMobileSidebar}
            className="lg:hidden p-1.5 sm:p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 transition-colors shrink-0"
            aria-label="Toggle navigation menu"
            title="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Institutional Brand Logo */}
          <Link to={isAuthenticated ? "/dashboard" : "/"} className="flex items-center gap-2 shrink-0 group">
            <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-gradient-to-br from-sovereign-800 via-sovereign-900 to-indigo-950 text-white flex items-center justify-center shadow-md shadow-sovereign-900/20 text-base font-bold border border-sovereign-700/50 transition-transform group-hover:scale-105 shrink-0">
              <Landmark className="w-4.5 h-4.5 text-sky-400" />
            </div>
            <div className="flex items-center gap-2">
              <span className="font-outfit font-extrabold text-base sm:text-lg text-slate-900 tracking-tight group-hover:text-sovereign-800 transition-colors whitespace-nowrap">
                Udyam Saathi
              </span>
            </div>
          </Link>

          {/* Clean vertical divider */}
          {isAuthenticated && (
            <div className="hidden md:block h-6 w-px bg-slate-200 shrink-0" />
          )}

          {/* Persistent Enterprise Switcher */}
          {isAuthenticated && (
            <div className="hidden md:block shrink-0">
              <BusinessSwitcher />
            </div>
          )}
        </div>

        {/* Right: Controls, Personas, AI Chat & Identity */}
        <div className="flex items-center gap-1 sm:gap-1.5 lg:gap-2.5 shrink-0">
          
          {/* Persona Switcher: Compact icon-only on mobile, full labels on lg+ */}
          <PersonaSwitcher compact />

          {/* Persistent AI Chatbot Navigation Button */}
          <ChatbotNavButton />

          {/* Live System Status Pill (Telemetry) - visible on xl+ */}
          <Link 
            to="/data-sources" 
            className={`hidden xl:flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-full border transition-all shrink-0 ${
              isHealthy 
                ? 'bg-emerald-50/90 border-emerald-200 text-emerald-800 hover:bg-emerald-100 shadow-subtle' 
                : 'bg-amber-50/90 border-amber-200 text-amber-800 hover:bg-amber-100 shadow-subtle'
            }`} 
            title="Click to view live database and ML pipeline status"
          >
            <span className="relative flex h-2 w-2 shrink-0">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isHealthy ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isHealthy ? 'bg-emerald-600' : 'bg-amber-600'}`} />
            </span>
            <span className="font-semibold text-[11px] whitespace-nowrap">{isHealthy ? 'Live' : 'Connecting...'}</span>
          </Link>

          {/* + Create New Business - quick action */}
          <Link
            to="/wizard"
            className="hidden 2xl:flex items-center gap-1.5 text-xs font-bold text-white bg-gradient-to-r from-sovereign-800 via-sky-700 to-sovereign-800 hover:from-sovereign-700 hover:to-sky-600 px-3 py-1.5 rounded-xl shadow-xs border border-sky-400/20 transition-all shrink-0 group whitespace-nowrap"
            title={t('newEnterprise')}
          >
            <PlusCircle className="w-3.5 h-3.5 text-sky-200 group-hover:rotate-90 transition-transform shrink-0" />
            <span>{t('newEnterprise')}</span>
          </Link>

          {/* Language Selector — visible on sm+; mobile users get it in the sidebar drawer */}
          <div className="hidden sm:block shrink-0">
            <LanguageSelector />
          </div>

          {/* User Auth Section */}
          {isAuthenticated ? (
            <div className="flex items-center gap-1.5 pl-1.5 sm:pl-2 border-l border-slate-200 shrink-0">
              <div 
                className="flex items-center gap-1.5 px-2 sm:px-2.5 py-1 rounded-xl bg-slate-100 border border-slate-200 shrink-0" 
                title={userProfile?.name || 'User'}
              >
                <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-700 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                  {userProfile?.name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <span className="text-xs font-bold text-slate-800 hidden xl:inline truncate max-w-[90px] 2xl:max-w-[120px]">
                  {userProfile?.name || 'User'}
                </span>
              </div>

              <button
                type="button"
                onClick={handleLogout}
                className="p-1.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition-colors cursor-pointer shrink-0"
                title={t('logout')}
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 shrink-0">
              <Link
                to="/login"
                className="text-xs font-bold text-sovereign-800 hover:bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200 transition cursor-pointer whitespace-nowrap"
              >
                {t('login')}
              </Link>
              <Link
                to="/register"
                className="text-xs font-bold text-white bg-sovereign-800 hover:bg-sovereign-700 px-3 py-1.5 rounded-xl transition shadow-sm cursor-pointer whitespace-nowrap"
              >
                {t('register')}
              </Link>
            </div>
          )}

        </div>

      </div>
    </header>
  );
}

export default Navbar;
