/**
 * RegisterPage.jsx — Rural Entrepreneur Registration with Phone-First Design.
 * Phone number is mandatory, email is optional. Auto-detects browser geolocation.
 * Styled in complete harmony with the Udyam Saathi Institutional Dashboard Theme.
 */

import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useBusiness } from "../context/BusinessContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { useLanguage } from "../context/LanguageContext";
import {
  Lock,
  Mail,
  User,
  Phone,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  Loader2,
  Zap,
  Sparkles,
  MapPin,
  CheckCircle2,
} from "lucide-react";

export const RegisterPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [gender, setGender] = useState("Unspecified");
  const [phone, setPhone] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState(null);

  // Geolocation auto-detection state
  const [detectedLocation, setDetectedLocation] = useState(null);
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);
  const [locationStatus, setLocationStatus] = useState("idle"); // idle | detecting | success | error

  const { registerWithEmail, loginWithGoogle, loginAsDemo, authError } = useAuth();
  const { t } = useLanguage();
  const { loadUserBusinesses } = useBusiness();
  const navigate = useNavigate();

  // Auto-detect geolocation on page load
  const detectLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setLocationStatus("error");
      return;
    }
    setIsDetectingLocation(true);
    setLocationStatus("detecting");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const loc = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        };
        setDetectedLocation(loc);
        setIsDetectingLocation(false);
        setLocationStatus("success");
      },
      (err) => {
        console.warn("Geolocation detection failed:", err.message);
        setIsDetectingLocation(false);
        setLocationStatus("error");
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }, []);

  useEffect(() => {
    detectLocation();
  }, [detectLocation]);

  // Validate Indian phone number (10 digits)
  const isValidPhone = (ph) => /^[6-9]\d{9}$/.test(ph.replace(/\s/g, ""));

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Phone is mandatory
    if (!name.trim()) {
      setLocalError("कृपया अपना नाम दर्ज करें / Please enter your name.");
      return;
    }
    if (!phone.trim() || !isValidPhone(phone.trim())) {
      setLocalError("कृपया अपना 10 अंकों का मोबाइल नंबर दर्ज करें / Please enter a valid 10-digit mobile number.");
      return;
    }
    if (!password || password.length < 6) {
      setLocalError("कृपया कम से कम 6 अक्षरों का पासवर्ड दर्ज करें / Password must be at least 6 characters.");
      return;
    }

    setLocalError(null);
    setIsSubmitting(true);

    // Use phone-based email if no email provided (for Firebase compatibility)
    const effectiveEmail = email.trim() || `${phone.trim()}@udyam.phone.in`;

    try {
      await registerWithEmail(effectiveEmail, password, {
        name: name.trim(),
        gender,
        phone: phone.trim(),
        latitude: detectedLocation?.latitude || null,
        longitude: detectedLocation?.longitude || null,
      });
      // Redirect to the new conversational onboarding instead of wizard
      navigate("/onboarding", { replace: true });
    } catch (err) {
      setLocalError(err.message || "खाता बनाने में विफल / Failed to create account.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleSignup = async () => {
    setLocalError(null);
    setIsSubmitting(true);
    try {
      const authRes = await loginWithGoogle();
      const userToken = authRes?.user?.getIdToken ? await authRes.user.getIdToken() : null;
      try {
        const res = await loadUserBusinesses(userToken);
        navigate(res?.hasBusinesses ? "/dashboard" : "/onboarding", { replace: true });
      } catch (_) {
        navigate("/onboarding", { replace: true });
      }
    } catch (err) {
      setLocalError(err.message || "Google signup was cancelled or failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoAccess = async () => {
    setLocalError(null);
    setIsSubmitting(true);
    try {
      const authRes = await loginAsDemo("evaluator@udyam.gov.in", "Demo Evaluator");
      const userToken = authRes?.user?.getIdToken ? await authRes.user.getIdToken() : null;
      try {
        const res = await loadUserBusinesses(userToken);
        navigate(res?.hasBusinesses ? "/dashboard" : "/onboarding", { replace: true });
      } catch (_) {
        navigate("/onboarding", { replace: true });
      }
    } catch (err) {
      setLocalError(err.message || "Demo access failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8 sm:py-12 px-3.5 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-sovereign-100 selection:text-sovereign-900 overflow-x-hidden w-full max-w-full">
      <div className="absolute right-4 top-4 z-20">
        <LanguageSelector />
      </div>

      {/* Subtle Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[34rem] h-[34rem] bg-sovereign-100/60 blur-[140px] rounded-full pointer-events-none -z-10" />
      <div className="absolute bottom-10 right-1/4 w-80 h-80 bg-sky-100/50 blur-[140px] rounded-full pointer-events-none -z-10" />

      <div className="max-w-xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center mb-6 sm:mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-4 group">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-sovereign-900 via-sovereign-800 to-sovereign-700 flex items-center justify-center text-white font-black text-xl shadow-md shadow-sovereign-950/20 group-hover:scale-105 transition-transform">
              उ
            </div>
            <span className="text-2xl font-bold font-display text-slate-900 tracking-tight">
              Udyam Saathi
            </span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-display">
            {t('createAccount') || 'उद्यमी खाता बनाएँ'}
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-slate-600 font-medium">
            अपना प्रोफ़ाइल बनाएँ और AI-संचालित व्यवसाय सहायता प्राप्त करें
          </p>
        </div>

        {/* Form Container */}
        <div className="bg-white py-6 px-4 sm:py-8 sm:px-10 shadow-xl shadow-slate-200/60 rounded-2xl border border-slate-200">
          
          {/* Quick Demo One-Click Access Button */}
          <div className="mb-6">
            <button
              type="button"
              onClick={handleDemoAccess}
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-emerald-50 hover:bg-emerald-100/80 border border-emerald-300 text-emerald-900 font-bold text-xs shadow-xs transition-all duration-200 group"
            >
              <Zap className="w-4 h-4 text-emerald-700 group-hover:scale-110 transition-transform" />
              <span>Skip & Instant Access as Demo Evaluator</span>
            </button>
          </div>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-3 text-slate-400 font-semibold tracking-wider text-[11px]">
                Or create new profile
              </span>
            </div>
          </div>

          {/* Error Banner */}
          {(localError || authError) && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-xs shadow-xs">
              <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
              <p className="leading-relaxed font-medium">{localError || authError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Section 1: Promoter Identity (Name + Phone First) */}
            <div>
              <div className="flex items-center gap-2 pb-2 mb-3.5 border-b border-slate-200 text-sovereign-800 text-xs font-bold uppercase tracking-wider">
                <User className="w-4 h-4 text-sovereign-700" />
                <span>1. आपकी पहचान / Your Identity</span>
              </div>

              <div className="space-y-4">
                {/* Full Name — Required */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    पूरा नाम / Full Name <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative rounded-xl shadow-subtle">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <User className="h-4 w-4" />
                    </div>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. रमेश चंद्र शर्मा"
                      required
                      className="block w-full pl-10 pr-4 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 transition shadow-subtle"
                    />
                  </div>
                </div>

                {/* Phone Number — Required */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    मोबाइल नंबर / Mobile Number <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative rounded-xl shadow-subtle">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Phone className="h-4 w-4" />
                    </div>
                    <div className="absolute inset-y-0 left-10 flex items-center pointer-events-none">
                      <span className="text-sm text-slate-500 font-medium">+91</span>
                    </div>
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => {
                        const val = e.target.value.replace(/[^0-9]/g, '').slice(0, 10);
                        setPhone(val);
                      }}
                      placeholder="9876543210"
                      required
                      maxLength={10}
                      className="block w-full pl-[5.5rem] pr-4 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 transition shadow-subtle"
                    />
                  </div>
                  <p className="mt-1 text-[11px] text-slate-500">
                    यह नंबर आपके खाते से जुड़ा रहेगा / This number will be linked to your account
                  </p>
                </div>

                {/* Gender */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    लिंग / Gender
                  </label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="block w-full px-3 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 transition shadow-subtle"
                  >
                    <option value="Unspecified">निर्दिष्ट नहीं / Unspecified</option>
                    <option value="Male">पुरुष / Male</option>
                    <option value="Female">महिला / Female</option>
                    <option value="Other">अन्य / Other</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Section 2: Account Security */}
            <div>
              <div className="flex items-center gap-2 pb-2 mb-3.5 border-b border-slate-200 text-sovereign-800 text-xs font-bold uppercase tracking-wider">
                <ShieldCheck className="w-4 h-4 text-sovereign-700" />
                <span>2. खाता सुरक्षा / Account Security</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    ईमेल / Email <span className="text-slate-400 font-normal">(वैकल्पिक / Optional)</span>
                  </label>
                  <div className="relative rounded-xl shadow-subtle">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Mail className="h-4 w-4" />
                    </div>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="optional@email.com"
                      className="block w-full pl-10 pr-4 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 transition shadow-subtle"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    पासवर्ड / Password <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative rounded-xl shadow-subtle">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Lock className="h-4 w-4" />
                    </div>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Min 6 characters"
                      required
                      minLength={6}
                      className="block w-full pl-10 pr-4 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 transition shadow-subtle"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Location Detection Status Banner */}
            <div className={`p-3 rounded-xl flex items-center gap-2 text-xs font-medium transition-all duration-300 ${
              locationStatus === "success"
                ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
                : locationStatus === "detecting"
                ? "bg-sky-50 border border-sky-200 text-sky-800"
                : locationStatus === "error"
                ? "bg-amber-50 border border-amber-200 text-amber-800"
                : "bg-slate-50 border border-slate-200 text-slate-600"
            }`}>
              {locationStatus === "success" ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>📍 आपका स्थान सफलतापूर्वक पहचाना गया / Location detected successfully</span>
                </>
              ) : locationStatus === "detecting" ? (
                <>
                  <Loader2 className="w-4 h-4 text-sky-600 animate-spin shrink-0" />
                  <span>📍 आपका स्थान पहचान रहे हैं... / Detecting your location...</span>
                </>
              ) : locationStatus === "error" ? (
                <>
                  <MapPin className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>
                    📍 स्थान पहचानने में असमर्थ / Unable to detect location.{" "}
                    <button
                      type="button"
                      onClick={detectLocation}
                      className="underline font-bold hover:text-amber-900 transition-colors"
                    >
                      पुनः प्रयास करें / Retry
                    </button>
                  </span>
                </>
              ) : (
                <>
                  <MapPin className="w-4 h-4 text-slate-500 shrink-0" />
                  <span>📍 Location will be auto-detected</span>
                </>
              )}
            </div>

            {/* Note about MIRA onboarding */}
            <div className="p-3 rounded-xl bg-sovereign-50 border border-sovereign-200 text-xs text-sovereign-900 flex items-center gap-2 font-medium">
              <Sparkles className="w-4 h-4 text-sovereign-700 shrink-0" />
              <span>
                आगे MIRA आपसे बातचीत करके आपके व्यवसाय की जानकारी लेगी / Next, MIRA will chat with you to understand your business idea.
              </span>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-sovereign-700 hover:from-sovereign-800 hover:to-sovereign-600 text-white font-bold text-sm shadow-md shadow-sovereign-900/20 hover:shadow-lg transition-all duration-200 disabled:opacity-50 group"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>खाता बना रहे हैं... / Creating Account...</span>
                </>
              ) : (
                <>
                  <span>खाता बनाएँ और MIRA से बात करें / Create Account & Talk to MIRA</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Social Sign-in Divider */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-3 text-slate-400 font-semibold tracking-wider text-[11px]">
                  Or register with
                </span>
              </div>
            </div>

            <div className="mt-5">
              <button
                type="button"
                onClick={handleGoogleSignup}
                disabled={isSubmitting}
                className="w-full inline-flex items-center justify-center gap-3 py-2.5 px-4 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-sm font-semibold shadow-subtle hover:border-slate-400 transition-colors disabled:opacity-50"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                  />
                </svg>
                <span>Google Enterprise SSO</span>
              </button>
            </div>
          </div>
        </div>

        {/* Existing Account Prompt */}
        <p className="mt-6 text-center text-xs text-slate-600 font-medium">
          Already registered?{" "}
          <Link to="/login" className="font-bold text-sovereign-800 hover:text-sovereign-600 underline transition-colors">
            Sign in to existing account &rarr;
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
