export async function authenticatedSession(user, getToken, profileRequest) {
  const token = await getToken(user);
  if (typeof token !== 'string' || !token) throw new Error('Identity provider did not supply an ID token.');
  const profile = await profileRequest(token);
  if (!profile?.firebase_uid || profile.firebase_uid !== user.uid) throw new Error('Server session identity does not match the identity provider.');
  return {user,profile,token,isDemoMode:!!user.isAnonymous};
}
