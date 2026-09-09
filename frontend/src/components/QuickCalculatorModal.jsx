import React, { useState } from 'react';
import { Calculator, X, Sparkles, TrendingUp, Coins, Check } from 'lucide-react';
import { calculateFinancials } from '../services/api';
import { TranslatedText } from './TranslatedText';

export function QuickCalculatorModal({ isOpen, onClose }) {
  const [inputMode, setInputMode] = useState('margin'); // 'margin' | 'cost'
  const [margin, setMargin] = useState(100000);
  const [cost, setCost] = useState(1000000);
  const [turnover, setTurnover] = useState(1200000);
  const [tenure, setTenure] = useState(7);
  const [moratorium, setMoratorium] = useState(6);
  const [promoterCategory, setPromoterCategory] = useState('general');
  const [sector, setSector] = useState('dairy');
  const [isRural, setIsRural] = useState(true);
  const [calcResult, setCalcResult] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleMarginChange = (val) => {
    const num = Math.max(1000, Number(val));
    setMargin(num);
    const computedCost = Math.round(num * 10);
    setCost(computedCost);
    if (computedCost <= 140000) {
      setTenure(3);
      setMoratorium(3);
    } else if (computedCost <= 5000000) {
      setTenure(7);
      setMoratorium(6);
    }
  };

  const handleCostChange = (val) => {
    const num = Math.max(10000, Number(val));
    setCost(num);
    setMargin(Math.round(num * 0.10));
    if (num <= 140000) {
      setTenure(3);
      setMoratorium(3);
    } else if (num <= 5000000) {
      setTenure(7);
      setMoratorium(6);
    }
  };

  const isMicroFinance = Number(cost) <= 140000;
  const isTermLoan = Number(cost) > 140000 && Number(cost) <= 5000000;

  const handleCompute = async (e) => {
    e.preventDefault();
    setLoading(true);
    const res = await calculateFinancials({
      project_cost: Number(cost),
      annual_turnover_estimate: Number(turnover),
      tenure_years: Number(tenure),
      moratorium_months: Number(moratorium),
      promoter_category: promoterCategory,
      sector: sector,
      is_rural: isRural,
      business_category: 'manufacturing',
    });
    setCalcResult(res);
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2.5 sm:p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden my-4 sm:my-8">
        
        {/* Header */}
        <div className="bg-slate-50 px-4 py-3 sm:px-6 sm:py-4 border-b border-slate-200 flex justify-between items-center gap-2">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-sovereign-50 text-sovereign-800 border border-sovereign-200 shrink-0">
              <Calculator className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-sm sm:text-base font-bold text-slate-900 font-outfit">
                <TranslatedText text="Instant DSCR & Concessional Loan Sizing" />
              </h2>
              <p className="text-[10px] sm:text-[11px] text-slate-500">
                <TranslatedText text="Deterministic banking underwriting & scheme router" />
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 shrink-0">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scheme Routing Badge */}
        <div className="px-4 pt-3 sm:px-6">
          <div className={`p-2.5 rounded-xl border flex items-center justify-between text-xs ${
            isMicroFinance 
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900' 
              : isTermLoan
              ? 'bg-sky-50 border-sky-200 text-sky-900'
              : 'bg-indigo-50 border-indigo-200 text-indigo-900'
          }`}>
            <div className="flex items-center gap-2 font-bold">
              <span className={`w-2 h-2 rounded-full ${isMicroFinance ? 'bg-emerald-600' : isTermLoan ? 'bg-sky-600' : 'bg-indigo-600'}`} />
              <TranslatedText text={
                isMicroFinance 
                  ? "Auto-Selected: Micro Finance Scheme (≤ ₹1.40L • 6.5% p.a.)"
                  : isTermLoan 
                  ? "Auto-Selected: Term Loan Scheme (₹1.40L - ₹50L • 8.0% p.a.)"
                  : "Commercial / CGTMSE Credit Tier (> ₹50L)"
              } />
            </div>
            <span className="text-[10px] font-semibold opacity-80">
              <TranslatedText text="SCA Tier" />
            </span>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleCompute} className="p-4 sm:p-6 space-y-4">
          
          {/* Input Mode Selector */}
          <div className="flex items-center justify-between bg-slate-100 p-1 rounded-xl text-xs font-bold">
            <button
              type="button"
              onClick={() => setInputMode('margin')}
              className={`flex-1 py-1.5 rounded-lg transition text-center ${
                inputMode === 'margin' ? 'bg-white text-sovereign-900 shadow-xs' : 'text-slate-600'
              }`}
            >
              <TranslatedText text="I have Margin Cash (10%)" />
            </button>
            <button
              type="button"
              onClick={() => setInputMode('cost')}
              className={`flex-1 py-1.5 rounded-lg transition text-center ${
                inputMode === 'cost' ? 'bg-white text-sovereign-900 shadow-xs' : 'text-slate-600'
              }`}
            >
              <TranslatedText text="I know Project Cost" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {inputMode === 'margin' ? (
              <div>
                <label className="block text-[11px] font-bold text-slate-700 mb-1">
                  <TranslatedText text="Available Margin Cash (₹)" />
                </label>
                <input
                  type="number"
                  min={5000}
                  step={5000}
                  value={margin}
                  onChange={e => handleMarginChange(e.target.value)}
                  className="w-full bg-amber-50/50 border border-amber-300 rounded-xl px-3.5 py-2 text-xs text-amber-900 font-mono font-bold focus:ring-2 focus:ring-amber-500"
                />
                <span className="text-[10px] text-slate-500 mt-0.5 block">
                  <TranslatedText text="Sizes Project Outlay to:" /> ₹{(margin * 10).toLocaleString('en-IN')}
                </span>
              </div>
            ) : (
              <div>
                <label className="block text-[11px] font-bold text-slate-700 mb-1">
                  <TranslatedText text="Project Cost (₹)" />
                </label>
                <input
                  type="number"
                  min={25000}
                  step={5000}
                  value={cost}
                  onChange={e => handleCostChange(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 font-mono focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600"
                />
                <span className="text-[10px] text-slate-500 mt-0.5 block">
                  <TranslatedText text="Requires 10% Margin:" /> ₹{Math.round(cost * 0.10).toLocaleString('en-IN')}
                </span>
              </div>
            )}

            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">
                <TranslatedText text="Annual Turnover (₹)" />
              </label>
              <input
                type="number"
                min={25000}
                step={5000}
                value={turnover}
                onChange={e => setTurnover(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 font-mono focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600"
              />
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">
                <TranslatedText text={`Loan Tenure (${tenure} Years)`} />
              </label>
              <input
                type="number"
                min={1}
                max={15}
                step={0.5}
                value={tenure}
                onChange={e => setTenure(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 font-mono focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600"
              />
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">
                <TranslatedText text={`Moratorium (${moratorium} Months)`} />
              </label>
              <input
                type="number"
                min={0}
                max={24}
                value={moratorium}
                onChange={e => setMoratorium(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 font-mono focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-sovereign-800 hover:bg-sovereign-700 text-xs font-bold text-white shadow-sm transition cursor-pointer"
          >
            {loading ? (
              <TranslatedText text="Calculating Math..." />
            ) : (
              <TranslatedText text="Compute Instant Loan Metrics" />
            )}
          </button>

          {/* Results Display */}
          {calcResult && (
            <div className="mt-4 p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 animate-in fade-in">
              <div className="flex flex-wrap justify-between items-center gap-1 border-b border-slate-200 pb-2">
                <span className="text-xs font-bold text-slate-900">
                  <TranslatedText text="Debt Service Coverage (DSCR):" />
                </span>
                <span className="text-base font-outfit font-extrabold text-sovereign-800 font-mono">
                  {calcResult.dscr?.dscr?.toFixed(2)}x (<TranslatedText text={calcResult.dscr?.verdict || 'VIABLE'} />)
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-700">
                <div>
                  <TranslatedText text="Monthly EMI:" /> <strong className="font-mono text-slate-900">₹{Math.round(calcResult.amortization?.monthly_emi || 0).toLocaleString('en-IN')}</strong>
                </div>
                <div>
                  <TranslatedText text="Concessional Loan (90%):" /> <strong className="font-mono text-slate-900">₹{Math.round(calcResult.loan_principal || (cost * 0.90)).toLocaleString('en-IN')}</strong>
                </div>
                <div>
                  <TranslatedText text="Promoter Margin (10%):" /> <strong className="font-mono text-amber-700">₹{Math.round(calcResult.promoter_margin_amount || (cost * 0.10)).toLocaleString('en-IN')}</strong>
                </div>
                <div>
                  <TranslatedText text="Top Subsidy / Benefit:" /> <strong className="font-mono text-emerald-700">{calcResult.top_scheme?.subsidy_grant_amount > 0 ? `₹${Math.round(calcResult.top_scheme.subsidy_grant_amount).toLocaleString('en-IN')}` : isMicroFinance ? '6.5% Concessional' : '8.0% Concessional'}</strong>
                </div>
              </div>
            </div>
          )}
        </form>

      </div>
    </div>
  );
}

export default QuickCalculatorModal;
