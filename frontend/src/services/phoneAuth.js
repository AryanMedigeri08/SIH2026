import { RecaptchaVerifier, signInWithPhoneNumber } from 'firebase/auth';
import { auth } from './firebaseClient';

export function indianPhone(value) {
  const digits = value.replace(/\D/g, '');
  const national = digits.length === 12 && digits.startsWith('91') ? digits.slice(2) : digits;
  if (!/^[6-9]\d{9}$/.test(national)) throw new Error('Enter a valid 10-digit Indian mobile number.');
  return `+91${national}`;
}

// Kept outside React state: neither challenge nor OTP belongs in a saved draft.
export function phoneChallenge(element) {
  const verifier = new RecaptchaVerifier(auth, element, { size: 'normal' });
  let confirmation = null;
  return {
    async send(phone, language) {
      auth.languageCode = language;
      confirmation = await signInWithPhoneNumber(auth, indianPhone(phone), verifier);
    },
    async confirm(code) {
      if (!confirmation || !/^\d{6}$/.test(code)) throw new Error('Enter the six-digit SMS verification code.');
      return confirmation.confirm(code);
    },
    clear() { confirmation = null; verifier.clear(); },
  };
}
