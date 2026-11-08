export function normalizeIndicDigits(value) {
  const bases = [0x0966, 0x0be6, 0x0c66, 0x0ce6];
  return [...value].map(char => {
    for (const base of bases) { const index = char.codePointAt(0) - base; if (index >= 0 && index < 10) return String(index); }
    return char;
  }).join('');
}

export function indianPhone(value) {
  const digits = normalizeIndicDigits(value).replace(/\D/g, '');
  const national = digits.length === 12 && digits.startsWith('91') ? digits.slice(2) : digits;
  if (!/^[6-9]\d{9}$/.test(national)) throw new Error('Enter a valid 10-digit Indian mobile number.');
  return `+91${national}`;
}

export function phoneError(error) {
  return ({
    'auth/invalid-verification-code': 'The verification code is incorrect. Please check the SMS and try again.',
    'auth/code-expired': 'This code has expired. Request a new code.',
    'auth/too-many-requests': 'Too many attempts. Please wait before trying again.',
    'auth/quota-exceeded': 'SMS verification is temporarily unavailable. Please try again later.',
    'auth/operation-not-allowed': 'Phone sign-in needs to be enabled by the app administrator.',
    'auth/unauthorized-domain': 'Phone sign-in is not configured for this website. Please contact the app administrator.',
    'auth/invalid-app-credential': 'Phone verification could not start. Please reload and try again.',
  })[error?.code] || error?.message || 'Verification could not complete. Please try again.';
}
