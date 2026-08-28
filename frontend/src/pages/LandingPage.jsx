/**
 * LandingPage.jsx — Sovereign Public Marketing & Gateway Hero Page.
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
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { LanguageSelector } from "../components/LanguageSelector";
import { useLanguage } from "../context/LanguageContext";

export const LandingPage = () => {
  const { isAuthenticated, userProfile } = useAuth();
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Banner / Ticker */}
      <div className="border-b border-cyan-500/20 bg-gradient-to-r from-cyan-950/40 via-slate-900/60 to-blue-950/40 px-4 py-2 text-center text-xs text-cyan-300 flex items-center justify-center gap-2">
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
          SIH 2026 PS 26091
        </span>
        <span>National Micro-Enterprise Feasibility & Bank DPR Advisory Engine</span>
      </div>

      {/* Main Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-20 md:pt-24 md:pb-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="absolute right-4 top-4 z-10"><LanguageSelector /></div>
        {/* Ambient Glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/10 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-blue-600/10 blur-[140px] rounded-full pointer-events-none" />

        <div className="relative text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-cyan-500/30 text-xs text-cyan-300 font-medium mb-6 shadow-lg shadow-cyan-950/50 backdrop-blur-md">
            <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
            <span>Empowering 6.3 Crore Indian MSMEs with Institutional Intelligence</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight font-display text-white leading-tight">
            Institutional Credit Appraisal for{" "}
            <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-400 bg-clip-text text-transparent">
              Rural & Semi-Urban
            </span>{" "}
            Enterprises
          </h1>

          <p className="mt-6 text-base sm:text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Stop relying on rough guesswork. Udyam Saathi pairs verified Census & MSME district datasets with
            RBI-compliant financial math, XGBoost ML viability scoring, and automated 7-Section Bank DPR compilation.
          </p>

          {/* Action CTAs */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            {isAuthenticated ? (
              <Link
                to="/wizard"
                className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-base shadow-xl shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all duration-200 transform hover:-translate-y-0.5"
              >
                <span>Continue Appraisal ({userProfile?.name?.split(" ")[0] || "Entrepreneur"})</span>
                <ArrowRight className="w-5 h-5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-base shadow-xl shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all duration-200 transform hover:-translate-y-0.5"
                >
                  <span>Start Free Feasibility Appraisal</span>
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-base transition-colors"
                >
                  <span>{t('login')}</span>
                </Link>
              </>
            )}

            <Link
              to="/calculator"
              className="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 text-slate-300 font-medium text-sm transition-colors"
            >
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>Quick Loan & Subsidy Calculator</span>
            </Link>
          </div>

          {/* Value Badges */}
          <div className="mt-12 pt-8 border-t border-slate-800/80 grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
              <div className="text-2xl font-bold text-cyan-400 font-display">100%</div>
              <div className="text-xs text-slate-400 mt-1">Deterministic Financial Math</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
              <div className="text-2xl font-bold text-teal-400 font-display">10 Schemes</div>
              <div className="text-xs text-slate-400 mt-1">PMEGP, Mudra, Stand-Up, PMFME</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
              <div className="text-2xl font-bold text-blue-400 font-display">613 Metrics</div>
              <div className="text-xs text-slate-400 mt-1">Live LGD & Amenities Catchment</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
              <div className="text-2xl font-bold text-amber-400 font-display">7-Section DPR</div>
              <div className="text-xs text-slate-400 mt-1">Bank-Ready PDF / HTML Export</div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-16 bg-slate-900/50 border-t border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-white font-display">
              Four-Tier Engineered Appraisal Architecture
            </h2>
            <p className="text-sm sm:text-base text-slate-400 mt-2">
              Clean separation of concerns: mathematical rigor in Tier 1, ML confidence in Tier 2, multilingual synthesis in Tier 3, and bank memorandum generation in Tier 4.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <PieChart className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-slate-100 font-display">Tier 1: Financial Invariants</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Computes DSCR, 5-year compounding cashflow, working capital cycles, and optimal subsidy grant matching across 10 statutory schemes.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-teal-500/40 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-teal-500/10 border border-teal-500/20 text-teal-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-slate-100 font-display">Tier 2: XGBoost + TreeSHAP</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Supervised 10-dimensional ML classifier trained on synthetic rural MSME distributions, paired with true game-theoretic TreeSHAP feature attribution.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-blue-500/40 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-slate-100 font-display">Tier 3: Executive Synthesis</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Multi-lingual narrative generation across English, Hindi, Marathi, Tamil, Telugu, and Kannada with zero mathematical hallucination guarantee.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/40 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-slate-100 font-display">Tier 4: 7-Section Bank DPR</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Generates complete bank credit memoranda with Means of Finance, 5-Year Profit & Loss, Balance Sheet, and Statutory Checklist.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-800/80 py-8 px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950 font-bold text-xs">
              उ
            </div>
            <span className="font-semibold text-slate-300 font-display">Udyam Saathi (उद्यम साथी)</span>
            <span className="text-slate-600">|</span>
            <span>SIH 2026 PS 26091</span>
          </div>

          <div className="flex items-center gap-6">
            <Link to="/schemes" className="hover:text-cyan-400 transition-colors">Schemes Catalog</Link>
            <Link to="/data-sources" className="hover:text-cyan-400 transition-colors">Data Lineage</Link>
            <Link to="/calculator" className="hover:text-cyan-400 transition-colors">Quick Calculator</Link>
            <Link to="/login" className="hover:text-cyan-400 transition-colors">Sign In</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
