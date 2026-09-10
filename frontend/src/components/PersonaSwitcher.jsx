import React from 'react';
import { UserCheck, ShieldCheck, Sparkles, Building2 } from 'lucide-react';
import { useViewMode, VIEW_MODES } from '../context/ViewModeContext';
import { TranslatedText } from './TranslatedText';

export function PersonaSwitcher({ compact = false }) {
  const { viewMode, setViewMode, isBeneficiary, isBanker } = useViewMode();

  return (
    <div className="inline-flex items-center p-0.5 sm:p-1 bg-slate-100/90 hover:bg-slate-200/80 border border-slate-200/90 rounded-xl transition-all shadow-xs shrink-0">
      {/* Beneficiary Pill */}
      <button
        type="button"
        onClick={() => setViewMode(VIEW_MODES.BENEFICIARY)}
        className={`flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1 rounded-lg text-xs font-bold transition-all shrink-0 ${
          isBeneficiary
            ? 'bg-white text-emerald-800 shadow-sm border border-emerald-200/60 ring-1 ring-emerald-500/10'
            : 'text-slate-600 hover:text-slate-900'
        }`}
        title="Beneficiary Mode: Clean, empowering, jargon-free view for rural entrepreneurs"
      >
        <UserCheck className={`w-3.5 h-3.5 shrink-0 transition-colors ${isBeneficiary ? 'text-emerald-700' : 'text-slate-400'}`} />
        <span className={`whitespace-nowrap ${compact ? 'hidden sm:inline' : 'inline'}`}>
          <TranslatedText text="Beneficiary" />
        </span>
      </button>

      {/* Banker / Auditor Pill */}
      <button
        type="button"
        onClick={() => setViewMode(VIEW_MODES.BANKER)}
        className={`flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1 rounded-lg text-xs font-bold transition-all shrink-0 ${
          isBanker
            ? 'bg-sovereign-900 text-white shadow-sm border border-sovereign-700 ring-1 ring-sky-500/20'
            : 'text-slate-600 hover:text-slate-900'
        }`}
        title="Banker & Auditor Mode: Full 10-D ML telemetry, TreeSHAP waterfall, and institutional credit audit"
      >
        <ShieldCheck className={`w-3.5 h-3.5 shrink-0 transition-colors ${isBanker ? 'text-sky-300' : 'text-slate-400'}`} />
        <span className={`whitespace-nowrap ${compact ? 'hidden sm:inline' : 'inline'}`}>
          <span className="inline lg:hidden"><TranslatedText text="Banker" /></span>
          <span className="hidden lg:inline"><TranslatedText text="Banker / Auditor" /></span>
        </span>
      </button>
    </div>
  );
}

export default PersonaSwitcher;
