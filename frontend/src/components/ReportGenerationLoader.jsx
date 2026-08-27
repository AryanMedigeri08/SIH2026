import React, { useState, useEffect } from 'react';
import { 
  Database, Landmark, Sparkles, BrainCircuit, 
  CheckCircle2, Clock, ShieldCheck, Activity, Loader2 
} from 'lucide-react';

export function ReportGenerationLoader({ enterpriseName, districtName, sector }) {
  const stages = [
    { id: 1, title: "Querying Census 2011 Catchment Demographics & TAM", detail: "Retrieving rural population growth projections and purchasing power" },
    { id: 2, title: "Checking Ministry of MSME District Enterprise Density", detail: `Analyzing competitive enterprise saturation in ${districtName || 'the district'}` },
    { id: 3, title: "Evaluating 10 Central & State Subsidy Guidelines", detail: "Optimizing PMEGP, PMFME, MUDRA, and Stand-Up India incentives" },
    { id: 4, title: "Computing 5-Year Loan Amortization & RBI DSCR", detail: "Strict deterministic financial math with moratorium capital modeling" },
    { id: 5, title: "Executing 10-D XGBoost Viability Classifier & TreeSHAP", detail: "Calculating exact Shapley game-theoretic factor attributions" },
    { id: 6, title: "Synthesizing Multilingual Bank Appraisal Memorandum", detail: "Compiling 7-section statutory credit memorandum with Groq Cloud LLM" },
  ];

  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStage((prev) => {
        if (prev < stages.length - 1) return prev + 1;
        return prev;
      });
    }, 450);

    return () => clearInterval(interval);
  }, []);

  const progressPercent = Math.min(Math.round(((activeStage + 1) / stages.length) * 100), 98);

  return (
    <div className="max-w-2xl mx-auto py-12 px-4 animate-in fade-in duration-300">
      <div className="glass-panel p-8 bg-white border border-slate-200 shadow-xl rounded-2xl space-y-6">
        
        {/* Top Header with Pulse */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-sovereign-50 border border-sovereign-200 text-sovereign-800 mb-1 shadow-sm">
            <Sparkles className="w-6 h-6 animate-spin text-sovereign-700" />
          </div>
          <h2 className="text-xl font-bold font-outfit text-slate-900">
            Generating Bank-Ready Feasibility Appraisal
          </h2>
          <p className="text-xs text-slate-600 max-w-md mx-auto font-medium">
            Evaluating <strong className="text-slate-900">{enterpriseName || 'Proposed Enterprise'}</strong> in <strong className="text-slate-900">{districtName || 'Target Catchment'}</strong> with zero financial hallucination.
          </p>
        </div>

        {/* Dynamic Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-slate-600">Pipeline Execution Progress</span>
            <span className="font-mono text-sovereign-800 font-bold">{progressPercent}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden p-0.5 border border-slate-200">
            <div 
              className="bg-gradient-to-r from-sovereign-800 via-sky-600 to-emerald-600 h-full rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Staged Checklist */}
        <div className="space-y-2.5 pt-2">
          {stages.map((stage, idx) => {
            const isDone = idx < activeStage;
            const isCurrent = idx === activeStage;

            return (
              <div 
                key={stage.id}
                className={`p-3 rounded-xl border transition-all flex items-center justify-between text-xs ${
                  isCurrent 
                    ? 'bg-sovereign-50/80 border-sovereign-300 shadow-sm' 
                    : isDone 
                    ? 'bg-emerald-50/50 border-emerald-200 text-emerald-900' 
                    : 'bg-slate-50/40 border-slate-200 text-slate-400 opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="shrink-0">
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    ) : isCurrent ? (
                      <Loader2 className="w-4 h-4 text-sovereign-700 animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center text-[9px] text-slate-400">
                        {stage.id}
                      </div>
                    )}
                  </div>
                  <div>
                    <div className={`font-bold ${isCurrent ? 'text-slate-900' : isDone ? 'text-emerald-950' : 'text-slate-500'}`}>
                      {stage.title}
                    </div>
                    <div className="text-[11px] text-slate-500 font-normal mt-0.5">
                      {stage.detail}
                    </div>
                  </div>
                </div>

                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded shrink-0">
                  {isDone ? (
                    <span className="text-emerald-700 font-bold">Done</span>
                  ) : isCurrent ? (
                    <span className="text-sovereign-800 font-bold animate-pulse">Running...</span>
                  ) : (
                    <span className="text-slate-400">Queued</span>
                  )}
                </span>
              </div>
            );
          })}
        </div>

        {/* Grounding Attribution Lineage Tag */}
        <div className="text-[10px] text-slate-500 flex items-center justify-between pt-3 border-t border-slate-200">
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Zero-Hallucination Tier 1-4 Architecture
          </span>
          <span className="font-mono text-slate-600">
            FastAPI • TreeSHAP • Groq LLM
          </span>
        </div>

      </div>
    </div>
  );
}
export default ReportGenerationLoader;
