import React, { useRef, useState } from 'react';
import { CaseStudiesBar } from '../components/CaseStudiesBar';
import { Dashboard } from '../components/Dashboard/Dashboard';
import { useAuth } from '../context/AuthContext';
import { useAuthCopy } from '../components/AuthExperience';
import { auth, RecaptchaVerifier } from '../services/firebaseClient';

export function DashboardPage({
  reportData,
  activeCaseId,
  isLoading,
  onSelectCase,
  onOpenDpr,
  onOpenWizard,
}) {
  const { isDemoMode, firebaseUser, addPasskey, sendPhoneLinkCode, completePhoneLink } = useAuth();
  const c = useAuthCopy();
  const [passkeyMessage, setPasskeyMessage] = useState('');
  const [passkeyBusy, setPasskeyBusy] = useState(false);
  const [linkPhone, setLinkPhone] = useState('');
  const [linkCode, setLinkCode] = useState('');
  const [linkConfirmation, setLinkConfirmation] = useState(null);
  const [linkMessage, setLinkMessage] = useState('');
  const [linkBusy, setLinkBusy] = useState(false);
  const linkVerifier = useRef(null);
  const phoneLinked = Boolean(firebaseUser?.providerData?.some((provider) => provider.providerId === 'phone'));

  const setUpPasskey = async () => {
    setPasskeyBusy(true);
    setPasskeyMessage('');
    try {
      await addPasskey();
      setPasskeyMessage('Passkey saved. You can use your device to sign in next time.');
    } catch (error) {
      setPasskeyMessage(error.message || 'Could not save passkey.');
    } finally {
      setPasskeyBusy(false);
    }
  };

  const handlePhoneLink = async (event) => {
    event.preventDefault();
    setLinkBusy(true); setLinkMessage('');
    try {
      if (!linkConfirmation) {
        if (!/^[6-9]\d{9}$/.test(linkPhone)) throw new Error('Enter a valid 10-digit mobile number.');
        if (!linkVerifier.current) linkVerifier.current = new RecaptchaVerifier(auth, 'link-phone-recaptcha', { size: 'invisible' });
        setLinkConfirmation(await sendPhoneLinkCode(`+91${linkPhone}`, linkVerifier.current));
        setLinkMessage('Enter the verification code sent to your phone.');
      } else {
        if (!/^\d{6}$/.test(linkCode)) throw new Error('Enter the 6-digit SMS code.');
        await completePhoneLink(linkConfirmation, linkCode);
        setLinkMessage('Mobile number linked to this account. Your enterprises will remain here.');
        setLinkConfirmation(null);
      }
    } catch (error) {
      setLinkMessage(error.message || 'Could not verify phone.');
      if (!linkConfirmation) { linkVerifier.current?.clear(); linkVerifier.current = null; }
    } finally { setLinkBusy(false); }
  };

  return (
    <div className="space-y-4">
      {!isDemoMode && <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 rounded-2xl border border-violet-200 bg-violet-50 px-4 py-3 text-sm text-violet-900"><span>Use Face ID, fingerprint, or Windows Hello on your next visit.</span><button type="button" disabled={passkeyBusy} onClick={setUpPasskey} className="rounded-xl bg-violet-900 px-4 py-2 font-bold text-white disabled:opacity-50">{c.addPasskey}</button>{passkeyMessage && <span role="status" className="w-full">{passkeyMessage}</span>}</div>}
      {!isDemoMode && !phoneLinked && <form onSubmit={handlePhoneLink} className="mx-auto flex max-w-7xl flex-wrap items-center gap-2 rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900"><span className="w-full font-semibold">Existing account? Verify your phone here to use SMS sign-in without creating a separate account.</span><span className="rounded-lg bg-white px-2 py-2">+91</span><input aria-label="Mobile number" className="min-w-0 flex-1 rounded-lg border border-sky-200 px-3 py-2" type="tel" inputMode="numeric" maxLength={10} value={linkPhone} disabled={!!linkConfirmation} onChange={(e) => setLinkPhone(e.target.value.replace(/\D/g, '').slice(0, 10))} placeholder="10-digit mobile number" />{linkConfirmation && <input aria-label="SMS code" className="w-28 rounded-lg border border-sky-200 px-3 py-2" type="text" inputMode="numeric" maxLength={6} value={linkCode} onChange={(e) => setLinkCode(e.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="SMS code" />}<div id="link-phone-recaptcha" /><button type="submit" disabled={linkBusy} className="rounded-lg bg-sky-900 px-4 py-2 font-bold text-white disabled:opacity-50">{linkConfirmation ? 'Verify phone' : 'Send code'}</button>{linkMessage && <span role="status" className="w-full">{linkMessage}</span>}</form>}
      {/* 1-Click Preset Cases Bar — ONLY visible in Quick Login / Evaluator Demo Mode */}
      {isDemoMode && (
        <CaseStudiesBar
          activeCaseId={activeCaseId}
          onSelectCase={onSelectCase}
          isLoading={isLoading}
        />
      )}

      {/* Main Content Area */}
      {isLoading ? (
        <div className="max-w-7xl mx-auto py-24 px-4 text-center">
          <div className="inline-block p-5 rounded-2xl bg-white border border-slate-200 shadow-card mb-4">
            <div className="w-10 h-10 border-4 border-sovereign-800 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
          <h3 className="text-lg font-bold font-outfit text-slate-900">
            Executing 4-Tier Zero-Hallucination Pipeline...
          </h3>
          <p className="text-xs text-slate-600 mt-1 max-w-md mx-auto">
            Connecting Census 2011 demographics, 613 village amenities API, XGBoost viability model & Groq LLM credit synthesis.
          </p>
        </div>
      ) : (
        <Dashboard
          reportData={reportData}
          onOpenDpr={onOpenDpr}
          onOpenWizard={onOpenWizard}
        />
      )}
    </div>
  );
}
export default DashboardPage;
