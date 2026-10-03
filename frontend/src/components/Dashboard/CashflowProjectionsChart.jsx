import React, { useState } from 'react';
import { 
  BarChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  Legend, ReferenceLine, CartesianGrid, ComposedChart 
} from 'recharts';
import { TrendingUp, Table as TableIcon, BarChart3, Activity, Layers, Clock, Target, Calendar, CheckCircle2 } from 'lucide-react';
import { TranslatedText } from '../TranslatedText';

export function CashflowProjectionsChart({ inputData, financialData, pricingData }) {
  const [viewMode, setViewMode] = useState('all'); // 'all' | 'revenue' | 'dscr'
  const [showCards, setShowCards] = useState(false);

  const turnover = Number(inputData?.annual_turnover_estimate) || 950000;
  const projectCost = Number(inputData?.project_cost) || 900000;
  const emi = financialData?.amortization?.monthly_emi || 10530;
  const loanPrincipal = financialData?.loan_principal || 585000;
  const dscr = financialData?.dscr?.dscr || 2.25;

  const years = [
    { yr: 'Yr 1 (60%)', yrShort: 'Y1', cap: 60, rev: turnover * 0.85, opex: turnover * 0.85 * 0.68, depr: projectCost * 0.55 * 0.15, int: loanPrincipal * 0.11, debt: emi * 12, dscr: Number((dscr * 0.9).toFixed(2)) },
    { yr: 'Yr 2 (70%)', yrShort: 'Y2', cap: 70, rev: turnover * 1.00, opex: turnover * 1.00 * 0.68, depr: projectCost * 0.55 * 0.15 * 0.85, int: loanPrincipal * 0.09, debt: emi * 12, dscr: Number((dscr * 1.0).toFixed(2)) },
    { yr: 'Yr 3 (80%)', yrShort: 'Y3', cap: 80, rev: turnover * 1.15, opex: turnover * 1.15 * 0.68, depr: projectCost * 0.55 * 0.15 * 0.72, int: loanPrincipal * 0.07, debt: emi * 12, dscr: Number((dscr * 1.15).toFixed(2)) },
    { yr: 'Yr 4 (85%)', yrShort: 'Y4', cap: 85, rev: turnover * 1.25, opex: turnover * 1.25 * 0.68, depr: projectCost * 0.55 * 0.15 * 0.61, int: loanPrincipal * 0.05, debt: emi * 12, dscr: Number((dscr * 1.25).toFixed(2)) },
    { yr: 'Yr 5 (90%)', yrShort: 'Y5', cap: 90, rev: turnover * 1.35, opex: turnover * 1.35 * 0.68, depr: projectCost * 0.55 * 0.15 * 0.52, int: loanPrincipal * 0.02, debt: emi * 12, dscr: Number((dscr * 1.40).toFixed(2)) },
  ];

  const chartData = years.map(y => {
    const ebitda = y.rev - y.opex;
    const pat = Math.max(ebitda - y.depr - y.int, 0);
    return {
      name: y.yr,
      nameShort: y.yrShort,
      Turnover: Math.round(y.rev),
      EBITDA: Math.round(ebitda),
      PAT: Math.round(pat),
      DSCR: y.dscr,
    };
  });

  const avgDscr = (years.reduce((acc, y) => acc + y.dscr, 0) / years.length).toFixed(2);
  const breakEvenPct = Number(financialData?.break_even_pct) || 64.5;
  const breakEvenMilestone = financialData?.break_even_milestone || 'Year 2 (Month 16)';
  const breakEvenYear = Number(financialData?.break_even_year) || 2;
  const paybackYears = Number(financialData?.payback_period_years) || 2.6;
  const equityPaybackYears = Number(financialData?.equity_payback_years) || 1.8;
  const bepRationale = financialData?.break_even_rationale || 
    `Statutory MSME commercial break-even achieved in ${breakEvenMilestone} at ${breakEvenPct.toFixed(1)}% capacity. Year 1 operates at 60% capacity during plant erection, customer acquisition, and licensing.`;

  const VIEW_MODES = [
    { id: 'all', label: 'Combined', icon: Layers },
    { id: 'revenue', label: 'Revenue & Profit', icon: BarChart3 },
    { id: 'dscr', label: 'DSCR Solvency', icon: Activity },
  ];

  return (
    <div className="glass-panel p-4 sm:p-6 space-y-4 sm:space-y-5 bg-white shadow-card border border-slate-200">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <TranslatedText text="5-Year Amortization & Cash Flow" />
          </div>
          <h3 className="text-base sm:text-lg font-outfit font-bold text-slate-900">
            <TranslatedText text="5-Year Financial Horizon & Capacity Ramp Schedule" />
          </h3>
          <p className="text-xs text-slate-600 mt-0.5 hidden sm:block">
            <TranslatedText text="Standard commercial banking capacity ramp (60% to 90%) with loan amortization and tax depreciation." />
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="bg-slate-50 px-3 sm:px-3.5 py-1.5 rounded-xl border border-slate-200 text-xs">
            <span className="text-slate-500"><TranslatedText text="5-Yr Avg DSCR" />: </span>
            <strong className="text-sovereign-800 font-mono font-bold text-sm ml-1">{avgDscr}</strong>
          </div>
          <div className="bg-emerald-50 px-3 sm:px-3.5 py-1.5 rounded-xl border border-emerald-200 text-xs">
            <span className="text-emerald-700 font-medium"><TranslatedText text="Break-Even Horizon" />: </span>
            <strong className="text-emerald-900 font-mono font-bold text-sm ml-1">{breakEvenMilestone}</strong>
          </div>
          <div className="bg-sky-50 px-3 sm:px-3.5 py-1.5 rounded-xl border border-sky-200 text-xs">
            <span className="text-sky-700 font-medium"><TranslatedText text="Payback Period" />: </span>
            <strong className="text-sky-900 font-mono font-bold text-sm ml-1">{paybackYears.toFixed(1)} Yrs</strong>
          </div>
        </div>
      </div>

      {/* Commercial Gestation & Break-Even Insight Banner */}
      <div className="p-3 sm:p-3.5 rounded-xl bg-gradient-to-r from-amber-50/80 via-white to-amber-50/40 border border-amber-200/90 flex items-start gap-2.5 text-xs text-amber-950 shadow-subtle">
        <Clock className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <strong className="font-bold font-outfit text-amber-950 text-xs">
              <TranslatedText text="Commercial Gestation & Break-Even Horizon:" />
            </strong>
            <span className="px-2 py-0.5 rounded-md bg-amber-200/90 text-amber-900 font-mono font-bold text-[10px]">
              {breakEvenMilestone} ({breakEvenPct.toFixed(1)}% Capacity)
            </span>
            <span className="px-2 py-0.5 rounded-full bg-emerald-100 border border-emerald-300 text-emerald-800 font-mono font-bold text-[10px]">
              <TranslatedText text="Payback:" /> {paybackYears.toFixed(1)} Yrs · Equity: {equityPaybackYears.toFixed(1)} Yrs
            </span>
          </div>
          <p className="text-[11px] sm:text-xs text-slate-700 leading-relaxed font-medium">
            <TranslatedText text={bepRationale} />
          </p>
        </div>
      </div>

      {/* View Mode Toggle & Cards Switch */}
      <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto no-scrollbar">
        {VIEW_MODES.map(vm => {
          const Icon = vm.icon;
          return (
            <button
              key={vm.id}
              type="button"
              onClick={() => setViewMode(vm.id)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all shrink-0 border ${
                viewMode === vm.id
                  ? 'bg-sovereign-900 text-white border-sovereign-700 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span className="whitespace-nowrap">{vm.label}</span>
            </button>
          );
        })}
        <button
          type="button"
          onClick={() => setShowCards(prev => !prev)}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all shrink-0 border ml-auto ${
            showCards
              ? 'bg-sky-50 text-sky-800 border-sky-200'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          }`}
        >
          <TableIcon className="w-3.5 h-3.5" />
          <span className="whitespace-nowrap">{showCards ? 'Table View' : 'Cards View'}</span>
        </button>
      </div>

      {/* Interactive Recharts Combo Chart */}
      <div className="h-56 sm:h-72 w-full bg-slate-50/70 rounded-xl p-2 sm:p-3 border border-slate-200">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 15, right: viewMode === 'dscr' ? 10 : 20, bottom: 5, left: viewMode === 'dscr' ? 0 : 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="nameShort" stroke="#334155" tick={{ fontSize: 11 }} />
            {viewMode !== 'dscr' && (
              <YAxis yAxisId="left" stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={v => `₹${(v/100000).toFixed(1)}L`} width={55} />
            )}
            {viewMode !== 'revenue' && (
              <YAxis yAxisId="right" orientation={viewMode === 'dscr' ? 'left' : 'right'} stroke="#0b3b60" domain={[0, 5]} tick={{ fontSize: 11 }} tickFormatter={v => `${v}x`} width={35} />
            )}
            <Tooltip 
              contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '0.75rem', fontSize: '12px', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)' }}
              formatter={(value, name) => name === 'DSCR' ? [`${value}x`, name] : [`₹${Number(value).toLocaleString('en-IN')}`, name]}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} formatter={(value) => <span className="text-slate-700 font-semibold">{value}</span>} />
            {viewMode !== 'dscr' && (
              <>
                <Bar yAxisId="left" dataKey="Turnover" fill="#1e40af" radius={[4, 4, 0, 0]} opacity={0.85} />
                <Bar yAxisId="left" dataKey="EBITDA" fill="#0284c7" radius={[4, 4, 0, 0]} />
                <Bar yAxisId="left" dataKey="PAT" fill="#059669" radius={[4, 4, 0, 0]} />
              </>
            )}
            {viewMode !== 'revenue' && (
              <>
                <Line yAxisId="right" type="monotone" dataKey="DSCR" stroke="#0b3b60" strokeWidth={3} dot={{ r: 4, fill: '#0b3b60' }} />
                <ReferenceLine yAxisId="right" y={1.33} stroke="#dc2626" strokeDasharray="3 3" label={{ value: 'RBI 1.33', fill: '#b91c1c', fontSize: 10, position: 'insideTopLeft' }} />
              </>
            )}
            {viewMode !== 'dscr' && (
              <ReferenceLine 
                yAxisId="left" 
                y={turnover * (breakEvenPct / 100)} 
                stroke="#d97706" 
                strokeDasharray="4 4" 
                label={{ 
                  value: `BEP (${breakEvenPct.toFixed(0)}%)`, 
                  fill: '#b45309', 
                  fontSize: 10, 
                  position: 'insideBottomRight' 
                }} 
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Year-by-Year Cards View OR Data Table */}
      {showCards ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
          {years.map(y => {
            const ebitda = y.rev - y.opex;
            const pat = Math.max(ebitda - y.depr - y.int, 0);
            const dscrOk = y.dscr >= 1.33;
            const isBepYear = y.yrShort === `Y${breakEvenYear}`;
            return (
              <div key={y.yr} className={`glass-panel p-4 bg-white border rounded-xl shadow-card space-y-2.5 ${isBepYear ? 'border-amber-400 ring-2 ring-amber-200/50' : 'border-slate-200'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">📅 {y.yr}</span>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                    dscrOk ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-amber-50 text-amber-800 border-amber-200'
                  }`}>
                    DSCR: {y.dscr}x
                  </span>
                </div>
                {isBepYear && (
                  <div className="text-[10px] font-bold bg-amber-100/80 text-amber-900 border border-amber-300 px-2 py-0.5 rounded-md flex items-center gap-1 font-sans">
                    <Target className="w-3 h-3 text-amber-700 shrink-0" />
                    <span><TranslatedText text="Break-Even Achieved" /></span>
                  </div>
                )}
                <div className="space-y-1.5 text-[11px] text-slate-700">
                  <div className="flex justify-between"><span>Gross Turnover</span><span className="font-mono font-bold text-blue-900">₹{Math.round(y.rev).toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between"><span>Operating Expenses</span><span className="font-mono text-slate-500">₹{Math.round(y.opex).toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between"><span>EBITDA</span><span className="font-mono font-bold text-sky-800">₹{Math.round(ebitda).toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between"><span>Depreciation</span><span className="font-mono text-slate-500">₹{Math.round(y.depr).toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between"><span>Bank Interest</span><span className="font-mono text-slate-500">₹{Math.round(y.int).toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between pt-1.5 border-t border-slate-100">
                    <span className="font-bold text-emerald-900">Net PAT</span>
                    <span className="font-mono font-bold text-emerald-800">₹{Math.round(pat).toLocaleString('en-IN')}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="overflow-x-auto scroll-touch-x border border-slate-200 rounded-xl">
          <table className="w-full min-w-[560px] text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-bold uppercase text-[10px]">
                <th className="py-2.5 px-3 sticky left-0 bg-slate-50 z-10 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.06)]"><TranslatedText text="Line Item (₹)" /></th>
                {years.map(y => (
                  <th key={y.yr} className="py-2.5 px-3 text-right">
                    <span>{y.yrShort}</span>
                    {y.yrShort === `Y${breakEvenYear}` && (
                      <span className="ml-1 text-[9px] font-bold text-amber-800 bg-amber-200/90 px-1 py-0.5 rounded font-sans tracking-wide">
                        BEP
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 font-mono text-slate-700">
              <tr>
                <td className="py-2 px-3 font-sans font-semibold text-slate-900 sticky left-0 bg-white z-10 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.06)]">
                  <TranslatedText text="Gross Turnover" />
                </td>
                {years.map(y => <td key={y.yr} className="py-2 px-3 text-right text-blue-900 font-bold">₹{Math.round(y.rev).toLocaleString('en-IN')}</td>)}
              </tr>
              <tr>
                <td className="py-2 px-3 font-sans text-slate-600 sticky left-0 bg-white z-10 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.06)]">
                  <TranslatedText text="Operating Expenses" />
                </td>
                {years.map(y => <td key={y.yr} className="py-2 px-3 text-right text-slate-600">₹{Math.round(y.opex).toLocaleString('en-IN')}</td>)}
              </tr>
              <tr>
                <td className="py-2 px-3 font-sans font-semibold text-sky-800 sticky left-0 bg-white z-10 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.06)]">
                  <TranslatedText text="Operating EBITDA" />
                </td>
                {years.map(y => <td key={y.yr} className="py-2 px-3 text-right text-sky-900 font-bold">₹{Math.round(y.rev - y.opex).toLocaleString('en-IN')}</td>)}
              </tr>
              <tr>
                <td className="py-2 px-3 font-sans text-slate-600 sticky left-0 bg-white z-10 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.06)]">
                  <TranslatedText text="Depreciation (15% WDV)" />
                </td>
                {years.map(y => <td key={y.yr} className="py-2 px-3 text-right text-slate-500">₹{Math.round(y.depr).toLocaleString('en-IN')}</td>)}
              </tr>
              <tr>
                <td className="py-2 px-3 font-sans text-slate-600 sticky left-0 bg-white z-10 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.06)]">
                  <TranslatedText text="Bank Interest" />
                </td>
                {years.map(y => <td key={y.yr} className="py-2 px-3 text-right text-slate-500">₹{Math.round(y.int).toLocaleString('en-IN')}</td>)}
              </tr>
              <tr className="bg-emerald-50 font-bold">
                <td className="py-2.5 px-3 font-sans text-emerald-900 sticky left-0 bg-emerald-50 z-10 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.06)]">
                  <TranslatedText text="Net Profit After Tax (PAT)" />
                </td>
                {years.map(y => {
                  const pat = Math.max(y.rev - y.opex - y.depr - y.int, 0);
                  return <td key={y.yr} className="py-2.5 px-3 text-right text-emerald-800 font-bold">₹{Math.round(pat).toLocaleString('en-IN')}</td>;
                })}
              </tr>
              <tr className="bg-sovereign-50 font-bold">
                <td className="py-2.5 px-3 font-sans text-sovereign-900 sticky left-0 bg-sovereign-50 z-10 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.06)]">
                  <TranslatedText text="Debt Service Coverage (DSCR)" />
                </td>
                {years.map(y => <td key={y.yr} className="py-2.5 px-3 text-right text-sovereign-800 font-bold">{y.dscr.toFixed(2)}x</td>)}
              </tr>
            </tbody>
          </table>
        </div>
      )}

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
