import React from 'react';
import { LANGUAGES, useLanguage } from '../../context/LanguageContext';
import { MiraAvatar } from './MiraGuide';
import { copy } from './copy';

export function MiraLanguageChoice({ onContinue }) {
  const { language, setLanguage } = useLanguage();
  return <main className="mira-page"><div className="mira-shell max-w-3xl space-y-6 py-8 text-center">
    <div className="flex justify-center"><MiraAvatar /></div>
    <h1 className="text-3xl font-extrabold">{copy('welcome', language)}</h1>
    <div className="grid gap-4 sm:grid-cols-2">
      {LANGUAGES.map(item => <button type="button" key={item.code} lang={item.code}
        onClick={() => { setLanguage(item.code); onContinue(item.code); }} className="mira-secondary py-6 text-2xl">
        {item.native}<span className="mt-1 block text-base">{item.label}</span>
      </button>)}
    </div>
  </div></main>;
}
