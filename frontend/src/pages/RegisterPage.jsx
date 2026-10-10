import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Fingerprint, Loader2, MapPin, Phone, UserRound, Chrome, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useBusiness } from '../context/BusinessContext';
import { useAuthCopy, AuthField, AuthLayout } from '../components/AuthExperience';
import { auth, RecaptchaVerifier } from '../services/firebaseClient';
import { reverseGeocodeCoords, detectLocationFromIP } from '../services/api';
import { authErrorMessage } from '../services/authErrorMessage';
import { destinationAfterSignIn } from '../services/authNavigation';
import { useLanguage } from '../context/LanguageContext';

const inputClass = 'w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-base outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-100';
const phoneIsValid = (value) => /^[6-9]\d{9}$/.test(value);

export function RegisterPage() {
  const c = useAuthCopy();
  const { language } = useLanguage();
  const { sendPhoneCode, completePhoneSignIn, loginWithGoogle, loginAsDemo, addPasskey, logout } = useAuth();
  const { loadUserBusinesses } = useBusiness();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [emailSkipped, setEmailSkipped] = useState(false);
  const [nameFinished, setNameFinished] = useState(false);
  const [confirmation, setConfirmation] = useState(null);
  const [code, setCode] = useState('');
  const [registered, setRegistered] = useState(false);
  const [location, setLocation] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const verifier = useRef(null);
  const phoneInput = useRef(null);
  const emailInput = useRef(null);
  const codeInput = useRef(null);

  useEffect(() => {
    let cancelled = false;
    async function locate() {
      const fallback = async () => {
        const result = await detectLocationFromIP().catch(() => null);
        if (!cancelled && result) setLocation(result);
      };
      if (!navigator.geolocation) return fallback();
      navigator.geolocation.getCurrentPosition(async (position) => {
        const result = await reverseGeocodeCoords(position.coords.latitude, position.coords.longitude).catch(() => null);
        if (!cancelled && result) setLocation({ ...result, latitude: position.coords.latitude, longitude: position.coords.longitude });
        else fallback();
      }, fallback, { timeout: 7000, maximumAge: 60000 });
    }
    locate();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!location) return;
    localStorage.setItem('user_detected_location', JSON.stringify(location));
  }, [location]);

  const step = registered ? 'passkey' : confirmation ? 'code' : !nameFinished ? 'name' : !phoneIsValid(phone) ? 'phone' : (!emailSkipped && !email.trim()) ? 'email' : 'send';
  useEffect(() => {
    if (step === 'phone') phoneInput.current?.focus();
    if (step === 'email') emailInput.current?.focus();
    if (step === 'code') codeInput.current?.focus();
  }, [step]);
  const prompt = step === 'name' ? c.guideName : step === 'phone' ? c.guidePhone : step === 'email' ? c.guideEmail : step === 'code' ? c.guideCode : step === 'passkey' ? c.guidePasskey : c.guideCode;

  const sendCode = async (event) => {
    event.preventDefault();
    if (!name.trim() || !phoneIsValid(phone)) { setError(c.errors.namePhone); return; }
    if (email && !/^\S+@\S+\.\S+$/.test(email)) { setError(c.errors.email); return; }
    setBusy(true); setError('');
    try {
      if (!verifier.current) verifier.current = new RecaptchaVerifier(auth, 'phone-recaptcha', { size: 'invisible' });
      const result = await sendPhoneCode(`+91${phone}`, verifier.current);
      setConfirmation(result);
    } catch (err) {
      setError(authErrorMessage(err, c.errors.send, language));
      verifier.current?.clear(); verifier.current = null;
    } finally { setBusy(false); }
  };

  const verifyCode = async (event) => {
    event.preventDefault();
    if (!/^\d{6}$/.test(code)) { setError(c.errors.code); return; }
    setBusy(true); setError('');
    try {
      await completePhoneSignIn(confirmation, code, {
        name: name.trim(), email: email.trim() || null,
        latitude: location?.latitude ?? null, longitude: location?.longitude ?? null,
      });
      setRegistered(true);
    } catch (err) { setError(authErrorMessage(err, c.errors.verify, language)); }
    finally { setBusy(false); }
  };

  const enterWith = async (method) => {
    setBusy(true); setError('');
    try {
      const session = await method();
      if (session.profile?.role && session.profile.role !== 'entrepreneur') {
        await logout();
        throw new Error('Staff accounts must use the role selector on the sign-in page.');
      }
      const destination = await destinationAfterSignIn(session, loadUserBusinesses);
      navigate(destination, { replace: true });
    } catch (err) { setError(authErrorMessage(err, c.errors.signIn, language)); }
    finally { setBusy(false); }
  };

  const finishPasskey = async () => {
    setBusy(true); setError('');
    try {
      await addPasskey();
      navigate('/onboarding', { replace: true });
    } catch (err) { setError(authErrorMessage(err, c.errors.passkey, language)); }
    finally { setBusy(false); }
  };

  return <AuthLayout mode="register" prompt={prompt}>
    <div className="mb-6 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-violet-700"><UserRound className="h-4 w-4" /> {c.register}</div>
    {error && <p role="alert" className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
    {registered ? <div className="space-y-5">
      <div className="rounded-2xl bg-emerald-50 p-5 text-emerald-900"><h2 className="font-bold">{c.passkeyReady}</h2><p className="mt-2 text-sm">{c.device}</p></div>
      <button type="button" disabled={busy} onClick={finishPasskey} className="flex w-full items-center justify-center gap-2 rounded-xl bg-violet-900 px-4 py-3 font-bold text-white disabled:opacity-50"><Fingerprint className="h-5 w-5" />{c.addPasskey}</button>
      <button type="button" onClick={() => navigate('/onboarding', { replace: true })} className="w-full rounded-xl border border-slate-200 px-4 py-3 font-semibold text-slate-700">{c.skipPasskey}</button>
    </div> : <>
      <form onSubmit={confirmation ? verifyCode : sendCode} className="space-y-4">
        <AuthField label={c.name} active={step === 'name'} done={nameFinished && name.trim().length >= 2}>
          <input className={inputClass} autoComplete="name" value={name} disabled={!!confirmation} onChange={(e) => { setName(e.target.value); if (nameFinished && !e.target.value.trim()) setNameFinished(false); }} onBlur={() => { if (name.trim().length >= 2) setNameFinished(true); }} onKeyDown={(e) => { if (e.key === 'Enter' && name.trim().length >= 2) { e.preventDefault(); setNameFinished(true); } }} placeholder={c.name} required />
        </AuthField>
        <AuthField label={c.phone} active={step === 'phone'} done={phoneIsValid(phone)}>
          <div className="flex gap-2"><span className="grid place-items-center rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-bold">+91</span><input ref={phoneInput} className={inputClass} type="tel" inputMode="numeric" autoComplete="tel-national" maxLength={10} value={phone} disabled={!!confirmation} onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))} placeholder="98765 43210" required /></div>
        </AuthField>
        <AuthField label={c.email} active={step === 'email'} done={!!email.trim() || emailSkipped}>
          <input ref={emailInput} className={inputClass} type="email" autoComplete="email" value={email} disabled={!!confirmation || emailSkipped} onChange={(e) => setEmail(e.target.value)} placeholder="name@example.com" />
          {!email && !emailSkipped && <button type="button" onClick={() => setEmailSkipped(true)} className="mt-2 text-xs font-semibold text-violet-700 underline">{c.skipEmail}</button>}
        </AuthField>
        <div className="flex items-center gap-2 rounded-xl bg-sky-50 p-3 text-sm text-sky-900"><MapPin className="h-4 w-4 shrink-0" />{location ? `${c.location}: ${location.district_name || location.district || ''}, ${location.state_name || location.state || ''}` : c.locationLater}</div>
        {confirmation && <AuthField label={c.code} active={step === 'code'}><input ref={codeInput} className={inputClass} type="text" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="000000" required /></AuthField>}
        <div id="phone-recaptcha" />
        <button type="submit" disabled={busy || (!confirmation && (!nameFinished || !phoneIsValid(phone)))} className="flex w-full items-center justify-center gap-2 rounded-xl bg-violet-900 px-4 py-3.5 font-bold text-white shadow-lg shadow-violet-200 transition hover:bg-violet-800 disabled:cursor-not-allowed disabled:opacity-50">{busy ? <Loader2 className="h-5 w-5 animate-spin" /> : confirmation ? <Phone className="h-5 w-5" /> : <ArrowRight className="h-5 w-5" />}{confirmation ? c.verify : c.send}</button>
        {confirmation && <button type="button" disabled={busy} onClick={() => { setConfirmation(null); setCode(''); verifier.current?.clear(); verifier.current = null; }} className="w-full text-sm font-semibold text-violet-700 underline">{c.resend}</button>}
      </form>
      <div className="my-6 flex items-center gap-3 text-xs font-bold uppercase tracking-widest text-slate-400"><span className="h-px flex-1 bg-slate-200" />{c.or}<span className="h-px flex-1 bg-slate-200" /></div>
      <div className="grid gap-3 sm:grid-cols-2">
        <button disabled={busy} onClick={() => enterWith(loginWithGoogle)} className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-3 text-sm font-semibold hover:bg-slate-50"><Chrome className="h-4 w-4" />{c.google}</button>
        <button disabled={busy} onClick={() => enterWith(loginAsDemo)} className="flex items-center justify-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm font-semibold text-amber-900 hover:bg-amber-100"><Zap className="h-4 w-4" />{c.evaluator}</button>
      </div>
      <p className="mt-6 text-center text-sm text-slate-600">{c.haveAccount} <Link to="/login" className="font-bold text-violet-800 underline">{c.signIn}</Link></p>
    </>}
  </AuthLayout>;
}

export default RegisterPage;
