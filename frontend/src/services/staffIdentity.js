// Staff can sign in with the memorable ID issued by administration while
// Firebase receives a syntactically valid email identity internally.
export function firebaseStaffEmail(signInId) {
  const normalized = signInId.trim().toLowerCase();
  return normalized.endsWith('@udyam')
    ? `${normalized.slice(0, -6)}@udyam.example.com`
    : normalized;
}
