import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useAutoTranslate } from '../../hooks/useAutoTranslate';
import { odopHybridApi } from '../../services/api';
import { hybridInput } from '../Wizard/odopHybridState';
import { MiraGuide } from './MiraGuide';
import { MiraAnswer } from './MiraAnswer';
import { TranslatedText as T } from '../TranslatedText';
import { copy } from './copy';

export function MiraOdop({ form, onChoice, onBack, disabled = false, savedChoice }) {
  const { token } = useAuth();
  const { language } = useLanguage();
  const [context, setContext] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const active = useRef(true);
  useEffect(() => {
    active.current = true;
    odopHybridApi.context(token, form.state_name, form.district_name).then(data => { if (active.current) setContext(data); })
      .catch(err => { if (active.current) setError(err.message); }).finally(() => { if (active.current) setLoading(false); });
    return () => { active.current = false; };
  }, [token, form.state_name, form.district_name]);
  const prompt = loading ? copy('waiting', language) : result
    ? `The combination scored ${result.score} out of 100. ${result.label}. ${result.summary} Would you like to use the combination or keep your original idea?`
    : context?.has_odop_record
      ? `ODOP means One District One Product. Your district's product is ${context.odop_product}. A connection may offer branding, packaging, supplier or market opportunities, depending on scheme rules. Would you like to evaluate a combination with your idea?`
      : 'An exact district ODOP product could not be loaded. You can continue with your original idea.';
  const { translated: speech } = useAutoTranslate(prompt);
  const choose = async value => {
    if (value !== 'evaluate') { onChoice(value, result); return; }
    if (busy) return;
    setBusy(true); setError('');
    try {
      const data = await odopHybridApi.evaluate(token, { ...hybridInput(form), consent: true });
      if (active.current) setResult(data);
    } catch (err) { if (active.current) setError(err.message); }
    finally { if (active.current) setBusy(false); }
  };
  return <div className="mira-layout">
    <MiraGuide text={speech} />
    <div className="mira-card space-y-5">
      {result && <>
        <p className="text-3xl font-extrabold text-purple-900">{result.score}/100</p>
        <h2 className="text-xl font-bold"><T text={result.hybrid_name} /></h2>
        <p><T text={result.hybrid_description} /></p>
        <details><summary className="cursor-pointer font-semibold"><T text="Reasons, practical steps and risks" /></summary>
          {[...result.reasons, ...result.practical_steps, ...result.risks, ...result.missing_information].map((text, i) => <p className="mt-3" key={i}><T text={text} /></p>)}
        </details>
        <p className="text-sm text-slate-600"><T text={result.note} /></p>
      </>}
      {error && <p role="alert" className="mira-error"><T text={error} /></p>}
      {savedChoice && !result && <p className="rounded-xl bg-purple-50 p-3"><T text={`Saved choice: ${savedChoice === 'hybrid' ? 'use the combination' : 'keep the original idea'}. You can continue without evaluating again.`} /></p>}
      <MiraAnswer key={`${!!result}:${language}`} disabled={busy || loading || disabled} onAnswer={choose} onBack={onBack} initial={savedChoice && !result ? 'keep' : ''}
        options={result ? [{ value: 'hybrid', label: 'Use this combination' }, { value: 'original', label: 'Continue with my own idea' }]
          : [...(savedChoice ? [{ value: 'keep', label: 'Keep my saved choice' }] : []), ...(context?.has_odop_record ? [{ value: 'evaluate', label: error ? 'Try evaluation again' : 'Yes, evaluate the combination' }] : []), { value: 'original', label: 'No, continue with my own idea' }]} />
    </div>
  </div>;
}
