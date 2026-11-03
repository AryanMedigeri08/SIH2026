import React, { useState } from 'react';
import { Mic, Volume2, Square } from 'lucide-react';
import { useMiraSpeech } from '../hooks/useMiraSpeech';
import { useLanguage } from '../context/LanguageContext';
import { useAutoTranslate } from '../hooks/useAutoTranslate';

// Guides the existing Firebase form. Credentials are typed directly into that form.
export function MiraRegistrationGuide({ name, gender, category, onName, onGender, onCategory, signIn = false }) {
  const { language } = useLanguage();
  const [transcript, setTranscript] = useState('');
  const [guideError, setGuideError] = useState('');
  const [confirmedGender, setConfirmedGender] = useState(Boolean(gender && gender !== 'Unspecified'));
  const field = !name ? 'name' : !gender || (gender === 'Unspecified' && !confirmedGender) ? 'gender' : !category ? 'category' : 'credentials';
  const guidance = signIn ? 'Welcome back. Use your existing email and password or Google sign-in below. I will help you continue your saved business plan after sign-in.' : {
    name: 'Hello, I’m Mira. Let’s create your account together. What is your full name?',
    gender: 'How would you describe your gender? You can choose not to say.',
    category: 'Which caste or category should I use? This is collected only to check relevant scheme eligibility and contribution rules. You can correct it later.',
    credentials: 'Thank you. Enter your email and create a password in the secure form below. You can add a phone number if you wish. Then choose Create Account to continue with me.',
  }[field];
  const { translated } = useAutoTranslate(guidance);
  const speech = useMiraSpeech({ language, onTranscript: setTranscript });
  const apply = () => {
    const clean = transcript.trim();
    if (!clean) return;
    if (field === 'name') onName(clean.replace(/^my name is\s+/i, ''));
    if (field === 'gender') {
      const choice = { male: 'Male', female: 'Female', other: 'Other', unspecified: 'Unspecified', 'prefer not to say': 'Unspecified' }[clean.toLowerCase()];
      if (!choice) { setGuideError('I couldn’t match that answer. Choose a gender below or correct the transcript.'); return; }
      onGender(choice); setConfirmedGender(true);
    }
    if (field === 'category') {
      const choice = clean.toLowerCase().replace(/[.\s]/g, '');
      if (!['general', 'sc', 'st', 'obc', 'minority', 'ph', 'artisan', 'women', 'women_shg'].includes(choice)) { setGuideError('I couldn’t match that category. Select it in the form below or correct the transcript.'); return; }
      onCategory(choice);
    }
    setTranscript('');
    setGuideError('');
  };
  return <aside className="rounded-2xl bg-sovereign-50 border border-sovereign-200 p-4 mb-5 space-y-3" aria-label="Mira registration guide">
    <p className="text-sm font-semibold text-sovereign-900" aria-live="polite">{translated || guidance}</p>
    <div className="flex flex-wrap gap-2">
      <button type="button" className="mira-secondary" onClick={() => speech.speaking ? speech.stopSpeaking() : speech.speak(translated || guidance)}><Volume2 size={16} />{speech.speaking ? 'Stop' : 'Listen to Mira'}</button>
      {!signIn && field !== 'credentials' && <button type="button" className="mira-primary" disabled={speech.transcribing} onClick={() => speech.isRecording ? speech.stopRecording() : speech.startRecording()}>
        {speech.isRecording ? <Square size={16} /> : <Mic size={16} />}{speech.isRecording ? 'Finish' : 'Speak your answer'}
      </button>}
      {!signIn && field === 'gender' && ['Male', 'Female', 'Other', 'Unspecified'].map(choice => <button key={choice} type="button" className="mira-secondary" onClick={() => { onGender(choice); setConfirmedGender(true); }}>{choice === 'Unspecified' ? 'Prefer not to say' : choice}</button>)}
    </div>
    {transcript && <div className="space-y-2"><label className="text-sm">Check what Mira heard<input className="mira-input mt-1" value={transcript} onChange={e => setTranscript(e.target.value)} /></label>
      <button type="button" className="mira-primary" onClick={apply}>Use this answer</button><p className="text-xs">You can also correct any profile field in the form below.</p></div>}
    {(guideError || speech.speechError || speech.transcribing) && <p role="status" className="text-sm">{guideError || speech.speechError || 'Listening to your recording…'}</p>}
  </aside>;
}
