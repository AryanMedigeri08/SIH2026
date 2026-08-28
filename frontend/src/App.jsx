import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Navigate, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar/Sidebar';
import { CaseStudiesBar } from './components/CaseStudiesBar';
import { ReportGenerationLoader } from './components/ReportGenerationLoader';
import { AuthProvider, useAuth } from './context/AuthContext';
import { BusinessProvider, useBusiness } from './context/BusinessContext';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import { ProtectedRoute } from './components/ProtectedRoute';

// Public & Auth Pages
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';

// Routed Appraisal Pages
import { OverviewPage } from './pages/report/OverviewPage';
import { ViabilityPage } from './pages/report/ViabilityPage';
import { MarketDemandPage } from './pages/report/MarketDemandPage';
import { GovernmentSchemesPage } from './pages/report/GovernmentSchemesPage';
import { FinancialsPage } from './pages/report/FinancialsPage';
import { RiskAssessmentPage } from './pages/report/RiskAssessmentPage';
import { SwotAnalysisPage } from './pages/report/SwotAnalysisPage';
import { BankDprPage } from './pages/report/BankDprPage';

// Standalone System Pages
import { WizardPage } from './pages/WizardPage';
import { CalculatorPage } from './pages/CalculatorPage';
import { DataSourcesPage } from './pages/DataSourcesPage';
import { SchemesPage } from './pages/SchemesPage';
import { ReportDetailPage } from './pages/ReportDetailPage';
import { NotFoundPage } from './pages/NotFoundPage';

// Skeletons
import {
  OverviewSkeleton,
  ViabilitySkeleton,
  MarketSkeleton,
  SchemesSkeleton,
  FinancialsSkeleton,
  RiskSkeleton,
  SwotSkeleton,
  DprSkeleton,
} from './components/Skeletons/CardSkeletons';

import { BarChart3, Sparkles, ArrowRight } from 'lucide-react';
import { DprModal } from './components/DprModal';
import { QuickCalculatorModal } from './components/QuickCalculatorModal';
import { checkHealth, generateFeasibility, fetchFeasibilityReport } from './services/api';
import { PITCH_CASES } from './data/pitchCases';
import confetti from 'canvas-confetti';

// Empty State View when no enterprise appraisal is loaded
function EmptyAppraisalState({ onOpenWizard }) {
  const navigate = useNavigate();
  return (
    <div className="py-12 sm:py-16 px-4 text-center">
      <div className="bg-white/90 backdrop-blur-md border border-slate-200/90 rounded-3xl p-8 sm:p-12 max-w-xl mx-auto shadow-xl space-y-6 relative overflow-hidden">
        {/* Ambient Background Glow */}
        <div className="absolute -top-16 -right-16 w-36 h-36 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute -bottom-16 -left-16 w-36 h-36 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />

        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-sovereign-900 to-indigo-900 border border-sovereign-700 text-cyan-300 mx-auto flex items-center justify-center shadow-lg shadow-sovereign-950/20">
          <BarChart3 className="w-8 h-8 text-cyan-300" />
        </div>

        <div className="space-y-2">
          <h3 className="text-xl sm:text-2xl font-bold font-display text-slate-900 tracking-tight">
            No Active Enterprise Assessment Loaded
          </h3>
          <p className="text-xs sm:text-sm text-slate-600 font-medium leading-relaxed max-w-md mx-auto">
            Select one of the benchmark scenarios from the <span className="font-semibold text-sovereign-900">Preset Scenarios</span> bar above, or launch a new enterprise appraisal.
          </p>
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => onOpenWizard ? onOpenWizard() : navigate('/wizard')}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 text-xs font-bold text-white bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-indigo-950 hover:from-sovereign-800 hover:to-indigo-900 px-6 py-3 rounded-xl shadow-md shadow-sovereign-950/20 border border-sovereign-700 transition-all duration-200 group"
          >
            <Sparkles className="w-4 h-4 text-cyan-300 group-hover:scale-110 transition-transform" />
            <span>Launch Feasibility Wizard</span>
            <ArrowRight className="w-4 h-4 text-slate-300 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Route Wrapper Component for Page-Switch Skeletons & Empty State Handling
function AppraisalSectionWrapper({ 
  children, 
  skeleton: SkeletonComponent, 
  reportData, 
  isLoading,
  onOpenWizard
}) {
  if (isLoading) {
    return <SkeletonComponent />;
  }

  if (!reportData) {
    return <EmptyAppraisalState onOpenWizard={onOpenWizard} />;
  }

  return (
    <div className="animate-in fade-in duration-200">
      {children}
    </div>
  );
}

export function AppContent() {
  const [health, setHealth] = useState(null);
  const [activeCaseId, setActiveCaseId] = useState(null);
  const [isLoadingInitial, setIsLoadingInitial] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingMeta, setGeneratingMeta] = useState({});

  // Sidebar Layout State
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Modals
  const [isDprOpen, setIsDprOpen] = useState(false);
  const [isCalculatorOpen, setIsCalculatorOpen] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, token } = useAuth();
  const {
    reportData,
    dprData,
    activeBusiness,
    businesses,
    loadingBusinesses,
    hasBusinesses,
    createAndSaveBusiness,
    loadBenchmarkCase,
    setReportData,
  } = useBusiness();
  const { language } = useLanguage();

  const isAuthOrLanding = ['/', '/landing', '/login', '/register'].includes(location.pathname);

  // Health check on app start
  useEffect(() => {
    async function init() {
      const h = await checkHealth();
      setHealth(h);
    }
    init();
  }, []);

  const lastLoadedReportUrlRef = useRef(null);
  const isSelectingCaseRef = useRef(false);

  // URL reportId synchronization: If route is /reports/:reportId/..., auto-load that specific report from API
  useEffect(() => {
    if (isSelectingCaseRef.current) return;

    const match = location.pathname.match(/\/reports\/([^\/]+)/);
    if (match && match[1]) {
      const urlReportId = match[1];
      if (urlReportId !== 'full' && lastLoadedReportUrlRef.current !== urlReportId && token) {
        lastLoadedReportUrlRef.current = urlReportId;
        async function loadReportFromUrl() {
          try {
            setIsLoadingInitial(true);
            const rep = await fetchFeasibilityReport(urlReportId, token);
            if (rep && rep.report_id) {
              setReportData(rep);
            }
          } catch (e) {
            console.warn(`Could not load report ${urlReportId} from URL:`, e);
          } finally {
            setIsLoadingInitial(false);
          }
        }
        loadReportFromUrl();
      }
    } else {
      lastLoadedReportUrlRef.current = null;
    }
  }, [location.pathname, token, setReportData]);

  const handleSelectCase = async (pitchCase) => {
    isSelectingCaseRef.current = true;
    setActiveCaseId(pitchCase.id);
    setIsGenerating(true);
    setGeneratingMeta({
      enterpriseName: pitchCase.formData?.enterprise_name,
      districtName: pitchCase.formData?.district_name,
      sector: pitchCase.formData?.sector,
    });

    // If currently on a /reports/:id path, immediately switch to root to prevent stale URL sync
    if (location.pathname.startsWith('/reports/')) {
      navigate('/dashboard', { replace: true });
    }

    try {
      const rep = await loadBenchmarkCase(pitchCase);
      if (rep?.ml_viability?.verdict === 'SUITABLE') {
        confetti({ particleCount: 50, spread: 60, origin: { y: 0.85 } });
      }
      navigate('/dashboard');
    } catch (err) {
      alert(`Feasibility error: ${err.message}`);
    } finally {
      setIsGenerating(false);
      // Give React router microtask a tick before re-enabling URL auto-watcher
      setTimeout(() => {
        isSelectingCaseRef.current = false;
      }, 100);
    }
  };

  const handleWizardSubmit = async (formData) => {
    setIsGenerating(true);
    setGeneratingMeta({
      enterpriseName: formData?.enterprise_name,
      districtName: formData?.district_name,
      sector: formData?.sector,
    });

    try {
      const created = await createAndSaveBusiness(formData);
      setActiveCaseId(null);
      confetti({ particleCount: 80, spread: 70, origin: { y: 0.8 } });
      navigate('/dashboard');
      return created;
    } catch (err) {
      alert(`Enterprise appraisal error: ${err.message}`);
      throw err;
    } finally {
      setIsGenerating(false);
    }
  };

  // If on Landing / Login / Register pages, render full screen without app sidebar
  if (isAuthOrLanding) {
    return (
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/landing" element={<Navigate to="/" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 selection:bg-sovereign-200 selection:text-sovereign-900">
      
      {/* Top Navbar with Multi-Business Switcher */}
      <Navbar
        health={health}
        onToggleMobileSidebar={() => setIsMobileSidebarOpen(prev => !prev)}
      />

      {/* Main Workspace Layout with Collapsible Sidebar */}
      <div className="flex-1 flex max-w-[1600px] w-full mx-auto">
        
        {/* Collapsible Left Sidebar */}
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(prev => !prev)}
          isMobileOpen={isMobileSidebarOpen}
          onCloseMobile={() => setIsMobileSidebarOpen(false)}
          reportId={reportData?.report_id}
        />

        {/* Main Content Body */}
        <main className="flex-1 min-w-0 px-4 sm:px-6 lg:px-8 py-6 space-y-6 overflow-x-hidden">
          
          {/* Top Benchmark Pitch Cases Bar */}
          <CaseStudiesBar
            activeCaseId={activeCaseId}
            onSelectCase={handleSelectCase}
            isLoading={isGenerating || isLoadingInitial || loadingBusinesses}
          />

          {/* Staged Full-Page Loader for New Assessment Generation */}
          {isGenerating ? (
            <ReportGenerationLoader
              enterpriseName={generatingMeta.enterpriseName}
              districtName={generatingMeta.districtName}
              sector={generatingMeta.sector}
            />
          ) : (
            <Routes>
              {/* Protected Overview & Core Synthesis Dashboard */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={OverviewSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses} onOpenWizard={() => navigate('/wizard')}>
                      <OverviewPage
                        reportData={reportData}
                        onOpenDpr={() => setIsDprOpen(true)}
                        onOpenWizard={() => navigate('/wizard')}
                      />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reports/:reportId"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={OverviewSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses} onOpenWizard={() => navigate('/wizard')}>
                      <OverviewPage
                        reportData={reportData}
                        onOpenDpr={() => setIsDprOpen(true)}
                        onOpenWizard={() => navigate('/wizard')}
                      />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />

              {/* 1. ML Viability & TreeSHAP */}
              <Route
                path="/viability"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={ViabilitySkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <ViabilityPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reports/:reportId/viability"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={ViabilitySkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <ViabilityPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />

              {/* 2. Market & Local Demand */}
              <Route
                path="/market"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={MarketSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <MarketDemandPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reports/:reportId/market"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={MarketSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <MarketDemandPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />

              {/* 3. Government Scheme Optimizer */}
              <Route
                path="/schemes"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={SchemesSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <GovernmentSchemesPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reports/:reportId/schemes"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={SchemesSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <GovernmentSchemesPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />

              {/* 4. Financials & Cash Flow */}
              <Route
                path="/financials"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={FinancialsSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <FinancialsPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reports/:reportId/financials"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={FinancialsSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <FinancialsPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />

              {/* 5. Comprehensive Risk Assessment */}
              <Route
                path="/risk"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={RiskSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <RiskAssessmentPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reports/:reportId/risk"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={RiskSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <RiskAssessmentPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />

              {/* 6. Grounded SWOT Matrix */}
              <Route
                path="/swot"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={SwotSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <SwotAnalysisPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reports/:reportId/swot"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={SwotSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <SwotAnalysisPage reportData={reportData} />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />

              {/* 7. Official Bank DPR Package */}
              <Route
                path="/dpr"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={DprSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <BankDprPage
                        reportData={reportData}
                        onOpenModal={() => setIsDprOpen(true)}
                      />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reports/:reportId/dpr"
                element={
                  <ProtectedRoute>
                    <AppraisalSectionWrapper skeleton={DprSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                      <BankDprPage
                        reportData={reportData}
                        onOpenModal={() => setIsDprOpen(true)}
                      />
                    </AppraisalSectionWrapper>
                  </ProtectedRoute>
                }
              />

              {/* 7-Step Feasibility Wizard */}
              <Route
                path="/wizard"
                element={
                  <ProtectedRoute>
                    <WizardPage
                      onWizardSubmit={handleWizardSubmit}
                      isLoading={isGenerating}
                    />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/new-assessment"
                element={
                  <ProtectedRoute>
                    <WizardPage
                      onWizardSubmit={handleWizardSubmit}
                      isLoading={isGenerating}
                    />
                  </ProtectedRoute>
                }
              />

              {/* Public Discovery Pages */}
              <Route path="/calculator" element={<CalculatorPage />} />
              <Route path="/data-sources" element={<DataSourcesPage />} />
              <Route path="/master-schemes" element={<SchemesPage />} />
              <Route
                path="/reports/:reportId/full"
                element={
                  <ProtectedRoute>
                    <ReportDetailPage onOpenWizard={() => navigate('/wizard')} />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          )}

        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-5 text-center text-xs text-slate-600 shadow-subtle">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="font-medium">🇮🇳 Udyam Saathi (उद्यम साथी) • Smart India Hackathon 2026</span>
          <span className="font-mono text-[11px] text-slate-500 font-medium">
            Multi-Page Institutional Architecture • Multi-Business State Persistence • FastAPI • PostgreSQL • XGBoost • Groq LLM
          </span>
        </div>
      </footer>

      {/* Global Modals */}
      <DprModal
        isOpen={isDprOpen}
        onClose={() => setIsDprOpen(false)}
        reportId={reportData?.report_id}
        reportData={reportData}
      />

      <QuickCalculatorModal
        isOpen={isCalculatorOpen}
        onClose={() => setIsCalculatorOpen(false)}
      />

    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <LanguageProvider>
          <BusinessProvider>
            <AppContent />
          </BusinessProvider>
        </LanguageProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
