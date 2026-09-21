import React from 'react';
import { NavLink, useLocation, Link, useNavigate } from 'react-router-dom';
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
  ChevronLeft,
  ChevronRight,
  Sparkles,
  X,
  Building2,
  PlusCircle,
  Layers,
  Tag,
  Megaphone,
  LogOut,
} from 'lucide-react';
import { useBusiness } from '../../context/BusinessContext';
import { BusinessSwitcher, BusinessStatusPill } from '../BusinessSwitcher';
import { LanguageSelector } from '../LanguageSelector';
import { TranslatedText } from '../TranslatedText';
import { useLanguage } from '../../context/LanguageContext';
import { useViewMode } from '../../context/ViewModeContext';
import { useAuth } from '../../context/AuthContext';

export function Sidebar({
  isCollapsed,
  onToggleCollapse,
  isMobileOpen,
  onCloseMobile,
  reportId,
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const { activeBusiness } = useBusiness();
  const { isBeneficiary } = useViewMode();
  const { t } = useLanguage();
  const { isAuthenticated, userProfile, logout } = useAuth();

  const handleLogout = () => {
    onCloseMobile();
    navigate('/login', { replace: true });
    void logout();
  };

  const reportNavItems = isBeneficiary
    ? [
        {
          id: 'overview',
          name: 'My Business Plan',
          path: reportId ? `/reports/${reportId}` : '/dashboard',
          icon: LayoutDashboard,
          badge: null,
        },
        {
          id: 'pricing',
          name: 'Pricing & Margins',
          path: reportId ? `/reports/${reportId}/pricing` : '/pricing',
          icon: Tag,
          badge: 'Unit Profit',
        },
        {
          id: 'marketing',
          name: 'Village Marketing Kit',
          path: reportId ? `/reports/${reportId}/marketing` : '/marketing',
          icon: Megaphone,
          badge: 'WhatsApp/Haat',
        },
        {
          id: 'schemes',
          name: 'Government Subsidies',
          path: reportId ? `/reports/${reportId}/schemes` : '/schemes',
          icon: Award,
          badge: 'Grant ₹',
        },
        {
          id: 'calculator',
          name: 'Loan Calculator & EMI',
          path: '/calculator',
          icon: Calculator,
          badge: 'Quarterly',
        },
        {
          id: 'dpr',
          name: 'Print Bank Application',
          path: reportId ? `/reports/${reportId}/dpr` : '/dpr',
          icon: FileText,
          badge: 'Download PDF',
        },
      ]
    : [
        {
          id: 'overview',
          name: 'Master Appraisal Memo',
          path: reportId ? `/reports/${reportId}` : '/dashboard',
          icon: LayoutDashboard,
          badge: null,
        },
        {
          id: 'viability',
          name: '10-D ML Viability & TreeSHAP',
          path: reportId ? `/reports/${reportId}/viability` : '/viability',
          icon: BrainCircuit,
          badge: 'TreeSHAP',
        },
        {
          id: 'market',
          name: 'Market Demographics & TAM',
          path: reportId ? `/reports/${reportId}/market` : '/market',
          icon: Target,
          badge: 'Census 2011',
        },
        {
          id: 'schemes',
          name: 'Scheme Optimizer',
          path: reportId ? `/reports/${reportId}/schemes` : '/schemes',
          icon: Award,
          badge: '10 Slabs',
        },
        {
          id: 'financials',
          name: 'Financials & DSCR Solvency',
          path: reportId ? `/reports/${reportId}/financials` : '/financials',
          icon: TrendingUp,
          badge: '5-Yr Horiz.',
        },
        {
          id: 'risk',
          name: '8-Pillar Risk Radar',
          path: reportId ? `/reports/${reportId}/risk` : '/risk',
          icon: ShieldAlert,
          badge: '8 Pillars',
        },
        {
          id: 'swot',
          name: 'SWOT Appraisal Matrix',
          path: reportId ? `/reports/${reportId}/swot` : '/swot',
          icon: Grid3X3,
          badge: 'Grounded',
        },
        {
          id: 'dpr',
          name: 'Bank DPR Memorandum',
          path: reportId ? `/reports/${reportId}/dpr` : '/dpr',
          icon: FileText,
          badge: '7-Section',
        },
      ];

  const utilityNavItems = isBeneficiary
    ? []
    : [
        {
          id: 'calculator',
          name: 'DSCR Sensitivity Engine',
          path: '/calculator',
          icon: Calculator,
        },
        {
          id: 'data-sources',
          name: 'Data Sources Lineage',
          path: '/data-sources',
          icon: Database,
          badge: 'Audit',
        },
      ];

  const checkIsActive = (itemId, itemPath) => {
    const current = location.pathname;
    if (itemId === 'overview') {
      return (
        current === '/dashboard' ||
        current === `/reports/${reportId}` ||
        (/^\/reports\/[^\/]+$/.test(current) &&
          !current.includes('/viability') &&
          !current.includes('/market') &&
          !current.includes('/schemes') &&
          !current.includes('/financials') &&
          !current.includes('/risk') &&
          !current.includes('/swot') &&
          !current.includes('/pricing') &&
          !current.includes('/marketing') &&
          !current.includes('/dpr'))
      );
    }
    return current === itemPath || current === `/${itemId}` || current.endsWith(`/${itemId}`);
  };

  const renderNavLinks = (items) => {
    return (
      <div className="space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = checkIsActive(item.id, item.path);

          return (
            <NavLink
              key={item.id}
              to={item.path}
              onClick={onCloseMobile}
              title={isCollapsed ? item.name : undefined}
              className={`group relative flex items-center ${
                isCollapsed ? 'justify-center px-2 py-2.5' : 'justify-between px-3 py-2.5'
              } rounded-xl text-xs font-medium transition-all duration-200 ${
                isActive
                  ? 'sidebar-item-active font-bold shadow-md shadow-sovereign-900/20 text-white'
                  : 'sidebar-item-inactive hover:bg-slate-100/90 text-slate-700'
              }`}
            >
              <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} min-w-0`}>
                <Icon
                  className={`w-4 h-4 shrink-0 transition-all duration-200 ${
                    isActive ? 'text-sky-300' : 'text-slate-500 group-hover:text-slate-900'
                  }`}
                />
                {!isCollapsed && (
                  <span className={`truncate ${isActive ? 'text-white font-bold' : 'text-slate-700'}`}>
                    <TranslatedText text={item.name} />
                  </span>
                )}
              </div>

              {!isCollapsed && item.badge && (
                <span className="sidebar-badge text-[9px] px-1.5 py-0.5 rounded-md font-mono font-bold shrink-0 transition-colors">
                  <TranslatedText text={item.badge} />
                </span>
              )}

              {/* Glowing active indicator rail */}
              {isActive && (
                <div className="absolute left-0 top-1.5 bottom-1.5 w-1.5 bg-gradient-to-b from-cyan-400 to-sky-400 rounded-r-full shadow-[0_0_8px_rgba(56,189,248,0.8)]" />
              )}
            </NavLink>
          );
        })}
      </div>
    );
  };

  const activeStatus = activeBusiness?.business_status || { code: 'draft', label: 'Draft' };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm lg:hidden animate-in fade-in duration-200"
          onClick={onCloseMobile}
        />
      )}

      {/* Fixed Sticky Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 z-40 bg-white/95 backdrop-blur-md border-r border-slate-200 flex flex-col justify-between transition-all duration-300 shadow-card lg:sticky lg:top-14 sm:lg:top-16 lg:h-[calc(100vh-3.5rem)] sm:lg:h-[calc(100vh-4rem)] lg:overflow-y-auto lg:overflow-x-hidden lg:shrink-0 ${
          isMobileOpen ? 'left-0 w-[min(72vw,18rem)]' : '-left-full lg:left-0'
        } ${isCollapsed ? 'lg:w-20' : 'lg:w-64'}`}
      >
        {/* Top Header / Collapse Control (Non-redundant branding) */}
        <div>
          <div className="h-14 px-3.5 border-b border-slate-200/80 flex items-center justify-between bg-gradient-to-b from-slate-50/80 to-white">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="p-1.5 rounded-lg bg-sovereign-50 text-sovereign-800 border border-sovereign-200 shrink-0">
                <Layers className="w-4 h-4 text-sovereign-800" />
              </div>
              {!isCollapsed && (
                <div className="leading-tight truncate">
                  <div className="font-outfit font-black text-xs text-slate-800 uppercase tracking-wider">
                    Navigation
                  </div>
                  <div className="text-[10px] text-slate-500 font-medium">
                    Credit Appraisal
                  </div>
                </div>
              )}
            </div>

            {/* Mobile Close Button */}
            <button
              onClick={onCloseMobile}
              className="lg:hidden text-slate-400 hover:text-slate-800 p-1.5 rounded-xl hover:bg-slate-100 transition"
              title="Close navigation"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Desktop Collapse / Expand Toggle */}
            <button
              onClick={onToggleCollapse}
              className="hidden lg:flex text-slate-400 hover:text-slate-800 p-1.5 rounded-xl hover:bg-slate-100 transition border border-transparent hover:border-slate-200"
              title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>

          {/* ═══════ Mobile-Only: Enterprise Switcher & Language Selector ═══════ */}
          <div className="lg:hidden px-3 pt-3 space-y-2.5">
            {/* Enterprise Switcher (full-width compact mode) */}
            {isAuthenticated && (
              <div>
                <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500 font-mono flex items-center gap-1 mb-1.5 px-0.5">
                  <Building2 className="w-3 h-3 text-sovereign-700" />
                  Your Enterprises
                </span>
                <BusinessSwitcher compact />
              </div>
            )}
            {/* Language Selector (full-width) */}
            <LanguageSelector compact />
          </div>

          {/* Active Enterprise Banner Pill (Clean info view - NO duplicate dropdown) */}
          {!isCollapsed && activeBusiness && (
            <div className="p-3 mx-3 mt-3 rounded-xl bg-slate-50 border border-slate-200/90 shadow-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500 font-mono flex items-center gap-1">
                  <Building2 className="w-3 h-3 text-sovereign-700" />
                  Active Enterprise
                </span>
                <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded bg-white border border-slate-200 text-slate-700">
                  {activeBusiness.sector || 'MSME'}
                </span>
              </div>
              <div className="font-outfit font-extrabold text-xs text-slate-900 truncate">
                {activeBusiness.business_name}
              </div>
              <div className="pt-0.5">
                <BusinessStatusPill status={activeStatus} size="xs" />
              </div>
            </div>
          )}

          {/* Nav Section: Dedicated Views */}
          <div className="px-3 py-3">
            <div className="flex items-center justify-between px-2 mb-2">
              <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-slate-500">
                {isCollapsed ? (isBeneficiary ? 'Biz' : 'Audit') : (isBeneficiary ? 'Business Toolkit' : 'Appraisal Sections')}
              </span>
              {!isCollapsed && (
                <span className="text-[9px] font-mono font-bold bg-slate-100 border border-slate-200 text-slate-600 px-1.5 py-0.2 rounded">
                  {reportNavItems.length} {isBeneficiary ? 'Tools' : 'Views'}
                </span>
              )}
            </div>
            {renderNavLinks(reportNavItems)}
          </div>

          {/* Nav Section: System Utilities (Rendered only when utilities exist) */}
          {utilityNavItems.length > 0 && (
            <div className="px-3 py-1 border-t border-slate-100">
              <div className="flex items-center justify-between px-2 mb-2 mt-2">
                <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-slate-500">
                  {isCollapsed ? 'Tools' : 'Underwriting Tools'}
                </span>
              </div>
              {renderNavLinks(utilityNavItems)}
            </div>
          )}
        </div>

        {/* Bottom Bar / Quick Action + Mobile User Identity */}
        <div className="p-3 border-t border-slate-200/80 bg-slate-50/50 space-y-2">
          {/* Mobile-Only: User Identity & Logout */}
          {isAuthenticated && (
            <div className="lg:hidden flex items-center justify-between gap-2 p-2.5 rounded-xl bg-white border border-slate-200 shadow-xs">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-700 text-white flex items-center justify-center text-[11px] font-bold shrink-0">
                  {userProfile?.name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 truncate">{userProfile?.name || 'User'}</div>
                  <div className="text-[10px] text-slate-500 truncate">{userProfile?.email || ''}</div>
                </div>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-[11px] font-bold transition-colors shrink-0"
                title="Sign out of Udyam Saathi"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden xs:inline">Logout</span>
              </button>
            </div>
          )}

          {!isCollapsed ? (
            <Link
              to="/wizard"
              onClick={onCloseMobile}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-gradient-to-r from-sovereign-800 to-sky-700 hover:from-sovereign-700 hover:to-sky-600 text-white text-xs font-bold shadow-md shadow-sovereign-900/15 border border-sky-400/20 transition-all group"
            >
              <PlusCircle className="w-3.5 h-3.5 text-sky-200 group-hover:rotate-90 transition-transform" />
              <span>+ New Enterprise</span>
            </Link>
          ) : (
            <Link
              to="/wizard"
              onClick={onCloseMobile}
              title="Create New Enterprise"
              className="w-full flex items-center justify-center p-2 rounded-xl bg-sovereign-800 text-white hover:bg-sovereign-700 transition shadow-sm"
            >
              <PlusCircle className="w-4 h-4" />
            </Link>
          )}
        </div>
      </aside>
    </>
  );
}

export default Sidebar;

