import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useBusiness } from '../../context/BusinessContext';
import { useLanguage } from '../../context/LanguageContext';
import { useAutoTranslate } from '../../hooks/useAutoTranslate';
import { onboardingApi, planningApi, projectsApi, fetchPlanningMachinery } from '../../services/api';
import { MiraGuide } from './MiraGuide';
import { MiraAnswer } from './MiraAnswer';
import { MiraOdop } from './MiraOdop';
import { MiraPlanResults } from './MiraPlanResults';
import { TranslatedText as T } from '../TranslatedText';
import { businessContext, conversationForm, conversationPlanningPayload, conversationExistingPayload } from './payloads';
import { copy } from './copy';

const money = value => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0);
export function MiraConversation({ initialDraft, onProgress, onFinish, onChangeJourney }) {
  const { token, userProfile } = useAuth();
  const { createAndSaveBusiness } = useBusiness();
  const { language } = useLanguage();
  const [draft, setDraft] = useState(initialDraft);
  const [question, setQuestion] = useState('loading');
  const [choices, setChoices] = useState([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [project, setProject] = useState(null);
  const [intent, setIntent] = useState(null);
  const [clarification, setClarification] = useState(null);
  const [reload, setReload] = useState(0);
  const alive = useRef(true);
  const guard = useRef(false);
  const stopSpeech = useRef(() => {});
  useEffect(() => {
    alive.current = true;
    const load = async () => {
      try {
        const [state, businesses] = await Promise.all([onboardingApi.question(token), planningApi.businesses(token)]);
        if (!alive.current) return;
        setDraft(state.draft); setQuestion(state.question); setChoices(businesses);
        if (state.draft.project_id) {
          const saved = await projectsApi.getProject(token, state.draft.project_id);
          if (alive.current) setProject(saved);
        } else if (state.draft.preview_id) {
          const saved = await planningApi.preview(token, state.draft.preview_id);
          if (alive.current) setResult(saved);
        }
      } catch (err) { if (alive.current) setError(err.message); }
    };
    load();
    return () => { alive.current = false; stopSpeech.current(); };
  }, [token, reload]);
  const apply = state => {
    setDraft(state.draft); setQuestion(state.question); onProgress(state.draft);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  const answer = async (value, extras = {}) => {
    if (guard.current) return;
    guard.current = true; setPending(true); setError(''); stopSpeech.current();
    try {
      if (question === 'idea') {
        if (clarification) { value = `${clarification.original}\n${value}`; setClarification(null); }
        else if (String(value).trim().length >= 10) {
          const interpreted = await onboardingApi.interpret(token, value, language);
          if (!alive.current) return;
          setIntent(interpreted);
          if (interpreted.clarification) { setClarification({ original: value, question: interpreted.clarification }); return; }
        }
      }
      const state = await onboardingApi.answer(token, { field: question, value, ...extras });
      if (alive.current) apply(state);
    } catch (err) { if (alive.current) setError(err.message); }
    finally { guard.current = false; if (alive.current) setPending(false); }
  };
  const edit = async field => {
    if (guard.current) return;
    const answers = { ...draft.answers };
    const affected = field === 'idea' ? ['idea','business_id','sector','business_category','idea_confirmed','odop_choice','enterprise_name','original_idea']
      : ['business_id','sector','business_category'].includes(field) ? ['business_id','sector','business_category','idea_confirmed','odop_choice','enterprise_name']
      : field === 'own_cash' ? ['own_cash','cash_confirmed'] : field === 'premise_type' ? ['premise_type','monthly_rent'] : [field];
    if (affected.includes('odop_choice') && answers.original_idea) answers.idea = answers.original_idea;
    affected.forEach(key => delete answers[key]); delete answers.review_confirmed;
    setPending(true); setError('');
    try {
      const updated = { ...draft, answers, completed: false, preview_id: null, project_id: null, language };
      await onboardingApi.save(token, updated);
      const state = await onboardingApi.question(token);
      setResult(null); setProject(null); setIntent(null); setClarification(null); apply(state);
    } catch (err) { setError(err.message); }
    finally { setPending(false); }
  };
  const calculate = async () => {
    if (guard.current) return;
    guard.current = true; setPending(true); setError(''); stopSpeech.current();
    try {
      const current = { ...draft, language };
      if (current.journey === 'existing') {
        const form = conversationForm(current, userProfile, choices);
        const schedule = await fetchPlanningMachinery({ ...form, project_cost: current.answers.project_cost || 900000, additional_business_details: businessContext(current) });
        if (!alive.current) return;
        const saved = await createAndSaveBusiness(conversationExistingPayload(current, userProfile, choices, schedule));
        const updated = { ...current, project_id: saved.project_id };
        setProject(saved); setDraft(updated); onProgress(updated);
        await onboardingApi.save(token, updated);
      } else {
        const evaluated = await planningApi.evaluate(token, conversationPlanningPayload(current, userProfile, choices));
        if (!alive.current) return;
        const updated = { ...current, preview_id: evaluated.draft_id };
        setResult(evaluated); setDraft(updated); onProgress(updated);
        await onboardingApi.save(token, updated);
      }
    } catch (err) { if (alive.current) setError(err.message); }
    finally { guard.current = false; if (alive.current) setPending(false); }
  };
  const accept = async (plan, acknowledge, risk) => {
    if (guard.current) return;
    guard.current = true; setPending(true); setError('');
    try {
      const saved = await planningApi.accept(token, result.draft_id, { proposal_id: plan.proposal_id, acknowledge_estimates: acknowledge, accept_risks: risk });
      await onFinish(saved, { ...draft, completed: true, project_id: saved.project_id });
    } catch (err) { setError(err.message); }
    finally { guard.current = false; if (alive.current) setPending(false); }
  };
  const a = draft.answers;
  let prompt = copy(question, language);
  let options = [];
  if (question === 'loading') prompt = copy('waiting', language);
  if (question === 'idea' && clarification) prompt = clarification.question;
  if (question === 'business_id') {
    prompt = 'Which business best matches your idea? Choose the closest match, or another business.';
    const suggested = choices.find(item => item.id === intent?.business_id);
    options = [...(suggested ? [{ value: suggested.id, label: `Suggested match: ${suggested.name}` }] : []),
      ...choices.filter(item => item !== suggested).map(item => ({ value: item.id, label: item.name })), { value: 'custom', label: 'Another business / custom idea' }];
  }
  if (question === 'sector') { prompt = 'Which sector best matches your business?'; options = ['dairy','food_processing','repair','apparel','fabrication','general'].map(value => ({ value, label: value.replaceAll('_', ' ') })); }
  if (question === 'business_category') { prompt = 'Will you make products or provide a service?'; options = [{ value: 'manufacturing', label: 'Make products' }, { value: 'service', label: 'Provide a service' }]; }
  if (question === 'idea_confirmed') { prompt = `Have I understood your idea correctly? ${a.idea}`; options = [{ value: true, label: 'Yes, that is my idea' }]; }
  if (question === 'cash_confirmed') { prompt = `You can contribute ${money(a.own_cash)} of your own money before any loan. Is that correct?`; options = [{ value: true, label: 'Yes, that is correct' }]; }
  if (question === 'premise_type') options = ['owned','rented','panchayat'].map(value => ({ value, label: copy(value, language) }));
  if (question === 'review_confirmed' || question === 'ready') prompt = copy('review', language);
  const { translated: speech } = useAutoTranslate(prompt);
  const banner = error && <p role="alert" className="mira-error"><T text={error} /><button type="button" onClick={() => { setError(''); setReload(n => n + 1); }} className="ml-3 underline"><T text="Reload saved progress" /></button></p>;
  if (result) return <>{banner}<MiraPlanResults result={result} pending={pending} onAccept={accept} onEdit={() => edit(draft.journey === 'budget_only' ? 'preferences' : 'idea')} /></>;
  if (project) return <>{banner}<ExistingResult project={project} pending={pending} onContinue={() => onFinish(project, { ...draft, completed: true })} onEdit={() => edit('own_cash')} /></>;
  const form = conversationForm(draft, userProfile, choices);
  if (question === 'odop_choice') return <>{banner}<MiraOdop form={form} onChoice={(choice, result) => answer(choice, choice === 'hybrid' ? { hybrid_name: result.hybrid_name, hybrid_description: result.hybrid_description } : {})} /></>;
  const reviewing = ['review_confirmed', 'ready'].includes(question);
  return <section className="space-y-5">
    {banner}
    <div className="mira-layout">
      <MiraGuide text={speech} onSpeechControl={stop => { stopSpeech.current = stop; }} />
      <div className="mira-card space-y-5">
        {reviewing && <div className="space-y-3">
          {Object.entries(a).filter(([key]) => !['idea_confirmed','cash_confirmed','review_confirmed','original_idea'].includes(key)).map(([key, value]) => <div key={key} className="border-b pb-3">
            <p className="text-sm font-semibold text-slate-600"><T text={key.replaceAll('_', ' ')} /></p>
            <p className="break-words text-lg">{value == null ? copy('unknown', language) : typeof value === 'boolean' ? String(value) : String(value)}</p>
            <button disabled={pending} type="button" className="mt-1 min-h-11 font-bold text-purple-900 underline" onClick={() => edit(key)}><T text="Change answer" /></button>
          </div>)}
          {a.premise_type === 'rented' && a.monthly_rent == null && <p className="rounded-lg bg-amber-50 p-3"><T text="Rent is unknown. The existing ₹2,500 monthly estimate will be used; confirm the actual rent before borrowing." /></p>}
          {draft.journey === 'existing' && a.project_cost == null && <p className="rounded-lg bg-amber-50 p-3"><T text="The existing ₹9,00,000 starting project estimate will be sized from the machinery schedule. This is not a supplier quote." /></p>}
        </div>}
        {question === 'loading' ? <p role="status">{copy('waiting', language)}</p> : question === 'ready'
          ? <button type="button" disabled={pending} onClick={calculate} className="mira-primary w-full">{copy(pending ? 'waiting' : 'calculate', language)}</button>
          : <MiraAnswer key={`${question}:${!!clarification}:${language}`} initial={question === 'enterprise_name' ? choices.find(item => item.id === a.business_id)?.name || a.idea?.slice(0, 100) || '' : ''}
            disabled={pending} stopSpeech={() => stopSpeech.current()} options={question === 'review_confirmed' ? [{ value: true, label: copy('yes', language) }] : options}
            optional={['skills','resources','preferences','equipment_quote','project_cost','annual_sales','monthly_rent'].includes(question) || (question === 'own_cash' && draft.journey === 'idea_only')}
            onAnswer={value => answer(value)} maxLength={question === 'enterprise_name' ? 160 : 800} />}
        {['idea_confirmed','cash_confirmed'].includes(question) && <button disabled={pending} type="button" className="mira-secondary" onClick={() => edit(question === 'idea_confirmed' ? 'idea' : 'own_cash')}><T text="No, change my answer" /></button>}
      </div>
    </div>
    <button disabled={pending} type="button" className="mira-secondary" onClick={onChangeJourney}><T text="Choose a different starting point" /></button>
  </section>;
}

function ExistingResult({ project, pending, onContinue, onEdit }) {
  const report = project.analysis_result.report;
  const f = report.financial_analysis;
  const cap = report.capital_structure || f.capital_structure;
  const concern = project.business_status?.reason || '';
  const message = `Your project cost is ${money(report.input_parameters.project_cost)}. Your own money is ${money(report.input_parameters.available_margin_capital)}. Bank loan is ${money(f.loan_principal)}. Monthly bank repayment is ${money(f.amortization.monthly_emi)}. ${concern} These figures are estimates. Do you understand the assessment and any concerns and want to continue?`;
  const { translated: speech } = useAutoTranslate(message);
  return <div className="mira-layout"><MiraGuide text={speech} /><div className="mira-card space-y-5">
    <h2 className="text-2xl font-bold"><T text={project.business_name} /></h2>
    <dl className="space-y-3">{[['Project cost',report.input_parameters.project_cost],['Your own money',report.input_parameters.available_margin_capital],['Bank loan',f.loan_principal],['Monthly bank repayment',f.amortization.monthly_emi]].map(([label,value]) => <div key={label} className="flex flex-wrap justify-between gap-3 border-b pb-2"><dt><T text={label} /></dt><dd className="font-bold">{money(value)}</dd></div>)}</dl>
    {concern && <p className="rounded-xl bg-amber-50 p-4 text-amber-950"><T text={concern} /></p>}
    <details className="rounded-xl border p-4"><summary className="cursor-pointer font-bold"><T text="Funding and SCA information" /></summary><p className="mt-3"><T text="These are calculated options, subject to eligibility and lender approval. Assistance is not cash already available." /></p>
      {Object.entries(cap || {}).filter(([key,value]) => /equity|gap|sca/.test(key) && typeof value === 'number').map(([key,value]) => <p className="mt-2" key={key}><T text={key.replaceAll('_',' ')} />: {money(value)}</p>)}
    </details>
    <MiraAnswer disabled={pending} onAnswer={value => value === true ? onContinue() : onEdit()} options={[{ value: true, label: 'I understand the estimates and concerns. Continue to my dashboard.' }, { value: false, label: 'Revise my investment and plan' }]} />
  </div></div>;
}
