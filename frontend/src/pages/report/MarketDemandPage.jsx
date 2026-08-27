import React from 'react';
import { TamFunnelChart } from '../../components/Dashboard/TamFunnelChart';
import { Target, Users, MapPin, Building2, TrendingUp, ShieldCheck } from 'lucide-react';

export function MarketDemandPage({ reportData }) {
  if (!reportData) return null;

  const p = reportData.input_parameters || {};
  const demographics = reportData.market_demographics || {};
  const pricing = reportData.pricing_recommendation || {};

  const pop2011 = demographics.catchment_population_2011 || 3850;
  const pop2026 = demographics.catchment_population_2026 || 4639;
  const growthPct = demographics.population_growth_pct || 20.5;
  const annualTam = demographics.annual_tam || 9493848;
  const density = demographics.msme_density_per_10k || 2694.55;

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-sky-600 bg-gradient-to-r from-white via-sky-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-sky-700 mb-1 flex items-center gap-1.5">
          <Target className="w-4 h-4 text-sky-600" />
          <span>Dimension 2 • Demographic Catchment & Total Addressable Market (TAM)</span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          Local Demand Sizing & Population Growth Projections
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          Derived from the Census 2011 Primary Census Abstract (PCA) with compound annual demographic growth modeling to 2026, combined with Ministry of MSME district enterprise saturation benchmarks.
        </p>
      </div>

      {/* Demographics Summary Metrics Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel p-4 bg-gradient-to-b from-sky-50/30 via-white to-white border border-slate-200/90 border-t-2 border-t-sky-500 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <Users className="w-3.5 h-3.5 text-sky-600" />
            <span>2026 Catchment Pop</span>
          </div>
          <strong className="text-xl sm:text-2xl font-mono font-extrabold text-slate-900 block mt-1">
            {pop2026.toLocaleString('en-IN')}
          </strong>
          <span className="text-[10px] text-emerald-700 font-semibold mt-0.5 block">
            +{growthPct}% growth from {pop2011.toLocaleString('en-IN')} (2011)
          </span>
        </div>

        <div className="glass-panel p-4 bg-gradient-to-b from-emerald-50/30 via-white to-white border border-slate-200/90 border-t-2 border-t-emerald-500 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <Target className="w-3.5 h-3.5 text-emerald-600" />
            <span>Annual TAM Demand</span>
          </div>
          <strong className="text-xl sm:text-2xl font-mono font-extrabold text-emerald-700 block mt-1">
            ₹{(annualTam / 100000).toFixed(2)} Lakhs
          </strong>
          <span className="text-[10px] text-slate-500 mt-0.5 block font-medium">Total Addressable Market</span>
        </div>

        <div className="glass-panel p-4 bg-gradient-to-b from-sovereign-50/30 via-white to-white border border-slate-200/90 border-t-2 border-t-sovereign-600 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <Building2 className="w-3.5 h-3.5 text-sovereign-700" />
            <span>MSME Density</span>
          </div>
          <strong className="text-xl sm:text-2xl font-mono font-extrabold text-sovereign-900 block mt-1">
            {density.toFixed(1)} / 10k
          </strong>
          <span className="text-[10px] text-slate-500 mt-0.5 block font-medium">District Registry Benchmark</span>
        </div>

        <div className="glass-panel p-4 bg-gradient-to-b from-amber-50/30 via-white to-white border border-slate-200/90 border-t-2 border-t-amber-500 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <MapPin className="w-3.5 h-3.5 text-amber-600" />
            <span>Location Hierarchy</span>
          </div>
          <strong className="text-sm font-bold text-slate-900 block mt-1 truncate">
            {p.village_name || 'Village'}, {p.district_name || 'District'}
          </strong>
          <span className="text-[10px] text-slate-500 mt-0.5 block font-medium">{p.state_name || 'State'} (LGD Verified)</span>
        </div>
      </div>

      {/* Conversion Funnel & Stage Cards */}
      <TamFunnelChart demographics={demographics} pricing={pricing} />

    </div>
  );
}
export default MarketDemandPage;
