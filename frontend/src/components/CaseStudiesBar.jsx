import React from 'react';
import { PITCH_CASES } from '../data/pitchCases';
import { Play } from 'lucide-react';

export function CaseStudiesBar({ activeCaseId, onSelectCase, isLoading }) {
  return (
    <div className="bg-slate-900/60 border-b border-indigo-500/10 py-2.5 px-4 overflow-x-auto">
      <div className="max-w-7xl mx-auto flex items-center gap-2 min-w-max">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mr-2">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
          SIH 2026 Pitch Cases:
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
                  ? 'bg-indigo-600/30 border-cyan-500/50 text-white shadow-glow'
                  : 'bg-slate-800/50 hover:bg-slate-800 border-slate-700/60 text-slate-300 hover:text-white'
              }`}
            >
              <Play className={`w-3 h-3 ${isSelected ? 'text-cyan-400 fill-cyan-400' : 'text-slate-500'}`} />
              <span className="font-medium">{c.name}</span>
              <span className={`text-[10px] font-semibold px-1.5 py-0.2 rounded border ${
                c.badgeColor === 'emerald'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : c.badgeColor === 'rose'
                  ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
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
