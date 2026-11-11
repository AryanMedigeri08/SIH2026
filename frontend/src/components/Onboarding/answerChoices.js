import { normalizeIndicDigits } from '../../services/registrationValidation.js';

const normalize = value => normalizeIndicDigits(String(value ?? '')).toLocaleLowerCase()
  .replace(/[.,!?।:;،؟]/gu, ' ').replace(/\s+/gu, ' ').trim();

export function resolveSpokenChoice(transcript, options, labels = []) {
  const text = normalize(transcript);
  if (!text) return undefined;
  if (/^\d+$/.test(text)) return options[Number(text) - 1]?.value;
  const yes = ['yes','हाँ','हां','होय','ஆம்','అవును','ಹೌದು'];
  const no = ['no','नहीं','नाही','இல்லை','కాదు','ಇಲ್ಲ'];
  const matches = options.filter((option, i) => {
    if (option.value === true && yes.includes(text)) return true;
    if (option.value === false && no.includes(text)) return true;
    return [option.value, option.label, labels[i]].some(value => {
      const candidate = normalize(value);
      return candidate === text || (text.length >= 2 && candidate.startsWith(`${text} `));
    });
  });
  return matches.length === 1 ? matches[0].value : undefined;
}
