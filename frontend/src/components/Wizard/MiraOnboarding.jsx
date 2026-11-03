import React, { useEffect, useRef, useState } from 'react';
import { Mic, Square, Volume2, VolumeX, Send, Pause, Play, Pencil, Check, RefreshCw } from 'lucide-react';
import { onboardingApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useMiraSpeech } from '../../hooks/useMiraSpeech';
import { BusinessLocationPicker } from './BusinessLocationPicker';

const labels = {
  personal: 'My own money', total: 'Total project budget', borrowing: 'Borrowing capacity', other: 'Other',
  unknown_budget: 'Estimate first', manufacture: 'Make products', process: 'Process raw materials', retail: 'Sell products',
  distribute: 'Distribute products', service: 'Provide services', explore: 'Explore ODOP', keep: 'Keep my idea', reject: 'Skip ODOP',
  owned: 'I own premises', rented: 'I need to rent', shared: 'Shared facilities', purchase: 'I need to buy', mobile: 'No fixed premises',
  increase: 'Increase my contribution', normal: 'Explore normal loan', sca: 'Explore SCA assistance', self: 'Use my own funds',
  monthly: 'Per month', annual: 'Per year', true: 'Yes, suitable', false: 'No, needs changing', Unspecified: 'Prefer not to say',
};
const numeric = new Set(['budget', 'personal_contribution', 'project_cost', 'rent_amount']);
const editableChoices = { activity: ['manufacture', 'process', 'retail', 'distribute', 'service', 'other'],
  budget_kind: ['personal', 'total', 'borrowing', 'other', 'unknown_budget'], premises: ['owned', 'rented', 'shared', 'purchase', 'mobile'],
  rent_period: ['monthly', 'annual'], gender: ['Male', 'Female', 'Other', 'Unspecified'],
  promoter_category: ['general', 'sc', 'st', 'obc', 'minority', 'ph', 'artisan', 'women', 'women_shg'],
  odop_preference: ['explore', 'keep', 'reject'], financing_choice: ['increase', 'normal', 'sca', 'self'],
  premises_suitable: [true, false] };
const formatMoney = amount => amount == null ? 'Not established' : `₹${Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;

function CostBreakdown({ onSave, disabled, activity, initial = {} }) {
  const [costs, setCosts] = useState(initial);
  const equipmentLabel = ['manufacture', 'process'].includes(activity) ? 'Machinery and equipment' : 'Tools, equipment and fixtures';
  return <form className="rounded-2xl border border-slate-200 p-4 space-y-3" aria-label="Applicable project costs" onSubmit={event => {
    event.preventDefault();
    const items = Object.fromEntries(Object.entries(costs).filter(([, val]) => val !== '').map(([key, val]) => [key, Number(val)]));
    if (Object.keys(items).length) onSave(items);
  }}>
    <p className="text-sm text-slate-600">Enter estimates in rupees for applicable items only. Leave irrelevant items blank. Include initial stock only once. Land purchase is excluded by the existing financing model; recurring rent is collected separately.</p>
    <div className="grid sm:grid-cols-2 gap-3">{[['equipment', equipmentLabel], ['premises_setup', 'Premises preparation / infrastructure'],
      ['inventory', ['retail', 'distribute'].includes(activity) ? 'Initial stock for sale' : 'Initial materials / supplies'],
      ['working_capital', 'Other initial working capital'], ['other', 'Other relevant setup costs']].map(([key, label]) => <label key={key} className="text-sm">{label}
        <input className="mira-input mt-1" aria-label={label} type="number" min="0" max="10000000000" step="0.01" value={costs[key] ?? ''}
          onChange={e => setCosts(previous => ({ ...previous, [key]: e.target.value }))} placeholder="Not applicable" disabled={disabled} />
      </label>)}</div>
    <button className="mira-primary" disabled={disabled}>Use these cost estimates</button>
  </form>;
}

export function MiraOnboarding({ onSubmit, isSubmitting }) {
  const { token, firebaseUser } = useAuth();
  const { language } = useLanguage();
  const [state, setState] = useState(null);
  const [reply, setReply] = useState('');
  const [input, setInput] = useState('');
  const [inputSource, setInputSource] = useState('text');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [readAloud, setReadAloud] = useState(false);
  const [editKey, setEditKey] = useState('');
  const [editValue, setEditValue] = useState('');
  const [needsReload, setNeedsReload] = useState(false);
  const pendingRequest = useRef(null);
  const inFlight = useRef(false);
  const latest = useRef(0);
  const speech = useMiraSpeech({ language, token, onTranscript: transcript => {
    setInput(previous => previous ? `${previous} ${transcript}` : transcript);
    setInputSource('voice');
  } });
  const accept = result => { setState(result.state); setReply(result.reply); setError(''); setNeedsReload(false); };
  const reload = async () => {
    const generation = ++latest.current;
    setBusy(true);
    try {
      const result = await onboardingApi.session(token, language);
      if (generation === latest.current) accept(result);
    } catch (err) { if (generation === latest.current) setError(err.message); }
    finally { if (generation === latest.current) setBusy(false); }
  };
  useEffect(() => {
    setState(null); setInput(''); setReply(''); pendingRequest.current = null;
  }, [firebaseUser?.uid]);
  useEffect(() => {
    if (token) reload();
    return () => { latest.current += 1; };
  }, [token]);
  useEffect(() => { if (state && token) reload(); }, [language]);
  useEffect(() => {
    if (readAloud && reply && !state?.paused) speech.speak(reply);
    return () => speech.stopSpeaking();
  }, [reply, readAloud, language]);

  const send = async (options = {}, retry = false) => {
    if (!state || inFlight.current || isSubmitting) return;
    inFlight.current = true;
    setBusy(true); setError(''); speech.stopSpeaking();
    const payload = retry ? pendingRequest.current : { revision: state.revision, request_id: crypto.randomUUID(),
      text: options.updates ? '' : input, source: inputSource, language, ...options };
    pendingRequest.current = payload;
    try {
      accept(await onboardingApi.turn(token, payload));
      pendingRequest.current = null;
      if (payload.text && payload.text === input) {
        setInput(''); setInputSource('text');
      }
      setEditKey('');
    } catch (err) {
      setError(err.status === 401 ? 'Please sign in again. Your saved conversation will resume after sign-in.' : err.message);
      setNeedsReload(err.status === 409);
    } finally { inFlight.current = false; setBusy(false); }
  };
  const finish = async () => {
    setBusy(true); setError(''); speech.stopSpeaking();
    try { await onSubmit({ onboarding_revision: state.revision, enterprise_name: state.fields.enterprise_name?.value,
      district_name: state.location?.district_name, sector: state.classification?.sector, language }); }
    catch (err) {
      await reload();
      setError(err.message || 'The report could not be generated. Your answers are saved; please retry.');
    }
    finally { setBusy(false); }
  };
  const startAnother = async () => {
    setBusy(true); setError('');
    try { accept(await onboardingApi.newSession(token, state.revision)); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };
  const saveEdit = event => {
    event.preventDefault();
    let val = numeric.has(editKey) ? Number(editValue) : editKey === 'premises_suitable' ? editValue === 'true' : editValue.trim();
    if (editValue === '') return;
    send({ updates: { [editKey]: val }, correction: true, text: `Correct ${editKey.replaceAll('_', ' ')}` });
  };
  const locked = busy || isSubmitting || speech.transcribing;
  const current = state?.next;
  const showLocation = ['location', 'area_verification'].includes(current?.field);
  const completed = current?.field === 'complete';
  const assessment = !locked && !editKey && !input && !state?.paused && state?.assessment;
  return <section className="max-w-4xl mx-auto space-y-5" aria-label="Mira onboarding">
    <header className="rounded-3xl bg-sovereign-900 p-5 sm:p-7 text-white flex gap-4 items-center">
      <img src="/mira-avatar.png" alt="" className="w-16 h-16 rounded-full object-cover border-2 border-white/40" />
      <div className="flex-1"><p className="text-xs uppercase tracking-widest text-cyan-200 mb-1">Your business, one conversation</p>
        <h1 className="text-2xl font-bold">Let’s build your plan with Mira</h1>
        <p className="text-sm text-slate-200 mt-2">Speak or type in your preferred language. You can come back to your saved answers.</p>
      </div>
    </header>
    <div className="flex flex-wrap gap-2 items-center">
      <button className="mira-secondary" onClick={() => { setReadAloud(!readAloud); if (readAloud) speech.stopSpeaking(); }} aria-pressed={readAloud}>
        {readAloud ? <Volume2 size={18} /> : <VolumeX size={18} />} {readAloud ? 'Read replies aloud: on' : 'Turn on spoken guidance'}
      </button>
      {state && !completed && <button className="mira-secondary" disabled={locked} onClick={() => send({ action: state.paused ? 'resume' : 'pause', text: '' })}>
        {state.paused ? <Play size={16} /> : <Pause size={16} />} {state.paused ? 'Resume' : 'Pause and save'}
      </button>}
      <span className="text-xs text-slate-500">{busy ? 'Saving or checking…' : state ? 'Progress saved' : 'Connecting…'}</span>
    </div>
    {state?.location_confirmed && <p className="rounded-xl bg-sovereign-50 border border-sovereign-100 px-4 py-3 text-sm text-sovereign-900">
      Business location: {state.location.village_name}, {state.location.block_name}, {state.location.district_name}, {state.location.state_name} · {state.location.is_rural ? 'Rural' : 'Urban / semi-urban'}
    </p>}
    {(error || speech.speechError) && <div role="alert" className="rounded-2xl border border-amber-300 bg-amber-50 p-4 space-y-3 text-sm text-amber-950">
      <p>{error || speech.speechError}</p>
      <div className="flex flex-wrap gap-2">
        {pendingRequest.current && !needsReload && <button className="mira-secondary" disabled={locked} onClick={() => send({}, true)}>Retry saved answer</button>}
        <button className="mira-secondary" disabled={locked} onClick={reload}><RefreshCw size={16} /> Reload saved conversation</button>
      </div>
    </div>}
    {state && <>
      <div className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-7 shadow-sm space-y-5">
        <div className="max-h-56 overflow-y-auto space-y-3 text-sm" aria-label="Conversation history">
          {state.history.slice(0, -1).slice(-8).map((message, index) => <div key={index} className={message.role === 'user' ? 'ml-8 rounded-2xl bg-sovereign-50 p-3 text-slate-700' : 'mr-8 text-slate-500 p-2'}>
            <span className="font-semibold">{message.role === 'user' ? 'You' : 'Mira'}: </span>{message.text}
          </div>)}
        </div>
        <div aria-live="polite" aria-atomic="true" className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-wider text-sovereign-700">Mira</p>
          <p className="text-lg sm:text-xl leading-relaxed font-medium text-slate-900">{reply || current?.text}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="mira-secondary" type="button" onClick={() => speech.speaking ? speech.stopSpeaking() : speech.speak(reply || current.text)}>
            {speech.speaking ? <Square size={16} /> : <Volume2 size={16} />} {speech.speaking ? 'Stop speaking' : 'Listen again'}
          </button>
          {!completed && <button className="mira-secondary" disabled={locked} onClick={() => send({ action: 'explain', text: '' })}>Explain simply</button>}
          {!completed && state.location && <button className="mira-secondary" disabled={locked} onClick={() => send({ action: 'change_location', text: '' })}>Change business location</button>}
        </div>
        {!state.paused && !completed && <>
          {showLocation && <BusinessLocationPicker key={state.location?.village_code ?? 'choose'} token={token} state={state} language={language} disabled={locked} onError={setError} onResult={accept} />}
          {['location_confirmation', 'business_confirmation', 'pending_changes'].includes(current.field) && <div className="flex flex-wrap gap-3">
            <button className="mira-primary" disabled={locked} onClick={() => send({ action: current.action, text: '' })}><Check size={18} /> Yes, use this</button>
            {current.field === 'pending_changes' && <button className="mira-secondary" disabled={locked} onClick={() => send({ action: 'discard_change', text: '' })}>Keep previous answers</button>}
            {current.field === 'business_confirmation' && <p className="text-sm text-slate-600 self-center">To correct this, tell Mira what to change or edit an answer below.</p>}
          </div>}
          {!!current.choices?.length && <div className="flex flex-wrap gap-2">{current.choices.map(choice => <button key={String(choice)} className="mira-secondary" disabled={locked}
            onClick={() => send({ updates: { [current.field === 'odop_explore' ? 'odop_preference' : current.field]: choice }, source: 'control' })}>
            {labels[String(choice)] || String(choice).replaceAll('_', ' ')}
          </button>)}</div>}
          {current.field === 'cost_items' && <CostBreakdown disabled={locked} activity={state.fields.activity?.value}
            onSave={cost_items => send({ updates: { cost_items }, source: 'control' })} />}
          {current.field === 'recommendations' && <div className="space-y-3">{state.recommendations.map(rec => <article key={rec.id} className="rounded-2xl border border-sovereign-100 p-4 space-y-2">
            <h2 className="font-bold">{rec.idea}</h2><p className="text-sm">{rec.description}</p>
            <p className="text-sm text-slate-600">{rec.why_region} {rec.market_evidence}</p>
            <p className="text-sm font-semibold">Indicative outlay: {rec.outlay_range.map(formatMoney).join(' – ')}</p>
            <p className="text-sm">{rec.space}</p>
            <p className="text-sm">Potential financing from the lower cost reference: {formatMoney(rec.potential_financing)}. Scheme to check: {rec.scheme}. {rec.scheme_note}</p>
            <button className="mira-primary" disabled={locked} onClick={() => send({ recommendation_id: rec.id, text: '' })}>Explore this idea</button>
          </article>)}<button className="mira-secondary" disabled={locked} onClick={() => send({ action: 'alternatives', text: '' })}>Reject these and find alternatives</button></div>}
          <form onSubmit={event => { event.preventDefault(); if (input.trim()) send(); }} className="space-y-3">
            <label className="block text-sm font-medium text-slate-700" htmlFor="mira-answer">{inputSource === 'voice' ? 'Check what Mira heard. Correct any words before sending.' : 'Your answer — you can give several details at once'}</label>
            <textarea id="mira-answer" className="mira-input min-h-24" value={input} maxLength={3000} onChange={e => setInput(e.target.value)}
              placeholder="Tell Mira in your own words…" disabled={locked} />
            <div className="flex flex-wrap gap-3">
              <button type="button" className="mira-primary" disabled={locked} onClick={() => speech.isRecording ? speech.stopRecording() : speech.startRecording()}>
                {speech.isRecording ? <Square size={20} /> : <Mic size={20} />} {speech.isRecording ? 'Finish recording' : 'Speak to Mira'}
              </button>
              {speech.isRecording && <button type="button" className="mira-secondary" onClick={speech.cancelRecording}>Cancel recording</button>}
              <button className="mira-secondary" type="submit" disabled={locked || speech.isRecording || !input.trim()}><Send size={18} /> Send answer</button>
            </div>
            {speech.transcribing && <p role="status" className="text-sm">Turning your speech into text…</p>}
          </form>
        </>}
      </div>
      {assessment && <div className="rounded-2xl bg-white border border-slate-200 p-5 space-y-3" aria-label="Financial assessment">
        <h2 className="font-bold text-lg">Your indicative financing assessment</h2>
        <dl className="grid grid-cols-2 gap-3 text-sm">{[
          ['Project outlay', assessment.project_outlay], ['Your own contribution', assessment.personal_contribution],
          ['Remaining funding need', assessment.capital_deficit], [assessment.budget_kind === 'borrowing' ? 'Shortfall after expected borrowing' : 'Shortfall against stated budget', assessment.budget_shortfall],
          ['Monthly rent used', assessment.monthly_rent], ['Candidate subsidy (separate)', assessment.subsidy_candidate],
          ['Normal loan EMI estimate', assessment.normal_loan.monthly_emi], ['SCA margin assistance candidate', assessment.capital_structure.sca_soft_loan_eligible_amount],
        ].map(([label, amount]) => <div key={label}><dt className="text-slate-500">{label}</dt><dd className="font-bold mt-1">{formatMoney(amount)}</dd></div>)}</dl>
        <p className="text-sm">Normal bank reference: {assessment.normal_loan.rate_pct}% · {assessment.normal_loan.tenure_years} years · {assessment.normal_loan.moratorium_months} months moratorium.</p>
        <p className="text-sm">SCA reference: {assessment.capital_structure.sca_interest_rate_pct}% · {assessment.capital_structure.sca_tenure_years} years. This is margin assistance, separate from the bank loan.</p>
        <p className="text-xs text-slate-500">{assessment.notice}</p>
      </div>}
      {state.regional && <div className="rounded-2xl border bg-white p-4 text-sm space-y-2"><h2 className="font-semibold">Regional assessment</h2>
        <p>{state.regional.evidence.plain_language_summary || 'Regional intelligence checked. Review the evidence and limitations in the full report.'}</p>
        <p className="text-slate-500">Confidence: {state.regional.evidence.confidence || 'Not established'}. {(state.regional.evidence.data_quality_limitations || []).join(' ')}</p>
      </div>}
      <details className="rounded-2xl border border-slate-200 bg-white p-4" open={Boolean(editKey)}>
        <summary className="font-semibold cursor-pointer">Review or correct your saved answers</summary>
        <dl className="mt-4 divide-y divide-slate-100">{Object.entries(state.fields).map(([key, field]) => <div className="py-3 flex justify-between gap-4 text-sm" key={key}>
          <div><dt className="text-slate-500 capitalize">{key.replaceAll('_', ' ')}</dt><dd className="mt-1 break-words">{typeof field.value === 'object' ? Object.entries(field.value).map(([k, v]) => `${k.replaceAll('_', ' ')}: ${formatMoney(v)}`).join('; ') : String(field.value)}</dd></div>
          {!completed && key !== 'project_cost' && <button className="mira-secondary self-start" aria-label={`Correct ${key.replaceAll('_', ' ')}`} disabled={locked || state.paused} onClick={() => { setEditKey(key); setEditValue(String(field.value)); }}><Pencil size={15} /> Edit</button>}
        </div>)}</dl>
        {editKey === 'cost_items' && <CostBreakdown initial={state.fields.cost_items.value} activity={state.fields.activity?.value} disabled={locked}
          onSave={cost_items => send({ updates: { cost_items }, correction: true, source: 'control' })} />}
        {editKey && editKey !== 'cost_items' && <form className="mt-4 space-y-3" onSubmit={saveEdit}>
          <label className="block font-medium text-sm">Correct {editKey.replaceAll('_', ' ')}
            {editableChoices[editKey] ? <select className="mira-input mt-2" value={editValue} onChange={e => setEditValue(e.target.value)}>
              {editableChoices[editKey].map(v => <option key={String(v)} value={String(v)}>{labels[String(v)] || String(v)}</option>)}
            </select> : <input className="mira-input mt-2" value={editValue} required type={numeric.has(editKey) ? 'number' : 'text'} min="0" step="any" onChange={e => setEditValue(e.target.value)} />}
          </label>
          <button className="mira-primary" disabled={locked}>Save correction</button>
          <button className="mira-secondary ml-2" type="button" onClick={() => setEditKey('')}>Cancel</button>
        </form>}
      </details>
      {current.field === 'ready' && <button className="mira-primary w-full justify-center py-4" disabled={locked || Boolean(input.trim()) || Boolean(editKey)} onClick={finish}>{isSubmitting ? 'Generating report…' : 'Confirm details and generate feasibility report'}</button>}
      {completed && <div className="flex flex-wrap gap-3"><button className="mira-primary" disabled={locked} onClick={finish}>Open saved report</button><button className="mira-secondary" disabled={locked} onClick={startAnother}>Start another plan</button></div>}
    </>}
  </section>;
}
