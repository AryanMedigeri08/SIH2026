import React, { useState } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useAutoTranslate } from '../../hooks/useAutoTranslate';
import { TranslatedText as T } from '../TranslatedText';
import { MiraGuide } from './MiraGuide';
import { MiraAnswer } from './MiraAnswer';

const money = value => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0);
export function MiraPlanResults({ result, onAccept, onEdit, pending }) {
  const { language } = useLanguage();
  const [selected, setSelected] = useState(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [heard, setHeard] = useState(null);
  const plans = result.proposals;
  const current = plans.find(plan => plan.proposal_id === selected);
  const prompt = current ? acknowledged && current.concerns.length
    ? `Please review these concerns: ${current.concerns.join(' ')} Do you understand them and want to explore this plan?`
    : `This plan needs ${money(current.required_own_money)} of your own money. Can you arrange it and do you understand that the costs and sales are estimates?`
    : plans.length ? 'These plans have already passed appraisal. Which would you like to explore?'
      : 'No plan passed the checks with these details. Would you like to change your answers?';
  const { translated: speech } = useAutoTranslate(heard || prompt);
  const choose = value => {
    if (value !== true) { setSelected(null); setAcknowledged(false); return; }
    if (!acknowledged && current.concerns.length) { setAcknowledged(true); return; }
    onAccept(current, true, !!current.concerns.length);
  };
  return <section className="space-y-6 py-5">
    <MiraGuide text={speech} centered />
    {plans.length > 0 && plans.length < 3 && <p role="status" className="rounded-xl bg-amber-50 p-4 text-amber-950"><T text={`Only ${plans.length} plans passed appraisal. Failed plans are not recommended.`} /></p>}
    {current ? <div className="mira-card mx-auto max-w-2xl space-y-5">
      <h2 className="text-2xl font-bold"><T text={current.name} /></h2>
      {current.concerns.map((text, i) => <p className="rounded-lg bg-amber-50 p-3 text-amber-950" key={i}><T text={text} /></p>)}
      <MiraAnswer key={`${selected}:${acknowledged}:${language}`} disabled={pending} onAnswer={choose}
        options={[{ value: true, label: 'Yes, I understand and want to continue' }, { value: false, label: 'No, let me choose another plan' }]} />
    </div> : <div className="grid gap-5 lg:grid-cols-3">
      {plans.map((plan, i) => {
        const f = plan.financial_analysis;
        return <article key={plan.proposal_id} className="mira-card flex flex-col gap-4">
          <h2 className="text-xl font-bold">{i + 1}. <T text={plan.name} /></h2>
          <p><T text={plan.description} /></p>
          <dl className="space-y-3">{[['Project cost',plan.project_cost],['Own money needed',plan.required_own_money],['Loan',f.loan_principal],['Monthly bank repayment',f.amortization.monthly_emi]].map(([label, value]) =>
            <div key={label} className="flex flex-wrap justify-between gap-2 border-b pb-2"><dt><T text={label} /></dt><dd className="font-extrabold">{money(value)}</dd></div>)}</dl>
          <p className="text-sm"><T text={plan.odop_alignment?.is_aligned ? 'Connected to the district ODOP product or value chain.' : 'No confirmed ODOP alignment.'} /></p>
          <details className="rounded-xl bg-slate-50 p-3"><summary className="cursor-pointer font-bold"><T text="Local evidence, estimates and risks" /></summary>
            {[...plan.concerns, ...plan.warnings, ...(plan.regional.evidence?.missing_evidence || [])].map((text, index) => <p className="mt-3" key={index}><T text={text} /></p>)}
          </details>
          <button disabled={pending} className="mira-secondary mt-auto" type="button" onClick={() => setHeard(`${plan.name}. Project cost ${money(plan.project_cost)}. Own money needed ${money(plan.required_own_money)}. Bank loan ${money(f.loan_principal)}. Monthly bank repayment ${money(f.amortization.monthly_emi)}. ${plan.concerns.join(' ')}`)}><T text="Hear this plan" /></button>
          <button disabled={pending} className="mira-primary" type="button" onClick={() => { setHeard(null); setSelected(plan.proposal_id); setAcknowledged(false); }}><T text="Explore this plan" /></button>
        </article>;
      })}
    </div>}
    {!current && plans.length > 0 && <div className="mx-auto max-w-xl"><MiraAnswer disabled={pending} onAnswer={value => { setSelected(value); setHeard(null); setAcknowledged(false); }} options={plans.map(plan => ({ value: plan.proposal_id, label: plan.name }))} /></div>}
    <button type="button" disabled={pending} onClick={onEdit} className="mira-secondary"><T text="Change my answers / explore other options" /></button>
  </section>;
}
