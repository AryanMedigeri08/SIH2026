import React, { useState, useEffect } from 'react';
import { 
  Calculator, Coins, ShieldCheck, CheckCircle2, TrendingUp, 
  Award, ArrowRight, Percent, Clock, AlertTriangle 
} from 'lucide-react';
import { calculateFinancials } from '../services/api';

export function CalculatorPage() {
  const [params, setParams] = useState({
    project_cost: 900000,
    annual_turnover: 950000,
    business_category: 'manufacturing',
    sector: 'dairy',
    promoter_category: 'general',
    is_rural: true,
    tenure_years: 7,
    moratorium_months: 6,
    interest_rate_pct: 9.5,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Recalculate whenever params change (with slight debounce)
  useEffect(() => {
    const timer = setTimeout(async () => {
      setLoading(true);
      const res = await calculateFinancials(params);
      setResult(res);
      setLoading(false);
    }, 200);

    return () => clearTimeout(timer);
  }, [params]);

  const updateParam = (key, value) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  const dscr = result?.dscr || 2.26;
  const isViable = dscr >= 1.33;
  const isCaution = dscr >= 1.0 && dscr < 1.33;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-cyan-500 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-cyan-400 mb-1 flex items-center gap-1.5">
            <Calculator className="w-4 h-4" />
            <span>Interactive Financial Engineering Engine</span>
          </div>
          <h1 className="text-2xl font-outfit font-extrabold text-white">
            Standalone MSME Loan Sizing & DSCR Sensitivity Tool
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Simulate credit-linked capital subsidies, EMI amortization schedules with moratorium periods, and RBI-compliant Debt Service Coverage Ratios in real-time.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold px-3 py-1.5 rounded-full border flex items-center gap-1.5 ${
            isViable
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : isCaution
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isViable ? 'bg-emerald-400' : isCaution ? 'bg-amber-400' : 'bg-rose-400'}`} />
            <span>DSCR: {dscr.toFixed(2)} ({result?.dscr_verdict || 'VIABLE'})</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Form Column (Inputs) */}
        <div className="lg:col-span-5 glass-panel p-6 space-y-5">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2">
            1. Enterprise Capital & Operating Parameters
          </h3>

          {/* Project Cost Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label className="text-slate-300 font-semibold">Total Capital Outlay (₹)</label>
              <span className="text-cyan-400 font-mono font-bold">₹{params.project_cost.toLocaleString('en-IN')}</span>
            </div>
            <input
              type="range"
              min={50000}
              max={10000000}
              step={25000}
              value={params.project_cost}
              onChange={(e) => updateParam('project_cost', Number(e.target.value))}
              className="w-full accent-cyan-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>₹50K</span>
              <span>₹50L</span>
              <span>₹1 Cr</span>
            </div>
          </div>

          {/* Annual Turnover Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label className="text-slate-300 font-semibold">Estimated Annual Turnover (₹)</label>
              <span className="text-emerald-400 font-mono font-bold">₹{params.annual_turnover.toLocaleString('en-IN')}</span>
            </div>
            <input
              type="range"
              min={100000}
              max={20000000}
              step={50000}
              value={params.annual_turnover}
              onChange={(e) => updateParam('annual_turnover', Number(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer"
            />
          </div>

          {/* Sector & Category Selection */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400">Sector</label>
              <select
                value={params.sector}
                onChange={(e) => updateParam('sector', e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="dairy">Dairy Processing</option>
                <option value="food_processing">Food Processing</option>
                <option value="repair">Mobile / Auto Repair</option>
                <option value="textiles">Textiles & Boutique</option>
                <option value="pottery">Artisan Pottery / Clay</option>
                <option value="general">General Manufacturing</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400">Promoter Category</label>
              <select
                value={params.promoter_category}
                onChange={(e) => updateParam('promoter_category', e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="general">General (10% Margin)</option>
                <option value="women">Women Entrepreneur (5% Margin)</option>
                <option value="sc">SC / ST (5% Margin)</option>
                <option value="obc">OBC (5% Margin)</option>
                <option value="minority">Minority (5% Margin)</option>
              </select>
            </div>
          </div>

          {/* Rural vs Urban Toggle */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            <div>
              <span className="font-semibold text-white block">Enterprise Location Type</span>
              <span className="text-slate-400 text-[11px]">
                {params.is_rural ? 'Rural (35% Special / 25% Gen Subsidy)' : 'Urban (25% Special / 15% Gen Subsidy)'}
              </span>
            </div>
            <button
              type="button"
              onClick={() => updateParam('is_rural', !params.is_rural)}
              className={`px-3 py-1 rounded-lg font-bold text-xs transition-all ${
                params.is_rural
                  ? 'bg-cyan-500 text-black shadow-glow-cyan'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {params.is_rural ? 'Rural' : 'Urban'}
            </button>
          </div>

          <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2 pt-2">
            2. Bank Financing & Amortization
          </h3>

          {/* Loan Tenure & Moratorium */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400">Tenure ({params.tenure_years} Years)</label>
              <input
                type="range"
                min={1}
                max={10}
                value={params.tenure_years}
                onChange={(e) => updateParam('tenure_years', Number(e.target.value))}
                className="w-full accent-cyan-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-slate-400">Moratorium ({params.moratorium_months} Mo.)</label>
              <input
                type="range"
                min={0}
                max={12}
                value={params.moratorium_months}
                onChange={(e) => updateParam('moratorium_months', Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
          </div>

          {/* Interest Rate */}
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <label className="text-slate-400">Bank Interest Rate (% p.a.)</label>
              <span className="font-mono text-cyan-300">{params.interest_rate_pct}%</span>
            </div>
            <input
              type="range"
              min={7.0}
              max={15.0}
              step={0.25}
              value={params.interest_rate_pct}
              onChange={(e) => updateParam('interest_rate_pct', Number(e.target.value))}
              className="w-full accent-cyan-500"
            />
          </div>

        </div>

        {/* Right Output Column (Results) */}
        <div className="lg:col-span-7 space-y-4">
          
          {/* Top Matched Scheme Card */}
          <div className="glass-panel p-6 border-l-4 border-emerald-500 space-y-4">
            <div className="flex items-start justify-between gap-2">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded">
                  Optimal Financing Vehicle
                </span>
                <h2 className="text-lg sm:text-xl font-bold font-outfit text-white mt-1">
                  {result?.top_scheme_id || 'PMEGP'} — {result?.top_scheme_name || "Prime Minister's Employment Generation Programme"}
                </h2>
              </div>

              <div className="text-right">
                <span className="text-[10px] text-slate-400 block">Capital Subsidy Grant</span>
                <strong className="text-xl sm:text-2xl font-mono font-extrabold text-emerald-400">
                  ₹{(result?.subsidy_grant_amount || 225000).toLocaleString('en-IN')}
                </strong>
              </div>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                <span className="text-slate-400 text-[11px] block">Net Bank Loan</span>
                <strong className="text-white font-mono text-sm mt-0.5 block">
                  ₹{(result?.loan_principal || 585000).toLocaleString('en-IN')}
                </strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                <span className="text-slate-400 text-[11px] block">Monthly EMI</span>
                <strong className="text-cyan-400 font-mono text-sm mt-0.5 block">
                  ₹{(result?.monthly_emi || 10530).toLocaleString('en-IN')}
                </strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                <span className="text-slate-400 text-[11px] block">Working Capital</span>
                <strong className="text-indigo-300 font-mono text-sm mt-0.5 block">
                  ₹{(result?.working_capital_required || 190000).toLocaleString('en-IN')}
                </strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                <span className="text-slate-400 text-[11px] block">Total Interest</span>
                <strong className="text-slate-300 font-mono text-sm mt-0.5 block">
                  ₹{(result?.total_interest_payable || 230000).toLocaleString('en-IN')}
                </strong>
              </div>
            </div>
          </div>

          {/* Scheme Comparison Leaderboard */}
          <div className="glass-panel p-6 space-y-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Award className="w-4 h-4 text-cyan-400" />
              <span>Ranked Scheme Options for Selected Outlay</span>
            </h3>

            <div className="space-y-2">
              {(result?.ranked_schemes || []).map((s, idx) => (
                <div
                  key={s.scheme_id || idx}
                  className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs transition-all ${
                    idx === 0
                      ? 'bg-emerald-950/20 border-emerald-500/30'
                      : s.eligible
                      ? 'bg-slate-900/60 border-slate-800'
                      : 'bg-slate-950/40 border-slate-800/60 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className="w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-300 font-bold flex items-center justify-center text-xs shrink-0">
                      {idx + 1}
                    </span>
                    <div>
                      <strong className="text-white font-semibold">{s.scheme_id}</strong>
                      <span className="text-slate-400 text-[11px] ml-2">({s.scheme_name || s.full_name})</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-right">
                    <div>
                      <span className="text-[10px] text-slate-400 block">Grant Subsidy</span>
                      <strong className="font-mono text-emerald-400">
                        {s.subsidy_grant_amount > 0 ? `₹${Math.round(s.subsidy_grant_amount).toLocaleString('en-IN')}` : '₹0'}
                      </strong>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">Status</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                        s.eligible ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                      }`}>
                        {s.eligible ? 'Eligible' : 'Cap Exceeded'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
