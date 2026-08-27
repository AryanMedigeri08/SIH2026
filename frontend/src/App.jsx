import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { CaseStudiesBar } from './components/CaseStudiesBar';
import { Dashboard } from './components/Dashboard/Dashboard';
import { FeasibilityWizard } from './components/Wizard/FeasibilityWizard';
import { DprModal } from './components/DprModal';
import { QuickCalculatorModal } from './components/QuickCalculatorModal';
import { checkHealth, generateFeasibility } from './services/api';
import { PITCH_CASES } from './data/pitchCases';
import confetti from 'canvas-confetti';

export function App() {
  const [health, setHealth] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [activeCaseId, setActiveCaseId] = useState('case-1');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Modals
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [isDprOpen, setIsDprOpen] = useState(false);
  const [isCalculatorOpen, setIsCalculatorOpen] = useState(false);

  // Health check on mount
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
      setIsWizardOpen(false);
      if (rep?.ml_viability?.verdict === 'SUITABLE') {
        confetti({ particleCount: 80, spread: 70, origin: { y: 0.8 } });
      }
    } catch (err) {
      alert(`Feasibility pipeline error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#070b14] text-slate-100 selection:bg-cyan-500 selection:text-white">
      
      {/* Global Navigation Header */}
      <Navbar
        health={health}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenWizard={() => setIsWizardOpen(true)}
        onOpenCalculator={() => setIsCalculatorOpen(true)}
      />

      {/* 1-Click SIH Pitch Preset Cases Bar */}
      <CaseStudiesBar
        activeCaseId={activeCaseId}
        onSelectCase={handleSelectCase}
        isLoading={isLoading}
      />

      {/* Main Content Area */}
      <main className="flex-1">
        {isLoading ? (
          <div className="max-w-7xl mx-auto py-24 px-4 text-center">
            <div className="inline-block p-4 rounded-2xl bg-slate-900 border border-cyan-500/30 shadow-glow mb-4">
              <div className="w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
            </div>
            <h3 className="text-lg font-bold font-outfit text-white">
              Executing 4-Tier Zero-Hallucination Pipeline...
            </h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
              Connecting Census 2011 demographics, 613 village amenities API, XGBoost viability model & Llama-3-70B credit synthesis.
            </p>
          </div>
        ) : (
          <Dashboard
            reportData={reportData}
            onOpenDpr={() => setIsDprOpen(true)}
            onOpenWizard={() => setIsWizardOpen(true)}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/60 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>🇮🇳 Udyam Saathi (उद्यम साथी) • Smart India Hackathon 2026</span>
          <span className="font-mono text-[11px] text-slate-400">
            Powered by FastAPI • Neon PostgreSQL • XGBoost • Groq Llama-3-70B
          </span>
        </div>
      </footer>

      {/* Modals */}
      <FeasibilityWizard
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
        onSubmit={handleWizardSubmit}
        isSubmitting={isLoading}
        initialData={PITCH_CASES[0].formData}
      />

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

export default App;
