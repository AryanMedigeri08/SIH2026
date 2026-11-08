import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useAutoTranslate } from '../../hooks/useAutoTranslate';
import { onboardingApi } from '../../services/api';
import { MiraGuide } from './MiraGuide';
import { copy } from './copy';

const fields = ['state_name', 'district_name', 'block_name', 'village_name'];
const levels = ['states', 'districts', 'blocks', 'villages'];
export function MiraLocation({ location, onConfirm, detecting = false }) {
  const { token } = useAuth();
  const { language } = useLanguage();
  const [manual, setManual] = useState(!location?.village_name);
  const [values, setValues] = useState(() => Object.fromEntries(fields.map(key => [key, location?.[key] || ''])));
  const [options, setOptions] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const { translated: problem } = useAutoTranslate(error);
  const { translated: empty } = useAutoTranslate('No matching records are available. Try another parent location or retry loading.');
  useEffect(() => {
    if (!manual) return;
    let active = true;
    setBusy(true); setError('');
    const parents = { state: values.state_name, district: values.district_name, block: values.block_name };
    Promise.all(levels.map((level, i) => i === 0 || values[fields[i - 1]]
      ? onboardingApi.locations(token, level, Object.fromEntries(Object.entries(parents).slice(0, i))) : Promise.resolve([])))
      .then(data => { if (active) setOptions(Object.fromEntries(levels.map((key, i) => [key, data[i]]))); })
      .catch(err => { if (active) setError(err.message); }).finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [token, manual, values.state_name, values.district_name, values.block_name, retry]);
  useEffect(() => {
    if (location?.village_name && !manual) setValues(Object.fromEntries(fields.map(key => [key, location[key] || ''])));
  }, [location, manual]);
  const confirm = async () => {
    setBusy(true); setError('');
    try {
      const payload = { ...values, source: manual ? 'manual' : 'gps', confirmed: true,
        latitude: manual ? null : location?.latitude ?? null, longitude: manual ? null : location?.longitude ?? null };
      const result = await onboardingApi.confirm(token, payload);
      await onConfirm(result);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };
  const complete = fields.every(key => values[key]);
  const nextMissing = fields.findIndex(key => !values[key]);
  return <div className="mira-layout">
    <MiraGuide text={`${copy(manual ? 'manual' : 'location', language)}${!manual ? ` ${fields.slice().reverse().map(key => values[key]).filter(Boolean).join(', ')}` : ''}`} />
    <section className="mira-card space-y-5">
      {detecting && <p role="status">{copy('waiting', language)}</p>}
      {manual ? fields.map((field, i) => <label key={field} className="block space-y-2 font-bold">
        <span>{copy(field.replace('_name', ''), language)}</span>
        <select className="mira-input" required value={values[field]} disabled={busy || detecting || (i > 0 && !values[fields[i - 1]])}
          onChange={event => setValues(previous => ({ ...previous, [field]: event.target.value, ...Object.fromEntries(fields.slice(i + 1).map(key => [key, ''])) }))}>
          <option value="">—</option>{(options[levels[i]] || []).map(value => <option key={value} value={value}>{value}</option>)}
        </select>
      </label>) : <p className="text-xl font-semibold leading-relaxed">{fields.slice().reverse().map(key => values[key]).filter(Boolean).join(', ')}</p>}
      {manual && !busy && nextMissing >= 0 && options[levels[nextMissing]]?.length === 0 && <p className="text-slate-700">{empty}</p>}
      {error && <p role="alert" className="mira-error">{problem}</p>}
      {manual && <button type="button" onClick={() => setRetry(n => n + 1)} className="mira-secondary">{copy('retry', language)}</button>}
      <button type="button" disabled={!complete || busy || detecting} className="mira-primary w-full" onClick={confirm}>{copy(busy ? 'waiting' : 'yes', language)}</button>
      {!manual && <button type="button" className="mira-secondary w-full" onClick={() => setManual(true)}>{copy('change', language)}</button>}
    </section>
  </div>;
}
