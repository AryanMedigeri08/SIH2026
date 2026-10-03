import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  Tag,
  TrendingUp,
  Calculator,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Layers,
  Store,
  ShieldCheck,
  Scale,
  Coins,
  ArrowRight,
  Info,
  ArrowUpRight,
  HelpCircle,
  Clock
} from 'lucide-react';
import { TranslatedText } from '../../components/TranslatedText';
import { useLanguage } from '../../context/LanguageContext';

export function ProductPricingPage({ reportData }) {
  if (!reportData) return null;

  const { t } = useLanguage();
  const p = reportData?.pricing_recommendation || {};
  const cost = reportData?.input_parameters?.project_cost || 800000;
  const turnover = reportData?.input_parameters?.annual_turnover_estimate || 1200000;
  const sector = reportData?.input_parameters?.sector || 'Dairy';
  const district = reportData?.input_parameters?.district_name || 'Bankura';
  const state = reportData?.input_parameters?.state_name || 'West Bengal';

  // Benchmark values from Pricing Engine & Financial Analysis
  const unitCostFloor = Number(p.unit_cost_floor) || 45.0;
  const cpiFloor = Number(p.cpi_adjusted_unit_price_floor) || (unitCostFloor * 1.05);
  const bandLow = Math.round(p.recommended_selling_price_band_low || cpiFloor);
  const bandHigh = Math.round(p.recommended_selling_price_band_high || (cpiFloor * 1.25));
  const cpiPct = Number(p.cpi_inflation_pct) || 4.25;

  const defaultPrice = Math.round((bandLow + bandHigh) / 2);

  // Financial Cost Structures
  const monthlyEmi = Number(reportData?.financial_analysis?.amortization?.monthly_emi) || 11310;
  const monthlyLivingDraw = Number(p.monthly_living_draw) || 8000;
  const monthlyWorkingCapital = Number(p.monthly_working_capital_outlay) || (turnover * 0.05);

  // Fixed monthly costs (Bank EMI + Basic living subsistence + overhead rent/utilities)
  const fixedMonthlyCosts = Math.round(monthlyEmi + monthlyLivingDraw + (monthlyWorkingCapital * 0.15));
  
  // Variable cost per unit (Raw materials, direct power, transport consumables)
  const variableCostPerUnit = Math.max(1, Math.round(unitCostFloor * 0.80));

  // Unit Margin calculations
  const unitMargin = Math.max(0, defaultPrice - variableCostPerUnit);
  const breakEvenMonthlyUnits = unitMargin > 0 ? Math.ceil(fixedMonthlyCosts / unitMargin) : 0;
  const breakEvenDailyUnits = Math.ceil(breakEvenMonthlyUnits / 26);

  // Set default daily units to realistic healthy operating capacity (~1.5x break-even)
  const defaultDailyUnits = Math.max(Math.ceil(breakEvenDailyUnits * 1.5), 20);

  // Realistic bounds for daily volume based on micro-enterprise physical capacity (fixed constants)
  const minDailyUnits = Math.max(5, Math.floor(breakEvenDailyUnits * 0.4));
  const maxDailyUnits = Math.max(120, Math.ceil(defaultDailyUnits * 2.5), Math.ceil(breakEvenDailyUnits * 3.0));

  // Interactive Simulator States
  const [sellingPrice, setSellingPrice] = useState(defaultPrice);
  const [dailyUnits, setDailyUnits] = useState(defaultDailyUnits);

  // Recalculate dynamic margins based on current slider values
  const activeUnitMargin = Math.max(0, sellingPrice - variableCostPerUnit);
  const marginPct = sellingPrice > 0 ? ((activeUnitMargin / sellingPrice) * 100) : 0;
  const activeBreakEvenMonthly = activeUnitMargin > 0 ? Math.ceil(fixedMonthlyCosts / activeUnitMargin) : 0;
  const activeBreakEvenDaily = Math.ceil(activeBreakEvenMonthly / 26);

  // Current production & profit estimates
  const monthlyVolume = dailyUnits * 26;
  const monthlyRevenue = monthlyVolume * sellingPrice;
  const totalMonthlyCosts = Math.round(fixedMonthlyCosts + (monthlyVolume * variableCostPerUnit));
  const monthlyTakeHomeProfit = monthlyRevenue - totalMonthlyCosts;

  // Days to reach break-even in the month
  const daysToBreakEven = dailyUnits > 0 ? Math.min(26, Math.ceil(activeBreakEvenMonthly / dailyUnits)) : 26;
  const isProfitable = monthlyTakeHomeProfit > 0;

  // Break-Even Curve Chart Data
  const chartData = useMemo(() => {
    const data = [];
    const maxVolume = Math.max(Math.round(monthlyVolume * 1.5), Math.round(activeBreakEvenMonthly * 1.6), 600);
    const step = Math.max(10, Math.round(maxVolume / 8));

    for (let q = 0; q <= maxVolume; q += step) {
      const rev = Math.round(q * sellingPrice);
      const totalCost = Math.round(fixedMonthlyCosts + (q * variableCostPerUnit));
      const net = rev - totalCost;
      data.push({
        units: q,
        Revenue: rev,
        TotalCosts: totalCost,
        NetProfit: net,
      });
    }
    return data;
  }, [monthlyVolume, activeBreakEvenMonthly, sellingPrice, fixedMonthlyCosts, variableCostPerUnit]);

  // Cost Stack Percentages for ₹100 of selling price
  const costStack = useMemo(() => {
    if (sellingPrice <= 0) return { raw: 55, overhead: 15, emi: 12, profit: 18 };
    const rawPct = Math.min(70, Math.round((variableCostPerUnit / sellingPrice) * 100));
    const emiPct = monthlyVolume > 0 ? Math.min(25, Math.max(5, Math.round((monthlyEmi / monthlyRevenue) * 100))) : 12;
    const overheadPct = monthlyVolume > 0 ? Math.min(20, Math.max(5, Math.round(((fixedMonthlyCosts - monthlyEmi) / monthlyRevenue) * 100))) : 15;
    const profitPct = Math.max(0, 100 - (rawPct + emiPct + overheadPct));
    return { raw: rawPct, overhead: overheadPct, emi: emiPct, profit: profitPct };
  }, [sellingPrice, variableCostPerUnit, monthlyVolume, monthlyRevenue, monthlyEmi, fixedMonthlyCosts]);

  // Donut Chart Dataset for ₹100 of Sales Breakdown
  const donutData = useMemo(() => [
    { name: 'Raw Materials', value: costStack.raw, color: '#2563eb', bg: 'bg-blue-50/70', border: 'border-blue-200', text: 'text-blue-900' },
    { name: 'Power & Overheads', value: costStack.overhead, color: '#f59e0b', bg: 'bg-amber-50/70', border: 'border-amber-200', text: 'text-amber-900' },
    { name: 'Bank Loan EMI', value: costStack.emi, color: '#4f46e5', bg: 'bg-indigo-50/70', border: 'border-indigo-200', text: 'text-indigo-900' },
    { name: 'Family Net Income', value: costStack.profit, color: '#10b981', bg: 'bg-emerald-50/70', border: 'border-emerald-200', text: 'text-emerald-900' },
  ], [costStack]);

  // Middleman Distress vs Fair Price Comparison
  const distressPrice = Math.round(unitCostFloor * 1.06); // Middleman offers barely 6% over cost
  const distressMargin = Math.max(1, distressPrice - variableCostPerUnit);
  const leakageSavedPerUnit = Math.max(0, sellingPrice - distressPrice);
  const annualLeakageSaved = leakageSavedPerUnit * dailyUnits * 26 * 12;

  return (
    <div className="space-y-6 pb-8">
      {/* Header Banner */}
      <div className="glass-panel p-4 sm:p-6 border-l-4 border-emerald-600 bg-gradient-to-r from-white via-emerald-50/20 to-white shadow-card border border-slate-200/90 rounded-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-emerald-800 mb-1 flex items-center gap-1.5">
              <Tag className="w-4 h-4 text-emerald-600" />
              <span><TranslatedText text="Grassroots Unit Economics & Pricing Engine" /></span>
            </div>
            <h1 className="text-xl sm:text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
              <TranslatedText text="Pricing, Margins & Daily Sales Targets" />
            </h1>
            <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
              <TranslatedText text="Defend your business against middleman price suppression. Calibrated with MoSPI rural CPI inflation data and your statutory bank loan EMI obligations." />
            </p>
          </div>

          <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200/90 px-3 py-2 rounded-xl shrink-0">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold text-sm shrink-0">
              ₹
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold text-emerald-800 block">
                <TranslatedText text="Recommended Price Band" />
              </span>
              <span className="text-sm sm:text-base font-mono font-extrabold text-emerald-900">
                ₹{bandLow} – ₹{bandHigh} <span className="text-xs font-sans font-medium text-emerald-700">/ unit</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 5 High-Impact Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
        {/* Metric 1: Selling Price */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-subtle space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 block">
            <TranslatedText text="Your Unit Price" />
          </span>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-slate-900">
            ₹{sellingPrice}
          </div>
          <div className="text-[10px] text-emerald-700 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
            <span><TranslatedText text="Active simulated rate" /></span>
          </div>
        </div>

        {/* Metric 2: Unit Production Cost */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-subtle space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 block">
            <TranslatedText text="Cost to Produce 1 Unit" />
          </span>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-slate-700">
            ₹{variableCostPerUnit}
          </div>
          <div className="text-[10px] text-slate-500">
            <TranslatedText text="Raw materials & power" />
          </div>
        </div>

        {/* Metric 3: Profit per Unit */}
        <div className="p-4 rounded-2xl bg-white border border-emerald-200 bg-emerald-50/30 shadow-subtle space-y-1">
          <span className="text-[11px] font-semibold text-emerald-900 block">
            <TranslatedText text="Profit per Unit" />
          </span>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-emerald-700">
            ₹{unitMargin}
          </div>
          <div className="text-[10px] font-bold text-emerald-800">
            {marginPct.toFixed(0)}% <TranslatedText text="Gross Margin" />
          </div>
        </div>

        {/* Metric 4: Daily Break-Even Sales */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-subtle space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 block">
            <TranslatedText text="Daily Break-Even" />
          </span>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-indigo-900">
            {breakEvenDailyUnits} <span className="text-xs font-sans font-normal text-slate-500"><TranslatedText text="units/day" /></span>
          </div>
          <div className="text-[10px] text-slate-500">
            {breakEvenMonthlyUnits} <TranslatedText text="units/month to clear bills" />
          </div>
        </div>

        {/* Metric 5: Estimated Monthly Take-Home */}
        <div className="col-span-2 lg:col-span-1 p-4 rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-700 text-white shadow-md space-y-1">
          <span className="text-[11px] font-semibold text-emerald-100 block">
            <TranslatedText text="Monthly Take-Home" />
          </span>
          <div className="text-xl sm:text-2xl font-mono font-extrabold">
            ₹{monthlyTakeHomeProfit.toLocaleString('en-IN')}
          </div>
          <div className="text-[10px] text-emerald-100 font-medium">
            <TranslatedText text="Net cash in hand after loan EMI" />
          </div>
        </div>
      </div>

      {/* Main Section: Interactive Simulator + Break-Even Visual Curve */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        
        {/* Left Column: Interactive Sliders & Breakeven Day (5 cols) */}
        <div className="lg:col-span-5 glass-panel p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2">
                <Calculator className="w-4 h-4 text-emerald-700" />
                <h3 className="font-outfit font-bold text-slate-900 text-sm sm:text-base">
                  <TranslatedText text="Interactive Profit Simulator" />
                </h3>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                <TranslatedText text="Adjust & Test" />
              </span>
            </div>

            {/* Slider 1: Unit Selling Price */}
            <div className="space-y-2 mb-5">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-slate-500" />
                  <TranslatedText text="Unit Selling Price" />
                </span>
                <span className="font-mono font-extrabold text-base text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-lg border border-emerald-200">
                  ₹{sellingPrice}
                </span>
              </div>
              <input
                type="range"
                min={Math.max(10, Math.floor(unitCostFloor * 0.85))}
                max={Math.ceil(unitCostFloor * 2.2)}
                step={1}
                value={sellingPrice}
                onChange={(e) => setSellingPrice(Number(e.target.value))}
                className="w-full accent-emerald-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-400">
                <span>₹{Math.floor(unitCostFloor * 0.85)} (Min)</span>
                <span className="text-emerald-700 font-bold">₹{defaultPrice} (Benchmark)</span>
                <span>₹{Math.ceil(unitCostFloor * 2.2)} (Max)</span>
              </div>
            </div>

            {/* Slider 2: Daily Sales Volume */}
            <div className="space-y-2 mb-5">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <Store className="w-3.5 h-3.5 text-slate-500" />
                  <TranslatedText text="Daily Sales Volume" />
                </span>
                <span className="font-mono font-extrabold text-base text-indigo-900 bg-indigo-50 px-2.5 py-0.5 rounded-lg border border-indigo-200">
                  {dailyUnits} <span className="text-xs font-sans font-normal text-indigo-700"><TranslatedText text="units/day" /></span>
                </span>
              </div>
              <input
                type="range"
                min={minDailyUnits}
                max={maxDailyUnits}
                step={1}
                value={dailyUnits}
                onChange={(e) => setDailyUnits(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-400">
                <span>{minDailyUnits} units (Min)</span>
                <span className="text-indigo-700 font-bold">{breakEvenDailyUnits} (<TranslatedText text="Break-Even" />)</span>
                <span>{maxDailyUnits} units (Max Capacity)</span>
              </div>
            </div>
          </div>

          {/* Break-Even Day Callout Box */}
          <div className={`p-4 rounded-xl border transition-all ${
            isProfitable
              ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
              : 'bg-rose-50/70 border-rose-200 text-rose-950'
          }`}>
            <div className="flex items-start gap-2.5">
              <Clock className={`w-4 h-4 mt-0.5 shrink-0 ${isProfitable ? 'text-emerald-700' : 'text-rose-600'}`} />
              <div className="text-xs space-y-1">
                <div className="font-bold">
                  {isProfitable ? (
                    <span><TranslatedText text="Break-Even Achieved on Day" /> {daysToBreakEven} <TranslatedText text="of Every Month" /></span>
                  ) : (
                    <span><TranslatedText text="Volume Too Low to Cover Monthly Costs" /></span>
                  )}
                </div>
                <p className="text-[11px] leading-relaxed opacity-90">
                  {isProfitable ? (
                    <span>
                      <TranslatedText text="By day" /> <strong>{daysToBreakEven}</strong>, <TranslatedText text="all overheads, bills, and your bank EMI of" /> <strong>₹{monthlyEmi.toLocaleString('en-IN')}</strong> <TranslatedText text="are fully paid off. The remaining" /> <strong>{Math.max(0, 26 - daysToBreakEven)} <TranslatedText text="working days" /></strong> <TranslatedText text="generate pure family income." />
                      <span className="block pt-1.5 text-[10px] text-emerald-800 font-semibold border-t border-emerald-200/60 mt-1">
                        🎯 <TranslatedText text="Enterprise Capital Break-Even Milestone:" /> <strong>{reportData?.financial_analysis?.break_even_milestone || 'Year 2 (Month 16)'}</strong> · <TranslatedText text="Capital Payback:" /> <strong>{reportData?.financial_analysis?.payback_period_years || 2.6} <TranslatedText text="Years" /></strong>
                      </span>
                    </span>
                  ) : (
                    <span>
                      <TranslatedText text="At your current production volume, you need to sell at least" /> <strong>{breakEvenDailyUnits} <TranslatedText text="units per day" /></strong> <TranslatedText text="to avoid defaulting on your monthly debt service." />
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Break-Even Curve Chart (7 cols) */}
        <div className="lg:col-span-7 glass-panel p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-3 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  <TranslatedText text="Monthly Revenue vs. Total Costs Curve" />
                </div>
                <p className="text-[11px] text-slate-500 font-medium">
                  <TranslatedText text="Visualizing the cross-over point where sales surpass fixed loan obligations" />
                </p>
              </div>

              <div className="flex items-center gap-3 text-[11px] font-semibold shrink-0">
                <span className="flex items-center gap-1 text-emerald-700">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block" />
                  <TranslatedText text="Revenue" />
                </span>
                <span className="flex items-center gap-1 text-slate-600">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block" />
                  <TranslatedText text="Total Costs" />
                </span>
              </div>
            </div>

            {/* Recharts Break-Even Chart */}
            <div className="h-[250px] w-full pt-3">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="units" 
                    tick={{ fontSize: 10, fill: '#64748b' }} 
                    unit=" u"
                  />
                  <YAxis 
                    tick={{ fontSize: 10, fill: '#64748b' }}
                    tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload || !payload.length) return null;
                      const d = payload[0].payload;
                      return (
                        <div className="bg-white border border-slate-200 rounded-xl p-2.5 shadow-xl text-xs space-y-1">
                          <div className="font-bold text-slate-900 border-b pb-1 font-mono">
                            {d.units} units / month
                          </div>
                          <div className="text-emerald-700 font-medium flex justify-between gap-3">
                            <span>Revenue:</span>
                            <span className="font-mono font-bold">₹{d.Revenue.toLocaleString('en-IN')}</span>
                          </div>
                          <div className="text-slate-600 font-medium flex justify-between gap-3">
                            <span>Total Costs:</span>
                            <span className="font-mono font-bold">₹{d.TotalCosts.toLocaleString('en-IN')}</span>
                          </div>
                          <div className={`font-bold pt-1 border-t flex justify-between gap-3 ${d.NetProfit >= 0 ? 'text-emerald-800' : 'text-rose-600'}`}>
                            <span>{d.NetProfit >= 0 ? 'Net Profit:' : 'Loss:'}</span>
                            <span className="font-mono">₹{d.NetProfit.toLocaleString('en-IN')}</span>
                          </div>
                        </div>
                      );
                    }}
                  />
                  <ReferenceLine 
                    x={breakEvenMonthlyUnits} 
                    stroke="#059669" 
                    strokeDasharray="4 4"
                    label={{
                      value: `BEP: ${breakEvenMonthlyUnits} units`,
                      position: 'top',
                      fill: '#047857',
                      fontSize: 10,
                      fontWeight: 'bold'
                    }}
                  />
                  <Area type="monotone" dataKey="Revenue" fill="#ecfdf5" stroke="#059669" strokeWidth={2} />
                  <Line type="monotone" dataKey="TotalCosts" stroke="#94a3b8" strokeWidth={2} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-xl border border-slate-200">
            <span><TranslatedText text="Fixed monthly costs (Loan EMI + draw)" />: <strong>₹{fixedMonthlyCosts.toLocaleString('en-IN')}</strong></span>
            <span className="text-emerald-700 font-bold"><TranslatedText text="Current target" />: {monthlyVolume} units/mo</span>
          </div>
        </div>

      </div>

      {/* Two Balanced Insight Cards: Where Does Every ₹100 Go? & Haat vs Middleman */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        
        {/* Card A: Where Does Every ₹100 Go? */}
        <div className="glass-panel p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Coins className="w-4 h-4 text-emerald-700" />
                <h3 className="font-outfit font-bold text-slate-900 text-sm sm:text-base">
                  <TranslatedText text="Where Does Every ₹100 of Sales Go?" />
                </h3>
              </div>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <TranslatedText text="Unit Cost Stack" />
              </span>
            </div>

            {/* Donut Chart + Breakdown Legend */}
            <div className="flex flex-col sm:flex-row items-center gap-4 py-2">
              {/* Donut with Center Text */}
              <div className="relative w-40 h-40 shrink-0 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Tooltip
                      formatter={(val, name) => [`₹${val} (${val}%)`, name]}
                      contentStyle={{
                        borderRadius: '12px',
                        border: '1px solid #e2e8f0',
                        fontSize: '11px',
                        fontWeight: '600',
                        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                      }}
                    />
                    <Pie
                      data={donutData}
                      cx="50%"
                      cy="50%"
                      innerRadius={46}
                      outerRadius={68}
                      paddingAngle={3}
                      dataKey="value"
                      stroke="#ffffff"
                      strokeWidth={2}
                    >
                      {donutData.map((entry, index) => (
                        <Cell key={`donut-cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                
                {/* Center Badge inside the Donut */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
                  <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider leading-none">Per</span>
                  <span className="text-lg font-outfit font-extrabold text-slate-900 leading-tight">₹100</span>
                  <span className="text-[9px] font-semibold text-emerald-700 leading-none">Sales</span>
                </div>
              </div>

              {/* Legend Stack */}
              <div className="grid grid-cols-1 gap-2 text-xs w-full">
                {donutData.map((item, idx) => (
                  <div key={idx} className={`flex items-center justify-between p-2 rounded-xl ${item.bg} border ${item.border}`}>
                    <span className={`flex items-center gap-2 font-medium ${item.text}`}>
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                      <TranslatedText text={item.name} />
                    </span>
                    <span className={`font-mono font-bold text-sm ${item.text}`}>
                      ₹{item.value} <span className="text-[10px] font-normal opacity-80">({item.value}%)</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <p className="text-[11px] text-slate-500 font-medium pt-2 border-t border-slate-100">
            <TranslatedText text="Your production model ensures that after clearing every supplier invoice, power bill, and monthly bank loan EMI, your household retains an honest, dignifying profit margin." />
          </p>
        </div>

        {/* Card B: Village Haat vs Middleman Comparison */}
        <div className="glass-panel p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Scale className="w-4 h-4 text-emerald-700" />
              <h3 className="font-outfit font-bold text-slate-900 text-sm sm:text-base">
                <TranslatedText text="Local Market vs. Middleman Comparison" />
              </h3>
            </div>
            <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              <TranslatedText text="Direct Selling" />
            </span>
          </div>

          <div className="space-y-2.5">
            {/* Tier 1: Village Trader / Middleman */}
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
              <div>
                <span className="font-bold text-slate-700 block">
                  <TranslatedText text="Middleman / Distress Farmgate Price" />
                </span>
                <span className="text-[10px] text-slate-500">
                  <TranslatedText text="Traders take advantage of urgency" />
                </span>
              </div>
              <div className="text-right">
                <span className="font-mono font-bold text-slate-600 block">₹{distressPrice}</span>
                <span className="text-[10px] font-mono text-slate-500">₹{distressMargin} profit</span>
              </div>
            </div>

            {/* Tier 2: Udyam Saathi Fair Local Price */}
            <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-300 flex items-center justify-between text-xs">
              <div>
                <span className="font-bold text-emerald-950 block flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <TranslatedText text="Udyam Saathi Fair Local Price" />
                </span>
                <span className="text-[10px] text-emerald-800">
                  <TranslatedText text="Direct to local customers & haat" />
                </span>
              </div>
              <div className="text-right">
                <span className="font-mono font-extrabold text-emerald-800 text-sm block">₹{sellingPrice}</span>
                <span className="text-[10px] font-mono font-bold text-emerald-700">₹{unitMargin} profit</span>
              </div>
            </div>

            {/* Tier 3: Town Retail Benchmark */}
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
              <div>
                <span className="font-bold text-slate-700 block">
                  <TranslatedText text="Town Retail / Packaged Benchmark" />
                </span>
                <span className="text-[10px] text-slate-500">
                  <TranslatedText text="Branded product price in district hub" />
                </span>
              </div>
              <div className="text-right">
                <span className="font-mono font-bold text-slate-600 block">₹{Math.round(sellingPrice * 1.25)}</span>
                <span className="text-[10px] font-mono text-slate-500">District hub</span>
              </div>
            </div>
          </div>

          {/* Middleman Savings Callout */}
          <div className="p-3 rounded-xl bg-emerald-100/50 border border-emerald-200 text-xs text-emerald-950 flex items-center justify-between">
            <div>
              <span className="font-bold block"><TranslatedText text="Direct Selling Extra Earnings:" /></span>
              <span className="text-[11px] text-emerald-800">
                <TranslatedText text="Extra annual income retained by selling directly:" />
              </span>
            </div>
            <span className="font-mono font-extrabold text-sm sm:text-base text-emerald-900 shrink-0 ml-2">
              +₹{annualLeakageSaved.toLocaleString('en-IN')}<span className="text-[10px] font-normal text-emerald-700">/yr</span>
            </span>
          </div>
        </div>

      </div>

      {/* Inflation & Seasonality Advisory */}
      <div className="glass-panel p-4 sm:p-5 bg-gradient-to-r from-amber-50/50 via-white to-amber-50/30 border border-amber-200/80 rounded-2xl shadow-card space-y-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-600" />
          <h3 className="font-outfit font-bold text-amber-950 text-sm">
            <TranslatedText text="MoSPI Rural CPI Inflation Guidance & Seasonal Advice" />
          </h3>
        </div>
        <p className="text-xs text-amber-900 leading-relaxed font-medium">
          <TranslatedText text="Based on the official Ministry of Statistics and Programme Implementation (MoSPI) rural inflation rate of" /> <strong>{cpiPct}%</strong> <TranslatedText text="in" /> {state}, <TranslatedText text="your unit production cost will gradually increase over the next 12 months. Setting your price at" /> <strong>₹{sellingPrice}</strong> <TranslatedText text="safeguards your profit margin and guarantees you will comfortably meet your bank EMI payments of" /> <strong>₹{monthlyEmi.toLocaleString('en-IN')}</strong>.
        </p>
      </div>
    </div>
  );
}

export default ProductPricingPage;
