import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { auth, googleProvider, signInWithPopup, signInWithRedirect, getRedirectResult,
  signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut as firebaseSignOut,
  onAuthStateChanged, getIdToken, updateFirebaseProfile, signInWithPhoneNumber, signInWithCustomToken } from '../services/firebaseClient';
import { authApi } from '../services/api';
import { authenticateWithPasskey, enrollPasskey } from '../services/passkeys';
import { authenticatedSession } from '../services/authenticatedSession';

const AuthContext = createContext(null);
const EVALUATOR_KEY = 'udyam_evaluator_session_v1';
const evaluatorUser = token => ({ uid: null, isEvaluator: true, isAnonymous: true, getIdToken: async () => token });

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);
  const epoch = useRef(0);
  const explicit = useRef(false);
  const refreshing = useRef(false);
  const current = useRef(null);
  const publish = value => { current.current = value; setSession(value); };
  const clear = () => { sessionStorage.removeItem(EVALUATOR_KEY); publish(null); };
  const confirmedSession = useCallback(async (user, profileData = null) => {
    return authenticatedSession(user, value => getIdToken(value, false), token => profileData ? authApi.registerProfile(token, profileData) : authApi.syncSession(token));
  }, []);

  useEffect(() => {
    // Old unsigned fallback identities are not production authentication.
    localStorage.removeItem('udyam_saathi_auth_session');
    const unsubscribe = onAuthStateChanged(auth, async user => {
      if (explicit.current) return;
      const generation = ++epoch.current;
      setLoading(true);
      try {
        const saved = sessionStorage.getItem(EVALUATOR_KEY);
        let accepted = null;
        if (saved) {
          const profile = await authApi.syncSession(saved);
          const localUser = evaluatorUser(saved); localUser.uid = profile.firebase_uid;
          accepted = { user: localUser, profile, token: saved, isDemoMode: true };
        } else if (user) accepted = await confirmedSession(user);
        if (generation === epoch.current) publish(accepted);
      } catch (_) {
        if (generation === epoch.current) { clear(); setAuthError('Your session could not be verified. Please sign in again.'); }
      } finally { if (generation === epoch.current) setLoading(false); }
    });
    // Complete redirects explicitly; the same Firebase observer verifies the
    // backend session before protected routes become available.
    getRedirectResult(auth).catch(error => setAuthError(error.code || 'Google sign-in could not finish.'));
    return () => { epoch.current += 1; unsubscribe(); };
  }, [confirmedSession]);

  const authenticate = async (operation, profileData = null) => {
    const generation = ++epoch.current;
    explicit.current = true; setLoading(true); setAuthError(null);
    try {
      const credential = await operation();
      if (profileData?.name) await updateFirebaseProfile(credential.user, { displayName: profileData.name });
      const accepted = await confirmedSession(credential.user, profileData);
      if (generation !== epoch.current) throw new Error('Sign-in was interrupted. Please try again.');
      sessionStorage.removeItem(EVALUATOR_KEY); publish(accepted);
      return accepted; // Every provider returns the verified token to navigation.
    } catch (error) {
      if (generation === epoch.current) {
        clear(); setAuthError(error.code || 'The server could not establish your session.');
        try { await firebaseSignOut(auth); } catch (_) {}
      }
      throw error;
    } finally { explicit.current = false; if (generation === epoch.current) setLoading(false); }
  };
  const loginWithGoogle = () => authenticate(async () => {
    try { return await signInWithPopup(auth, googleProvider); }
    catch (error) {
      if (error.code === 'auth/popup-blocked') { sessionStorage.removeItem(EVALUATOR_KEY); await signInWithRedirect(auth, googleProvider); }
      throw error;
    }
  });
  const loginWithEmail = (email, password) => authenticate(() => signInWithEmailAndPassword(auth, email, password));
  const registerWithEmail = (email, password, data = {}) => authenticate(() => createUserWithEmailAndPassword(auth, email, password), data);
  const sendPhoneCode = (phone, verifier) => {
    auth.languageCode = document.documentElement.lang || 'en';
    return signInWithPhoneNumber(auth, phone, verifier);
  };
  const completePhoneSignIn = (confirmation, code, data = null) => authenticate(() => confirmation.confirm(code), data);
  const loginWithPasskey = () => authenticate(async () => {
    const { custom_token } = await authenticateWithPasskey();
    return signInWithCustomToken(auth, custom_token);
  });
  const addPasskey = async () => {
    if (!current.current || current.current.isDemoMode) throw new Error('Use your verified account to add a passkey.');
    return enrollPasskey(await current.current.user.getIdToken());
  };
  const loginAsDemo = async () => {
    const generation = ++epoch.current;
    explicit.current = true; setLoading(true); setAuthError(null);
    try {
      await firebaseSignOut(auth);
      const issued = await authApi.createEvaluator();
      const profile = await authApi.syncSession(issued.token);
      if (generation !== epoch.current) throw new Error('Sign-in was interrupted.');
      const user = evaluatorUser(issued.token); user.uid = profile.firebase_uid;
      const accepted = { user, profile, token: issued.token, isDemoMode: true };
      sessionStorage.setItem(EVALUATOR_KEY, issued.token); publish(accepted);
      return accepted;
    } catch (error) { if (generation === epoch.current) { clear(); setAuthError('Evaluator access is unavailable. Please retry.'); } throw error; }
    finally { explicit.current = false; if (generation === epoch.current) setLoading(false); }
  };
  const logout = async () => {
    const old = current.current;
    epoch.current += 1; explicit.current = true; clear(); setLoading(false);
    try {
      if (old) await authApi.logout(old.token).catch(() => {});
      await firebaseSignOut(auth).catch(() => {});
    } finally { explicit.current = false; }
  };
  const updateProfile = async data => {
    if (!current.current) throw new Error('Please sign in.');
    const before = current.current;
    const profile = await authApi.updateMyProfile(before.token, data);
    if (current.current?.token === before.token) publish({ ...before, profile });
    return profile;
  };
  const refreshProfile = async () => {
    if (!current.current) return null;
    const before = current.current;
    const profile = await authApi.getMyProfile(before.token);
    if (current.current?.token === before.token) publish({ ...before, profile });
    return profile;
  };
  useEffect(() => {
    const revoked = async () => {
      if (refreshing.current || !current.current) return;
      refreshing.current = true;
      const before = current.current;
      try {
        if (before.isDemoMode) throw new Error('Evaluator session expired.');
        const token = await before.user.getIdToken(true);
        const profile = await authApi.syncSession(token);
        if (current.current === before) publish({ ...before, token, profile });
      } catch (_) { if (current.current === before) clear(); }
      finally { refreshing.current = false; }
    };
    window.addEventListener('udyam:auth-revoked', revoked);
    return () => window.removeEventListener('udyam:auth-revoked', revoked);
  }, []);
  return <AuthContext.Provider value={{ firebaseUser: session?.user || null, userProfile: session?.profile || null,
    token: session?.token || null, loading, authError, isAuthenticated: !!session, isDemoMode: !!session?.isDemoMode,
    loginWithGoogle, loginWithEmail, registerWithEmail, sendPhoneCode, completePhoneSignIn, loginWithPasskey, addPasskey,
    loginAsDemo, logout, updateProfile, refreshProfile, getToken: async force => current.current ? current.current.user.getIdToken(force) : null }}>{children}</AuthContext.Provider>;
}
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
