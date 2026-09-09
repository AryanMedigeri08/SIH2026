import React from 'react';
import { Target, CheckCircle2, AlertTriangle, Lightbulb, ShieldAlert, Sparkles, Database, Cpu } from 'lucide-react';
import { TranslatedText } from '../TranslatedText';

export function SwotMatrixCard({ swotData, synthesisData }) {
  const s = swotData?.strengths || [];
  const w = swotData?.weaknesses || [];
  const o = swotData?.opportunities || [];
  const t = swotData?.threats || [];

  const genSource = swotData?.generation_source || (synthesisData?.is_fallback === false ? `AI_GROQ (${synthesisData?.model_name || 'GPT-OSS-20B'})` : 'DETERMINISTIC_FALLBACK');
  const isAiGenerated = genSource.startsWith('AI_GROQ') || (swotData?.is_fallback === false || synthesisData?.is_fallback === false);
  const modelLabel = synthesisData?.model_name ? synthesisData.model_name.split('/').pop() : 'gpt-oss-20b';

  return (
    <div className="glass-panel p-6 bg-white shadow-card border border-slate-200">
      <div className="mb-4">
        <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
          <Target className="w-3.5 h-3.5" />
          Strategic Commercial Evaluation
        </div>
        <h3 className="text-lg font-outfit font-bold text-slate-900 flex items-center gap-2">
          <span>Grounded SWOT Analysis Matrix</span>
          {isAiGenerated ? (
            <span className="text-[10px] font-semibold bg-indigo-50 text-indigo-800 border border-indigo-200 px-2 py-0.5 rounded-full inline-flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-indigo-600" />
              <span>AI GROQ RESPONSE ({modelLabel})</span>
            </span>
          ) : (
            <span className="text-[10px] font-semibold bg-slate-100 text-slate-800 border border-slate-200 px-2 py-0.5 rounded-full inline-flex items-center gap-1">
              <Cpu className="w-3 h-3 text-slate-600" />
              <span>DETERMINISTIC FALLBACK RESPONSE</span>
            </span>
          )}
        </h3>
        <p className="text-xs text-slate-600 mt-0.5 font-medium">
          Domain-grounded enterprise evaluation derived from demographic, competitive, and financial signals.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Strengths */}
        <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-4 space-y-2 transition-all hover:shadow-subtle">
          <div className="text-xs font-bold text-emerald-900 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Internal Strengths</span>
          </div>
          <ul className="space-y-2 text-xs text-slate-800 font-medium">
            {s.map((item, idx) => {
              const text = typeof item === 'object' ? item.text : item;
              const source = typeof item === 'object' ? item.data_source : null;
              return (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-emerald-600 mt-0.5 font-bold shrink-0">•</span>
                  <div className="leading-relaxed">
                    <TranslatedText text={text} />
                    {source && (
                      <span className="ml-1.5 px-1.5 py-0.2 rounded bg-white border border-emerald-200 text-[10px] text-emerald-800 font-mono font-normal inline-block">
                        {source}
                      </span>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Weaknesses */}
        <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 space-y-2 transition-all hover:shadow-subtle">
          <div className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Internal Weaknesses</span>
          </div>
          <ul className="space-y-2 text-xs text-slate-800 font-medium">
            {w.map((item, idx) => {
              const text = typeof item === 'object' ? item.text : item;
              const source = typeof item === 'object' ? item.data_source : null;
              return (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-amber-600 mt-0.5 font-bold shrink-0">•</span>
                  <div className="leading-relaxed">
                    <TranslatedText text={text} />
                    {source && (
                      <span className="ml-1.5 px-1.5 py-0.2 rounded bg-white border border-amber-200 text-[10px] text-amber-800 font-mono font-normal inline-block">
                        {source}
                      </span>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Opportunities */}
        <div className="bg-sky-50/70 border border-sky-200 rounded-xl p-4 space-y-2 transition-all hover:shadow-subtle">
          <div className="text-xs font-bold text-sky-900 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <Lightbulb className="w-4 h-4 text-sky-700 shrink-0" />
            <span>Market Opportunities</span>
          </div>
          <ul className="space-y-2 text-xs text-slate-800 font-medium">
            {o.map((item, idx) => {
              const text = typeof item === 'object' ? item.text : item;
              const source = typeof item === 'object' ? item.data_source : null;
              return (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-sky-700 mt-0.5 font-bold shrink-0">•</span>
                  <div className="leading-relaxed">
                    <TranslatedText text={text} />
                    {source && (
                      <span className="ml-1.5 px-1.5 py-0.2 rounded bg-white border border-sky-200 text-[10px] text-sky-800 font-mono font-normal inline-block">
                        {source}
                      </span>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Threats */}
        <div className="bg-rose-50/70 border border-rose-200 rounded-xl p-4 space-y-2 transition-all hover:shadow-subtle">
          <div className="text-xs font-bold text-rose-900 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
            <span>Macro & External Threats</span>
          </div>
          <ul className="space-y-2 text-xs text-slate-800 font-medium">
            {t.map((item, idx) => {
              const text = typeof item === 'object' ? item.text : item;
              const source = typeof item === 'object' ? item.data_source : null;
              return (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-rose-600 mt-0.5 font-bold shrink-0">•</span>
                  <div className="leading-relaxed">
                    <TranslatedText text={text} />
                    {source && (
                      <span className="ml-1.5 px-1.5 py-0.2 rounded bg-white border border-rose-200 text-[10px] text-rose-800 font-mono font-normal inline-block">
                        {source}
                      </span>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>

      </div>

      {/* Grounded Data Source Lineage Tag */}
      <div className="text-[10px] text-slate-500 flex flex-wrap items-center justify-between gap-2 pt-3 mt-4 border-t border-slate-200">
        <span className="flex items-center gap-1.5 text-slate-600">
          <Database className="w-3.5 h-3.5 text-sovereign-700" />
          <span><strong className="text-slate-700">Data Source:</strong> Upstream Multi-Signal Lineage (Census 2011 + MSME Density + XGBoost Output)</span>
        </span>
        <div className="flex items-center gap-2">
          <span className="text-slate-600 font-bold">Generation Source:</span>
          {isAiGenerated ? (
            <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-800 border border-indigo-200 font-mono font-bold text-[10px] flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-indigo-600" />
              <span>AI GROQ RESPONSE ({modelLabel})</span>
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200 font-mono font-bold text-[10px] flex items-center gap-1">
              <Cpu className="w-3 h-3 text-slate-600" />
              <span>DETERMINISTIC FALLBACK RESPONSE</span>
            </span>
          )}
        </div>
      </div>

    </div>
  );
}

export default SwotMatrixCard;
