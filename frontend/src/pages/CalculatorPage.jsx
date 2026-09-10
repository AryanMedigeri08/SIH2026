import React, { useState, useEffect, useMemo } from 'react';
import { 
  Calculator, Coins, ShieldCheck, CheckCircle2, TrendingUp, 
  Award, ArrowRight, Percent, Clock, AlertTriangle, Calendar,
  ChevronDown, ChevronUp, Layers, HelpCircle, ArrowUpRight, Check
} from 'lucide-react';
import { calculateFinancials } from '../services/api';
import { TranslatedText } from '../components/TranslatedText';

export function CalculatorPage() {
  // Input mode: 'margin' (Margin Capital 10%) or 'cost' (Total Project Cost)
  const [inputMode, setInputMode] = useState('margin');
  
  // Available Margin Money in hand (Default: Rs 1,00,000 for Rs 10,00,000 enterprise as per problem statement)
  const [marginMoney, setMarginMoney] = useState(100000);

  const [params, setParams] = useState({
    project_cost: 1000000,
    annual_turnover: 1200000,
    business_category: 'manufacturing',
    sector: 'dairy',
    promoter_category: 'general',
    is_rural: true,
    tenure_years: 7,
    moratorium_months: 6,
    interest_rate_pct: 8.0,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('quarterly'); // 'quarterly' | 'monthly' | 'ranking'
  const [showAllQuarters, setShowAllQuarters] = useState(false);

  // Quick Margin Money Presets for Rural Entrepreneurs
  const marginPresets = [
    { label: '₹14,000 (Micro Fin Max)', margin: 14000, cost: 140000, tenure: 3, morat: 3, rate: 6.5, scheme: 'Micro Finance' },
    { label: '₹50,000 (Small Unit)', margin: 50000, cost: 500000, tenure: 5, morat: 6, rate: 8.0, scheme: 'Term Loan' },
    { label: '₹1,00,000 (Standard ₹10L)', margin: 100000, cost: 1000000, tenure: 7, morat: 6, rate: 8.0, scheme: 'Term Loan' },
    { label: '₹2,50,000 (₹25L Outlay)', margin: 250000, cost: 2500000, tenure: 7, morat: 6, rate: 8.0, scheme: 'Term Loan' },
    { label: '₹5,00,000 (Term Loan Max)', margin: 500000, cost: 5000000, tenure: 7, morat: 6, rate: 8.0, scheme: 'Term Loan' },
  ];

  // Recalculate whenever params change (with debounce)
  useEffect(() => {
    const timer = setTimeout(async () => {
      setLoading(true);
      const res = await calculateFinancials(params);
      setResult(res);
      setLoading(false);
    }, 200);

    return () => clearTimeout(timer);
  }, [params]);

  // Handlers for switching and syncing input modes
  const handleMarginChange = (newMargin) => {
    const marginVal = Math.max(5000, Number(newMargin));
    setMarginMoney(marginVal);
    const calculatedCost = Math.round(marginVal * 10);
    
    // Auto-adjust scheme defaults based on government limits
    if (calculatedCost <= 140000) {
      setParams(prev => ({
        ...prev,
        project_cost: calculatedCost,
        tenure_years: 3,
        moratorium_months: 3,
        interest_rate_pct: 6.5,
      }));
    } else if (calculatedCost <= 5000000) {
      setParams(prev => ({
        ...prev,
        project_cost: calculatedCost,
        tenure_years: 7,
        moratorium_months: 6,
        interest_rate_pct: 8.0,
      }));
    } else {
      setParams(prev => ({
        ...prev,
        project_cost: calculatedCost,
        tenure_years: 7,
        moratorium_months: 6,
        interest_rate_pct: 9.5,
      }));
    }
  };

  const handleCostChange = (newCost) => {
    const costVal = Math.max(50000, Number(newCost));
    setParams(prev => ({ ...prev, project_cost: costVal }));
    setMarginMoney(Math.round(costVal * 0.10));
  };

  const updateParam = (key, value) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  const applySchemePreset = (preset) => {
    setMarginMoney(preset.margin);
    setParams(prev => ({
      ...prev,
      project_cost: preset.cost,
      tenure_years: preset.tenure,
      moratorium_months: preset.morat,
      interest_rate_pct: preset.rate,
    }));
  };

  const applyConcessionalTerms = (schemeType) => {
    if (schemeType === 'micro') {
      setParams(prev => ({
        ...prev,
        tenure_years: 3,
        moratorium_months: 3,
        interest_rate_pct: 6.5,
      }));
    } else {
      setParams(prev => ({
        ...prev,
        tenure_years: 7,
        moratorium_months: 6,
        interest_rate_pct: 8.0,
      }));
    }
  };

  // Scheme auto-routing tier
  const isMicroFinance = params.project_cost <= 140000;
  const isTermLoan = params.project_cost > 140000 && params.project_cost <= 5000000;
  const isMegaProject = params.project_cost > 5000000;

  const dscr = result?.dscr || 2.26;
  const isViable = dscr >= 1.33;
  const isCaution = dscr >= 1.0 && dscr < 1.33;

  const effectiveLoanPrincipal = result?.loan_principal ?? Math.round(params.project_cost * 0.90);

  // Generate Deterministic Quarterly Repayment Schedule (SCA Scheme Mandate)
  const quarterlyAmortization = useMemo(() => {
    const principal = Math.max(effectiveLoanPrincipal, 1000);
    const annualRate = params.interest_rate_pct;
    const tenureYears = params.tenure_years;
    const moratoriumMonths = params.moratorium_months;

    const totalMonths = Math.round(tenureYears * 12);
    const totalQuarters = Math.round(totalMonths / 3);
    const moratoriumQuarters = Math.floor(moratoriumMonths / 3);
    const repaymentQuarters = Math.max(1, totalQuarters - moratoriumQuarters);
    const quarterlyRate = (annualRate / 100) / 4;

    // Standard quarterly installment for repayment period
    let quarterlyEmi = 0;
    if (quarterlyRate > 0) {
      const factor = Math.pow(1 + quarterlyRate, repaymentQuarters);
      quarterlyEmi = principal * (quarterlyRate * factor) / (factor - 1);
    } else {
      quarterlyEmi = principal / repaymentQuarters;
    }

    let balance = principal;
    const rows = [];
    let totalInterest = 0;

    for (let q = 1; q <= totalQuarters; q++) {
      const isMoratorium = q <= moratoriumQuarters;
      const opening = balance;

      if (isMoratorium) {
        const interest = opening * quarterlyRate;
        totalInterest += interest;
        rows.push({
          quarter: q,
          isMoratorium: true,
          openingBalance: opening,
          principalPaid: 0,
          interestPaid: interest,
          totalInstallment: interest,
          closingBalance: opening,
        });
      } else {
        const interest = opening * quarterlyRate;
        totalInterest += interest;
        let principalPaid = quarterlyEmi - interest;
        if (q === totalQuarters || principalPaid > opening) {
          principalPaid = opening;
        }
        balance = Math.max(0, opening - principalPaid);
        rows.push({
          quarter: q,
          isMoratorium: false,
          openingBalance: opening,
          principalPaid: principalPaid,
          interestPaid: interest,
          totalInstallment: principalPaid + interest,
          closingBalance: balance,
        });
      }
    }

    return {
      totalQuarters,
      moratoriumQuarters,
      repaymentQuarters,
      quarterlyEmi,
      totalInterest,
      totalRepayment: principal + totalInterest,
      rows,
    };
  }, [effectiveLoanPrincipal, params.interest_rate_pct, params.tenure_years, params.moratorium_months]);

  const displayedRows = showAllQuarters 
    ? quarterlyAmortization.rows 
    : quarterlyAmortization.rows.slice(0, 6);

  return (
    <div className="max-w-7xl mx-auto px-3.5 sm:px-6 lg:px-8 py-4 sm:py-8 space-y-5 sm:space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-4 sm:p-6 border-l-4 border-sovereign-800 bg-white shadow-card border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-sovereign-700 mb-1 flex items-center gap-1.5">
            <Calculator className="w-4 h-4" />
            <TranslatedText text="Concessional Credit Sizing & Scheme Auto-Router" />
          </div>
          <h1 className="text-xl sm:text-2xl font-outfit font-extrabold text-slate-900">
            <TranslatedText text="Smart Scheme Calculator & Quarterly Amortization Engine" />
          </h1>
          <p className="text-xs text-slate-600 mt-1 max-w-2xl font-medium">
            <TranslatedText text="Input your available 10% margin capital to auto-size total enterprise outlay, route to Micro Finance vs. Term Loan concessional schemes, and inspect full quarterly repayment schedules with moratorium grace periods." />
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Active Scheme Badge */}
          <span className={`text-xs font-bold px-3 py-1.5 rounded-full border flex items-center gap-1.5 ${
            isMicroFinance 
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : isTermLoan
              ? 'bg-sky-50 border-sky-200 text-sky-800'
              : 'bg-indigo-50 border-indigo-200 text-indigo-800'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isMicroFinance ? 'bg-emerald-600' : isTermLoan ? 'bg-sky-600' : 'bg-indigo-600'}`} />
            <TranslatedText text={isMicroFinance ? "Micro Finance Scheme (≤ ₹1.40L)" : isTermLoan ? "Term Loan Scheme (₹1.40L - ₹50L)" : "Mega MSME Credit Tier"} />
          </span>

          <span className={`text-xs font-bold px-3 py-1.5 rounded-full border flex items-center gap-1.5 ${
            isViable
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : isCaution
              ? 'bg-amber-50 border-amber-200 text-amber-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isViable ? 'bg-emerald-600' : isCaution ? 'bg-amber-600' : 'bg-rose-600'}`} />
            <span>DSCR: {dscr.toFixed(2)} (<TranslatedText text={result?.dscr_verdict || 'VIABLE'} />)</span>
          </span>
        </div>
      </div>

      {/* Scheme Auto-Routing Banner */}
      <div className={`p-4 sm:p-5 rounded-2xl border transition-all ${
        isMicroFinance 
          ? 'bg-gradient-to-r from-emerald-50/80 via-white to-emerald-50/40 border-emerald-300 shadow-sm'
          : isTermLoan
          ? 'bg-gradient-to-r from-sky-50/80 via-white to-sky-50/40 border-sky-300 shadow-sm'
          : 'bg-gradient-to-r from-indigo-50/80 via-white to-indigo-50/40 border-indigo-300 shadow-sm'
      }`}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className={`text-[11px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-md text-white ${
                isMicroFinance ? 'bg-emerald-700' : isTermLoan ? 'bg-sky-700' : 'bg-indigo-700'
              }`}>
                <TranslatedText text="Government Scheme Match" />
              </span>
              <span className="text-xs font-bold text-slate-900">
                {isMicroFinance && <TranslatedText text="Micro Finance Scheme — SCA Concessional Tier" />}
                {isTermLoan && <TranslatedText text="Term Loan Scheme — State Channelizing Agency Concessional Tier" />}
                {isMegaProject && <TranslatedText text="Mega MSME Tier — Multi-Scheme Commercial & Credit Guarantee" />}
              </span>
            </div>
            <p className="text-xs text-slate-600">
              {isMicroFinance && (
                <TranslatedText text="Eligible for small units with project cost up to ₹1.40 Lakh. SCA/CA provides up to 90% (max ₹1.25 Lakh) at 6.5% p.a. interest, 3 years tenure, including a 3-month moratorium." />
              )}
              {isTermLoan && (
                <TranslatedText text="Eligible for larger projects up to ₹50.00 Lakh. SCA/CA provides up to 90% (max ₹45.00 Lakh) at 8.0% p.a. interest, up to 7 years tenure, including a 6-month moratorium." />
              )}
              {isMegaProject && (
                <TranslatedText text="For capital outlay exceeding ₹50.00 Lakh. Qualifies for Prime Minister's Employment Generation Programme (PMEGP 25%-35% subsidy) and CGTMSE collateral-free cover." />
              )}
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-2">
            {isMicroFinance && (params.interest_rate_pct !== 6.5 || params.tenure_years !== 3 || params.moratorium_months !== 3) && (
              <button
                type="button"
                onClick={() => applyConcessionalTerms('micro')}
                className="px-3 py-1.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs shadow-sm transition flex items-center gap-1.5"
              >
                <Check className="w-3.5 h-3.5" />
                <TranslatedText text="Apply 6.5% • 3 Yr • 3 Mo Micro Terms" />
              </button>
            )}
            {isTermLoan && (params.interest_rate_pct !== 8.0 || params.tenure_years !== 7 || params.moratorium_months !== 6) && (
              <button
                type="button"
                onClick={() => applyConcessionalTerms('term')}
                className="px-3 py-1.5 rounded-xl bg-sky-700 hover:bg-sky-800 text-white font-bold text-xs shadow-sm transition flex items-center gap-1.5"
              >
                <Check className="w-3.5 h-3.5" />
                <TranslatedText text="Apply 8.0% • 7 Yr • 6 Mo Term Terms" />
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Form Column (Inputs) */}
        <div className="lg:col-span-5 glass-panel p-4 sm:p-6 space-y-5 bg-white shadow-card border border-slate-200">
          
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Coins className="w-4 h-4 text-sovereign-700" />
              <TranslatedText text="1. Capital & Scheme Parameters" />
            </h3>

            {/* Input Mode Selector Toggle */}
            <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-[11px] font-semibold">
              <button
                type="button"
                onClick={() => setInputMode('margin')}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  inputMode === 'margin'
                    ? 'bg-sovereign-800 text-white shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <TranslatedText text="Available Margin (10%)" />
              </button>
              <button
                type="button"
                onClick={() => setInputMode('cost')}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  inputMode === 'cost'
                    ? 'bg-sovereign-800 text-white shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <TranslatedText text="Total Outlay" />
              </button>
            </div>
          </div>

          {/* Available Margin Money Input Mode */}
          {inputMode === 'margin' ? (
            <div className="space-y-3 p-3.5 rounded-xl bg-amber-50/60 border border-amber-200">
              <div className="flex justify-between items-center text-xs">
                <div>
                  <label className="text-slate-900 font-bold block">
                    <TranslatedText text="Your Available Cash Margin (10% Contribution)" />
                  </label>
                  <span className="text-[11px] text-slate-500">
                    <TranslatedText text="How much cash can you invest right now?" />
                  </span>
                </div>
                <span className="text-amber-800 font-mono font-bold text-base">
                  ₹{marginMoney.toLocaleString('en-IN')}
                </span>
              </div>

              <input
                type="range"
                min={5000}
                max={600000}
                step={5000}
                value={marginMoney}
                onChange={(e) => handleMarginChange(e.target.value)}
                className="w-full accent-amber-600 cursor-pointer"
              />

              {/* Sizing Math Note */}
              <div className="p-2.5 rounded-lg bg-white border border-amber-200 text-xs flex items-center justify-between">
                <div>
                  <span className="text-slate-500 text-[10px] block uppercase font-bold">
                    <TranslatedText text="Auto-Sized Project Cost (10× Margin)" />
                  </span>
                  <strong className="text-slate-900 font-mono text-sm">
                    ₹{params.project_cost.toLocaleString('en-IN')}
                  </strong>
                </div>
                <div className="text-right">
                  <span className="text-slate-500 text-[10px] block uppercase font-bold">
                    <TranslatedText text="Concessional Loan (90%)" />
                  </span>
                  <strong className="text-emerald-700 font-mono text-sm">
                    ₹{Math.round(params.project_cost * 0.90).toLocaleString('en-IN')}
                  </strong>
                </div>
              </div>

              {/* Quick Presets */}
              <div className="space-y-1.5 pt-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  <TranslatedText text="Quick Government Tier Presets:" />
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {marginPresets.map((p, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => applySchemePreset(p)}
                      className={`text-[10px] font-semibold px-2 py-1 rounded-md border transition-all ${
                        marginMoney === p.margin
                          ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
                          : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Total Project Outlay Mode */
            <div className="space-y-2 p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <div className="flex justify-between text-xs">
                <div>
                  <label className="text-slate-900 font-bold block">
                    <TranslatedText text="Total Enterprise Capital Outlay" />
                  </label>
                  <span className="text-[11px] text-slate-500">
                    <TranslatedText text="Full machinery, civil works & initial stock" />
                  </span>
                </div>
                <span className="text-sovereign-800 font-mono font-bold text-base">
                  ₹{params.project_cost.toLocaleString('en-IN')}
                </span>
              </div>
              <input
                type="range"
                min={50000}
                max={10000000}
                step={25000}
                value={params.project_cost}
                onChange={(e) => handleCostChange(e.target.value)}
                className="w-full accent-sovereign-800 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>₹50K</span>
                <span>₹1.40L (Micro Tier)</span>
                <span>₹50L (Term Tier)</span>
                <span>₹1 Cr</span>
              </div>

              <div className="p-2 rounded-lg bg-white border border-slate-200 text-xs flex justify-between items-center mt-2">
                <span className="text-slate-600">
                  <TranslatedText text="Required 10% Margin Cash:" />
                </span>
                <strong className="font-mono text-amber-700 font-bold">
                  ₹{Math.round(params.project_cost * 0.10).toLocaleString('en-IN')}
                </strong>
              </div>
            </div>
          )}

          {/* Annual Turnover Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label className="text-slate-700 font-bold">
                <TranslatedText text="Estimated Annual Turnover (₹)" />
              </label>
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
              <label className="text-slate-700 font-bold">
                <TranslatedText text="Sector" />
              </label>
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
              <label className="text-slate-700 font-bold">
                <TranslatedText text="Promoter Category" />
              </label>
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
              <span className="font-bold text-slate-900 block">
                <TranslatedText text="Enterprise Location Type" />
              </span>
              <span className="text-slate-500 text-[11px] font-medium">
                {params.is_rural ? (
                  <TranslatedText text="Rural (35% Special / 25% Gen Subsidy)" />
                ) : (
                  <TranslatedText text="Urban (25% Special / 15% Gen Subsidy)" />
                )}
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
              <TranslatedText text={params.is_rural ? 'Rural' : 'Urban'} />
            </button>
          </div>

          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-200 pb-2 pt-2 flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-sovereign-700" />
            <TranslatedText text="2. Bank Financing & Amortization" />
          </h3>

          {/* Loan Tenure & Moratorium */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="space-y-1">
              <label className="text-slate-700 font-bold">
                <TranslatedText text={`Tenure (${params.tenure_years} Years)`} />
              </label>
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
              <label className="text-slate-700 font-bold">
                <TranslatedText text={`Moratorium (${params.moratorium_months} Mo.)`} />
              </label>
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
              <label className="text-slate-700 font-bold">
                <TranslatedText text="Concessional / Bank Interest Rate (% p.a.)" />
              </label>
              <span className="font-mono text-sovereign-800 font-bold">{params.interest_rate_pct}%</span>
            </div>
            <input
              type="range"
              min={6.0}
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
                  <TranslatedText text="Optimal Financing Vehicle" />
                </span>
                <h2 className="text-base sm:text-xl font-bold font-outfit text-slate-900 mt-1">
                  {result?.top_scheme_id || (isMicroFinance ? 'MARGIN_MONEY_MICRO_FINANCE' : 'MARGIN_MONEY_TERM_LOAN')} — {result?.top_scheme_name || (isMicroFinance ? 'Margin Money Micro Finance Scheme' : 'Margin Money Term Loan Scheme')}
                </h2>
              </div>

              <div className="text-left sm:text-right">
                <span className="text-[10px] text-slate-500 font-medium block">
                  <TranslatedText text="Capital Subsidy / Benefit" />
                </span>
                <strong className="text-xl sm:text-2xl font-mono font-extrabold text-emerald-700">
                  {result?.subsidy_grant_amount > 0 
                    ? `₹${(result.subsidy_grant_amount).toLocaleString('en-IN')}` 
                    : isMicroFinance 
                    ? '6.5% Concessional' 
                    : '8.0% Concessional'}
                </strong>
              </div>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 pt-2">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500 text-[10px] sm:text-[11px] block font-medium truncate">
                  <TranslatedText text="Net Bank Loan (90%)" />
                </span>
                <strong className="text-slate-900 font-mono text-xs sm:text-sm mt-0.5 block font-bold truncate">
                  ₹{Math.round(effectiveLoanPrincipal).toLocaleString('en-IN')}
                </strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500 text-[10px] sm:text-[11px] block font-medium truncate">
                  <TranslatedText text="Quarterly Installment" />
                </span>
                <strong className="text-sovereign-800 font-mono text-xs sm:text-sm mt-0.5 block font-bold truncate">
                  ₹{Math.round(quarterlyAmortization.quarterlyEmi).toLocaleString('en-IN')}
                </strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500 text-[10px] sm:text-[11px] block font-medium truncate">
                  <TranslatedText text="Monthly EMI" />
                </span>
                <strong className="text-blue-900 font-mono text-xs sm:text-sm mt-0.5 block font-bold truncate">
                  ₹{(result?.monthly_emi || Math.round(quarterlyAmortization.quarterlyEmi / 3)).toLocaleString('en-IN')}
                </strong>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500 text-[10px] sm:text-[11px] block font-medium truncate">
                  <TranslatedText text="Total Interest" />
                </span>
                <strong className="text-slate-800 font-mono text-xs sm:text-sm mt-0.5 block font-bold truncate">
                  ₹{Math.round(quarterlyAmortization.totalInterest).toLocaleString('en-IN')}
                </strong>
              </div>
            </div>
          </div>

          {/* Schedule & Rankings Tab Selector */}
          <div className="glass-panel p-4 sm:p-6 space-y-4 bg-white shadow-card border border-slate-200">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-sovereign-800" />
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                  <TranslatedText text="Repayment & Underwriting Intelligence" />
                </h3>
              </div>

              {/* Navigation Tabs */}
              <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-bold">
                <button
                  type="button"
                  onClick={() => setActiveTab('quarterly')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    activeTab === 'quarterly'
                      ? 'bg-sovereign-800 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <TranslatedText text="Quarterly Schedule (SCA Mandate)" />
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('ranking')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    activeTab === 'ranking'
                      ? 'bg-sovereign-800 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <TranslatedText text="Scheme Options Leaderboard" />
                </button>
              </div>
            </div>

            {/* Tab 1: Interactive Quarterly Repayment Schedule */}
            {activeTab === 'quarterly' && (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-600">
                  <div className="flex items-center gap-3">
                    <span>
                      <strong className="text-slate-900">{quarterlyAmortization.totalQuarters}</strong> <TranslatedText text="Total Quarters" />
                    </span>
                    <span className="text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-medium">
                      {quarterlyAmortization.moratoriumQuarters} <TranslatedText text="Moratorium Quarters (Grace Period)" />
                    </span>
                  </div>

                  <span className="text-[11px] text-slate-500 font-mono">
                    <TranslatedText text="Interest Rate:" /> {params.interest_rate_pct}% p.a.
                  </span>
                </div>

                {/* Table */}
                <div className="overflow-x-auto border border-slate-200 rounded-xl">
                  <table className="w-full text-left text-xs text-slate-700">
                    <thead className="bg-slate-50 text-slate-900 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                      <tr>
                        <th className="py-2.5 px-3"><TranslatedText text="Quarter" /></th>
                        <th className="py-2.5 px-3"><TranslatedText text="Type" /></th>
                        <th className="py-2.5 px-3 font-mono text-right"><TranslatedText text="Opening Balance" /></th>
                        <th className="py-2.5 px-3 font-mono text-right"><TranslatedText text="Principal" /></th>
                        <th className="py-2.5 px-3 font-mono text-right"><TranslatedText text="Interest" /></th>
                        <th className="py-2.5 px-3 font-mono text-right"><TranslatedText text="Installment" /></th>
                        <th className="py-2.5 px-3 font-mono text-right"><TranslatedText text="Closing Balance" /></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono">
                      {displayedRows.map((row) => (
                        <tr 
                          key={row.quarter}
                          className={row.isMoratorium ? 'bg-amber-50/40 hover:bg-amber-50/70' : 'hover:bg-slate-50'}
                        >
                          <td className="py-2 px-3 font-bold text-slate-900">
                            Q{row.quarter}
                          </td>
                          <td className="py-2 px-3">
                            {row.isMoratorium ? (
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200 font-sans">
                                <TranslatedText text="Moratorium" />
                              </span>
                            ) : (
                              <span className="text-[10px] font-medium text-slate-600 font-sans">
                                <TranslatedText text="Regular" />
                              </span>
                            )}
                          </td>
                          <td className="py-2 px-3 text-right">
                            ₹{Math.round(row.openingBalance).toLocaleString('en-IN')}
                          </td>
                          <td className="py-2 px-3 text-right font-bold text-emerald-700">
                            {row.isMoratorium ? '₹0' : `₹${Math.round(row.principalPaid).toLocaleString('en-IN')}`}
                          </td>
                          <td className="py-2 px-3 text-right text-rose-700">
                            ₹{Math.round(row.interestPaid).toLocaleString('en-IN')}
                          </td>
                          <td className="py-2 px-3 text-right font-bold text-slate-900 bg-slate-50/60">
                            ₹{Math.round(row.totalInstallment).toLocaleString('en-IN')}
                          </td>
                          <td className="py-2 px-3 text-right text-slate-600">
                            ₹{Math.round(row.closingBalance).toLocaleString('en-IN')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Show All / Show Less Toggle Button */}
                {quarterlyAmortization.rows.length > 6 && (
                  <div className="pt-1 text-center">
                    <button
                      type="button"
                      onClick={() => setShowAllQuarters(!showAllQuarters)}
                      className="text-xs font-bold text-sovereign-800 hover:text-sovereign-900 inline-flex items-center gap-1.5 py-1 px-3 rounded-lg hover:bg-slate-100 transition"
                    >
                      {showAllQuarters ? (
                        <>
                          <ChevronUp className="w-4 h-4" />
                          <TranslatedText text="Collapse to First 6 Quarters" />
                        </>
                      ) : (
                        <>
                          <ChevronDown className="w-4 h-4" />
                          <TranslatedText text={`View Full Schedule (${quarterlyAmortization.rows.length} Quarters)`} />
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Scheme Comparison Leaderboard */}
            {activeTab === 'ranking' && (
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
                        <span className="text-[10px] text-slate-500 block font-medium">
                          <TranslatedText text="Financial Incentive" />
                        </span>
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
                        <span className="text-[10px] text-slate-500 block font-medium">
                          <TranslatedText text="Status" />
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md whitespace-nowrap inline-block ${
                          s.eligible 
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' 
                            : 'bg-slate-100 text-slate-600 border border-slate-200'
                        }`}>
                          <TranslatedText text={
                            s.eligible 
                              ? 'Eligible' 
                              : s.ineligibility_reason?.toLowerCase().includes('exceeds')
                              ? 'Cap Exceeded'
                              : s.ineligibility_reason?.toLowerCase().includes('category')
                              ? 'Category Limit'
                              : 'Ineligible'
                          } />
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

          </div>

        </div>

      </div>

    </div>
  );
}

export default CalculatorPage;
