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
    <div className="bg-slate-900/95 border border-slate-700/80 rounded-xl p-3.5 shadow-2xl backdrop-blur-md text-xs max-w-xs">
      <div className="font-bold text-white mb-1.5 flex items-center justify-between">
        <span>{data.full_name || label}</span>
        {data.collateral_free && (
          <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono text-[10px]">
            Collateral-Free
          </span>
        )}
      </div>
      <div className="space-y-1.5 text-slate-300">
        <div className="flex justify-between">
          <span className="text-emerald-400">Capital Subsidy Grant:</span>
          <span className="font-mono font-bold text-white">₹{data.subsidy.toLocaleString('en-IN')}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-amber-400">Total Interest Cost:</span>
          <span className="font-mono font-bold text-white">₹{data.interest.toLocaleString('en-IN')}</span>
        </div>
        <div className="flex justify-between pt-1 border-t border-slate-800">
          <span className="text-cyan-400 font-bold">Net Financial Benefit:</span>
          <span className="font-mono font-bold text-cyan-300">₹{data.netBenefit.toLocaleString('en-IN')}</span>
        </div>
        <div className="text-[10px] text-slate-400">
          Interest Rate: <strong className="text-slate-200">{data.rate}% p.a.</strong>
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
    <div className="glass-panel p-6 border-slate-800 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5 mb-1">
              <Award className="w-3.5 h-3.5" />
              Government Scheme Incentive Optimizer
            </div>
            <h3 className="text-lg font-outfit font-bold text-white">
              Subsidy vs. Interest & Net Benefit
            </h3>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono">
            Top {chartData.length} Schemes
          </span>
        </div>
        <p className="text-xs text-slate-400 mb-4">
          Compares upfront capital subsidy grant against cumulative interest repayment to maximize promoter savings.
        </p>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
            <YAxis
              stroke="#94a3b8"
              fontSize={11}
              tickFormatter={(v) => `₹${(v / 100000).toFixed(1)}L`}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
              formatter={(value) => <span className="text-slate-300">{value}</span>}
            />
            <Bar name="Capital Subsidy (₹)" dataKey="subsidy" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Bar name="Total Interest (₹)" dataKey="interest" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            <Bar name="Net Benefit (₹)" dataKey="netBenefit" fill="#06b6d4" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="text-[10px] text-slate-500 pt-3 border-t border-slate-800/80 flex items-center justify-between">
        <span className="flex items-center gap-1">
          <ShieldCheck className="w-3 h-3 text-emerald-400" />
          Schemes ranked by Net Financial Benefit (Subsidy Grant - Total Interest)
        </span>
        <span className="font-mono text-slate-400">PMEGP • PMFME • MUDRA • Stand-Up</span>
      </div>
    </div>
  );
}
export default SchemeComparisonChart;
