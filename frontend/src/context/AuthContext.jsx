/**
 * AuthContext.jsx — Unified Authentication & User Profile Context.
 * Bridges Firebase Client Auth SDK with Udyam Saathi REST API Backend.
 * Firebase is the sole session issuer; business profiles persist in the backend.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import {
  auth,
  googleProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  getIdToken,
  updateFirebaseProfile,
  signInWithPhoneNumber,
  signInWithCustomToken,
  signInAnonymously,
  linkWithPhoneNumber,
} from "../services/firebaseClient";
import { authApi } from "../services/api";
import { authenticateWithPasskey, enrollPasskey } from "../services/passkeys";

const AuthContext = createContext(null);
const LEGACY_SESSION_KEY = 'udyam_saathi_auth_session';

export const AuthProvider = ({ children }) => {
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const sessionEpoch = useRef(0);

  // Sync session with backend
  const handleAuthChange = useCallback(async (user) => {
    const epoch = ++sessionEpoch.current;
    if (user) {
      try {
        const idToken = await getIdToken(user, false);
        if (epoch !== sessionEpoch.current) return;
        setFirebaseUser(user);
        setToken(idToken);
        setIsDemoMode(Boolean(user.isAnonymous));
        const profile = await authApi.syncSession(idToken);
        if (epoch !== sessionEpoch.current) return;
        setUserProfile(profile);
      } catch (err) {
        if (epoch !== sessionEpoch.current) return;
        console.error("Auth state synchronization error:", err);
        setAuthError(err.message);
        setFirebaseUser(null);
        setUserProfile(null);
        setToken(null);
      } finally {
        setLoading(false);
      }
    } else {
      setFirebaseUser(null);
      setUserProfile(null);
      setToken(null);
      setIsDemoMode(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Older builds persisted unsigned synthetic sessions; never restore them.
    localStorage.removeItem(LEGACY_SESSION_KEY);
    const unsubscribe = onAuthStateChanged(auth, handleAuthChange);
    return () => unsubscribe();
  }, [handleAuthChange]);

  // Handle global auth-revoked event triggered by 401 API responses
  useEffect(() => {
    const handleAuthRevoked = async () => {
      const epoch = sessionEpoch.current;
      console.warn("[AuthContext] 401 token revoked/expired event received. Attempting refresh...");
      if (firebaseUser?.getIdToken) {
        try {
          const fresh = await firebaseUser.getIdToken(true);
          if (fresh) {
            const profile = await authApi.syncSession(fresh);
            if (epoch !== sessionEpoch.current) return;
            setToken(fresh);
            setUserProfile(profile);
            console.info("[AuthContext] Token refreshed and session re-synchronized successfully.");
            return;
          }
        } catch (refreshErr) {
          console.warn("[AuthContext] Forced token refresh failed:", refreshErr);
        }
      }
      // If refresh fails or user has no refresh capability, clear local state cleanly
      if (epoch !== sessionEpoch.current) return;
      sessionEpoch.current += 1;
      setFirebaseUser(null);
      setUserProfile(null);
      setToken(null);
      setIsDemoMode(false);
    };

    window.addEventListener("udyam:auth-revoked", handleAuthRevoked);
    return () => window.removeEventListener("udyam:auth-revoked", handleAuthRevoked);
  }, [firebaseUser]);

  // Email & Password Registration Flow
  const registerWithEmail = async (email, password, profileData = {}) => {
    setLoading(true);
    setAuthError(null);
    try {
      const cred = await createUserWithEmailAndPassword(auth, email, password);
      if (profileData.name && cred.user) {
        await updateFirebaseProfile(cred.user, { displayName: profileData.name });
      }
      const idToken = await getIdToken(cred.user, true);
      setFirebaseUser(cred.user);
      setToken(idToken);
      setIsDemoMode(false);

      const profile = await authApi.registerProfile(idToken, {
        name: profileData.name || cred.user.email?.split("@")[0] || "Entrepreneur",
        gender: profileData.gender || "Unspecified",
        phone: profileData.phone || null,
        additional_business_details: profileData.additional_business_details || null,
      });
      setUserProfile(profile);
      return { user: cred.user, profile, token: idToken };
    } catch (err) {
      setAuthError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Email & Password Login Flow
  const loginWithEmail = async (email, password) => {
    setLoading(true);
    setAuthError(null);
    try {
      const cred = await signInWithEmailAndPassword(auth, email, password);
      const idToken = await getIdToken(cred.user, true);
      setFirebaseUser(cred.user);
      setToken(idToken);
      setIsDemoMode(false);

      const profile = await authApi.syncSession(idToken);
      setUserProfile(profile);
      return { user: cred.user, profile, token: idToken };
    } catch (err) {
      setAuthError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Google One-Click OAuth Flow
  const loginWithGoogle = async () => {
    setLoading(true);
    setAuthError(null);
    try {
      const cred = await signInWithPopup(auth, googleProvider);
      const idToken = await getIdToken(cred.user, true);
      setFirebaseUser(cred.user);
      setToken(idToken);
      setIsDemoMode(false);

      const profile = await authApi.syncSession(idToken);
      setUserProfile(profile);
      return { user: cred.user, profile, token: idToken };
    } catch (err) {
      setAuthError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const sendPhoneCode = async (phoneE164, verifier) => {
    setAuthError(null);
    auth.languageCode = document.documentElement.lang || 'en';
    return signInWithPhoneNumber(auth, phoneE164, verifier);
  };

  const completePhoneSignIn = async (confirmation, code, profileData = null) => {
    setLoading(true);
    setAuthError(null);
    try {
      const cred = await confirmation.confirm(code);
      if (profileData?.name) await updateFirebaseProfile(cred.user, { displayName: profileData.name });
      const idToken = await getIdToken(cred.user, true);
      const profile = profileData
        ? await authApi.registerProfile(idToken, { ...profileData, phone: cred.user.phoneNumber })
        : await authApi.syncSession(idToken);
      setFirebaseUser(cred.user);
      setToken(idToken);
      setUserProfile(profile);
      setIsDemoMode(false);
      return { user: cred.user, profile, token: idToken };
    } catch (err) {
      setAuthError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const sendPhoneLinkCode = async (phoneE164, verifier) => {
    if (!auth.currentUser || auth.currentUser.isAnonymous) throw new Error('Sign in to your existing account first.');
    auth.languageCode = document.documentElement.lang || 'en';
    return linkWithPhoneNumber(auth.currentUser, phoneE164, verifier);
  };

  const completePhoneLink = async (confirmation, code) => {
    const linked = await confirmation.confirm(code);
    const idToken = await getIdToken(linked.user, true);
    const profile = await authApi.syncSession(idToken);
    setFirebaseUser(linked.user);
    setToken(idToken);
    setUserProfile(profile);
    return { user: linked.user, profile, token: idToken };
  };

  const loginWithPasskey = async () => {
    setLoading(true);
    setAuthError(null);
    try {
      const { custom_token } = await authenticateWithPasskey();
      const cred = await signInWithCustomToken(auth, custom_token);
      const idToken = await getIdToken(cred.user, true);
      const profile = await authApi.syncSession(idToken);
      setFirebaseUser(cred.user);
      setToken(idToken);
      setUserProfile(profile);
      setIsDemoMode(false);
      return { user: cred.user, profile, token: idToken };
    } catch (err) {
      setAuthError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const addPasskey = async () => {
    if (!firebaseUser) throw new Error('Sign in before adding a passkey.');
    return enrollPasskey(await firebaseUser.getIdToken());
  };

  // Evaluators get isolated, Firebase-issued anonymous sessions.
  const loginAsDemo = async () => {
    setLoading(true);
    setAuthError(null);
    try {
      const cred = await signInAnonymously(auth);
      const idToken = await getIdToken(cred.user, true);
      const profile = await authApi.syncSession(idToken);
      setFirebaseUser(cred.user);
      setToken(idToken);
      setUserProfile(profile);
      setIsDemoMode(true);
      return { user: cred.user, profile, token: idToken };
    } catch (err) {
      setAuthError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Sign Out Flow
  const logout = async () => {
    sessionEpoch.current += 1;
    localStorage.removeItem(LEGACY_SESSION_KEY);
    const sessionToken = token;
    // Clear client authentication first.  The server call below is important
    // for token revocation, but a slow or unavailable network must never keep
    // protected enterprise state on screen.
    setFirebaseUser(null);
    setUserProfile(null);
    setToken(null);
    setIsDemoMode(false);
    setLoading(false);
    try {
      if (sessionToken) {
        try {
          await authApi.logout(sessionToken);
        } catch (_) {}
      }
      try {
        await firebaseSignOut(auth);
      } catch (_) {}
    } catch (err) {
      console.error("Sign out error:", err);
    }
  };

  // Refresh User Profile
  const refreshProfile = async () => {
    if (!token) return null;
    try {
      const profile = await authApi.getMyProfile(token);
      setUserProfile(profile);
      return profile;
    } catch (err) {
      console.error("Failed to refresh user profile:", err);
      return null;
    }
  };

  // Update Profile
  const updateProfile = async (updateData) => {
    if (!token) throw new Error("Unauthenticated");
    try {
      const updated = await authApi.updateMyProfile(token, updateData);
      setUserProfile(updated);
      return updated;
    } catch (err) {
      setAuthError(err.message);
      throw err;
    }
  };

  const value = {
    firebaseUser,
    userProfile,
    token,
    loading,
    authError,
    isDemoMode,
    isAuthenticated: !!firebaseUser && !!token && !!userProfile,
    registerWithEmail,
    loginWithEmail,
    loginWithGoogle,
    loginAsDemo,
    sendPhoneCode,
    completePhoneSignIn,
    sendPhoneLinkCode,
    completePhoneLink,
    loginWithPasskey,
    addPasskey,
    logout,
    refreshProfile,
    updateProfile,
    getToken: async (forceRefresh = false) => {
      if (!firebaseUser) return null;
      if (firebaseUser.getIdToken) {
        return await firebaseUser.getIdToken(forceRefresh);
      }
      return token;
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
