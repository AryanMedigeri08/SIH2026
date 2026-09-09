import React, { useRef, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  BrainCircuit,
  Target,
  Award,
  TrendingUp,
  ShieldAlert,
  Grid3X3,
  FileText,
} from 'lucide-react';
import { TranslatedText } from './TranslatedText';

export function MobileReportTabs({ reportId }) {
  const location = useLocation();
  const activeTabRef = useRef(null);
  const containerRef = useRef(null);

  const tabs = [
    {
      id: 'overview',
      name: 'Overview',
      path: reportId ? `/reports/${reportId}` : '/dashboard',
      icon: LayoutDashboard,
    },
    {
      id: 'viability',
      name: '1. Viability',
      path: reportId ? `/reports/${reportId}/viability` : '/viability',
      icon: BrainCircuit,
    },
    {
      id: 'market',
      name: '2. Demand',
      path: reportId ? `/reports/${reportId}/market` : '/market',
      icon: Target,
    },
    {
      id: 'schemes',
      name: '3. Schemes',
      path: reportId ? `/reports/${reportId}/schemes` : '/schemes',
      icon: Award,
    },
    {
      id: 'financials',
      name: '4. Financials',
      path: reportId ? `/reports/${reportId}/financials` : '/financials',
      icon: TrendingUp,
    },
    {
      id: 'risk',
      name: '5. Risk Radar',
      path: reportId ? `/reports/${reportId}/risk` : '/risk',
      icon: ShieldAlert,
    },
    {
      id: 'swot',
      name: '6. SWOT',
      path: reportId ? `/reports/${reportId}/swot` : '/swot',
      icon: Grid3X3,
    },
    {
      id: 'dpr',
      name: '7. Bank DPR',
      path: reportId ? `/reports/${reportId}/dpr` : '/dpr',
      icon: FileText,
    },
  ];

  const checkIsActive = (itemId, itemPath) => {
    const current = location.pathname;
    if (itemId === 'overview') {
      return (
        current === '/dashboard' ||
        current === `/reports/${reportId}` ||
        (current.startsWith('/reports/') &&
          !current.includes('/viability') &&
          !current.includes('/market') &&
          !current.includes('/schemes') &&
          !current.includes('/financials') &&
          !current.includes('/risk') &&
          !current.includes('/swot') &&
          !current.includes('/dpr'))
      );
    }
    return current === itemPath || current === `/${itemId}` || current.endsWith(`/${itemId}`);
  };

  // Scroll active tab into view whenever route changes
  useEffect(() => {
    if (activeTabRef.current && containerRef.current) {
      activeTabRef.current.scrollIntoView({
        behavior: 'smooth',
        inline: 'center',
        block: 'nearest',
      });
    }
  }, [location.pathname]);

  return (
    <nav
      aria-label="Appraisal dimensions navigation"
      className="lg:hidden bg-white/95 backdrop-blur-md border border-slate-200/90 rounded-2xl p-1.5 shadow-subtle mb-3 overflow-hidden"
    >
      <div
        ref={containerRef}
        className="flex items-center gap-1.5 overflow-x-auto scroll-touch-x no-scrollbar py-0.5 px-1"
      >
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = checkIsActive(tab.id, tab.path);

          return (
            <NavLink
              key={tab.id}
              to={tab.path}
              ref={isActive ? activeTabRef : null}
              className={`flex items-center gap-1.5 text-xs font-semibold py-1.5 px-3 rounded-xl whitespace-nowrap transition-all duration-150 shrink-0 select-none ${
                isActive
                  ? 'bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-indigo-950 text-white shadow-md shadow-sovereign-950/20 font-bold border border-sovereign-700/60'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 border border-transparent'
              }`}
            >
              <Icon
                className={`w-3.5 h-3.5 shrink-0 transition-colors ${
                  isActive ? 'text-sky-300' : 'text-slate-400'
                }`}
              />
              <span><TranslatedText text={tab.name} /></span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}

export default MobileReportTabs;
