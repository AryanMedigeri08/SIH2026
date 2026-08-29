import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FeasibilityWizard } from '../components/Wizard/FeasibilityWizard';
import { Sparkles, ArrowLeft, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { PITCH_CASES } from '../data/pitchCases';
import { useLanguage } from '../context/LanguageContext';

export function WizardPage({ onWizardSubmit, isLoading }) {
  const navigate = useNavigate();
  const [selectedTemplateIndex, setSelectedTemplateIndex] = useState(0);
  const { language, setLanguage, t } = useLanguage();

  // Automatically reset active language to English when starting a fresh enterprise analysis
  useEffect(() => {
    if (language !== "en") {
      setLanguage("en");
    }
  }, []);

  const handleSubmit = async (formData) => {
    if (language !== "en") {
      setLanguage("en");
    }
    await onWizardSubmit({ ...formData, language: "en" });
    navigate('/dashboard');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Top Banner Header */}
      <div className="glass-panel p-6 border-l-4 border-sovereign-800 bg-white shadow-card border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <button
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 font-semibold mb-2 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{t('backToDashboard')}</span>
          </button>
          <h1 className="text-2xl font-outfit font-extrabold text-slate-900 flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-sovereign-50 text-sovereign-800 border border-sovereign-200">
              <Sparkles className="w-5 h-5" />
            </span>
            <span>7-Step Rural & Semi-Urban Enterprise Feasibility Wizard</span>
          </h1>
          <p className="text-xs text-slate-600 mt-1 max-w-2xl font-medium">
            Input enterprise specifications, LGD location hierarchy, capital outlay, supplementary business context, and loan parameters to generate an instant statutory bank appraisal report with zero financial hallucination.
          </p>
        </div>

        {/* Quick Preload Benchmark Template selector */}
        <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl text-xs space-y-1.5 shrink-0">
          <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider block">
            Preload Benchmark Case:
          </span>
          <select
            value={selectedTemplateIndex}
            onChange={(e) => setSelectedTemplateIndex(Number(e.target.value))}
            className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 w-full font-medium"
          >
            {PITCH_CASES.map((c, idx) => (
              <option key={c.id} value={idx}>
                {c.title} ({c.state})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Embedded Wizard Container */}
      <div className="relative">
        <FeasibilityWizard
          isOpen={true}
          onClose={() => navigate('/dashboard')}
          onSubmit={handleSubmit}
          isSubmitting={isLoading}
          initialData={{ ...PITCH_CASES[selectedTemplateIndex]?.formData, language: "en" }}
        />
      </div>

    </div>
  );
}
export default WizardPage;
