/**
 * AuthContext.jsx — Unified Authentication & User Profile Context.
 * Bridges Firebase Client Auth SDK with Udyam Saathi REST API Backend.
 * Features automatic Sovereign Token fallback if Firebase Web API Key is unconfigured.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
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
} from "../services/firebaseClient";
import { authApi } from "../services/api";

const AuthContext = createContext(null);
const LOCAL_SESSION_KEY = "udyam_saathi_auth_session";

export const AuthProvider = ({ children }) => {
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);
  const [isDemoMode, setIsDemoMode] = useState(false);

  // Helper to create sovereign mock user
  const createSovereignUser = (uid, email, name, sessionToken = null) => ({
    uid,
    email,
    displayName: name || email?.split("@")[0] || "Entrepreneur",
    getIdToken: async () => sessionToken || `test-token-${uid}:${email}`,
  });

  // Sync session with backend
  const handleAuthChange = useCallback(async (user) => {
    if (user) {
      try {
        const idToken = await getIdToken(user, false);
        setFirebaseUser(user);
        setToken(idToken);
        setIsDemoMode(false);

        try {
          const profile = await authApi.syncSession(idToken);
          setUserProfile(profile);
        } catch (backendErr) {
          console.warn("Backend session sync fallback:", backendErr);
          setUserProfile({
            firebase_uid: user.uid,
            name: user.displayName || user.email?.split("@")[0] || "Entrepreneur",
            email: user.email,
            gender: "Unspecified",
            auth_provider: user.providerData?.[0]?.providerId || "email",
            projects_count: 0,
          });
        }
      } catch (err) {
        console.error("Auth state synchronization error:", err);
        setAuthError(err.message);
      } finally {
        setLoading(false);
      }
    } else {
      // Check local storage for persistent sovereign session
      const saved = localStorage.getItem(LOCAL_SESSION_KEY);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          const devUser = createSovereignUser(parsed.uid, parsed.email, parsed.name, parsed.token);
          setFirebaseUser(devUser);
          setToken(parsed.token);
          setIsDemoMode(Boolean(parsed.isDemoMode));
          try {
            const profile = await authApi.syncSession(parsed.token);
            setUserProfile(profile);
          } catch (e) {
            setUserProfile({
              firebase_uid: parsed.uid,
              name: parsed.name,
              email: parsed.email,
              gender: "Unspecified",
              auth_provider: parsed.isDemoMode ? "demo" : "sovereign",
              projects_count: 0,
            });
          }
        } catch (e) {
          localStorage.removeItem(LOCAL_SESSION_KEY);
        }
      } else {
        setFirebaseUser(null);
        setUserProfile(null);
        setToken(null);
        setIsDemoMode(false);
      }
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, handleAuthChange);
    return () => unsubscribe();
  }, [handleAuthChange]);

  // Sovereign Fallback Login Helper
  const sovereignFallbackLogin = async (email, name = null, profileData = {}, isDemo = false) => {
    const cleanEmail = email.trim().toLowerCase();
    // Deterministic slug UID from email
    const safeSlug = cleanEmail.replace(/[^a-z0-9]/g, "_").slice(0, 24);
    const uid = `usr_${safeSlug}`;
    // A fresh opaque suffix makes a new local sign-in distinguishable from a
    // previously logged-out session. It is authentication state, not business
    // data, and is revoked by the backend on logout.
    const devToken = `test-token-${uid}:${cleanEmail}:${crypto.randomUUID()}`;
    const displayName = name || profileData.name || cleanEmail.split("@")[0] || "Entrepreneur";

    const devUser = createSovereignUser(uid, cleanEmail, displayName, devToken);
    setFirebaseUser(devUser);
    setToken(devToken);
    setIsDemoMode(isDemo);

    localStorage.setItem(
      LOCAL_SESSION_KEY,
      JSON.stringify({
        uid,
        email: cleanEmail,
        name: displayName,
        token: devToken,
        isDemoMode: isDemo,
      })
    );

    // Sync or Register profile with backend
    try {
      const profile = await authApi.registerProfile(devToken, {
        name: displayName,
        gender: profileData.gender || "Unspecified",
        phone: profileData.phone || null,
        additional_business_details: profileData.additional_business_details || null,
      });
      setUserProfile(profile);
      return { user: devUser, profile, token: devToken };
    } catch (e) {
      // If already registered, call syncSession
      const profile = await authApi.syncSession(devToken);
      setUserProfile(profile);
      return { user: devUser, profile, token: devToken };
    }
  };

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
      // If API key is not valid or network/quota error, automatically use sovereign token auth
      const isApiKeyError =
        err.code === "auth/api-key-not-valid" ||
        err.code === "auth/invalid-api-key" ||
        err.message?.includes("api-key-not-valid") ||
        err.message?.includes("invalid-api-key");

      if (isApiKeyError) {
        console.warn("Firebase Web API key not configured or invalid. Operating in Sovereign Token Auth mode.");
        return await sovereignFallbackLogin(email, profileData.name, profileData, false);
      }

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
      const isApiKeyError =
        err.code === "auth/api-key-not-valid" ||
        err.code === "auth/invalid-api-key" ||
        err.message?.includes("api-key-not-valid") ||
        err.message?.includes("invalid-api-key");

      if (isApiKeyError) {
        console.warn("Firebase Web API key not configured or invalid. Operating in Sovereign Token Auth mode.");
        return await sovereignFallbackLogin(email, null, {}, false);
      }

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
      return { user: cred.user, profile };
    } catch (err) {
      const isApiKeyError =
        err.code === "auth/api-key-not-valid" ||
        err.code === "auth/invalid-api-key" ||
        err.message?.includes("api-key-not-valid") ||
        err.message?.includes("invalid-api-key");

      if (isApiKeyError) {
        console.warn("Firebase Web API key unconfigured for Google Popup. Operating in Sovereign Google Mode.");
        return await sovereignFallbackLogin("google.entrepreneur@udyam.gov.in", "Google Enterprise User", {}, false);
      }

      setAuthError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Dedicated Demo One-Click Quick Login
  const loginAsDemo = async (email = "guest@udyam.gov.in", name = "Guest Entrepreneur") => {
    setLoading(true);
    setAuthError(null);
    try {
      return await sovereignFallbackLogin(email, name, {}, true);
    } finally {
      setLoading(false);
    }
  };

  // Sign Out Flow
  const logout = async () => {
    const sessionToken = token;
    // Clear client authentication first.  The server call below is important
    // for token revocation, but a slow or unavailable network must never keep
    // protected enterprise state on screen.
    localStorage.removeItem(LOCAL_SESSION_KEY);
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
    isAuthenticated: !!firebaseUser,
    registerWithEmail,
    loginWithEmail,
    loginWithGoogle,
    loginAsDemo,
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
