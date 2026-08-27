import React from 'react';
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
  Calculator,
  Database,
  Landmark,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  X,
  Building2,
} from 'lucide-react';

export function Sidebar({
  isCollapsed,
  onToggleCollapse,
  isMobileOpen,
  onCloseMobile,
  reportId,
}) {
  const location = useLocation();

  const reportNavItems = [
    {
      id: 'overview',
      name: 'Overview & Synthesis',
      path: reportId ? `/reports/${reportId}` : '/',
      exact: true,
      icon: LayoutDashboard,
      badge: null,
    },
    {
      id: 'viability',
      name: 'ML Viability & SHAP',
      path: reportId ? `/reports/${reportId}/viability` : '/viability',
      icon: BrainCircuit,
      badge: 'TreeSHAP',
    },
    {
      id: 'market',
      name: 'Market & Demand',
      path: reportId ? `/reports/${reportId}/market` : '/market',
      icon: Target,
      badge: 'Census 2011',
    },
    {
      id: 'schemes',
      name: 'Government Schemes',
      path: reportId ? `/reports/${reportId}/schemes` : '/schemes',
      icon: Award,
      badge: '10 Slabs',
    },
    {
      id: 'financials',
      name: 'Financials & Cash Flow',
      path: reportId ? `/reports/${reportId}/financials` : '/financials',
      icon: TrendingUp,
      badge: '5-Yr Horiz.',
    },
    {
      id: 'risk',
      name: 'Risk Assessment',
      path: reportId ? `/reports/${reportId}/risk` : '/risk',
      icon: ShieldAlert,
      badge: '8 Pillars',
    },
    {
      id: 'swot',
      name: 'SWOT Analysis',
      path: reportId ? `/reports/${reportId}/swot` : '/swot',
      icon: Grid3X3,
      badge: null,
    },
    {
      id: 'dpr',
      name: 'Bank DPR & Documents',
      path: reportId ? `/reports/${reportId}/dpr` : '/dpr',
      icon: FileText,
      badge: '7-Section',
    },
  ];

  const utilityNavItems = [
    {
      id: 'calculator',
      name: 'Loan Sizing Calculator',
      path: '/calculator',
      icon: Calculator,
    },
    {
      id: 'data-sources',
      name: 'Data Lineage & Schemas',
      path: '/data-sources',
      icon: Database,
    },
    {
      id: 'master-schemes',
      name: 'Master Schemes Catalog',
      path: '/master-schemes',
      icon: Landmark,
    },
  ];

  const renderNavLinks = (items) => {
    return (
      <div className="space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          // Determine active status accurately
          const isActive = item.exact 
            ? location.pathname === item.path || (item.id === 'overview' && (location.pathname === '/' || location.pathname === '/dashboard'))
            : location.pathname === item.path || (location.pathname.startsWith(item.path) && item.path !== '/');

          return (
            <NavLink
              key={item.id}
              to={item.path}
              onClick={onCloseMobile}
              title={isCollapsed ? item.name : undefined}
              className={`group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all relative ${
                isActive
                  ? 'bg-gradient-to-r from-sovereign-800 to-sovereign-900 text-white shadow-sm font-bold'
                  : 'text-slate-700 hover:bg-slate-100 hover:text-slate-950 font-medium'
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <Icon
                  className={`w-4 h-4 shrink-0 transition-transform ${
                    isActive ? 'text-white' : 'text-slate-500 group-hover:text-sovereign-800'
                  }`}
                />
                {!isCollapsed && (
                  <span className="truncate">{item.name}</span>
                )}
              </div>

              {!isCollapsed && item.badge && (
                <span
                  className={`text-[9px] px-1.5 py-0.5 rounded-md font-mono font-bold shrink-0 ${
                    isActive
                      ? 'bg-white/20 text-white'
                      : 'bg-slate-100 text-slate-600 border border-slate-200'
                  }`}
                >
                  {item.badge}
                </span>
              )}

              {/* Active rail indicator */}
              {isActive && (
                <div className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-sky-400 rounded-r-full" />
              )}
            </NavLink>
          );
        })}
      </div>
    );
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm lg:hidden animate-in fade-in"
          onClick={onCloseMobile}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 z-40 bg-white border-r border-slate-200 flex flex-col justify-between transition-all duration-300 shadow-card lg:static lg:z-auto ${
          isMobileOpen ? 'left-0 w-72' : '-left-full lg:left-0'
        } ${isCollapsed ? 'lg:w-20' : 'lg:w-64'}`}
      >
        {/* Top Header / Branding */}
        <div>
          <div className="h-16 px-4 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-sovereign-800 text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-sm">
                उ
              </div>
              {!isCollapsed && (
                <div className="leading-tight truncate">
                  <div className="font-outfit font-black text-sm text-slate-900 tracking-tight">
                    Udyam Saathi
                  </div>
                  <div className="text-[10px] text-sovereign-700 font-semibold uppercase tracking-wider">
                    Credit Feasibility
                  </div>
                </div>
              )}
            </div>

            {/* Mobile Close Button */}
            <button
              onClick={onCloseMobile}
              className="lg:hidden text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Desktop Collapse Toggle */}
            <button
              onClick={onToggleCollapse}
              className="hidden lg:flex text-slate-400 hover:text-slate-800 p-1.5 rounded-lg hover:bg-slate-100 transition"
              title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {isCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronLeft className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* Navigation Section: Feasibility Assessment Pages */}
          <div className="p-3 space-y-4 overflow-y-auto max-h-[calc(100vh-14rem)]">
            <div>
              {!isCollapsed && (
                <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                  Appraisal Sections
                </div>
              )}
              {renderNavLinks(reportNavItems)}
            </div>

            {/* Navigation Section: Standalone Financial & Data Tools */}
            <div className="pt-2 border-t border-slate-200">
              {!isCollapsed && (
                <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                  System Tools
                </div>
              )}
              {renderNavLinks(utilityNavItems)}
            </div>
          </div>
        </div>

        {/* Bottom Callout / Wizard Action */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/70">
          {!isCollapsed ? (
            <NavLink
              to="/wizard"
              onClick={onCloseMobile}
              className="flex items-center justify-center gap-2 w-full py-2.5 px-3 rounded-xl bg-sovereign-800 hover:bg-sovereign-700 text-white text-xs font-bold shadow-sm transition group"
            >
              <Sparkles className="w-3.5 h-3.5 text-sky-300 group-hover:rotate-12 transition-transform" />
              <span>New Assessment</span>
            </NavLink>
          ) : (
            <NavLink
              to="/wizard"
              onClick={onCloseMobile}
              title="Launch New Assessment Wizard"
              className="flex items-center justify-center w-full p-2.5 rounded-xl bg-sovereign-800 hover:bg-sovereign-700 text-white text-xs font-bold shadow-sm transition"
            >
              <Sparkles className="w-4 h-4 text-sky-300" />
            </NavLink>
          )}
        </div>
      </aside>
    </>
  );
}
export default Sidebar;
