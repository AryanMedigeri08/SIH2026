import React from 'react';
import { Bot, Sparkles, Languages, CheckCircle2, BookmarkCheck } from 'lucide-react';

export function ExecutiveNarrativeCard({ synthesisData }) {
  const synth = synthesisData || {};
  const summary = synth.executive_summary || "The proposed enterprise demonstrates sound financial and commercial feasibility with healthy debt coverage.";
  const recommendations = synth.strategic_recommendations || [];
  const bankNotes = synth.bank_appraisal_notes || "Enterprise satisfies credit underwriting benchmarks.";
  const lang = (synth.target_language || "en").toUpperCase();

  return (
    <div className="glass-panel p-6 border-l-4 border-cyan-500 space-y-4">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400">
            <Bot className="w-5 h-5" />
          </span>
          <div>
            <h3 className="text-base font-bold text-white">
              Multi-Lingual Executive Feasibility & Credit Appraisal Synthesis
            </h3>
            <p className="text-[11px] text-slate-400">
              Synthesized by Tier 3 Groq Cloud Llama-3-70B • Zero Financial Recalculation Invariant
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 flex items-center gap-1.5">
            <Languages className="w-3.5 h-3.5" /> Language: {lang}
          </span>
        </div>
      </div>

      {/* Synthesis Narrative */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-sm text-slate-200 leading-relaxed">
        {summary}
      </div>

      {/* Strategic Action Points */}
      {recommendations.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
            Strategic Recommendations & Growth Milestones:
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-300 font-bold flex items-center justify-center shrink-0 text-[11px]">
                  {idx + 1}
                </span>
                <span className="mt-0.5">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bank Credit Memorandum Notes */}
      <div className="p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/20 text-xs text-slate-300 flex items-start gap-2.5">
        <BookmarkCheck className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-indigo-300 font-semibold">Bank Credit Appraisal Memorandum: </strong>
          <span>{bankNotes}</span>
        </div>
      </div>

    </div>
  );
}
