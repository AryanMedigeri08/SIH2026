/**
 * firebaseClient.js — Client-side Firebase Authentication SDK Initializer.
 */

import { initializeApp, getApps, getApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  getIdToken,
  updateProfile as updateFirebaseProfile,
} from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDemoDummyKeyForBuildAndDevMode123",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "sihhhhhh.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "sihhhhhh",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "sihhhhhh.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "114385947287",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:114385947287:web:sihhhhhh1234567890",
};

// Initialize Firebase App Singleton
const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);

// Initialize Firebase Auth Singleton
export const auth = getAuth(app);

// Initialize Google OAuth Provider
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: "select_account" });

export {
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  getIdToken,
  updateFirebaseProfile,
};
