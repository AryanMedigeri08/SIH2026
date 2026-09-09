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
  const rawCompNorm = comp.competition_intensity_normalized !== undefined ? comp.competition_intensity_normalized : 0.05;
  const marketRoomPct = Math.max(0, 100 - (rawCompNorm * 100)).toFixed(1);

  // Pricing Engine Numbers
  const unitFloor = pricing.unit_cost_floor || 0;
  const cpiFloor = pricing.cpi_adjusted_unit_price_floor || 0;
  const bandLow = pricing.recommended_selling_price_band_low || cpiFloor;
  const bandHigh = pricing.recommended_selling_price_band_high || (cpiFloor * 1.20);
  const cpiPct = pricing.cpi_inflation_pct || 4.25;

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-4 sm:p-6 border-l-4 border-sky-600 bg-gradient-to-r from-white via-sky-50/20 to-white shadow-card border border-slate-200/90">
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

      {/* Grid: 4-Stage Demand Conversion Funnel + Demographic Catchment */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left: 4-Stage Demand Conversion Funnel */}
        <TamFunnelChart demographics={demographics} pricing={pricing} />

        {/* Right: Demographic Growth & Catchment Base Card */}
        <div className="glass-panel p-4 sm:p-6 bg-white border border-slate-200 rounded-2xl shadow-card space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-xl bg-sky-50 text-sky-700 border border-sky-200">
                <Users className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-outfit font-bold text-slate-900">
                  <TranslatedText text="Demographic Growth & Consumer Base" />
                </h3>
                <p className="text-xs text-slate-500 font-medium">
                  {demographics.census_details?.provenance || 'Census 2011 Rural Catchment Database (census_raw)'}
                </p>
              </div>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-lg bg-sky-50 border border-sky-200 text-sky-800 font-mono font-bold self-start sm:self-auto">
              +{growthRate}% <TranslatedText text="CAGR" />
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="text-slate-500 font-medium"><TranslatedText text="Base Pop (2011)" /></div>
              <div className="text-lg font-mono font-bold text-slate-800 mt-0.5">{pop2011.toLocaleString('en-IN')}</div>
              <div className="text-[10px] text-slate-500"><TranslatedText text="Census Benchmark" /></div>
            </div>
            <div className="p-3 rounded-xl bg-sky-50/60 border border-sky-100">
              <div className="text-sky-800 font-medium"><TranslatedText text="Projected Pop (2026)" /></div>
              <div className="text-lg font-mono font-bold text-sky-950 mt-0.5">{pop2026.toLocaleString('en-IN')}</div>
              <div className="text-[10px] text-sky-700 font-semibold">+{totalGrowthPct}% <TranslatedText text="Cumulative" /></div>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div className="text-slate-500 font-medium"><TranslatedText text="Projected Households" /></div>
              <div className="text-lg font-mono font-bold text-slate-800 mt-0.5">{households2026.toLocaleString('en-IN')}</div>
              <div className="text-[10px] text-slate-500"><TranslatedText text="4.8 persons / household" /></div>
            </div>
            <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100">
              <div className="text-emerald-800 font-medium"><TranslatedText text="Targeted Households" /></div>
              <div className="text-lg font-mono font-bold text-emerald-950 mt-0.5">{tam.target_households?.toLocaleString('en-IN') || Math.round(households2026 * 0.25).toLocaleString('en-IN')}</div>
              <div className="text-[10px] text-emerald-700 font-semibold">{penetrationRate}% <TranslatedText text="Penetration" /></div>
            </div>
          </div>

          {/* Location Lineage */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-slate-900">
              <MapPin className="w-3.5 h-3.5 text-sky-700 shrink-0" />
              <span><TranslatedText text="Resolved Demographic Catchment" />:</span>
            </div>
            <p className="text-[11px] text-slate-600 font-medium pl-5">
              {p.village_name || 'Village'}, {p.block_name ? `${p.block_name} Block, ` : ''}{p.district_name || 'District'}, {p.state_name || 'State'}
            </p>
          </div>
        </div>

      </div>

      {/* Row 2: 3-Column Grounded Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
        
        {/* Card 1: TAM Spending Profile */}
        <div className="glass-panel p-4 sm:p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-3">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-sky-50 text-sky-700 border border-sky-200">
              <ShoppingCart className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900"><TranslatedText text="Consumer Spending Profile" /></h3>
              <p className="text-[11px] text-slate-500 font-medium"><TranslatedText text="Sector Consumption Sizing" /></p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="Annual TAM Outlay" />:</span>
              <span className="font-mono font-bold text-slate-900">₹{(annualTam / 100000).toFixed(2)} Lakh</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-slate-600"><TranslatedText text="Monthly TAM Outlay" />:</span>
              <span className="font-mono font-bold text-sky-900">₹{(monthlyTam / 100000).toFixed(2)} Lakh</span>
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
              <span className="font-mono font-bold text-emerald-700">{marketRoomPct}% <TranslatedText text="Room" /></span>
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
