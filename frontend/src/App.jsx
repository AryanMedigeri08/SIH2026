import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar/Sidebar';
import { CaseStudiesBar } from './components/CaseStudiesBar';
import { ReportGenerationLoader } from './components/ReportGenerationLoader';
import { AuthProvider, useAuth } from './context/AuthContext';
import { BusinessProvider, useBusiness } from './context/BusinessContext';
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

// Modals & Services
import { DprModal } from './components/DprModal';
import { QuickCalculatorModal } from './components/QuickCalculatorModal';
import { checkHealth, generateFeasibility, fetchFeasibilityReport } from './services/api';
import { PITCH_CASES } from './data/pitchCases';
import confetti from 'canvas-confetti';

// Route Wrapper Component for Page-Switch Skeletons & Layout Shell
function AppraisalSectionWrapper({ 
  children, 
  skeleton: SkeletonComponent, 
  reportData, 
  isLoading 
}) {
  if (isLoading || !reportData) {
    return <SkeletonComponent />;
  }

  return (
    <div className="animate-in fade-in duration-200">
      {children}
    </div>
  );
}

export function AppContent() {
  const [health, setHealth] = useState(null);
  const [activeCaseId, setActiveCaseId] = useState('case-1');
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

  const isAuthOrLanding = ['/landing', '/login', '/register'].includes(location.pathname);

  // Health check and guest fallback initial load
  useEffect(() => {
    async function init() {
      const h = await checkHealth();
      setHealth(h);
      
      // If not authenticated and no report data yet, auto-load Pitch Case 1
      if (!isAuthenticated && !reportData) {
        try {
          setIsLoadingInitial(true);
          const rep = await generateFeasibility(PITCH_CASES[0].formData);
          setReportData(rep);
        } catch (e) {
          console.error("Initial load fallback:", e);
        } finally {
          setIsLoadingInitial(false);
        }
      }
    }
    init();
  }, [isAuthenticated, reportData, setReportData]);

  // URL reportId synchronization: If route is /reports/:reportId/..., auto-load that specific report from API
  useEffect(() => {
    const match = location.pathname.match(/\/reports\/([^\/]+)/);
    if (match && match[1]) {
      const urlReportId = match[1];
      if (urlReportId !== 'full' && reportData?.report_id !== urlReportId) {
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
    }
  }, [location.pathname, reportData?.report_id, token, setReportData]);

  const handleSelectCase = async (pitchCase) => {
    setActiveCaseId(pitchCase.id);
    setIsGenerating(true);
    setGeneratingMeta({
      enterpriseName: pitchCase.formData?.enterprise_name,
      districtName: pitchCase.formData?.district_name,
      sector: pitchCase.formData?.sector,
    });

    try {
      const rep = await loadBenchmarkCase(pitchCase);
      if (rep?.ml_viability?.verdict === 'SUITABLE') {
        confetti({ particleCount: 50, spread: 60, origin: { y: 0.85 } });
      }
      navigate('/');
    } catch (err) {
      alert(`Feasibility error: ${err.message}`);
    } finally {
      setIsGenerating(false);
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
      navigate('/');
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
        <Route path="/landing" element={<LandingPage />} />
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
              {/* Overview & Core Synthesis */}
              <Route
                path="/"
                element={
                  <AppraisalSectionWrapper skeleton={OverviewSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <OverviewPage
                      reportData={reportData}
                      onOpenDpr={() => setIsDprOpen(true)}
                      onOpenWizard={() => navigate('/wizard')}
                    />
                  </AppraisalSectionWrapper>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <AppraisalSectionWrapper skeleton={OverviewSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <OverviewPage
                      reportData={reportData}
                      onOpenDpr={() => setIsDprOpen(true)}
                      onOpenWizard={() => navigate('/wizard')}
                    />
                  </AppraisalSectionWrapper>
                }
              />
              <Route
                path="/reports/:reportId"
                element={
                  <AppraisalSectionWrapper skeleton={OverviewSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <OverviewPage
                      reportData={reportData}
                      onOpenDpr={() => setIsDprOpen(true)}
                      onOpenWizard={() => navigate('/wizard')}
                    />
                  </AppraisalSectionWrapper>
                }
              />

              {/* 1. ML Viability & TreeSHAP */}
              <Route
                path="/viability"
                element={
                  <AppraisalSectionWrapper skeleton={ViabilitySkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <ViabilityPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />
              <Route
                path="/reports/:reportId/viability"
                element={
                  <AppraisalSectionWrapper skeleton={ViabilitySkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <ViabilityPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />

              {/* 2. Market & Local Demand */}
              <Route
                path="/market"
                element={
                  <AppraisalSectionWrapper skeleton={MarketSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <MarketDemandPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />
              <Route
                path="/reports/:reportId/market"
                element={
                  <AppraisalSectionWrapper skeleton={MarketSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <MarketDemandPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />

              {/* 3. Government Scheme Optimizer */}
              <Route
                path="/schemes"
                element={
                  <AppraisalSectionWrapper skeleton={SchemesSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <GovernmentSchemesPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />
              <Route
                path="/reports/:reportId/schemes"
                element={
                  <AppraisalSectionWrapper skeleton={SchemesSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <GovernmentSchemesPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />

              {/* 4. Financials & Cash Flow */}
              <Route
                path="/financials"
                element={
                  <AppraisalSectionWrapper skeleton={FinancialsSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <FinancialsPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />
              <Route
                path="/reports/:reportId/financials"
                element={
                  <AppraisalSectionWrapper skeleton={FinancialsSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <FinancialsPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />

              {/* 5. Comprehensive Risk Assessment */}
              <Route
                path="/risk"
                element={
                  <AppraisalSectionWrapper skeleton={RiskSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <RiskAssessmentPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />
              <Route
                path="/reports/:reportId/risk"
                element={
                  <AppraisalSectionWrapper skeleton={RiskSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <RiskAssessmentPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />

              {/* 6. Grounded SWOT Matrix */}
              <Route
                path="/swot"
                element={
                  <AppraisalSectionWrapper skeleton={SwotSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <SwotAnalysisPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />
              <Route
                path="/reports/:reportId/swot"
                element={
                  <AppraisalSectionWrapper skeleton={SwotSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <SwotAnalysisPage reportData={reportData} />
                  </AppraisalSectionWrapper>
                }
              />

              {/* 7. Official Bank DPR Package */}
              <Route
                path="/dpr"
                element={
                  <AppraisalSectionWrapper skeleton={DprSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <BankDprPage
                      reportData={reportData}
                      onOpenModal={() => setIsDprOpen(true)}
                    />
                  </AppraisalSectionWrapper>
                }
              />
              <Route
                path="/reports/:reportId/dpr"
                element={
                  <AppraisalSectionWrapper skeleton={DprSkeleton} reportData={reportData} isLoading={isLoadingInitial || loadingBusinesses}>
                    <BankDprPage
                      reportData={reportData}
                      onOpenModal={() => setIsDprOpen(true)}
                    />
                  </AppraisalSectionWrapper>
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
                element={<ReportDetailPage onOpenWizard={() => navigate('/wizard')} />}
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
        <BusinessProvider>
          <AppContent />
        </BusinessProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
