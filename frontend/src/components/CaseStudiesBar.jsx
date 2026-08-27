import React from 'react';
import { PITCH_CASES } from '../data/pitchCases';
import { Play, Sparkles, CheckCircle2 } from 'lucide-react';

export function CaseStudiesBar({ activeCaseId, onSelectCase, isLoading }) {
  return (
    <div className="bg-white/80 backdrop-blur-sm border border-slate-200/90 rounded-2xl p-2.5 shadow-card mb-6">
      <div className="flex items-center gap-2.5 overflow-x-auto min-w-max">
        <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-sovereign-50 border border-sovereign-200/80 text-sovereign-800 text-[11px] font-bold uppercase tracking-wider shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-sovereign-700" />
          <span>Preset Scenarios:</span>
        </div>

        <div className="flex items-center gap-2">
          {PITCH_CASES.map((c) => {
            const isSelected = activeCaseId === c.id;
            return (
              <button
                key={c.id}
                disabled={isLoading}
                onClick={() => onSelectCase(c)}
                className={`flex items-center gap-2 text-xs py-1.5 px-3 rounded-xl border transition-all duration-200 ${
                  isSelected
                    ? 'bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-indigo-950 border-sovereign-700 text-white shadow-md shadow-sovereign-950/20 font-bold scale-[1.02]'
                    : 'bg-white hover:bg-slate-50 border-slate-200/90 text-slate-700 hover:text-slate-950 hover:border-slate-300 shadow-subtle'
                }`}
              >
                <Play className={`w-3 h-3 transition-colors ${isSelected ? 'text-sky-300 fill-sky-300' : 'text-slate-400'}`} />
                <span className="font-semibold">{c.name}</span>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md border font-mono ${
                  isSelected
                    ? 'bg-white/20 border-white/30 text-white'
                    : c.badgeColor === 'emerald'
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : c.badgeColor === 'rose'
                    ? 'bg-rose-50 border-rose-200 text-rose-800'
                    : 'bg-amber-50 border-amber-200 text-amber-800'
                }`}>
                  {c.badge}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
export default CaseStudiesBar;
