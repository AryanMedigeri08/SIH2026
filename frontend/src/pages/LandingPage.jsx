/**
 * LandingPage.jsx — Sovereign Public Marketing & Gateway Hero Page.
 * Styled in complete alignment with the Udyam Saathi Institutional Dashboard Theme.
 */

import React from "react";
import { Link } from "react-router-dom";
import {
  TrendingUp,
  ShieldCheck,
  Building2,
  FileSpreadsheet,
  Cpu,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Zap,
  Award,
  Users,
  Compass,
  PieChart,
  Layers,
  ChevronRight,
  FileCheck,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { useLanguage } from "../context/LanguageContext";

export const LandingPage = () => {
  const { isAuthenticated, userProfile, loginAsDemo } = useAuth();
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col selection:bg-sovereign-100 selection:text-sovereign-900 overflow-x-hidden w-full max-w-full">
      {/* Top Banner / Ticker */}
      <div className="border-b border-sovereign-200 bg-gradient-to-r from-sovereign-50 via-white to-sky-50 px-2.5 py-1.5 sm:px-4 sm:py-2 text-center text-xs text-sovereign-800 flex flex-wrap items-center justify-center gap-1.5 sm:gap-2 shadow-xs">
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-sovereign-100 text-sovereign-900 border border-sovereign-300 font-mono shrink-0">
          MoMSME
        </span>
        <span className="font-semibold text-[11px] sm:text-xs">
          National Micro-Enterprise Feasibility & Bank DPR Advisory Engine
        </span>
      </div>

      {/* Main Top Header */}
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur-md sticky top-0 z-30 shadow-subtle">
        <div className="max-w-7xl mx-auto px-3.5 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sovereign-900 via-sovereign-800 to-sovereign-700 flex items-center justify-center text-white font-black text-lg shadow-md shadow-sovereign-950/20 group-hover:scale-105 transition-transform">
              उ
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-outfit font-bold text-lg text-slate-900 tracking-tight">
                  Udyam Saathi
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-sovereign-50 text-sovereign-800 border border-sovereign-200 px-1.5 py-0.5 rounded-md">
                  उद्यम साथी
                </span>
              </div>
              <span className="text-[11px] text-slate-500 font-medium block">
                Govt. of India • MSME Credit Intelligence
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <LanguageSelector />
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-slate-700 hover:text-slate-900 hover:bg-slate-100 font-bold text-xs transition-colors"
                >
                  <span>{t('signIn') || 'Sign In'}</span>
                </Link>
                <Link
                  to="/dashboard"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sovereign-800 hover:bg-sovereign-700 text-white font-bold text-xs shadow-md shadow-sovereign-900/20 transition-all"
                >
                  <span>Dashboard</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            ) : (
              <>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-slate-700 hover:text-slate-900 hover:bg-slate-100 font-bold text-xs transition-colors"
                >
                  <span>{t('signIn') || 'Sign In'}</span>
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-sovereign-700 hover:from-sovereign-800 hover:to-sovereign-600 text-white font-bold text-xs shadow-md shadow-sovereign-900/20 transition-all"
                >
                  <span>Get Started</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-16 md:pt-20 md:pb-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Subtle Ambient Background Gradients */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[36rem] h-[36rem] bg-sovereign-100/60 blur-[130px] rounded-full pointer-events-none -z-10" />
        <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-sky-100/50 blur-[140px] rounded-full pointer-events-none -z-10" />
        <div className="absolute bottom-10 right-1/4 w-80 h-80 bg-emerald-100/40 blur-[140px] rounded-full pointer-events-none -z-10" />

        <div className="relative text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sovereign-50 border border-sovereign-200 text-xs text-sovereign-900 font-semibold mb-6 shadow-xs">
            <Sparkles className="w-4 h-4 text-sovereign-700 animate-pulse" />
            <span>Empowering 6.3 Crore Indian MSMEs with Institutional Underwriting</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight font-display text-slate-900 leading-tight">
            Institutional Credit Appraisal for{" "}
            <span className="bg-gradient-to-r from-sovereign-900 via-sovereign-700 to-blue-700 bg-clip-text text-transparent">
              Rural & Semi-Urban
            </span>{" "}
            Enterprises
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-600 max-w-3xl mx-auto leading-relaxed">
            Eliminate subjective guesswork. Udyam Saathi pairs verified Census & MSME district datasets with
            RBI-compliant financial underwriting, supervised XGBoost ML viability scoring, and automated 7-Section Bank DPR compilation.
          </p>

          {/* Action CTAs */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            {isAuthenticated ? (
              <>
                <Link
                  to="/wizard"
                  className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-sovereign-700 hover:from-sovereign-800 hover:to-sovereign-600 text-white font-bold text-sm sm:text-base shadow-lg shadow-sovereign-900/25 transition-all duration-200 transform hover:-translate-y-0.5"
                >
                  <span>New Feasibility Appraisal ({userProfile?.name?.split(" ")[0] || "Enterprise"})</span>
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-800 font-bold text-sm sm:text-base shadow-subtle hover:border-slate-400 transition-all cursor-pointer"
                >
                  <span>{t('signIn') || 'Sign In'}</span>
                </Link>
              </>
            ) : (
              <>
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-sovereign-700 hover:from-sovereign-800 hover:to-sovereign-600 text-white font-bold text-sm sm:text-base shadow-lg shadow-sovereign-900/25 transition-all duration-200 transform hover:-translate-y-0.5"
                >
                  <span>Start Free Feasibility Appraisal</span>
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-800 font-bold text-sm sm:text-base shadow-subtle hover:border-slate-400 transition-all cursor-pointer"
                >
                  <span>{t('signIn') || 'Sign In'}</span>
                </Link>
              </>
            )}

            <Link
              to="/calculator"
              className="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-sovereign-50 hover:bg-sovereign-100/80 border border-sovereign-200 text-sovereign-900 font-bold text-xs sm:text-sm shadow-subtle transition-colors"
            >
              <Cpu className="w-4 h-4 text-sovereign-700" />
              <span>Quick Loan & Subsidy Calculator</span>
            </Link>
          </div>

          {/* Value Badges */}
          <div className="mt-12 pt-8 border-t border-slate-200 grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card hover:shadow-card-hover transition-all">
              <div className="text-2xl font-bold text-sovereign-800 font-display">100%</div>
              <div className="text-xs text-slate-600 font-medium mt-1">Deterministic Financial Math</div>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card hover:shadow-card-hover transition-all">
              <div className="text-2xl font-bold text-emerald-700 font-display">10 Schemes</div>
              <div className="text-xs text-slate-600 font-medium mt-1">PMEGP, Mudra, Stand-Up, PMFME</div>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card hover:shadow-card-hover transition-all">
              <div className="text-2xl font-bold text-blue-700 font-display">613 Metrics</div>
              <div className="text-xs text-slate-600 font-medium mt-1">Live LGD & Amenities Catchment</div>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card hover:shadow-card-hover transition-all">
              <div className="text-2xl font-bold text-amber-700 font-display">7-Section DPR</div>
              <div className="text-xs text-slate-600 font-medium mt-1">Bank-Ready PDF / Print Export</div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-16 bg-white border-t border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-sovereign-50 text-sovereign-800 border border-sovereign-200 text-xs font-bold font-mono uppercase tracking-wider mb-2">
              System Specification
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 font-display">
              Four-Tier Engineered Appraisal Architecture
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 mt-2">
              Clean separation of concerns: mathematical rigor in Tier 1, ML confidence in Tier 2, multilingual synthesis in Tier 3, and statutory bank memorandum generation in Tier 4.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl bg-slate-50/70 border border-slate-200 hover:border-sovereign-400 hover:bg-white transition-all shadow-subtle group">
              <div className="w-12 h-12 rounded-xl bg-sovereign-100 border border-sovereign-200 text-sovereign-800 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <PieChart className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900 font-display">Tier 1: Financial Invariants</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed font-medium">
                Computes DSCR, 5-year compounding cashflow, working capital cycles, and optimal subsidy grant matching across 10 statutory schemes.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50/70 border border-slate-200 hover:border-teal-400 hover:bg-white transition-all shadow-subtle group">
              <div className="w-12 h-12 rounded-xl bg-teal-50 border border-teal-200 text-teal-800 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900 font-display">Tier 2: XGBoost + TreeSHAP</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed font-medium">
                Supervised 10-dimensional ML classifier trained on synthetic rural MSME distributions, paired with true game-theoretic TreeSHAP feature attribution.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50/70 border border-slate-200 hover:border-blue-400 hover:bg-white transition-all shadow-subtle group">
              <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900 font-display">Tier 3: Executive Synthesis</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed font-medium">
                Multi-lingual narrative generation across English, Hindi, Marathi, Tamil, Telugu, and Kannada with zero mathematical hallucination guarantee.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50/70 border border-slate-200 hover:border-amber-400 hover:bg-white transition-all shadow-subtle group">
              <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900 font-display">Tier 4: 7-Section Bank DPR</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed font-medium">
                Generates complete bank credit memoranda with Means of Finance, 5-Year Profit & Loss, Balance Sheet, and Statutory Checklist.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200 bg-slate-100 py-8 px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-600">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-sovereign-900 to-sovereign-700 flex items-center justify-center text-white font-bold text-xs">
              उ
            </div>
            <span className="font-bold text-slate-900 font-display">Udyam Saathi (उद्यम साथी)</span>
            <span className="text-slate-400">|</span>
            <span className="font-mono text-slate-500">MoMSME</span>
          </div>

          <div className="flex flex-wrap justify-center items-center gap-3 sm:gap-6 font-semibold">
            <Link to="/schemes" className="hover:text-sovereign-800 transition-colors">Schemes Catalog</Link>
            <Link to="/data-sources" className="hover:text-sovereign-800 transition-colors">Data Lineage</Link>
            <Link to="/calculator" className="hover:text-sovereign-800 transition-colors">Quick Calculator</Link>
            <Link to="/login" className="hover:text-sovereign-800 transition-colors">Sign In</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
