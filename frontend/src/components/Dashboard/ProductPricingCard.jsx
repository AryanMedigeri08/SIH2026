import React, { useState } from 'react';
import { 
  Tag, 
  TrendingUp, 
  Calculator, 
  HelpCircle, 
  CheckCircle2, 
  AlertCircle, 
  DollarSign, 
  Sparkles,
  Layers,
  ArrowUpRight
} from 'lucide-react';
import { TranslatedText } from '../TranslatedText';

export function ProductPricingCard({ reportData, pricingData }) {
  const p = reportData?.pricing_recommendation || pricingData || {};
  const cost = reportData?.input_parameters?.project_cost || 900000;
  const turnover = reportData?.input_parameters?.annual_turnover_estimate || 950000;
  const sector = reportData?.input_parameters?.sector || 'dairy';

  // Benchmark values
  const unitCostFloor = p.unit_cost_floor || 45.0;
  const cpiFloor = p.cpi_adjusted_unit_price_floor || (unitCostFloor * 1.05);
  const defaultPrice = p.recommended_selling_price_band_high 
    ? Math.round((p.recommended_selling_price_band_low + p.recommended_selling_price_band_high) / 2)
    : Math.round(cpiFloor * 1.25);

  const [sellingPrice, setSellingPrice] = useState(defaultPrice);

  // Derived unit economics
  const marginPerUnit = Math.max(0, sellingPrice - unitCostFloor);
  const marginPct = sellingPrice > 0 ? ((marginPerUnit / sellingPrice) * 100) : 0;
  
  // Fixed monthly costs (EMI + basic overhead)
  const monthlyEmi = reportData?.financial_projections?.amortization?.monthly_emi || 10500;
  const fixedOverhead = monthlyEmi + (turnover * 0.03); // EMI + utilities/rent
  const breakEvenUnitsMonthly = marginPerUnit > 0 ? Math.ceil(fixedOverhead / marginPerUnit) : 0;
  const breakEvenUnitsDaily = Math.ceil(breakEvenUnitsMonthly / 26); // 26 working days

  const estMonthlyUnits = p.expected_monthly_units || Math.round(turnover / (sellingPrice * 12) || 1200);
  const estMonthlyProfit = Math.round((marginPerUnit * estMonthlyUnits) - fixedOverhead);

  return (
    <div className="glass-panel p-4 sm:p-6 bg-white border border-slate-200/90 rounded-2xl shadow-card space-y-5 transition-all">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-xs">
            <Tag className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base sm:text-lg font-outfit font-bold text-slate-900">
                <TranslatedText text="Product Pricing & Profit Simulator" />
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300">
                <TranslatedText text="Grassroots Margins" />
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">
              <TranslatedText text="Calibrated against rural purchasing power and MoSPI consumer price inflation" />
            </p>
          </div>
        </div>

        <div className="text-left sm:text-right">
          <span className="text-[10px] text-slate-500 font-medium block">
            <TranslatedText text="Recommended Price Band" />
          </span>
          <span className="text-sm sm:text-base font-mono font-extrabold text-emerald-700">
            ₹{Math.round(p.recommended_selling_price_band_low || cpiFloor)} – ₹{Math.round(p.recommended_selling_price_band_high || (cpiFloor * 1.30))}
          </span>
        </div>
      </div>

      {/* Interactive Price Slider */}
      <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-3">
        <div className="flex justify-between items-center text-xs">
          <span className="font-bold text-slate-800">
            <TranslatedText text="Your Unit Selling Price (₹)" />
          </span>
          <span className="text-lg font-mono font-extrabold text-sovereign-800 bg-white px-3 py-0.5 rounded-lg border border-slate-300 shadow-xs">
            ₹{sellingPrice}
          </span>
        </div>

        <input
          type="range"
          min={Math.max(10, Math.floor(unitCostFloor * 0.8))}
          max={Math.ceil(unitCostFloor * 2.2)}
          step={1}
          value={sellingPrice}
          onChange={(e) => setSellingPrice(Number(e.target.value))}
          className="w-full accent-emerald-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
        />

        <div className="flex justify-between text-[10px] font-mono text-slate-500">
          <span>₹{Math.floor(unitCostFloor * 0.8)} (<TranslatedText text="Cost Floor" />)</span>
          <span className="font-bold text-emerald-700">₹{Math.round(cpiFloor)} (<TranslatedText text="Inflation Benchmark" />)</span>
          <span>₹{Math.ceil(unitCostFloor * 2.2)} (<TranslatedText text="Premium Tier" />)</span>
        </div>
      </div>

      {/* 3 Key Unit Economic Indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Unit Profit Margin */}
        <div className="p-3.5 rounded-xl bg-white border border-slate-200/90 shadow-subtle space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span><TranslatedText text="Profit per Unit" /></span>
            <span className="text-[10px] font-bold text-emerald-700 font-mono">
              {marginPct.toFixed(0)}% <TranslatedText text="Margin" />
            </span>
          </div>
          <div className="text-xl font-mono font-bold text-emerald-700">
            ₹{marginPerUnit.toFixed(1)}
          </div>
          <p className="text-[10px] text-slate-500">
            <TranslatedText text="Cost of production" />: ₹{unitCostFloor.toFixed(1)}
          </p>
        </div>

        {/* Daily Break-Even Target */}
        <div className="p-3.5 rounded-xl bg-white border border-slate-200/90 shadow-subtle space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span><TranslatedText text="Daily Sales Target" /></span>
            <span className="text-[10px] font-bold text-blue-700">
              <TranslatedText text="Break-Even" />
            </span>
          </div>
          <div className="text-xl font-mono font-bold text-slate-900">
            {breakEvenUnitsDaily} <span className="text-xs font-sans text-slate-500 font-normal"><TranslatedText text="units/day" /></span>
          </div>
          <p className="text-[10px] text-slate-500">
            <TranslatedText text="Monthly required" />: {breakEvenUnitsMonthly} <TranslatedText text="units to clear EMI & rent" />
          </p>
        </div>

        {/* Estimated Monthly Take-Home Net Profit */}
        <div className="p-3.5 rounded-xl bg-gradient-to-br from-emerald-50/60 to-white border border-emerald-200 shadow-subtle space-y-1">
          <div className="flex items-center justify-between text-xs text-emerald-800 font-medium">
            <span><TranslatedText text="Estimated Take-Home" /></span>
            <ArrowUpRight className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div className="text-xl font-mono font-extrabold text-emerald-800">
            ₹{estMonthlyProfit.toLocaleString('en-IN')}
          </div>
          <p className="text-[10px] text-emerald-700 font-medium">
            <TranslatedText text="Net monthly cash flow after loan EMI" />
          </p>
        </div>
      </div>

      {/* Practical Rural Business Guidance */}
      <div className="p-3.5 rounded-xl bg-amber-50/60 border border-amber-200/80 text-xs text-amber-900 space-y-1">
        <div className="flex items-center gap-1.5 font-bold text-amber-950">
          <Sparkles className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <span><TranslatedText text="Local Village Pricing Advice" /></span>
        </div>
        <p className="text-[11px] text-amber-900 leading-relaxed font-medium">
          <TranslatedText text="In rural markets, start at the lower half of the recommended band for the first 3 months to build a loyal neighborhood customer base. Once customers trust your quality, transition to standard rates." />
        </p>
      </div>
    </div>
  );
}

export default ProductPricingCard;
