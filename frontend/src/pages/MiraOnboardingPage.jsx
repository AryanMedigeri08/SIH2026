import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useBusiness } from '../context/BusinessContext';
import { useLanguage } from '../context/LanguageContext';
import { onboardingApi } from '../services/api';
import { LanguageSelector } from '../components/LanguageSelector';
import { TranslatedText as T } from '../components/TranslatedText';
import { MiraJourneyChoice } from '../components/Onboarding/MiraJourneyChoice';
import { MiraLocation } from '../components/Onboarding/MiraLocation';
import { MiraConversation } from '../components/Onboarding/MiraConversation';
import { copy } from '../components/Onboarding/copy';

export function MiraOnboardingPage() {
  const { token, logout } = useAuth();
  const { adoptEvaluatedBusiness } = useBusiness();
  const { language } = useLanguage();
  const navigate = useNavigate();
  const [draft, setDraft] = useState(null);
  const [phase, setPhase] = useState('loading');
  const [detecting, setDetecting] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const saved = await onboardingApi.session(token);
        if (!active) return;
        setDraft(saved);
        setPhase(saved.journey && !saved.completed ? saved.location?.confirmed ? 'conversation' : 'location' : 'choice');
        if (!saved.location && navigator.geolocation) {
          setDetecting(true);
          navigator.geolocation.getCurrentPosition(async position => {
            if (!active) return;
            try {
              const detected = await onboardingApi.detect(token, { latitude: position.coords.latitude, longitude: position.coords.longitude });
              if (active) setDraft(previous => ({ ...previous, location: detected }));
            } catch { /* Manual selection remains available, with no guessed address. */ }
            finally { if (active) setDetecting(false); }
          }, () => { if (active) setDetecting(false); }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 });
        }
      } catch (err) { if (active) setError(err.message); }
    };
    load();
    return () => { active = false; };
  }, [token, retry]);
  const choose = async journey => {
    setPending(true); setError('');
    try {
      const next = { ...draft, journey, language, answers: {}, completed: false, preview_id: null, project_id: null,
        location: draft.location ? { ...draft.location, confirmed: false } : null };
      await onboardingApi.save(token, next);
      setDraft(next); setPhase('location');
    } catch (err) { setError(err.message); }
    finally { setPending(false); }
  };
  const finish = async (project, completed) => {
    await onboardingApi.save(token, { ...completed, language, completed: true });
    adoptEvaluatedBusiness(project);
    navigate('/dashboard', { replace: true });
  };
  return <main className="mira-page"><div className="mira-shell">
    <header className="mb-5 flex flex-wrap items-center justify-between gap-4">
      <Link to="/" className="text-xl font-extrabold text-purple-950">Udyam Saathi</Link>
      <div className="flex items-center gap-4"><LanguageSelector /><button type="button" onClick={async () => { await logout(); navigate('/'); }} className="min-h-12 font-bold text-purple-900 underline"><T text="Sign out" /></button></div>
    </header>
    {error && <div role="alert" className="mira-error"><T text={error} /><button type="button" onClick={() => { setError(''); setRetry(n => n + 1); }} className="ml-3 underline"><T text="Retry" /></button></div>}
    {phase === 'loading' && <p role="status">{copy('waiting', language)}</p>}
    {phase === 'choice' && <MiraJourneyChoice onChoose={choose} busy={pending} />}
    {phase === 'location' && <MiraLocation key={`${detecting}:${JSON.stringify(draft.location)}`} location={draft.location} detecting={detecting} onConfirm={async location => {
      const { is_rural, classification_source, hierarchy_source, ...canonical } = location;
      const next = { ...draft, language, location: canonical, answers: {} };
      await onboardingApi.save(token, next);
      setDraft(next); setPhase('conversation');
    }} />}
    {phase === 'conversation' && <MiraConversation initialDraft={draft} onProgress={setDraft} onFinish={finish} onChangeJourney={() => setPhase('choice')} />}
  </div></main>;
}
