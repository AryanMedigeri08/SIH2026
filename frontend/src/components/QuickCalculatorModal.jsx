import React, { useState } from 'react';
import { Calculator, X, Sparkles, TrendingUp } from 'lucide-react';
import { calculateFinancials } from '../services/api';

export function QuickCalculatorModal({ isOpen, onClose }) {
  const [cost, setCost] = useState(1000000);
  const [turnover, setTurnover] = useState(1500000);
  const [tenure, setTenure] = useState(7);
  const [moratorium, setMoratorium] = useState(6);
  const [promoterCategory, setPromoterCategory] = useState('general');
  const [sector, setSector] = useState('dairy');
  const [isRural, setIsRural] = useState(true);
  const [calcResult, setCalcResult] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0b1120] border border-cyan-500/30 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden my-8">
        
        {/* Header */}
        <div className="bg-slate-900/90 px-6 py-4 border-b border-slate-800 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
              <Calculator className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-base font-bold text-white font-outfit">Instant DSCR & Loan Sizing Calculator</h2>
              <p className="text-[11px] text-slate-400">Deterministic banking underwriting calculator</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleCompute} className="p-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Project Cost (₹)</label>
              <input
                type="number"
                min={25000}
                step={5000}
                value={cost}
                onChange={e => setCost(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Annual Turnover (₹)</label>
              <input
                type="number"
                min={25000}
                step={5000}
                value={turnover}
                onChange={e => setTurnover(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Loan Tenure (Years)</label>
              <input
                type="number"
                min={1}
                max={15}
                step={0.5}
                value={tenure}
                onChange={e => setTenure(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Moratorium (Months)</label>
              <input
                type="number"
                min={0}
                max={24}
                value={moratorium}
                onChange={e => setMoratorium(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-xs font-bold text-white shadow-glow transition"
          >
            {loading ? 'Calculating Math...' : 'Compute Instant Loan Metrics'}
          </button>

          {/* Results Display */}
          {calcResult && (
            <div className="mt-4 p-4 rounded-xl bg-slate-900/90 border border-cyan-500/30 space-y-3 animate-in fade-in">
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-white">Debt Service Coverage (DSCR):</span>
                <span className="text-base font-outfit font-extrabold text-cyan-400 font-mono">
                  {calcResult.dscr?.dscr?.toFixed(2)}x ({calcResult.dscr?.verdict})
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-slate-300">
                <div>Monthly EMI: <strong className="font-mono text-white">₹{Math.round(calcResult.amortization?.monthly_emi || 0).toLocaleString('en-IN')}</strong></div>
                <div>Principal Loan: <strong className="font-mono text-white">₹{Math.round(calcResult.loan_principal || 0).toLocaleString('en-IN')}</strong></div>
                <div>Promoter Margin: <strong className="font-mono text-cyan-300">₹{Math.round(calcResult.promoter_margin_amount || 0).toLocaleString('en-IN')}</strong></div>
                <div>Top Subsidy: <strong className="font-mono text-emerald-400">₹{Math.round(calcResult.top_scheme?.subsidy_grant_amount || 0).toLocaleString('en-IN')}</strong></div>
              </div>
            </div>
          )}
        </form>

      </div>
    </div>
  );
}
