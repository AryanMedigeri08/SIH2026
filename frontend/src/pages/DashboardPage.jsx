import React from 'react';
import { CaseStudiesBar } from '../components/CaseStudiesBar';
import { Dashboard } from '../components/Dashboard/Dashboard';

export function DashboardPage({
  reportData,
  activeCaseId,
  isLoading,
  onSelectCase,
  onOpenDpr,
  onOpenWizard,
}) {
  return (
    <div className="space-y-4">
      {/* 1-Click SIH Pitch Preset Cases Bar */}
      <CaseStudiesBar
        activeCaseId={activeCaseId}
        onSelectCase={onSelectCase}
        isLoading={isLoading}
      />

      {/* Main Content Area */}
      {isLoading ? (
        <div className="max-w-7xl mx-auto py-24 px-4 text-center">
          <div className="inline-block p-4 rounded-2xl bg-slate-900 border border-cyan-500/30 shadow-glow mb-4">
            <div className="w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
          <h3 className="text-lg font-bold font-outfit text-white">
            Executing 4-Tier Zero-Hallucination Pipeline...
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            Connecting Census 2011 demographics, 613 village amenities API, XGBoost viability model & Groq LLM credit synthesis.
          </p>
        </div>
      ) : (
        <Dashboard
          reportData={reportData}
          onOpenDpr={onOpenDpr}
          onOpenWizard={onOpenWizard}
        />
      )}
    </div>
  );
}
