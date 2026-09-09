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

  const dscr = result?.dscr?.dscr || 2.26;
  const isViable = dscr >= 1.33;
  const isCaution = dscr >= 1.0 && dscr < 1.33;

  return (
    <div className="max-w-7xl mx-auto px-3.5 sm:px-6 lg:px-8 py-4 sm:py-8 space-y-5 sm:space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-4 sm:p-6 border-l-4 border-sovereign-800 bg-white shadow-card border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-sovereign-700 mb-1 flex items-center gap-1.5">
            <Calculator className="w-4 h-4" />
            <span>Interactive Financial Engineering Engine</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-outfit font-extrabold text-slate-900">
            Standalone MSME Loan Sizing & DSCR Sensitivity Tool
          </h1>
          <p className="text-xs text-slate-600 mt-1 max-w-2xl font-medium">
            Simulate credit-linked capital subsidies, EMI amortization schedules with moratorium periods, and RBI-compliant Debt Service Coverage Ratios in real-time.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold px-3 py-1.5 rounded-full border flex items-center gap-1.5 ${
            isViable
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : isCaution
              ? 'bg-amber-50 border-amber-200 text-amber-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isViable ? 'bg-emerald-600' : isCaution ? 'bg-amber-600' : 'bg-rose-600'}`} />
            <span>DSCR: {dscr.toFixed(2)} ({result?.dscr_verdict || 'VIABLE'})</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Form Column (Inputs) */}
        <div className="lg:col-span-5 glass-panel p-4 sm:p-6 space-y-5 bg-white shadow-card border border-slate-200">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-200 pb-2">
            1. Enterprise Capital & Operating Parameters
          </h3>

          {/* Project Cost Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label className="text-slate-700 font-bold">Total Capital Outlay (₹)</label>
              <span className="text-sovereign-800 font-mono font-bold">₹{params.project_cost.toLocaleString('en-IN')}</span>
            </div>
            <input
              type="range"
              min={50000}
              max={10000000}
              step={25000}
              value={params.project_cost}
              onChange={(e) => updateParam('project_cost', Number(e.target.value))}
              className="w-full accent-sovereign-800 cursor-pointer"
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
              <label className="text-slate-700 font-bold">Estimated Annual Turnover (₹)</label>
              <span className="text-emerald-700 font-mono font-bold">₹{params.annual_turnover.toLocaleString('en-IN')}</span>
            </div>
            <input
              type="range"
              min={100000}
              max={20000000}
              step={50000}
              value={params.annual_turnover}
              onChange={(e) => updateParam('annual_turnover', Number(e.target.value))}
              className="w-full accent-emerald-700 cursor-pointer"
            />
          </div>

          {/* Sector & Category Selection */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="space-y-1">
              <label className="text-slate-700 font-bold">Sector</label>
              <select
                value={params.sector}
                onChange={(e) => updateParam('sector', e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 font-medium"
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
              <label className="text-slate-700 font-bold">Promoter Category</label>
              <select
                value={params.promoter_category}
                onChange={(e) => updateParam('promoter_category', e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 font-medium"
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
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
            <div>
              <span className="font-bold text-slate-900 block">Enterprise Location Type</span>
              <span className="text-slate-500 text-[11px] font-medium">
                {params.is_rural ? 'Rural (35% Special / 25% Gen Subsidy)' : 'Urban (25% Special / 15% Gen Subsidy)'}
              </span>
            </div>
            <button
              type="button"
              onClick={() => updateParam('is_rural', !params.is_rural)}
              className={`px-3 py-1 rounded-lg font-bold text-xs transition-all ${
                params.is_rural
                  ? 'bg-sovereign-800 text-white shadow-sm'
                  : 'bg-slate-200 text-slate-700'
              }`}
            >
              {params.is_rural ? 'Rural' : 'Urban'}
            </button>
          </div>

          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-200 pb-2 pt-2">
            2. Bank Financing & Amortization
          </h3>

          {/* Loan Tenure & Moratorium */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="space-y-1">
              <label className="text-slate-700 font-bold">Tenure ({params.tenure_years} Years)</label>
              <input
                type="range"
                min={1}
                max={10}
                value={params.tenure_years}
                onChange={(e) => updateParam('tenure_years', Number(e.target.value))}
                className="w-full accent-sovereign-800"
              />
            </div>
            <div className="space-y-1">
              <label className="text-slate-700 font-bold">Moratorium ({params.moratorium_months} Mo.)</label>
              <input
                type="range"
                min={0}
                max={12}
                value={params.moratorium_months}
                onChange={(e) => updateParam('moratorium_months', Number(e.target.value))}
                className="w-full accent-blue-700"
              />
            </div>
          </div>

          {/* Interest Rate */}
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <label className="text-slate-700 font-bold">Bank Interest Rate (% p.a.)</label>
              <span className="font-mono text-sovereign-800 font-bold">{params.interest_rate_pct}%</span>
            </div>
            <input
              type="range"
              min={7.0}
              max={15.0}
              step={0.25}
              value={params.interest_rate_pct}
              onChange={(e) => updateParam('interest_rate_pct', Number(e.target.value))}
              className="w-full accent-sovereign-800"
            />
          </div>

        </div>

        {/* Right Output Column (Results) */}
        <div className="lg:col-span-7 space-y-4">
          
          {/* Top Matched Scheme Card */}
          <div className="glass-panel p-4 sm:p-6 border-l-4 border-emerald-600 bg-white shadow-card border border-slate-200 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded">
                  Optimal Financing Vehicle
                </span>
                <h2 className="text-base sm:text-xl font-bold font-outfit text-slate-900 mt-1">
                  {result?.top_scheme_id || 'PMEGP'} — {result?.top_scheme_name || "Prime Minister's Employment Generation Programme"}
                </h2>
              </div>

              <div className="text-left sm:text-right">
                <span className="text-[10px] text-slate-500 font-medium block">Capital Subsidy Grant</span>
                <strong className="text-xl sm:text-2xl font-mono font-extrabold text-emerald-700">
                  ₹{(result?.subsidy_grant_amount || 225000).toLocaleString('en-IN')}
                </strong>
              </div>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 pt-2">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500 text-[10px] sm:text-[11px] block font-medium truncate">Net Bank Loan</span>
                <strong className="text-slate-900 font-mono text-xs sm:text-sm mt-0.5 block font-bold truncate">
                  ₹{(result?.loan_principal || 585000).toLocaleString('en-IN')}
                </strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500 text-[10px] sm:text-[11px] block font-medium truncate">Monthly EMI</span>
                <strong className="text-sovereign-800 font-mono text-xs sm:text-sm mt-0.5 block font-bold truncate">
                  ₹{(result?.monthly_emi || 10530).toLocaleString('en-IN')}
                </strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500 text-[10px] sm:text-[11px] block font-medium truncate">Working Capital</span>
                <strong className="text-blue-900 font-mono text-xs sm:text-sm mt-0.5 block font-bold truncate">
                  ₹{(result?.working_capital_required || 190000).toLocaleString('en-IN')}
                </strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500 text-[10px] sm:text-[11px] block font-medium truncate">Total Interest</span>
                <strong className="text-slate-800 font-mono text-xs sm:text-sm mt-0.5 block font-bold truncate">
                  ₹{(result?.total_interest_payable || 230000).toLocaleString('en-IN')}
                </strong>
              </div>
            </div>
          </div>

          {/* Scheme Comparison Leaderboard */}
          <div className="glass-panel p-4 sm:p-6 space-y-3 bg-white shadow-card border border-slate-200">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Award className="w-4 h-4 text-sovereign-700 shrink-0" />
              <span>Ranked Scheme Options for Selected Outlay</span>
            </h3>

            <div className="space-y-2">
              {(result?.ranked_schemes || []).map((s, idx) => (
                <div
                  key={s.scheme_id || idx}
                  className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs transition-all ${
                    idx === 0
                      ? 'bg-sovereign-50 border-2 border-sovereign-700 shadow-sm'
                      : s.eligible
                      ? 'bg-white border-slate-200 shadow-subtle'
                      : 'bg-slate-50 border-slate-200 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className="w-6 h-6 rounded-full bg-sovereign-100 text-sovereign-800 font-bold flex items-center justify-center text-xs shrink-0">
                      {idx + 1}
                    </span>
                    <div>
                      <strong className="text-slate-900 font-bold">{s.scheme_id}</strong>
                      <span className="text-slate-500 text-[11px] ml-2 font-medium">({s.scheme_name || s.full_name})</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between sm:justify-end gap-2 sm:gap-4 text-left sm:text-right">
                    <div>
                      <span className="text-[10px] text-slate-500 block font-medium">Financial Incentive</span>
                      <strong className="font-mono text-emerald-700 font-bold block text-xs">
                        {s.subsidy_grant_amount > 0 
                          ? `₹${Math.round(s.subsidy_grant_amount).toLocaleString('en-IN')} Grant` 
                          : s.interest_savings_amount > 0 || s.benefit_type === 'INTEREST_SUBVENTION'
                          ? `${(11.0 - (s.effective_interest_rate_pct || 11.0)).toFixed(1)}% Subvention`
                          : s.eligible
                          ? 'Collateral-Free Credit'
                          : '₹0 (Ineligible)'}
                      </strong>
                    </div>
                    <div className="shrink-0 min-w-[80px]">
                      <span className="text-[10px] text-slate-500 block font-medium">Status</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md whitespace-nowrap inline-block ${
                        s.eligible 
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' 
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}>
                        {s.eligible 
                          ? 'Eligible' 
                          : s.ineligibility_reason?.toLowerCase().includes('exceeds')
                          ? 'Cap Exceeded'
                          : s.ineligibility_reason?.toLowerCase().includes('category')
                          ? 'Category Limit'
                          : 'Ineligible'}
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
export default CalculatorPage;
