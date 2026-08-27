import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { WizardPage } from './pages/WizardPage';
import { CalculatorPage } from './pages/CalculatorPage';
import { DataSourcesPage } from './pages/DataSourcesPage';
import { SchemesPage } from './pages/SchemesPage';
import { ReportDetailPage } from './pages/ReportDetailPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { DprModal } from './components/DprModal';
import { QuickCalculatorModal } from './components/QuickCalculatorModal';
import { checkHealth, generateFeasibility } from './services/api';
import { PITCH_CASES } from './data/pitchCases';
import confetti from 'canvas-confetti';

export function AppContent() {
  const [health, setHealth] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [activeCaseId, setActiveCaseId] = useState('case-1');
  const [isLoading, setIsLoading] = useState(false);

  // Modals
  const [isDprOpen, setIsDprOpen] = useState(false);
  const [isCalculatorOpen, setIsCalculatorOpen] = useState(false);

  // Initial Health check and benchmark load
  useEffect(() => {
    async function init() {
      const h = await checkHealth();
      setHealth(h);
      
      // Auto-load Case 1 on initial start
      try {
        setIsLoading(true);
        const rep = await generateFeasibility(PITCH_CASES[0].formData);
        setReportData(rep);
      } catch (e) {
        console.error("Initial load fallback:", e);
      } finally {
        setIsLoading(false);
      }
    }
    init();
  }, []);

  const handleSelectCase = async (pitchCase) => {
    setActiveCaseId(pitchCase.id);
    setIsLoading(true);
    try {
      const rep = await generateFeasibility(pitchCase.formData);
      setReportData(rep);
      if (rep?.ml_viability?.verdict === 'SUITABLE') {
        confetti({ particleCount: 50, spread: 60, origin: { y: 0.85 } });
      }
    } catch (err) {
      alert(`Feasibility error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleWizardSubmit = async (formData) => {
    setIsLoading(true);
    try {
      const rep = await generateFeasibility(formData);
      setReportData(rep);
      setActiveCaseId(null);
      if (rep?.ml_viability?.verdict === 'SUITABLE') {
        confetti({ particleCount: 80, spread: 70, origin: { y: 0.8 } });
      }
      return rep;
    } catch (err) {
      alert(`Feasibility pipeline error: ${err.message}`);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#070b14] text-slate-100 selection:bg-cyan-500 selection:text-white">
      
      {/* Global Navigation Header with Active Route Tabs */}
      <Navbar
        health={health}
        onOpenWizard={() => {}}
        onOpenCalculator={() => setIsCalculatorOpen(true)}
      />

      {/* Main Dynamic View Area via Route Switching */}
      <main className="flex-1">
        <Routes>
          <Route
            path="/"
            element={
              <DashboardPage
                reportData={reportData}
                activeCaseId={activeCaseId}
                isLoading={isLoading}
                onSelectCase={handleSelectCase}
                onOpenDpr={() => setIsDprOpen(true)}
              />
            }
          />
          <Route
            path="/dashboard"
            element={
              <DashboardPage
                reportData={reportData}
                activeCaseId={activeCaseId}
                isLoading={isLoading}
                onSelectCase={handleSelectCase}
                onOpenDpr={() => setIsDprOpen(true)}
              />
            }
          />
          <Route
            path="/wizard"
            element={
              <WizardPage
                onWizardSubmit={handleWizardSubmit}
                isLoading={isLoading}
              />
            }
          />
          <Route
            path="/new-assessment"
            element={
              <WizardPage
                onWizardSubmit={handleWizardSubmit}
                isLoading={isLoading}
              />
            }
          />
          <Route path="/calculator" element={<CalculatorPage />} />
          <Route path="/data-sources" element={<DataSourcesPage />} />
          <Route path="/schemes" element={<SchemesPage />} />
          <Route
            path="/reports/:reportId"
            element={<ReportDetailPage />}
          />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/60 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>🇮🇳 Udyam Saathi (उद्यम साथी) • Smart India Hackathon 2026</span>
          <span className="font-mono text-[11px] text-slate-400">
            Modular Production Architecture • FastAPI • Neon DB • XGBoost • Groq LLM
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
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
