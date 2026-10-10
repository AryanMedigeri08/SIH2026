import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { onboardingCopy, onboardingText } from '../src/i18n/onboardingCopy.js';

test('location confirmation and progress never fall back to another language', () => {
  const scripts = {
    hi: /[\u0900-\u097f]/,
    mr: /[\u0900-\u097f]/,
    te: /[\u0c00-\u0c7f]/,
    ta: /[\u0b80-\u0bff]/,
    kn: /[\u0c80-\u0cff]/,
  };
  const keys = [
    'confirmLocation', 'changeLocation', 'selectLocation', 'submitLocation',
    'guide', 'journey', 'businessIdeaStep', 'speaking', 'thinking',
  ];
  for (const language of Object.keys(onboardingCopy)) {
    for (const key of keys) {
      assert.ok(onboardingCopy[language][key], `${language}:${key} missing`);
      const text = onboardingText(language, key);
      if (scripts[language]) assert.match(text, scripts[language], `${language}:${key} in wrong language`);
    }
  }
  assert.notEqual(onboardingText('kn', 'confirmLocation'), onboardingText('hi', 'confirmLocation'));
});

test('every directly referenced onboarding label exists in all six languages', () => {
  const source = readFileSync(new URL('../src/pages/OnboardingPage.jsx', import.meta.url), 'utf8');
  const keys = [...source.matchAll(/onboardingText\(selectedLang,\s*"([A-Za-z]+)"\)/g)].map(match => match[1]);
  assert.ok(keys.length > 50);
  for (const [language, dictionary] of Object.entries(onboardingCopy)) {
    for (const key of keys) assert.ok(dictionary[key], `${language}:${key} missing`);
    assert.deepEqual(Object.keys(dictionary).sort(), Object.keys(onboardingCopy.en).sort(), `${language} catalog is incomplete`);
  }
});
