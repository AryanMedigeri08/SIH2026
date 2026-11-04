import React, { useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, Chrome, Fingerprint, Loader2, Phone, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useBusiness } from '../context/BusinessContext';
import { AuthField, AuthLayout, useAuthCopy } from '../components/AuthExperience';
import { auth, RecaptchaVerifier } from '../services/firebaseClient';
import { authErrorMessage } from '../services/authErrorMessage';
import { destinationAfterSignIn } from '../services/authNavigation';
import { useLanguage } from '../context/LanguageContext';

const inputClass = 'w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-base outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-100';

export function LoginPage() {
  const c = useAuthCopy();
  const { language } = useLanguage();
  const { loginWithPasskey, sendPhoneCode, completePhoneSignIn, loginWithGoogle, loginWithEmail, loginAsDemo } = useAuth();
  const { loadUserBusinesses } = useBusiness();
  const navigate = useNavigate();
  const location = useLocation();
  const verifier = useRef(null);
  const [phone, setPhone] = useState('');
  const [confirmation, setConfirmation] = useState(null);
  const [code, setCode] = useState('');
  const [legacy, setLegacy] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const enterWith = async (method) => {
    setBusy(true); setError('');
    try {
      const session = await method();
      const from = location.state?.from?.pathname;
      const destination = await destinationAfterSignIn(session, loadUserBusinesses, from);
      navigate(destination, { replace: true });
    } catch (err) { setError(authErrorMessage(err, c.errors.signIn, language)); }
    finally { setBusy(false); }
  };
  const sendCode = async (event) => {
    event.preventDefault();
    if (!/^[6-9]\d{9}$/.test(phone)) { setError(c.guidePhone); return; }
    setBusy(true); setError('');
    try {
      if (!verifier.current) verifier.current = new RecaptchaVerifier(auth, 'login-recaptcha', { size: 'invisible' });
      setConfirmation(await sendPhoneCode(`+91${phone}`, verifier.current));
    } catch (err) { setError(authErrorMessage(err, c.errors.send, language)); verifier.current?.clear(); verifier.current = null; }
    finally { setBusy(false); }
  };
  const verifyCode = (event) => { event.preventDefault(); enterWith(() => completePhoneSignIn(confirmation, code)); };
  const emailLogin = (event) => { event.preventDefault(); enterWith(() => loginWithEmail(email, password)); };

  return <AuthLayout mode="login" prompt={confirmation ? c.guideCode : c.guideLogin}>
    <div className="mb-6 text-xs font-bold uppercase tracking-widest text-violet-700">{c.signIn}</div>
    {error && <p role="alert" className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
    <button type="button" disabled={busy} onClick={() => enterWith(loginWithPasskey)} className="flex w-full items-center justify-center gap-3 rounded-2xl bg-violet-900 px-4 py-4 text-base font-bold text-white shadow-lg shadow-violet-200 hover:bg-violet-800 disabled:opacity-50"><Fingerprint className="h-6 w-6" />{c.passkey}</button>
    <p className="mt-2 text-center text-xs text-slate-500">Face ID · Fingerprint · Windows Hello · Device PIN</p>
    <div className="my-6 flex items-center gap-3 text-xs font-bold uppercase tracking-widest text-slate-400"><span className="h-px flex-1 bg-slate-200" />{c.orPhone}<span className="h-px flex-1 bg-slate-200" /></div>
    <form onSubmit={confirmation ? verifyCode : sendCode} className="space-y-4">
      <AuthField label={c.phone} active={!confirmation} done={!!confirmation}>
        <div className="flex gap-2"><span className="grid place-items-center rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-bold">+91</span><input className={inputClass} type="tel" inputMode="numeric" autoComplete="tel-national" maxLength={10} value={phone} disabled={!!confirmation} onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))} placeholder="98765 43210" required /></div>
      </AuthField>
      {confirmation && <AuthField label={c.code} active><input className={inputClass} type="text" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="000000" required /></AuthField>}
      <div id="login-recaptcha" />
      <button type="submit" disabled={busy || (confirmation ? code.length !== 6 : phone.length !== 10)} className="flex w-full items-center justify-center gap-2 rounded-xl border border-violet-200 bg-violet-50 px-4 py-3 font-bold text-violet-900 hover:bg-violet-100 disabled:opacity-50">{busy ? <Loader2 className="h-5 w-5 animate-spin" /> : <Phone className="h-5 w-5" />}{confirmation ? c.verify : c.send}</button>
      {confirmation && <button type="button" disabled={busy} onClick={() => { setConfirmation(null); setCode(''); verifier.current?.clear(); verifier.current = null; }} className="w-full text-sm font-semibold text-violet-700 underline">{c.resend}</button>}
    </form>
    <div className="mt-5 grid gap-3 sm:grid-cols-2">
      <button type="button" disabled={busy} onClick={() => enterWith(loginWithGoogle)} className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-3 text-sm font-semibold hover:bg-slate-50"><Chrome className="h-4 w-4" />{c.google}</button>
      <button type="button" disabled={busy} onClick={() => enterWith(loginAsDemo)} className="flex items-center justify-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm font-semibold text-amber-900 hover:bg-amber-100"><Zap className="h-4 w-4" />{c.evaluator}</button>
    </div>
    <button type="button" onClick={() => setLegacy((value) => !value)} className="mt-5 w-full text-center text-sm font-semibold text-slate-600 underline">{c.oldLogin}</button>
    <p className="mt-2 text-center text-xs leading-relaxed text-slate-500">{c.existingNote}</p>
    {legacy && <form onSubmit={emailLogin} className="mt-4 space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4"><input className={inputClass} type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={c.email} required /><input className={inputClass} type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder={c.password} required /><button type="submit" disabled={busy} className="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3 font-bold text-white"><ArrowRight className="h-4 w-4" />{c.signIn}</button></form>}
    <p className="mt-6 text-center text-sm text-slate-600">{c.newAccount} <Link to="/register" className="font-bold text-violet-800 underline">{c.create}</Link></p>
  </AuthLayout>;
}

export default LoginPage;
