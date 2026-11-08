import React, { useEffect, useRef, useState } from 'react';
import { ArrowLeft, CheckCircle2, Loader2, MapPin } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { planningApi } from '../../services/api';

const money = value => value == null ? 'Not yet known' : new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0,
}).format(value);
const inputClass = 'w-full min-h-12 rounded-xl border border-slate-400 bg-white px-3 py-3 text-base text-slate-950 focus:outline-none focus:ring-2 focus:ring-purple-600';
const primaryClass = 'min-h-12 rounded-xl bg-purple-800 px-5 py-3 text-base font-bold text-white hover:bg-purple-900 focus:outline-none focus:ring-4 focus:ring-purple-300 disabled:opacity-50 disabled:cursor-not-allowed';

function Field({ label, children, hint }) {
  return <label className="block space-y-2 text-base font-semibold text-slate-900">
    <span>{label}</span>{children}{hint && <span className="block text-sm font-normal text-slate-600">{hint}</span>}
  </label>;
}

function PlanCard({ plan, onChoose, choosing }) {
  const [acknowledge, setAcknowledge] = useState(false);
  const [acceptRisk, setAcceptRisk] = useState(false);
  const f = plan.financial_analysis;
  const evidence = plan.regional.evidence || {};
  const needsReview = plan.concerns.length > 0;
  const unknownCash = plan.available_own_money == null;
  return <article className="flex flex-col gap-4 rounded-2xl border-2 border-slate-300 bg-white p-5 shadow-sm">
    <div>
      <span className={`inline-block rounded-full px-3 py-1 text-sm font-bold ${needsReview ? 'bg-amber-100 text-amber-950' : 'bg-green-100 text-green-950'}`}>
        {needsReview ? 'Needs your review' : 'Estimated fit'}
      </span>
      <h3 className="mt-3 text-xl font-bold text-slate-950">{plan.name}</h3>
      <p className="mt-1 text-base text-slate-700">{plan.configuration}</p>
    </div>
    <dl className="space-y-3 text-base">
      {[
        ['Estimated project cost', plan.project_cost],
        ['Own money to arrange', plan.required_own_money],
        ['Loan after scheme calculation', f.loan_principal],
        ['Monthly bank repayment', f.amortization.monthly_emi],
      ].map(([label, value]) => <div key={label} className="flex flex-wrap justify-between gap-x-2 border-b border-slate-100 pb-2">
        <dt className="text-slate-700">{label}</dt><dd className="font-bold text-slate-950">{money(value)}</dd>
      </div>)}
    </dl>
    {plan.equity_gap > 0 && <p className="rounded-lg bg-amber-50 p-3 font-semibold text-amber-950">
      You need {money(plan.equity_gap)} more own money. Review funding options before starting.
    </p>}
    <p className="text-sm text-slate-700">{plan.cost_source === 'user_equipment_quote' ? 'Based on your equipment quote. Other costs are estimates.' : 'Dynamic estimate calibrated to sector benchmarks. Machinery schedule configured automatically.'}</p>
    <details className="rounded-xl bg-slate-50 p-3 text-slate-800">
      <summary className="cursor-pointer py-1 text-base font-bold">Why this plan? See details</summary>
      <div className="mt-3 space-y-3 text-base">
        <p>{plan.description}</p>
        <p><strong>Local assessment:</strong> {plan.regional.recommendation.replaceAll('_', ' ').toLowerCase()}. Evidence confidence: {plan.regional.confidence.replaceAll('_', ' ').toLowerCase()}.</p>
        {[...(evidence.top_positive_drivers || []), ...(evidence.top_risk_factors || []), ...(evidence.missing_evidence || [])].map((text, i) => <p key={i}>{text}</p>)}
        <p><strong>ODOP connection:</strong> {plan.odop_alignment?.is_aligned ? 'Aligned with district product or value chain.' : 'No confirmed alignment for this business.'}</p>
        <p>Estimated annual sales: <strong>{money(plan.input_parameters.annual_turnover_estimate)}</strong></p>
        <p>Working capital required: <strong>{money(f.working_capital.working_capital_required)}</strong></p>
        <p>Repayment cover (DSCR): <strong>{f.dscr.dscr.toFixed(2)}×</strong></p>
        <p>Existing capital-structure equity: {money(f.capital_structure.required_promoter_equity)}. Existing scheme margin: {money(f.promoter_margin_amount)}.</p>
        {plan.warnings.map((text, i) => <p className="text-sm" key={i}>{text}</p>)}
      </div>
    </details>
    {needsReview && <div className="space-y-2 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
      {plan.concerns.map((text, i) => <p key={i}>{text}</p>)}
    </div>}
    <div className="mt-auto space-y-3">
      <label className="flex cursor-pointer items-start gap-3 text-base text-slate-900">
        <input type="checkbox" checked={acknowledge} onChange={e => setAcknowledge(e.target.checked)} className="mt-1 h-5 w-5 shrink-0 accent-purple-800" />
        <span>{unknownCash ? `I can arrange ${money(plan.required_own_money)} and understand these are estimates.` : 'I understand these costs and sales are estimates.'}</span>
      </label>
      {needsReview && <label className="flex cursor-pointer items-start gap-3 text-base text-slate-900">
        <input type="checkbox" checked={acceptRisk} onChange={e => setAcceptRisk(e.target.checked)} className="mt-1 h-5 w-5 shrink-0 accent-purple-800" />
        <span>I understand the concerns above and want to explore this plan.</span>
      </label>}
      <button type="button" onClick={() => onChoose(plan, acknowledge, acceptRisk)} disabled={!!choosing || !acknowledge || (needsReview && !acceptRisk)} className={`${primaryClass} w-full`}>
        {choosing === plan.proposal_id ? 'Opening plan…' : 'Review this plan'}
      </button>
    </div>
  </article>;
}

export function EnterprisePlanner({ path, onBack, onAccept }) {
  const { token, userProfile } = useAuth();
  const [form, setForm] = useState({
    own_cash: '', business_id: '', idea_description: '', custom_sector: 'general', custom_category: 'manufacturing',
    promoter_name: userProfile?.name || '', gender: ['Male', 'Female', 'Other'].find(g => g.toLowerCase() === userProfile?.gender?.toLowerCase()) || 'Unspecified', promoter_category: 'general',
    state_name: '', district_name: '', block_name: '', village_name: '', is_rural: true,
    premise_type: 'owned', monthly_rent: '',
  });
  const [choices, setChoices] = useState([]);
  const [locations, setLocations] = useState({ states: [], districts: [], blocks: [], villages: [] });
  const [loadingLocations, setLoadingLocations] = useState({});
  const [locationError, setLocationError] = useState('');
  const [reload, setReload] = useState(0);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState(null);
  const [choosing, setChoosing] = useState(null);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);

  useEffect(() => {
    let active = true;
    planningApi.businesses(token).then(data => { if (active) setChoices(data); })
      .catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [token, reload]);

  // Fetch only actual LGD results. Reset descendants as soon as a parent changes.
  useEffect(() => {
    let active = true;
    const load = async (level, params) => {
      setLoadingLocations(prev => ({ ...prev, [level]: true }));
      try {
        const data = await planningApi.locations(token, level, params);
        if (active) setLocations(prev => ({ ...prev, [level]: data }));
      } catch (e) {
        if (active) setLocationError(e.message || 'Location list could not load. Please retry.');
      } finally {
        if (active) setLoadingLocations(prev => ({ ...prev, [level]: false }));
      }
    };
    setLocationError('');
    load('states', {});
    if (form.state_name) load('districts', { state_name: form.state_name });
    const district = locations.districts.find(d => d.district_name === form.district_name);
    const block = locations.blocks.find(b => b.development_block_name === form.block_name);
    if (form.district_name) load('blocks', { district_name: form.district_name, state_name: form.state_name,
      ...(district?.district_code ? { district_code: district.district_code } : {}) });
    if (form.district_name && form.block_name) load('villages', { district_name: form.district_name, block_name: form.block_name,
      ...(district?.district_code ? { district_code: district.district_code } : {}),
      ...(block?.development_block_code ? { block_code: block.development_block_code } : {}) });
    return () => { active = false; };
  }, [token, form.state_name, form.district_name, form.block_name, reload]);

  const update = (key, value) => {
    setForm(prev => {
      const next = { ...prev, [key]: value };
      if (key === 'state_name') Object.assign(next, { district_name: '', block_name: '', village_name: '' });
      if (key === 'district_name') Object.assign(next, { block_name: '', village_name: '' });
      if (key === 'block_name') next.village_name = '';
      return next;
    });
    if (key === 'state_name') setLocations(prev => ({ ...prev, districts: [], blocks: [], villages: [] }));
    if (key === 'district_name') setLocations(prev => ({ ...prev, blocks: [], villages: [] }));
    if (key === 'block_name') setLocations(prev => ({ ...prev, villages: [] }));
    setResult(null);
    setError('');
  };

  const evaluate = async event => {
    event.preventDefault();
    setPending(true); setError('');
    try {
      const payload = {
        ...form, path, business_id: path === 'idea_only' ? form.business_id : null,
        own_cash: form.own_cash === '' ? null : Number(form.own_cash),
        monthly_rent: form.premise_type === 'rented' ? Number(form.monthly_rent) : 0,
      };
      const data = await planningApi.evaluate(token, payload);
      if (mounted.current) { setResult(data); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    } catch (e) {
      if (mounted.current) setError(e.message || 'Could not compare plans. Please try again.');
    } finally { if (mounted.current) setPending(false); }
  };

  const accept = async (plan, acknowledge, risk) => {
    setChoosing(plan.proposal_id); setError('');
    try {
      const accepted = await planningApi.accept(token, result.draft_id, {
        proposal_id: plan.proposal_id, acknowledge_estimates: acknowledge, accept_risks: risk,
      });
      if (mounted.current) onAccept(accepted);
    } catch (e) { if (mounted.current) setError(e.message); }
    finally { if (mounted.current) setChoosing(null); }
  };

  const locationSelect = (label, key, level, nameKey, disabled) => <Field label={label} key={key}>
    <select required value={form[key]} onChange={e => update(key, e.target.value)} className={inputClass} disabled={disabled || loadingLocations[level]}>
      <option value="">{loadingLocations[level] ? 'Loading…' : `Choose ${label.toLowerCase()}`}</option>
      {locations[level].map((item, i) => <option key={i} value={item[nameKey]}>{item[nameKey]}</option>)}
    </select>
  </Field>;

  return <section className="space-y-6">
    <button type="button" onClick={onBack} disabled={pending || !!choosing} className="inline-flex min-h-12 items-center gap-2 rounded-xl border border-slate-400 bg-white px-4 text-base font-bold text-slate-900 disabled:opacity-50">
      <ArrowLeft size={20} /> Choose a different starting point
    </button>
    <div>
      <h1 className="text-2xl font-bold text-slate-950">{result ? 'Compare your plans' : path === 'budget_only' ? 'Find a business for your money' : 'Find the investment for your idea'}</h1>
      <p className="mt-2 text-base text-slate-700">{result ? 'Choose a plan to review in the existing application. Nothing is saved as a business yet.' : 'First, tell us where you will work and what you have available.'}</p>
    </div>
    {error && <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-4 text-base text-red-900">{error}</div>}
    {result ? <>
      <p className="rounded-xl bg-blue-50 p-4 text-base text-blue-950">{result.search_note} {result.failed_trials > 0 && `${result.failed_trials} trial(s) could not be evaluated.`}</p>
      <div className="grid items-stretch gap-5 lg:grid-cols-3">
        {result.proposals.map(plan => <PlanCard key={plan.proposal_id} plan={plan} choosing={choosing} onChoose={accept} />)}
      </div>
      <button type="button" disabled={!!choosing} onClick={() => { setResult(null); setError(''); }} className="min-h-12 rounded-xl border-2 border-purple-800 bg-white px-5 py-3 text-base font-bold text-purple-900">Change details and compare again</button>
    </> : <form onSubmit={evaluate} className="space-y-6">
      <fieldset disabled={pending} className="space-y-6 disabled:opacity-70">
        <div className="rounded-2xl border border-slate-300 bg-white p-5 space-y-5">
          <h2 className="flex items-center gap-2 text-xl font-bold text-slate-950"><MapPin size={22} /> Where will you start?</h2>
          <div className="grid gap-5 sm:grid-cols-2">
            {locationSelect('State', 'state_name', 'states', 'state_name', false)}
            {locationSelect('District', 'district_name', 'districts', 'district_name', !form.state_name)}
            {locationSelect('Block', 'block_name', 'blocks', 'development_block_name', !form.district_name)}
            {locationSelect('Village', 'village_name', 'villages', 'village_name', !form.block_name)}
          </div>
          {locationError && <div role="alert" className="text-base text-red-900">{locationError} <button type="button" className="min-h-12 font-bold underline" onClick={() => setReload(n => n + 1)}>Retry loading</button></div>}
          {!locationError && form.block_name && !loadingLocations.villages && locations.villages.length === 0 && <p role="status" className="text-base text-amber-900">No villages returned for this block. Check the block or try again when the location service is available.</p>}
        </div>
        <div className="rounded-2xl border border-slate-300 bg-white p-5 space-y-5">
          <h2 className="text-xl font-bold text-slate-950">Your idea and own money</h2>
          {path === 'idea_only' && <>
            <Field label="Which business matches your idea?">
              <select required value={form.business_id} onChange={e => update('business_id', e.target.value)} className={inputClass}>
                <option value="">Choose a business</option>
                {choices.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
                <option value="custom">Another business (Custom Idea)</option>
              </select>
            </Field>
            {form.business_id === 'custom' && <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Sector"><select className={inputClass} value={form.custom_sector} onChange={e => update('custom_sector', e.target.value)}>
                {['dairy', 'food_processing', 'repair', 'apparel', 'fabrication', 'general'].map(value => <option key={value} value={value}>{value.replaceAll('_', ' ')}</option>)}
              </select></Field>
              <Field label="Business type"><select className={inputClass} value={form.custom_category} onChange={e => update('custom_category', e.target.value)}><option value="manufacturing">Manufacturing</option><option value="service">Service</option></select></Field>
            </div>}
          </>}
          <Field label={path === 'idea_only' ? 'Describe what you want to sell or make' : 'Your skills, available space or resources (optional)'}>
            <textarea required={path === 'idea_only'} minLength={path === 'idea_only' ? 10 : undefined} maxLength={800} rows={3} value={form.idea_description} onChange={e => update('idea_description', e.target.value)} className={inputClass} placeholder="For example: products, customers, skills, equipment or raw materials" />
          </Field>
          <Field label={path === 'budget_only' ? 'How much own money can you invest? (₹)' : 'Own money available, if known (₹, optional)'} hint="Enter your own contribution, not the loan or total project cost. Leave blank if unknown; enter 0 if none is available.">
            <input type="number" required={path === 'budget_only'} min="0" max="100000000" step="1" inputMode="numeric" value={form.own_cash} onChange={e => update('own_cash', e.target.value)} className={inputClass} />
          </Field>
        </div>
        <div className="rounded-2xl border border-slate-300 bg-white p-5 space-y-5">
          <h2 className="text-xl font-bold text-slate-950">About you and your workspace</h2>
          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Your name"><input required maxLength={100} value={form.promoter_name} onChange={e => update('promoter_name', e.target.value)} className={inputClass} autoComplete="name" /></Field>
            <Field label="Category"><select value={form.promoter_category} onChange={e => update('promoter_category', e.target.value)} className={inputClass}>
              {['general', 'sc', 'st', 'obc', 'women', 'artisan', 'women_shg'].map(value => <option key={value} value={value}>{value.replaceAll('_', ' ').toUpperCase()}</option>)}
            </select></Field>
            <Field label="Gender"><select value={form.gender} onChange={e => update('gender', e.target.value)} className={inputClass}>{['Male', 'Female', 'Other', 'Unspecified'].map(value => <option key={value}>{value}</option>)}</select></Field>
            <Field label="Workspace"><select value={form.premise_type} onChange={e => update('premise_type', e.target.value)} className={inputClass}><option value="owned">Owned</option><option value="rented">Rented</option><option value="panchayat">Panchayat space</option></select></Field>
            {form.premise_type === 'rented' && <Field label="Monthly rent (₹)"><input required type="number" min="0" max="1000000" inputMode="numeric" value={form.monthly_rent} onChange={e => update('monthly_rent', e.target.value)} className={inputClass} /></Field>}
          </div>
        </div>
      </fieldset>
      <button disabled={pending || !!locationError || !token} className={`${primaryClass} inline-flex items-center justify-center gap-2 w-full sm:w-auto`}>
        {pending ? <><Loader2 className="animate-spin" size={22} /> Comparing plans…</> : <><CheckCircle2 size={22} /> Compare plans</>}
      </button>
      {pending && <p role="status" aria-live="polite" className="text-base text-slate-700">Checking local evidence and running the existing financial appraisal for each trial. This may take a few minutes. Please keep this page open.</p>}
    </form>}
  </section>;
}
