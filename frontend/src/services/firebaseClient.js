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
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyAnbjud7DPB3ux8HO87myuSclNbFn1z7JI",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "sihhhhhh.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "sihhhhhh",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "sihhhhhh.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "75156104537",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:75156104537:web:ed9855b2fa0694fd1d5848",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-5TMWJR7S4V",
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
