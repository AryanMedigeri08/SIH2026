import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Award, CheckCircle, ShieldCheck } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-xs max-w-xs">
      <div className="font-bold text-slate-900 mb-1.5 flex items-center justify-between">
        <span>{data.full_name || label}</span>
        {data.collateral_free && (
          <span className="px-2 py-0.5 rounded bg-sovereign-50 text-sovereign-800 border border-sovereign-200 font-mono text-[10px]">
            Collateral-Free
          </span>
        )}
      </div>
      <div className="space-y-1.5 text-slate-700">
        <div className="flex justify-between">
          <span className="text-emerald-700 font-semibold">Capital Subsidy Grant:</span>
          <span className="font-mono font-bold text-slate-900">₹{data.subsidy.toLocaleString('en-IN')}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-amber-700 font-semibold">Total Interest Cost:</span>
          <span className="font-mono font-bold text-slate-900">₹{data.interest.toLocaleString('en-IN')}</span>
        </div>
        <div className="flex justify-between pt-1 border-t border-slate-200">
          <span className="text-sovereign-800 font-bold">Net Financial Benefit:</span>
          <span className="font-mono font-bold text-sovereign-900">₹{data.netBenefit.toLocaleString('en-IN')}</span>
        </div>
        <div className="text-[10px] text-slate-500">
          Interest Rate: <strong className="text-slate-700">{data.rate}% p.a.</strong>
        </div>
      </div>
    </div>
  );
};

export function SchemeComparisonChart({ schemes }) {
  const schemeList = schemes || [];

  const chartData = React.useMemo(() => {
    return schemeList.slice(0, 4).map((s) => ({
      name: s.scheme_id,
      full_name: s.full_name,
      subsidy: Number(s.subsidy_grant_amount || 0),
      interest: Number(s.total_interest_payable || 0),
      netBenefit: Number(s.net_financial_benefit || 0),
      rate: s.effective_interest_rate_pct || 9.5,
      collateral_free: Boolean(s.collateral_free),
      eligible: Boolean(s.eligible),
    }));
  }, [schemeList]);

  if (!chartData.length) return null;

  return (
    <div className="glass-panel p-6 border-slate-200 flex flex-col justify-between bg-white shadow-card">
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
              <Award className="w-3.5 h-3.5" />
              Government Scheme Incentive Optimizer
            </div>
            <h3 className="text-lg font-outfit font-bold text-slate-900">
              Subsidy vs. Interest & Net Benefit
            </h3>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-lg bg-sovereign-50 border border-sovereign-200 text-sovereign-800 font-mono font-semibold">
            Top {chartData.length} Schemes
          </span>
        </div>
        <p className="text-xs text-slate-600 mb-4">
          Compares upfront capital subsidy grant against cumulative interest repayment to maximize promoter savings.
        </p>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="name" stroke="#334155" fontSize={11} tickLine={false} />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickFormatter={(v) => `₹${(v / 100000).toFixed(1)}L`}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
              formatter={(value) => <span className="text-slate-700 font-semibold">{value}</span>}
            />
            <Bar name="Capital Subsidy (₹)" dataKey="subsidy" fill="#059669" radius={[4, 4, 0, 0]} />
            <Bar name="Total Interest (₹)" dataKey="interest" fill="#d97706" radius={[4, 4, 0, 0]} />
            <Bar name="Net Benefit (₹)" dataKey="netBenefit" fill="#0b3b60" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="text-[10px] text-slate-500 pt-3 border-t border-slate-200 flex items-center justify-between">
        <span className="flex items-center gap-1 text-slate-600">
          <ShieldCheck className="w-3 h-3 text-emerald-600" />
          Schemes ranked by Net Financial Benefit (Subsidy Grant - Total Interest)
        </span>
        <span className="font-mono text-slate-500 font-medium">PMEGP • PMFME • MUDRA • Stand-Up</span>
      </div>
    </div>
  );
}
export default SchemeComparisonChart;
