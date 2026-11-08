import React, { useEffect, useState } from 'react';
import { Loader2, Sparkles } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { odopHybridApi } from '../../services/api';
import { hybridInput, hybridInputKey, validHybridReview } from './odopHybridState';

const primary = 'min-h-12 rounded-xl bg-purple-800 px-5 py-3 text-base font-bold text-white hover:bg-purple-900 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-4 focus:ring-purple-200';
const secondary = 'min-h-12 rounded-xl border-2 border-purple-700 bg-white px-5 py-3 text-base font-bold text-purple-950 hover:bg-purple-50 focus:outline-none focus:ring-4 focus:ring-purple-200';

export function OdopHybridStep({ form, review, onReview, onSelect, onSkip, title = 'Step 3: ODOP alignment' }) {
  const { token } = useAuth();
  const active = validHybridReview(review, form) ? review : null;
  const [context, setContext] = useState(null);
  const [contextError, setContextError] = useState('');
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let current = true;
    setLoading(true); setContext(null); setContextError('');
    odopHybridApi.context(token, form.state_name, form.district_name)
      .then(value => { if (current) setContext(value); })
      .catch(error => { if (current) setContextError(error.message); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [token, form.state_name, form.district_name, retry]);

  const evaluate = async () => {
    if (active?.result) {
      onReview(previous => ({ ...previous, choice: 'yes' }));
      return;
    }
    const key = hybridInputKey(form);
    const requestId = crypto.randomUUID();
    onReview({ input_key: key, original_form: { ...form }, choice: 'yes', request_id: requestId, busy: true });
    try {
      const result = await odopHybridApi.evaluate(token, { ...hybridInput(form), consent: true });
      onReview(previous => previous?.request_id === requestId && previous.choice === 'yes'
        ? { ...previous, result, busy: false, error: null } : previous);
    } catch (error) {
      onReview(previous => previous?.request_id === requestId && previous.choice === 'yes'
        ? { ...previous, error: error.message, busy: false } : previous);
    }
  };

  const result = active?.result;
  const tone = result?.band === 'recommended' ? 'border-green-300 bg-green-50 text-green-950'
    : result?.band === 'possible' ? 'border-amber-300 bg-amber-50 text-amber-950' : 'border-rose-300 bg-rose-50 text-rose-950';
  return <section className="space-y-5 text-base text-slate-900">
    <h3 className="flex items-center gap-2 text-xl font-bold"><Sparkles size={22} /> {title}</h3>
    <div className="rounded-xl border border-slate-300 bg-slate-50 p-4 space-y-3">
      <p><strong>What is ODOP?</strong> One District One Product promotes products a district is known for.</p>
      <p><strong>Possible benefits:</strong> help with branding, packaging, market links and shared services. Support depends on the product, local facilities and scheme rules.</p>
      <a className="inline-block font-semibold text-purple-800 underline" href="https://www.mofpi.gov.in/en/node/3285" target="_blank" rel="noreferrer">Read the official ODOP overview</a>
      {loading ? <p role="status">Loading your district’s product…</p> : context?.has_odop_record ? <p className="rounded-lg bg-white p-3">
        <strong>{context.district_name} ODOP:</strong> {context.odop_product}
        {context.secondary_product && <span className="block mt-1">Also listed: {context.secondary_product}</span>}
      </p> : <p className="rounded-lg bg-white p-3">{contextError || 'No exact ODOP product is available for this district. You can continue with your own idea.'}
        {contextError && <button type="button" onClick={() => setRetry(n => n + 1)} className="ml-2 min-h-11 font-bold underline">Retry loading</button>}
      </p>}
    </div>
    <div className="rounded-xl border-2 border-purple-300 p-4 space-y-4">
      <p className="font-bold">Would you like to evaluate a combination of your business idea and your district’s ODOP product?</p>
      <p className="text-sm text-slate-600">Choosing Yes sends your enterprise details, idea and district product to the AI evaluator. The score checks business synergy; the normal financial appraisal comes later.</p>
      <div className="flex flex-col gap-3 sm:flex-row">
        <button type="button" onClick={evaluate} disabled={loading || !context?.has_odop_record || active?.busy || !form.enterprise_name?.trim()} className={primary}>
          {active?.busy ? <span className="inline-flex items-center gap-2"><Loader2 className="animate-spin" size={20} /> Evaluating…</span>
            : active?.error ? 'Try evaluation again' : 'Yes, evaluate the combination'}
        </button>
        <button type="button" onClick={onSkip} className={secondary}>No, continue with my own idea</button>
      </div>
    </div>
    {active?.error && <p role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-950">{active.error}</p>}
    {result && <div className="space-y-4">
      <div className={`rounded-xl border p-4 ${tone}`}>
        <p className="text-2xl font-extrabold">{result.score}/100 <span className="text-base font-bold">— {result.label}</span></p>
        <p className="mt-2">{result.summary}</p>
      </div>
      <div className="rounded-xl border border-slate-300 p-4 space-y-3">
        <h4 className="text-lg font-bold">Proposed combination: {result.hybrid_name}</h4>
        <p>{result.hybrid_description}</p>
        <ul className="list-disc space-y-2 pl-5">{result.reasons.map((text, index) => <li key={index}>{text}</li>)}</ul>
        <details className="rounded-lg bg-slate-50 p-3">
          <summary className="cursor-pointer py-1 font-bold">Practical steps and things to check</summary>
          <ul className="mt-3 list-disc space-y-2 pl-5">{[...result.practical_steps, ...result.risks, ...result.missing_information].map((text, index) => <li key={index}>{text}</li>)}</ul>
        </details>
        <p className="text-sm text-slate-600">{result.note}</p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <button type="button" onClick={() => onSelect('hybrid')} className={result.band === 'recommended' ? primary : secondary}>Use this combination</button>
          <button type="button" onClick={() => onSelect('original')} className={secondary}>Continue with my own idea</button>
        </div>
        {active.selection && <p className="text-sm font-semibold">Current choice: {active.selection === 'hybrid' ? 'the combination' : 'your original idea'}.</p>}
      </div>
    </div>}
  </section>;
}
