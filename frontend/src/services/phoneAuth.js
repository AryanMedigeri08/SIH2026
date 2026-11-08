import { RecaptchaVerifier, signInWithPhoneNumber } from 'firebase/auth';
import { auth } from './firebaseClient';
import { indianPhone } from './registrationValidation';
export { indianPhone } from './registrationValidation';

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
