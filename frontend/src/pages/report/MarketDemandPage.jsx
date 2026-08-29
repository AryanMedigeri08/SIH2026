import React from 'react';
import { TamFunnelChart } from '../../components/Dashboard/TamFunnelChart';
import { Target, Users, MapPin, Building2, TrendingUp, ShieldCheck, ShoppingCart, IndianRupee, Store, Gauge, Tag } from 'lucide-react';
import { TranslatedText } from '../../components/TranslatedText';

export function MarketDemandPage({ reportData }) {
  if (!reportData) return null;

  const p = reportData.input_parameters || {};
  const demographics = reportData.market_demographics || {};
  const pricing = reportData.pricing_recommendation || {};

  const popProj = demographics.population_projection || {};
  const tam = demographics.tam || {};
  const msmeDens = demographics.msme_density || {};
  const msmeDet = demographics.msme_details || {};
  const comp = demographics.competition || {};

  const pop2011 = popProj.base_population_2011 || demographics.census_details?.base_population_2011 || 0;
  const pop2026 = popProj.projected_population || demographics.catchment_population_2026 || 0;
  const growthRate = popProj.growth_rate_used ? (popProj.growth_rate_used * 100).toFixed(2) : '1.35';
  const totalGrowthPct = pop2011 > 0 ? (((pop2026 - pop2011) / pop2011) * 100).toFixed(1) : '21.7';
  const households2026 = popProj.projected_households || Math.round(pop2026 / 4.8);

  const annualTam = tam.annual_tam || demographics.annual_tam || 0;
  const monthlyTam = tam.monthly_tam || (annualTam / 12);
  const penetrationRate = tam.penetration_rate ? (tam.penetration_rate * 100).toFixed(0) : '25';
  const monthlyFrequency = tam.monthly_frequency || 4;
  const avgTicketSize = tam.avg_ticket_size || 100;
  const monthlyUnits = tam.monthly_units || 0;

  const density = msmeDens.msme_density_per_10k || demographics.msme_density_per_10k || 0;
  const totalMsmes = msmeDet.total_msme || msmeDens.district_msme_total || 0;
  const competitorsCount = comp.estimated_local_competitors || 0;
  const competitionNormalized = comp.competition_intensity_normalized ? (comp.competition_intensity_normalized * 100).toFixed(1) : '30.0';

  // Pricing Engine Numbers
  const unitFloor = pricing.unit_cost_floor || 0;
  const cpiFloor = pricing.cpi_adjusted_unit_price_floor || 0;
  const bandLow = pricing.recommended_selling_price_band_low || cpiFloor;
  const bandHigh = pricing.recommended_selling_price_band_high || (cpiFloor * 1.20);
  const cpiPct = pricing.cpi_inflation_pct || 4.25;

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-sky-600 bg-gradient-to-r from-white via-sky-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-sky-700 mb-1 flex items-center gap-1.5">
          <Target className="w-4 h-4 text-sky-600" />
          <span><TranslatedText text="Dimension 2 • Demographic Catchment & Total Addressable Market (TAM)" /></span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          <TranslatedText text="Local Demand Sizing & Population Growth Projections" />
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          <TranslatedText text="Derived from the Census 2011 Primary Census Abstract (PCA) with compound annual demographic growth modeling to 2026, combined with Ministry of MSME district enterprise saturation benchmarks." />
        </p>
      </div>

      {/* Demographics Summary Metrics Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel p-4 bg-gradient-to-b from-sky-50/30 via-white to-white border border-slate-200/90 border-t-2 border-t-sky-500 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <Users className="w-3.5 h-3.5 text-sky-600" />
            <span><TranslatedText text="2026 Catchment Pop" /></span>
          </div>
          <strong className="text-xl sm:text-2xl font-mono font-extrabold text-slate-900 block mt-1">
            {pop2026.toLocaleString('en-IN')}
          </strong>
          <span className="text-[10px] text-emerald-700 font-semibold mt-0.5 block">
            +{totalGrowthPct}% ({growthRate}% CAGR) from {pop2011.toLocaleString('en-IN')}
          </span>
        </div>

        <div className="glass-panel p-4 bg-gradient-to-b from-emerald-50/30 via-white to-white border border-slate-200/90 border-t-2 border-t-emerald-500 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <Target className="w-3.5 h-3.5 text-emerald-600" />
            <span><TranslatedText text="Annual TAM Demand" /></span>
          </div>
          <strong className="text-xl sm:text-2xl font-mono font-extrabold text-emerald-700 block mt-1">
            ₹{(annualTam / 100000).toFixed(2)} Lakhs
          </strong>
          <span className="text-[10px] text-slate-500 mt-0.5 block font-medium">
            ₹{Math.round(monthlyTam).toLocaleString('en-IN')}/mo <TranslatedText text="Spending" />
          </span>
        </div>

        <div className="glass-panel p-4 bg-gradient-to-b from-sovereign-50/30 via-white to-white border border-slate-200/90 border-t-2 border-t-sovereign-600 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <Building2 className="w-3.5 h-3.5 text-sovereign-700" />
            <span><TranslatedText text="MSME Density" /></span>
          </div>
          <strong className="text-xl sm:text-2xl font-mono font-extrabold text-sovereign-900 block mt-1">
            {density.toFixed(1)} / 10k
          </strong>
          <span className="text-[10px] text-slate-500 mt-0.5 block font-medium">
            {totalMsmes.toLocaleString('en-IN')} <TranslatedText text="Total District Units" />
          </span>
        </div>

        <div className="glass-panel p-4 bg-gradient-to-b from-amber-50/30 via-white to-white border border-slate-200/90 border-t-2 border-t-amber-500 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <MapPin className="w-3.5 h-3.5 text-amber-600" />
            <span><TranslatedText text="Location Hierarchy" /></span>
          </div>
          <strong className="text-sm font-bold text-slate-900 block mt-1 truncate">
            {p.village_name || 'Village'}, {p.district_name || 'District'}
          </strong>
          <span className="text-[10px] text-slate-500 mt-0.5 block font-medium">{p.state_name || 'State'} (LGD Verified)</span>
        </div>
      </div>

      {/* Conversion Funnel & Stage Cards */}
      <TamFunnelChart demographics={demographics} pricing={pricing} />

      {/* Deep-Dive Grid: Micro-Demand Parameters + Competition Saturation + CPI Pricing Guidance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        {/* Card 1: Sector Micro-Demand Parameters */}
        <div className="glass-panel p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-3">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-sky-50 text-sky-700 border border-sky-200">
              <ShoppingCart className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900"><TranslatedText text="Sector Micro-Demand Model" /></h3>
              <p className="text-[11px] text-slate-500 font-medium"><TranslatedText text="Catchment Consumer Behavior" /></p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="Catchment Households" />:</span>
              <span className="font-mono font-bold text-slate-900">{households2026.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="Sector Penetration Rate" />:</span>
              <span className="font-mono font-bold text-sky-800">{penetrationRate}%</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="Purchase Frequency" />:</span>
              <span className="font-mono font-bold text-slate-900">{monthlyFrequency} <TranslatedText text="cycles / month" /></span>
            </div>
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="Average Ticket Size" />:</span>
              <span className="font-mono font-bold text-emerald-800">₹{avgTicketSize} / <TranslatedText text="purchase" /></span>
            </div>
          </div>
        </div>

        {/* Card 2: District MSME Competition & Cluster Analysis */}
        <div className="glass-panel p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-3">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-amber-50 text-amber-700 border border-amber-200">
              <Store className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900"><TranslatedText text="Competition & Cluster Density" /></h3>
              <p className="text-[11px] text-slate-500 font-medium"><TranslatedText text="Udyam Registration Registry" /></p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="District Registered MSMEs" />:</span>
              <span className="font-mono font-bold text-slate-900">{totalMsmes.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="MSME Density per 10k" />:</span>
              <span className="font-mono font-bold text-sovereign-900">{density.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="Est. Local Competitors" />:</span>
              <span className="font-mono font-bold text-amber-800">{Math.round(competitorsCount)} <TranslatedText text="Units" /></span>
            </div>
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="Market Room Index" />:</span>
              <span className="font-mono font-bold text-emerald-700">{competitionNormalized}% <TranslatedText text="Room" /></span>
            </div>
          </div>
        </div>

        {/* Card 3: CPI-Compounded Forward Pricing Guidance */}
        <div className="glass-panel p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-3">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200">
              <Tag className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900"><TranslatedText text="Forward Pricing Guidance" /></h3>
              <p className="text-[11px] text-slate-500 font-medium"><TranslatedText text="MoSPI CPI-Adjusted Floor" /></p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="State Rural CPI Inflation" />:</span>
              <span className="font-mono font-bold text-slate-900">{cpiPct.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="Unadjusted Unit Cost Floor" />:</span>
              <span className="font-mono font-bold text-slate-900">₹{unitFloor.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="12-Mo CPI Forward Floor" />:</span>
              <span className="font-mono font-bold text-amber-800">₹{cpiFloor.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded-xl bg-emerald-50/70 border border-emerald-200">
              <span className="text-emerald-900 font-bold"><TranslatedText text="Recommended Band" />:</span>
              <span className="font-mono font-black text-emerald-800">₹{bandLow.toFixed(1)} – ₹{bandHigh.toFixed(1)}</span>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
export default MarketDemandPage;
