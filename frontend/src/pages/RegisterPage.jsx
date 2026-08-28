/**
 * RegisterPage.jsx — Multi-Section Sovereign Account & Promoter Profile Registration.
 */

import React, { useState } from "react";
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
} from "lucide-react";

export const RegisterPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [gender, setGender] = useState("Unspecified");
  const [phone, setPhone] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState(null);

  const { registerWithEmail, loginWithGoogle, loginAsDemo, authError } = useAuth();
  const { t } = useLanguage();
  const { loadUserBusinesses } = useBusiness();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password || !name) {
      setLocalError("Please fill in your name, email, and password.");
      return;
    }
    if (password.length < 6) {
      setLocalError("Password must be at least 6 characters.");
      return;
    }

    setLocalError(null);
    setIsSubmitting(true);

    try {
      await registerWithEmail(email.trim(), password, {
        name: name.trim(),
        gender,
        phone: phone.trim() || null,
      });
      // Direct user into the 7-Step Feasibility Wizard to input business details & supplementary context
      navigate("/wizard", { replace: true });
    } catch (err) {
      setLocalError(err.message || "Failed to create promoter account.");
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
        navigate(res?.hasBusinesses ? "/" : "/wizard", { replace: true });
      } catch (_) {
        navigate("/wizard", { replace: true });
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
      const authRes = await loginAsDemo("evaluator@sih.gov.in", "SIH Jury Evaluator");
      const userToken = authRes?.user?.getIdToken ? await authRes.user.getIdToken() : null;
      try {
        const res = await loadUserBusinesses(userToken);
        navigate(res?.hasBusinesses ? "/" : "/wizard", { replace: true });
      } catch (_) {
        navigate("/wizard", { replace: true });
      }
    } catch (err) {
      setLocalError(err.message || "Demo access failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-cyan-500/30 selection:text-cyan-200">
      <div className="absolute right-4 top-4 z-20"><LanguageSelector /></div>
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[32rem] h-[32rem] bg-cyan-500/10 blur-[140px] rounded-full pointer-events-none" />

      <div className="max-w-xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-4 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950 font-black text-lg shadow-lg shadow-cyan-500/30 group-hover:scale-105 transition-transform">
              उ
            </div>
            <span className="text-xl font-bold font-display text-white">Udyam Saathi</span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white font-display">
            {t('createAccount')}
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-slate-400">
            Set up your verified profile for AI-driven feasibility appraisals and institutional bank DPR generation.
          </p>
        </div>

        {/* Form Container */}
        <div className="bg-slate-900/90 py-8 px-6 sm:px-10 shadow-2xl rounded-2xl border border-slate-800 backdrop-blur-xl">
          {/* Quick Demo One-Click Access Button */}
          <div className="mb-6">
            <button
              type="button"
              onClick={handleDemoAccess}
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-500/20 via-cyan-500/20 to-teal-500/20 hover:from-emerald-500/30 hover:to-cyan-500/30 border border-emerald-500/40 text-emerald-300 font-bold text-xs shadow-lg shadow-emerald-950/40 transition-all duration-200 group"
            >
              <Zap className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
              <span>Skip & Instant Access as Demo Evaluator</span>
            </button>
          </div>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-900 px-3 text-slate-500 font-medium tracking-wider">
                Or create new profile
              </span>
            </div>
          </div>

          {/* Error Banner */}
          {(localError || authError) && (
            <div className="mb-6 p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 flex items-start gap-3 text-rose-300 text-xs">
              <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
              <p className="leading-relaxed">{localError || authError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Section 1: Security & Identity */}
            <div>
              <div className="flex items-center gap-2 pb-2 mb-3.5 border-b border-slate-800 text-cyan-400 text-xs font-bold uppercase tracking-wider">
                <ShieldCheck className="w-4 h-4" />
                <span>1. Account Credentials</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Email Address <span className="text-rose-400">*</span>
                  </label>
                  <div className="relative rounded-xl shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Mail className="h-4 w-4" />
                    </div>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="promoter@enterprise.in"
                      required
                      className="block w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Account Password <span className="text-rose-400">*</span>
                  </label>
                  <div className="relative rounded-xl shadow-sm">
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
                      className="block w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-colors"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Section 2: Promoter Profile */}
            <div>
              <div className="flex items-center gap-2 pb-2 mb-3.5 border-b border-slate-800 text-teal-400 text-xs font-bold uppercase tracking-wider">
                <User className="w-4 h-4" />
                <span>2. Promoter Profile</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Full Legal Name <span className="text-rose-400">*</span>
                  </label>
                  <div className="relative rounded-xl shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <User className="h-4 w-4" />
                    </div>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Ramesh Chandra Sharma"
                      required
                      className="block w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Gender
                  </label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="block w-full px-3 py-2.5 bg-slate-950/80 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-colors"
                  >
                    <option value="Unspecified">Unspecified</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="mt-3.5">
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Mobile / Phone Number (Optional)
                </label>
                <div className="relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Phone className="h-4 w-4" />
                  </div>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="9876543210"
                    className="block w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* Note on Step-by-Step Business Details */}
            <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700 text-xs text-slate-300 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400 shrink-0" />
              <span>
                Business details & supplementary context are seamlessly entered in the 7-Step Feasibility Wizard next.
              </span>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm shadow-xl shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all duration-200 disabled:opacity-50 group"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Registering Sovereign Account...</span>
                </>
              ) : (
                <>
                  <span>Create Account & Start Feasibility Wizard</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Social Sign-in Divider */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-800" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-slate-900 px-3 text-slate-500 font-medium tracking-wider">
                  Or register with
                </span>
              </div>
            </div>

            <div className="mt-6">
              <button
                type="button"
                onClick={handleGoogleSignup}
                disabled={isSubmitting}
                className="w-full inline-flex items-center justify-center gap-3 py-2.5 px-4 rounded-xl bg-slate-950 hover:bg-slate-800/80 border border-slate-700 text-slate-200 text-sm font-medium transition-colors disabled:opacity-50"
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
        <p className="mt-6 text-center text-xs text-slate-400">
          Already registered?{" "}
          <Link to="/login" className="font-semibold text-cyan-400 hover:text-cyan-300 transition-colors">
            Sign in to existing account &rarr;
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
