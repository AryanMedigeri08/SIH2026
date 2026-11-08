import React from 'react';
import { ArrowRight, Lightbulb, Wallet, Calculator } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { MiraGuide } from './MiraGuide';
import { copy } from './copy';

export function MiraJourneyChoice({ onChoose, busy = false }) {
  const { language } = useLanguage();
  return <section className="space-y-8 py-8">
    <MiraGuide text={copy('journey', language)} centered />
    <div className="grid gap-4 md:grid-cols-3">
      {[['existing', Lightbulb], ['budget_only', Wallet], ['idea_only', Calculator]].map(([id, Icon], i) =>
        <button type="button" key={id} disabled={busy} onClick={() => onChoose(id)} className="mira-card text-left transition hover:!border-purple-700 focus:outline-none focus:ring-4 focus:ring-purple-300 disabled:opacity-50">
          <Icon size={30} className="mb-5 text-purple-800" aria-hidden="true" />
          <span className="text-sm font-semibold text-purple-700">{i + 1}</span>
          <span className="mt-2 block text-xl font-extrabold leading-relaxed text-purple-950">{copy(id, language)}</span>
          <ArrowRight className="mt-5 text-purple-800" aria-hidden="true" />
        </button>)}
    </div>
  </section>;
}
