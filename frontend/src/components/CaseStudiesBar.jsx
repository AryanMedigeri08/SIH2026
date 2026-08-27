import React from 'react';
import { PITCH_CASES } from '../data/pitchCases';
import { Play } from 'lucide-react';

export function CaseStudiesBar({ activeCaseId, onSelectCase, isLoading }) {
  return (
    <div className="bg-slate-100/90 border-b border-slate-200 py-2.5 px-4 overflow-x-auto shadow-inner">
      <div className="max-w-7xl mx-auto flex items-center gap-2 min-w-max">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5 mr-2">
          <span className="w-2 h-2 rounded-full bg-sovereign-700"></span>
          Benchmark Scenarios:
        </span>

        {PITCH_CASES.map((c) => {
          const isSelected = activeCaseId === c.id;
          return (
            <button
              key={c.id}
              disabled={isLoading}
              onClick={() => onSelectCase(c)}
              className={`flex items-center gap-2 text-xs py-1.5 px-3 rounded-lg border transition-all ${
                isSelected
                  ? 'bg-sovereign-800 border-sovereign-900 text-white shadow-sm font-semibold'
                  : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700 hover:text-slate-900 shadow-sm'
              }`}
            >
              <Play className={`w-3 h-3 ${isSelected ? 'text-white fill-white' : 'text-slate-400'}`} />
              <span className="font-medium">{c.name}</span>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                isSelected
                  ? 'bg-white/20 border-white/40 text-white'
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
  );
}
export default CaseStudiesBar;
