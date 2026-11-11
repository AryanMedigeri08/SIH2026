import React from 'react';
import { Check, Sparkles } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { copy } from './copy';

const phaseFor = question => ['idea','business_id','sector','business_category','idea_confirmed'].includes(question) ? 'idea'
  : question === 'odop_choice' ? 'odop' : ['own_cash','cash_confirmed','equipment_quote','project_cost','annual_sales'].includes(question) ? 'money'
    : ['premise_type','monthly_rent','skills','resources','preferences'].includes(question) ? 'workspace' : 'plan';

export function MiraProgress({ journey, question, sequence = [], completed = 0, evaluated = false }) {
  const { language } = useLanguage();
  if (!sequence.length || ['loading','journey','location'].includes(question)) return null;
  const phases = journey === 'budget_only' ? ['money','workspace','plan'] : ['idea','odop','money','workspace','plan'];
  const phase = evaluated ? 'plan' : phaseFor(question);
  const total = sequence.length + 2; // Actual answers, appraisal and plan acceptance.
  const done = Math.min(total, completed + (evaluated ? 1 : 0));
  const percent = Math.round(done / total * 100);
  const active = phases.indexOf(phase);
  return <section className="mira-progress" aria-label={copy('progress', language)}>
    <div className="mira-progress-heading"><span className="inline-flex items-center gap-2 font-bold"><Sparkles size={18} />{copy('progress', language)}</span>
      <span className="text-sm font-semibold">{percent}%</span></div>
    <div role="progressbar" aria-label={copy('progress', language)} aria-valuenow={done} aria-valuemin={0} aria-valuemax={total} className="mira-progress-track">
      <div className="mira-progress-fill" style={{ width: `${percent}%` }} />
    </div>
    <ol className="mira-milestones">{phases.map((item, i) => <li key={item} aria-current={item === phase ? 'step' : undefined} className={i < active ? 'mira-milestone-done' : item === phase ? 'mira-milestone-current' : ''}>
      <span aria-hidden="true">{i < active ? <Check size={13} /> : i + 1}</span>{copy(`phase_${item}`, language)}
    </li>)}</ol>
    <p className="mira-progress-hint">{copy(`hint_${phase}`, language)}</p>
  </section>;
}
