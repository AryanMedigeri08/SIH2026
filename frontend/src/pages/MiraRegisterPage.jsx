import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useAutoTranslate } from '../hooks/useAutoTranslate';
import { MiraGuide } from '../components/Onboarding/MiraGuide';
import { MiraLanguageChoice } from '../components/Onboarding/MiraLanguageChoice';
import { copy, registrationSteps } from '../components/Onboarding/copy';
import { indianPhone, phoneChallenge } from '../services/phoneAuth';

export function MiraRegisterPage() {
  const { language } = useLanguage();
  const { completePhoneRegistration, completePhoneSignIn } = useAuth();
  const [params] = useSearchParams();
  const signingIn = params.get('signin') === '1';
  const navigate = useNavigate();
  const [chosenLanguage, setChosenLanguage] = useState(null);
  const [step, setStep] = useState(signingIn ? 3 : 0);
  const [values, setValues] = useState({ name: '', gender: '', category: '', phone: '', otp: '' });
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [retryAt, setRetryAt] = useState(0);
  const challenge = useRef(null);
  const verified = useRef(null);
  const busy = useRef(false);
  const input = useRef(null);
  const key = registrationSteps[step];
  const { translated: translatedError } = useAutoTranslate(error);
  useEffect(() => { input.current?.focus(); setError(''); }, [step, chosenLanguage]);
  useEffect(() => () => challenge.current?.clear(), []);
  const update = value => setValues(previous => ({ ...previous, [key]: value }));
  const send = async () => {
    indianPhone(values.phone);
    challenge.current?.clear();
    challenge.current = phoneChallenge('mira-phone-recaptcha');
    await challenge.current.send(values.phone, chosenLanguage || language);
    setRetryAt(Date.now() + 60000);
    setStep(4);
  };
  const submit = async event => {
    event.preventDefault();
    if (busy.current) return;
    busy.current = true; setPending(true); setError('');
    try {
      if (key === 'name' && (!/[\p{L}]/u.test(values.name) || values.name.trim().length > 100)) throw new Error('Please enter your name.');
      if (['gender', 'category'].includes(key) && !values[key]) throw new Error('Please choose an option.');
      if (key === 'phone') { await send(); return; }
      if (key === 'otp') {
        if (!verified.current) verified.current = await challenge.current.confirm(values.otp.trim());
        if (signingIn) {
          const session = await completePhoneSignIn(verified.current);
          navigate(session.profile.projects_count > 0 ? '/dashboard' : '/onboarding', { replace: true });
          return;
        }
        await completePhoneRegistration(verified.current, {
          name: values.name.trim(), gender: values.gender, promoter_category: values.category,
          preferred_language: chosenLanguage || language,
        });
        navigate('/onboarding', { replace: true, state: { detectLocation: true } });
        return;
      }
      setStep(previous => previous + 1);
    } catch (err) { setError(err.message || 'Verification could not complete. Please try again.'); }
    finally { busy.current = false; setPending(false); }
  };
  const resend = async () => {
    if (pending || Date.now() < retryAt) return;
    setPending(true); setError('');
    try { await send(); setValues(previous => ({ ...previous, otp: '' })); }
    catch (err) { setError(err.message); }
    finally { setPending(false); }
  };
  if (!chosenLanguage) return <MiraLanguageChoice onContinue={setChosenLanguage} />;
  return <main className="mira-page"><div className="mira-shell">
    <header className="flex items-center justify-between gap-4 py-3">
      <Link to="/" className="text-xl font-bold text-purple-950">Udyam Saathi</Link>
      <button type="button" disabled={pending} className="mira-secondary" onClick={() => setChosenLanguage(null)}>{language.toUpperCase()}</button>
    </header>
    <div className="mira-layout">
      <MiraGuide text={copy(key, chosenLanguage)} />
      <section className="mira-card space-y-6" aria-label={copy(key, chosenLanguage)}>
        <p className="text-sm font-semibold text-purple-900">{step + 1} / {registrationSteps.length}</p>
        <form onSubmit={submit} className="space-y-5">
          {['gender', 'category'].includes(key) ? <fieldset disabled={pending} className="grid gap-3">
            <legend className="sr-only">{copy(key, chosenLanguage)}</legend>
            {(key === 'gender' ? [['Male','male'],['Female','female'],['Other','other']] : [['general','general'],['sc','SC'],['st','ST'],['obc','OBC']]).map(([value,label]) =>
              <label key={value} className={`mira-secondary flex cursor-pointer items-center gap-3 ${values[key] === value ? '!border-purple-800 !bg-purple-50' : ''}`}>
                <input type="radio" name={key} required value={value} checked={values[key] === value} onChange={() => update(value)} className="h-5 w-5 accent-purple-800" />{copy(label, chosenLanguage)}
              </label>)}
          </fieldset> : <label className="block space-y-3 font-semibold">
            <span>{copy(key, chosenLanguage)}</span>
            <input ref={input} key={key} required disabled={pending} className="mira-input" value={values[key]} onChange={e => update(e.target.value)}
              type={key === 'phone' ? 'tel' : 'text'} inputMode={['phone','otp'].includes(key) ? 'numeric' : 'text'}
              autoComplete={key === 'name' ? 'name' : key === 'phone' ? 'tel-national' : 'one-time-code'}
              maxLength={key === 'name' ? 100 : key === 'phone' ? 14 : 6} pattern={key === 'otp' ? '[0-9]{6}' : undefined} />
          </label>}
          {key === 'phone' && <p className="text-sm text-slate-600">{copy('phoneNotice', chosenLanguage)}</p>}
          <div id="mira-phone-recaptcha" className={key === 'phone' || key === 'otp' ? '' : 'hidden'} />
          {error && <p role="alert" className="mira-error">{translatedError}</p>}
          <button className="mira-primary w-full" disabled={pending}>{copy(pending ? 'waiting' : key === 'phone' ? 'sendCode' : key === 'otp' ? 'verify' : 'next', chosenLanguage)}</button>
        </form>
        {key === 'otp' && <button type="button" disabled={pending} onClick={resend} className="mira-secondary w-full">{copy('resend', chosenLanguage)}</button>}
        {step > (signingIn ? 3 : 0) && <button type="button" disabled={pending} className="mira-secondary" onClick={() => {
          if (key === 'otp') { challenge.current?.clear(); challenge.current = null; verified.current = null; }
          setStep(previous => previous - 1);
        }}>{copy('back', chosenLanguage)}</button>}
        <Link to="/login" className="block font-semibold text-purple-900 underline">{copy('existingAccount', chosenLanguage)}</Link>
      </section>
    </div>
  </div></main>;
}
