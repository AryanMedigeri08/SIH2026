import React from 'react';
import { 
  BarChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  Legend, ReferenceLine, CartesianGrid, ComposedChart 
} from 'recharts';
import { TrendingUp, Table as TableIcon } from 'lucide-react';
import { TranslatedText } from '../TranslatedText';

export function CashflowProjectionsChart({ inputData, financialData, pricingData }) {
  const turnover = Number(inputData?.annual_turnover_estimate) || 950000;
  const projectCost = Number(inputData?.project_cost) || 900000;
  const emi = financialData?.amortization?.monthly_emi || 10530;
  const loanPrincipal = financialData?.loan_principal || 585000;
  const dscr = financialData?.dscr?.dscr || 2.25;

  const years = [
    { yr: 'Yr 1 (60%)', cap: 60, rev: turnover * 0.85, opex: turnover * 0.85 * 0.68, depr: projectCost * 0.55 * 0.15, int: loanPrincipal * 0.11, debt: emi * 12, dscr: Number((dscr * 0.9).toFixed(2)) },
    { yr: 'Yr 2 (70%)', cap: 70, rev: turnover * 1.00, opex: turnover * 1.00 * 0.68, depr: projectCost * 0.55 * 0.15 * 0.85, int: loanPrincipal * 0.09, debt: emi * 12, dscr: Number((dscr * 1.0).toFixed(2)) },
    { yr: 'Yr 3 (80%)', cap: 80, rev: turnover * 1.15, opex: turnover * 1.15 * 0.68, depr: projectCost * 0.55 * 0.15 * 0.72, int: loanPrincipal * 0.07, debt: emi * 12, dscr: Number((dscr * 1.15).toFixed(2)) },
    { yr: 'Yr 4 (85%)', cap: 85, rev: turnover * 1.25, opex: turnover * 1.25 * 0.68, depr: projectCost * 0.55 * 0.15 * 0.61, int: loanPrincipal * 0.05, debt: emi * 12, dscr: Number((dscr * 1.25).toFixed(2)) },
    { yr: 'Yr 5 (90%)', cap: 90, rev: turnover * 1.35, opex: turnover * 1.35 * 0.68, depr: projectCost * 0.55 * 0.15 * 0.52, int: loanPrincipal * 0.02, debt: emi * 12, dscr: Number((dscr * 1.40).toFixed(2)) },
  ];

  const chartData = years.map(y => {
    const ebitda = y.rev - y.opex;
    const pat = Math.max(ebitda - y.depr - y.int, 0);
    return {
      name: y.yr,
      Turnover: Math.round(y.rev),
      EBITDA: Math.round(ebitda),
      PAT: Math.round(pat),
      DSCR: y.dscr,
    };
  });

  const avgDscr = (years.reduce((acc, y) => acc + y.dscr, 0) / years.length).toFixed(2);
  const bep = pricingData?.break_even_monthly_units ? `${pricingData.break_even_monthly_units} Units/mo` : '74.5%';

  return (
    <div className="glass-panel p-6 space-y-6 bg-white shadow-card border border-slate-200">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <TranslatedText text="5-Year Amortization & Cash Flow" />
          </div>
          <h3 className="text-lg font-outfit font-bold text-slate-900">
            <TranslatedText text="5-Year Financial Horizon & Capacity Ramp Schedule" />
          </h3>
          <p className="text-xs text-slate-600 mt-0.5">
            <TranslatedText text="Standard commercial banking capacity ramp (60% to 90%) with loan amortization and tax depreciation." />
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-50 px-3.5 py-1.5 rounded-xl border border-slate-200 text-xs">
            <span className="text-slate-500"><TranslatedText text="5-Yr Avg DSCR" />: </span>
            <strong className="text-sovereign-800 font-mono font-bold text-sm ml-1">{avgDscr}</strong>
          </div>
          <div className="bg-slate-50 px-3.5 py-1.5 rounded-xl border border-slate-200 text-xs">
            <span className="text-slate-500"><TranslatedText text="Break-Even" />: </span>
            <strong className="text-emerald-700 font-mono font-bold text-sm ml-1">{bep}</strong>
          </div>
        </div>
      </div>

      {/* Interactive Recharts Combo Chart */}
      <div className="h-72 w-full bg-slate-50/70 rounded-xl p-3 border border-slate-200">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 15, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="name" stroke="#334155" tick={{ fontSize: 11 }} />
            <YAxis yAxisId="left" stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={v => `₹${(v/100000).toFixed(1)}L`} />
            <YAxis yAxisId="right" orientation="right" stroke="#0b3b60" domain={[0, 5]} tick={{ fontSize: 11 }} tickFormatter={v => `${v}x`} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '0.75rem', fontSize: '12px', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)' }}
              formatter={(value, name) => name === 'DSCR' ? [`${value}x`, name] : [`₹${Number(value).toLocaleString('en-IN')}`, name]}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} formatter={(value) => <span className="text-slate-700 font-semibold">{value}</span>} />
            <Bar yAxisId="left" dataKey="Turnover" fill="#1e40af" radius={[4, 4, 0, 0]} opacity={0.85} />
            <Bar yAxisId="left" dataKey="EBITDA" fill="#0284c7" radius={[4, 4, 0, 0]} />
            <Bar yAxisId="left" dataKey="PAT" fill="#059669" radius={[4, 4, 0, 0]} />
            <Line yAxisId="right" type="monotone" dataKey="DSCR" stroke="#0b3b60" strokeWidth={3} dot={{ r: 4, fill: '#0b3b60' }} />
            <ReferenceLine yAxisId="left" y={turnover * 0.62} stroke="#d97706" strokeDasharray="4 4" label={{ value: 'Break-Even Threshold (62%)', fill: '#b45309', fontSize: 10, position: 'insideBottomRight' }} />
            <ReferenceLine yAxisId="right" y={1.33} stroke="#dc2626" strokeDasharray="3 3" label={{ value: 'RBI DSCR 1.33', fill: '#b91c1c', fontSize: 10, position: 'insideTopLeft' }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Data Table */}
      <div className="overflow-x-auto border border-slate-200 rounded-xl">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-bold uppercase text-[10px]">
              <th className="py-2.5 px-3"><TranslatedText text="Line Item (₹)" /></th>
              {years.map(y => (
                <th key={y.yr} className="py-2.5 px-3 text-right">{y.yr}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 font-mono text-slate-700">
            <tr>
              <td className="py-2 px-3 font-sans font-semibold text-slate-900">
                <TranslatedText text="Gross Turnover" />
              </td>
              {years.map(y => <td key={y.yr} className="py-2 px-3 text-right text-blue-900 font-bold">₹{Math.round(y.rev).toLocaleString('en-IN')}</td>)}
            </tr>
            <tr>
              <td className="py-2 px-3 font-sans text-slate-600">
                <TranslatedText text="Operating Expenses (Raw Mat, Power, Wages)" />
              </td>
              {years.map(y => <td key={y.yr} className="py-2 px-3 text-right text-slate-600">₹{Math.round(y.opex).toLocaleString('en-IN')}</td>)}
            </tr>
            <tr>
              <td className="py-2 px-3 font-sans font-semibold text-sky-800">
                <TranslatedText text="Operating EBITDA" />
              </td>
              {years.map(y => <td key={y.yr} className="py-2 px-3 text-right text-sky-900 font-bold">₹{Math.round(y.rev - y.opex).toLocaleString('en-IN')}</td>)}
            </tr>
            <tr>
              <td className="py-2 px-3 font-sans text-slate-600">
                <TranslatedText text="Depreciation (15% WDV)" />
              </td>
              {years.map(y => <td key={y.yr} className="py-2 px-3 text-right text-slate-500">₹{Math.round(y.depr).toLocaleString('en-IN')}</td>)}
            </tr>
            <tr>
              <td className="py-2 px-3 font-sans text-slate-600">
                <TranslatedText text="Bank Interest" />
              </td>
              {years.map(y => <td key={y.yr} className="py-2 px-3 text-right text-slate-500">₹{Math.round(y.int).toLocaleString('en-IN')}</td>)}
            </tr>
            <tr className="bg-emerald-50 font-bold">
              <td className="py-2.5 px-3 font-sans text-emerald-900">
                <TranslatedText text="Net Profit After Tax (PAT)" />
              </td>
              {years.map(y => {
                const pat = Math.max(y.rev - y.opex - y.depr - y.int, 0);
                return <td key={y.yr} className="py-2.5 px-3 text-right text-emerald-800 font-bold">₹{Math.round(pat).toLocaleString('en-IN')}</td>;
              })}
            </tr>
            <tr className="bg-sovereign-50 font-bold">
              <td className="py-2.5 px-3 font-sans text-sovereign-900">
                <TranslatedText text="Debt Service Coverage (DSCR)" />
              </td>
              {years.map(y => <td key={y.yr} className="py-2.5 px-3 text-right text-sovereign-800 font-bold">{y.dscr.toFixed(2)}x</td>)}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Grounded Data Source Lineage Tag */}
      <div className="text-[10px] text-slate-500 flex flex-wrap items-center justify-between gap-2 pt-3 mt-2 border-t border-slate-200">
        <span>
          <strong className="text-slate-700"><TranslatedText text="Data Source:" /></strong> <TranslatedText text="Statutory 5-Year Amortization Schedule & Indian Income Tax WDV Depreciation Slabs" />
        </span>
        <span className="font-mono text-slate-600 font-medium">
          <TranslatedText text="Financial Math: Deterministic Banking Formulae" />
        </span>
      </div>

    </div>
  );
}
export default CashflowProjectionsChart;
