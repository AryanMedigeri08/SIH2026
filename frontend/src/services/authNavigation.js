export async function destinationAfterSignIn(session, loadUserBusinesses, requestedPath = null) {
  if (!session?.token) throw new Error('Authenticated session did not provide an ID token.');
  const result = await loadUserBusinesses(session.token);
  if (result.error) throw result.error;
  if (requestedPath && !['/login', '/register'].includes(requestedPath)) return requestedPath;
  return result.hasBusinesses ? '/dashboard' : '/onboarding';
}
