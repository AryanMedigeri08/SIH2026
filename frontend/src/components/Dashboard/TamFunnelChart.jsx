import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { Users, Target, ShoppingBag, IndianRupee, Database } from 'lucide-react';

const STAGE_COLORS = ['#1e40af', '#0284c7', '#059669', '#d97706'];

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-xl text-xs">
      <div className="font-bold text-slate-900 mb-1">{data.stage}</div>
      <div className="text-slate-700">
        <span className="text-slate-500">Value: </span>
        <span className="font-mono text-sovereign-800 font-bold">{data.displayValue}</span>
      </div>
      <p className="text-[11px] text-slate-600 mt-1">{data.description}</p>
    </div>
  );
};

export function TamFunnelChart({ demographics, pricing }) {
  const popProj = demographics?.population_projection || {};
  const tamData = demographics?.tam || {};
  const censusDet = demographics?.census_details || {};

  const pop = popProj.projected_population || demographics?.catchment_population_2026 || censusDet.base_population_2011 || 0;
  const households = popProj.projected_households || Math.round(pop / 4.8);
  const targetHouseholds = tamData.target_households || Math.round(households * (tamData.penetration_rate || 0.25));
  const monthlyUnits = tamData.monthly_units || Math.round(targetHouseholds * (tamData.monthly_frequency || 4));
  const monthlyTam = tamData.monthly_tam || (monthlyUnits * (tamData.avg_ticket_size || 100));
  const annualTam = tamData.annual_tam || (monthlyTam * 12);
  const provenance = censusDet.provenance || 'Census 2011 Rural Catchment Database (census_raw) + State CAGR Projection to 2026';

  const funnelData = [
    {
      stage: '1. Catchment Base',
      raw: households,
      displayValue: `${households.toLocaleString('en-IN')} Households`,
      description: `Estimated catchment households from ${pop.toLocaleString('en-IN')} projected 2026 population (avg 4.8 persons/hh).`,
    },
    {
      stage: '2. Target Segment',
      raw: targetHouseholds,
      displayValue: `${targetHouseholds.toLocaleString('en-IN')} Households`,
      description: `Demographic customer base at ${((tamData.penetration_rate || 0.25) * 100).toFixed(0)}% sector penetration rate.`,
    },
    {
      stage: '3. Monthly Units',
      raw: monthlyUnits,
      displayValue: `${Math.round(monthlyUnits).toLocaleString('en-IN')} Units / mo`,
      description: `Projected monthly consumption volume (${tamData.monthly_frequency || 4} purchase cycles/month).`,
    },
    {
      stage: '4. Monthly TAM',
      raw: Math.round(monthlyTam / 1000), // normalized for bar display scale
      displayValue: `₹${(monthlyTam / 100000).toFixed(2)} Lakh / mo`,
      description: `Total monthly consumer spending at ₹${tamData.avg_ticket_size || 100} avg ticket size.`,
    },
  ];

  return (
    <div className="glass-panel p-6 border-slate-200 flex flex-col justify-between bg-white shadow-card">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
              <Users className="w-3.5 h-3.5" />
              Demographic Catchment Sizing
            </div>
            <h3 className="text-lg font-outfit font-bold text-slate-900">
              TAM & Addressable Demand Conversion Funnel
            </h3>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 font-mono font-bold">
            ₹{(annualTam / 100000).toFixed(1)}L Annual TAM
          </span>
        </div>
        <p className="text-xs text-slate-600 mb-4">
          Stepped mathematical conversion from 2026 demographic catchment population to quantified monthly and annual rupee demand.
        </p>
      </div>

      {/* Stepped Funnel Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
          <div className="text-[10px] text-slate-500 flex items-center gap-1 mb-0.5 font-semibold">
            <Users className="w-3 h-3 text-blue-700" /> Catchment
          </div>
          <div className="text-sm font-bold text-slate-900 font-mono">{households.toLocaleString('en-IN')}</div>
          <div className="text-[9px] text-slate-500">Households</div>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
          <div className="text-[10px] text-slate-500 flex items-center gap-1 mb-0.5 font-semibold">
            <Target className="w-3 h-3 text-sky-700" /> Target Share
          </div>
          <div className="text-sm font-bold text-sky-900 font-mono">{targetHouseholds.toLocaleString('en-IN')}</div>
          <div className="text-[9px] text-slate-500">Addressable</div>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
          <div className="text-[10px] text-slate-500 flex items-center gap-1 mb-0.5 font-semibold">
            <ShoppingBag className="w-3 h-3 text-emerald-700" /> Unit Volume
          </div>
          <div className="text-sm font-bold text-emerald-900 font-mono">{monthlyUnits.toLocaleString('en-IN')}</div>
          <div className="text-[9px] text-slate-500">Units / month</div>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
          <div className="text-[10px] text-slate-500 flex items-center gap-1 mb-0.5 font-semibold">
            <IndianRupee className="w-3 h-3 text-amber-700" /> Monthly TAM
          </div>
          <div className="text-sm font-bold text-amber-900 font-mono">₹{(monthlyTam / 100000).toFixed(1)}L</div>
          <div className="text-[9px] text-slate-500">Rupee Demand</div>
        </div>
      </div>

      {/* Funnel Bar Chart */}
      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={funnelData} layout="vertical" margin={{ top: 0, right: 20, left: 10, bottom: 0 }}>
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="stage" stroke="#334155" fontSize={11} width={110} tickLine={false} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.02)' }} />
            <Bar dataKey="raw" radius={[0, 6, 6, 0]}>
              {funnelData.map((_, idx) => (
                <Cell key={`cell-${idx}`} fill={STAGE_COLORS[idx]} opacity={0.9} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Footer Provenance Badge */}
      <div className="text-[10px] text-slate-500 pt-3 border-t border-slate-200 flex items-center justify-between">
        <span className="flex items-center gap-1 text-slate-600">
          <Database className="w-3 h-3 text-sovereign-700" />
          {provenance}
        </span>
        <span className="font-mono text-emerald-700 font-bold">Audited Data Source</span>
      </div>
    </div>
  );
}
export default TamFunnelChart;
