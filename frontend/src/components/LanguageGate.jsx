import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { LANGUAGES, useLanguage } from '../context/LanguageContext';

export const LANGUAGE_CHOSEN = 'udyam_mira_language_selected';
export function LanguageGate({ children }) {
  const { setLanguage } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [chosen, setChosen] = useState(() => LANGUAGES.some(item => item.code === sessionStorage.getItem(LANGUAGE_CHOSEN)));
  if (chosen) return children;
  return <main className="min-h-screen bg-gradient-to-br from-rose-50 via-white to-sky-50 flex items-center p-5">
    <section className="w-full max-w-2xl mx-auto text-center space-y-6" aria-label="Choose your language">
      <img src="/mira-avatar.png" alt="Mira" className="w-24 h-24 rounded-full object-cover mx-auto shadow-lg" />
      <h1 className="text-3xl font-bold text-slate-900">Choose your language</h1>
      <p className="text-slate-600">अपनी भाषा चुनें · तुमची भाषा निवडा · మీ భాషను ఎంచుకోండి · உங்கள் மொழியைத் தேர்ந்தெடுக்கவும் · ನಿಮ್ಮ ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">{LANGUAGES.map(item => <button key={item.code}
        className="rounded-2xl border border-violet-200 bg-white px-4 py-5 shadow-sm hover:bg-violet-50 focus:ring-4 focus:ring-violet-200"
        onClick={() => { sessionStorage.setItem(LANGUAGE_CHOSEN, item.code); setLanguage(item.code, {transition:false}); if (['/','/landing'].includes(location.pathname)) navigate('/register', {replace:true}); setChosen(true); }}>
        <strong className="text-xl block">{item.native}</strong><span className="text-sm text-slate-500">{item.label}</span>
      </button>)}</div>
    </section>
  </main>;
}
