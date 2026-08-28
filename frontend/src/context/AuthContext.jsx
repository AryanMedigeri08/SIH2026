/**
 * AuthContext.jsx — Unified Authentication & User Profile Context.
 * Bridges Firebase Client Auth SDK with Udyam Saathi REST API Backend.
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

export const AuthProvider = ({ children }) => {
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Sync session with backend when Firebase Auth state changes
  const handleAuthChange = useCallback(async (user) => {
    setLoading(true);
    setAuthError(null);

    if (!user) {
      setFirebaseUser(null);
      setUserProfile(null);
      setToken(null);
      setLoading(false);
      return;
    }

    try {
      const idToken = await getIdToken(user, /* forceRefresh */ false);
      setFirebaseUser(user);
      setToken(idToken);

      // Sync session with Postgres database
      try {
        const profile = await authApi.syncSession(idToken);
        setUserProfile(profile);
      } catch (backendErr) {
        console.warn("Backend session sync fallback:", backendErr);
        // Fallback minimal profile if backend is starting up or in test mode
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
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, handleAuthChange);
    return () => unsubscribe();
  }, [handleAuthChange]);

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

      // Persist full profile into Neon Postgres
      const profile = await authApi.registerProfile(idToken, {
        name: profileData.name || cred.user.email?.split("@")[0] || "Entrepreneur",
        gender: profileData.gender || "Unspecified",
        phone: profileData.phone || null,
        additional_business_details: profileData.additional_business_details || null,
      });
      setUserProfile(profile);
      return { user: cred.user, profile };
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

      const profile = await authApi.syncSession(idToken);
      setUserProfile(profile);
      return { user: cred.user, profile };
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

      const profile = await authApi.syncSession(idToken);
      setUserProfile(profile);
      return { user: cred.user, profile };
    } catch (err) {
      setAuthError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Sign Out Flow
  const logout = async () => {
    setLoading(true);
    try {
      await firebaseSignOut(auth);
      setFirebaseUser(null);
      setUserProfile(null);
      setToken(null);
    } catch (err) {
      console.error("Sign out error:", err);
    } finally {
      setLoading(false);
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
    isAuthenticated: !!firebaseUser,
    registerWithEmail,
    loginWithEmail,
    loginWithGoogle,
    logout,
    refreshProfile,
    updateProfile,
    getToken: async (forceRefresh = false) => {
      if (!firebaseUser) return null;
      return await getIdToken(firebaseUser, forceRefresh);
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
