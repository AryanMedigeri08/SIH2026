import React, { useState, useEffect } from 'react';
import { 
  Building2, MapPin, User, Coins, Clock, CheckCircle2, 
  ChevronRight, ChevronLeft, Sparkles, X, Loader2 
} from 'lucide-react';
import { fetchStates, fetchDistricts, fetchBlocks, fetchVillages } from '../../services/api';

export function FeasibilityWizard({ isOpen, onClose, onSubmit, isSubmitting, initialData }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    enterprise_name: "Joypur Fresh Dairy Processing Unit",
    business_category: "manufacturing",
    sector: "dairy",
    promoter_name: "Dipankar Ghosh",
    promoter_category: "general",
    gender: "Male",
    state_name: "West Bengal",
    district_name: "Bankura",
    block_name: "Joypur",
    village_name: "Joypur",
    is_rural: true,
    project_cost: 900000,
    annual_turnover_estimate: 950000,
    tenure_years: 7,
    moratorium_months: 6,
    language: "en",
    ...initialData,
  });

  // LGD Dropdown states
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [blocks, setBlocks] = useState([]);
  const [villages, setVillages] = useState([]);
  const [loadingLgd, setLoadingLgd] = useState(false);

  useEffect(() => {
    if (initialData) {
      setFormData(prev => ({ ...prev, ...initialData }));
    }
  }, [initialData]);

  // Initial states load
  useEffect(() => {
    async function loadStates() {
      const s = await fetchStates();
      setStates(s || []);
    }
    loadStates();
  }, []);

  // Cascading state -> districts
  useEffect(() => {
    if (!formData.state_name) return;
    async function loadDistricts() {
      setLoadingLgd(true);
      const d = await fetchDistricts(formData.state_name);
      setDistricts(d || []);
      setLoadingLgd(false);
    }
    loadDistricts();
  }, [formData.state_name]);

  // Cascading district -> blocks & villages
  useEffect(() => {
    if (!formData.district_name) return;
    async function loadSubunits() {
      setLoadingLgd(true);
      const [b, v] = await Promise.all([
        fetchBlocks(formData.district_name),
        fetchVillages(formData.district_name),
      ]);
      setBlocks(b || []);
      setVillages(v || []);
      setLoadingLgd(false);
    }
    loadSubunits();
  }, [formData.district_name]);

  if (!isOpen) return null;

  const steps = [
    { num: 1, title: 'Enterprise', icon: Building2 },
    { num: 2, title: 'LGD Location', icon: MapPin },
    { num: 3, title: 'Promoter', icon: User },
    { num: 4, title: 'Capital & Sales', icon: Coins },
    { num: 5, title: 'Loan Terms', icon: Clock },
    { num: 6, title: 'Review & Run', icon: CheckCircle2 },
  ];

  const handleNext = () => setCurrentStep(prev => Math.min(prev + 1, 6));
  const handleBack = () => setCurrentStep(prev => Math.max(prev - 1, 1));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0b1120] border border-indigo-500/25 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden my-8">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 px-6 py-5 border-b border-indigo-500/20 flex justify-between items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-400">
                <Sparkles className="w-5 h-5" />
              </span>
              <h2 className="font-outfit text-xl font-bold text-white">
                6-Step Enterprise Feasibility Appraisal Wizard
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Multi-Tier LGD demographic mapping, financial solvency & credit synthesis engine.
            </p>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Stepper Progress Bar */}
        <div className="bg-slate-900/80 px-6 py-3 border-b border-slate-800 flex justify-between items-center">
          {steps.map((s, idx) => {
            const Icon = s.icon;
            const isDone = s.num < currentStep;
            const isCurrent = s.num === currentStep;
            return (
              <div key={s.num} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  isDone 
                    ? 'bg-emerald-500 text-white' 
                    : isCurrent 
                    ? 'bg-cyan-500 text-black ring-4 ring-cyan-500/20 shadow-glow-cyan' 
                    : 'bg-slate-800 text-slate-500'
                }`}>
                  {isDone ? '✓' : <Icon className="w-4 h-4" />}
                </div>
                <span className={`text-xs font-medium hidden sm:inline ${
                  isCurrent ? 'text-cyan-400 font-semibold' : isDone ? 'text-slate-300' : 'text-slate-500'
                }`}>
                  {s.title}
                </span>
                {idx < steps.length - 1 && (
                  <div className="w-4 sm:w-8 h-0.5 bg-slate-800 mx-1 hidden md:block" />
                )}
              </div>
            );
          })}
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 sm:p-8 space-y-6">
          
          {/* Step 1: Enterprise Profile */}
          {currentStep === 1 && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Building2 className="w-4 h-4 text-cyan-400" />
                Step 1: Enterprise Identity & Industry Classification
              </h3>
              
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Enterprise Commercial Name</label>
                <input
                  type="text"
                  required
                  value={formData.enterprise_name}
                  onChange={e => setFormData({ ...formData, enterprise_name: e.target.value })}
                  placeholder="e.g. Joypur Fresh Dairy Processing Unit"
                  className="w-full bg-slate-900/90 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400 transition"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Business Type</label>
                  <select
                    value={formData.business_category}
                    onChange={e => setFormData({ ...formData, business_category: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                  >
                    <option value="manufacturing">Manufacturing (Production / Processing)</option>
                    <option value="service">Service (Repair, Retail, Digital)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Industry Sector</label>
                  <select
                    value={formData.sector}
                    onChange={e => setFormData({ ...formData, sector: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                  >
                    <option value="dairy">Dairy & Milk Processing</option>
                    <option value="food_processing">Food Processing & Agro Milling</option>
                    <option value="repair">Auto, Mobile & Electronics Repair</option>
                    <option value="apparel">Apparel, Tailoring & Handloom</option>
                    <option value="fabrication">Light Engineering & Metal Fabrication</option>
                    <option value="artisan_trades">Artisan & Craft Trades</option>
                    <option value="general">General Commercial MSME</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: LGD Location Hierarchy */}
          {currentStep === 2 && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="flex justify-between items-center">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-cyan-400" />
                  Step 2: Local Government Directory (LGD) Hierarchy
                </h3>
                {loadingLgd && (
                  <span className="text-xs text-cyan-400 flex items-center gap-1.5">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" /> Querying Census & LGD...
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">1. State / UT</label>
                  <select
                    value={formData.state_name}
                    onChange={e => setFormData({ ...formData, state_name: e.target.value, district_name: '', block_name: '', village_name: '' })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                  >
                    {states.map(s => (
                      <option key={s.state_code || s.state_name} value={s.state_name}>{s.state_name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">2. District</label>
                  <select
                    value={formData.district_name}
                    onChange={e => setFormData({ ...formData, district_name: e.target.value, block_name: '', village_name: '' })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                  >
                    <option value="">-- Select District --</option>
                    {districts.map(d => (
                      <option key={d.district_code || d.district_name} value={d.district_name}>{d.district_name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">3. Development Block</label>
                  <select
                    value={formData.block_name}
                    onChange={e => setFormData({ ...formData, block_name: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                  >
                    <option value="">-- Select Block --</option>
                    {blocks.map(b => (
                      <option key={b.development_block_code || b.development_block_name} value={b.development_block_name}>{b.development_block_name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">4. Gram Panchayat / Village</label>
                  <select
                    value={formData.village_name}
                    onChange={e => setFormData({ ...formData, village_name: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                  >
                    <option value="">-- Select Village --</option>
                    {villages.map(v => (
                      <option key={v.village_code || v.village_name} value={v.village_name}>{v.village_name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="pt-2">
                <label className="block text-xs font-semibold text-slate-300 mb-2">Area Classification (Affects PMEGP 25% vs 35% subsidy)</label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 text-xs text-slate-200 cursor-pointer">
                    <input
                      type="radio"
                      name="is_rural"
                      checked={formData.is_rural === true}
                      onChange={() => setFormData({ ...formData, is_rural: true })}
                      className="accent-cyan-400"
                    />
                    <span>Rural Area (Up to 35% PMEGP Subsidy)</span>
                  </label>
                  <label className="flex items-center gap-2 text-xs text-slate-200 cursor-pointer">
                    <input
                      type="radio"
                      name="is_rural"
                      checked={formData.is_rural === false}
                      onChange={() => setFormData({ ...formData, is_rural: false })}
                      className="accent-cyan-400"
                    />
                    <span>Urban / Semi-Urban Area (15% Subsidy)</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Promoter Details */}
          {currentStep === 3 && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <User className="w-4 h-4 text-cyan-400" />
                Step 3: Promoter Identity & Social Beneficiary Category
              </h3>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Promoter Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.promoter_name}
                  onChange={e => setFormData({ ...formData, promoter_name: e.target.value })}
                  placeholder="e.g. Dipankar Ghosh"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Social / Statutory Category</label>
                  <select
                    value={formData.promoter_category}
                    onChange={e => setFormData({ ...formData, promoter_category: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                  >
                    <option value="general">General Category (10% Margin)</option>
                    <option value="women">Women Entrepreneur (5% Margin • Special Slab)</option>
                    <option value="sc">Scheduled Caste (SC) (5% Margin)</option>
                    <option value="st">Scheduled Tribe (ST) (5% Margin)</option>
                    <option value="obc">Other Backward Class (OBC) (5% Margin)</option>
                    <option value="artisan">Artisan / Traditional Craftsman</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Gender</label>
                  <select
                    value={formData.gender}
                    onChange={e => setFormData({ ...formData, gender: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other / Transgender</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Capital Outlay & Sales */}
          {currentStep === 4 && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Coins className="w-4 h-4 text-cyan-400" />
                Step 4: Total Capital Investment & Annual Turnover Target
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Total Project Outlay (₹)</label>
                  <input
                    type="number"
                    required
                    min={25000}
                    step={5000}
                    value={formData.project_cost}
                    onChange={e => setFormData({ ...formData, project_cost: Number(e.target.value) })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white font-mono focus:outline-none focus:border-cyan-400"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Includes Machinery, Civil, Working Capital & Contingency</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Estimated Annual Gross Sales (₹)</label>
                  <input
                    type="number"
                    required
                    min={25000}
                    step={5000}
                    value={formData.annual_turnover_estimate}
                    onChange={e => setFormData({ ...formData, annual_turnover_estimate: Number(e.target.value) })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white font-mono focus:outline-none focus:border-cyan-400"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Projected 100% capacity annual sales revenue</p>
                </div>
              </div>

              <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl flex justify-between items-center text-xs">
                <span className="text-slate-300">Turnover to Capital Leverage:</span>
                <strong className="text-cyan-400 font-mono">
                  {formData.project_cost > 0 ? (formData.annual_turnover_estimate / formData.project_cost).toFixed(2) : 0}x
                </strong>
              </div>
            </div>
          )}

          {/* Step 5: Loan Terms & Moratorium */}
          {currentStep === 5 && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                Step 5: Commercial Bank Loan Repayment & Grace Terms
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Requested Repayment Tenure (Years)</label>
                  <input
                    type="number"
                    min={1}
                    max={15}
                    step={0.5}
                    value={formData.tenure_years}
                    onChange={e => setFormData({ ...formData, tenure_years: Number(e.target.value) })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white font-mono focus:outline-none focus:border-cyan-400"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Standard MSME bank term loan tenure: 5 to 7 years</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Moratorium Grace Period (Months)</label>
                  <input
                    type="number"
                    min={0}
                    max={24}
                    value={formData.moratorium_months}
                    onChange={e => setFormData({ ...formData, moratorium_months: Number(e.target.value) })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white font-mono focus:outline-none focus:border-cyan-400"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Repayment begins after operational stabilization</p>
                </div>
              </div>
            </div>
          )}

          {/* Step 6: Language & Final Verification */}
          {currentStep === 6 && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                Step 6: Target Language & Verification
              </h3>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Credit Appraisal & Synthesis Language</label>
                <select
                  value={formData.language}
                  onChange={e => setFormData({ ...formData, language: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
                >
                  <option value="en">English (Official Bank Format)</option>
                  <option value="hi">हिंदी (Hindi)</option>
                  <option value="mr">मराठी (Marathi)</option>
                  <option value="ta">தமிழ் (Tamil)</option>
                  <option value="te">తెలుగు (Telugu)</option>
                  <option value="kn">ಕನ್ನಡ (Kannada)</option>
                </select>
              </div>

              {/* Summary card */}
              <div className="bg-slate-900/90 border border-slate-700/80 rounded-xl p-4 text-xs space-y-2">
                <div className="font-bold text-cyan-400 uppercase tracking-wider text-[11px]">Assessment Summary:</div>
                <div className="grid grid-cols-2 gap-2 text-slate-300">
                  <div>Enterprise: <strong>{formData.enterprise_name}</strong></div>
                  <div>Sector: <strong className="uppercase">{formData.sector}</strong></div>
                  <div>Location: <strong>{formData.village_name}, {formData.district_name} ({formData.state_name})</strong></div>
                  <div>Promoter: <strong>{formData.promoter_name} ({formData.promoter_category.toUpperCase()})</strong></div>
                  <div>Project Cost: <strong className="text-emerald-400 font-mono">₹{formData.project_cost.toLocaleString('en-IN')}</strong></div>
                  <div>Turnover: <strong className="text-cyan-400 font-mono">₹{formData.annual_turnover_estimate.toLocaleString('en-IN')}</strong></div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Controls */}
          <div className="flex justify-between items-center pt-4 border-t border-slate-800">
            {currentStep > 1 ? (
              <button
                type="button"
                onClick={handleBack}
                className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-white px-4 py-2.5 rounded-xl border border-slate-700 hover:bg-slate-800 transition"
              >
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
            ) : <div />}

            {currentStep < 6 ? (
              <button
                type="button"
                onClick={handleNext}
                className="flex items-center gap-1.5 text-xs font-semibold text-black bg-cyan-400 hover:bg-cyan-300 px-5 py-2.5 rounded-xl shadow-glow-cyan transition"
              >
                Next Step <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2 text-xs font-bold text-white bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 px-6 py-2.5 rounded-xl shadow-glow-emerald transition disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Executing 4-Tier Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Run Bank Feasibility Analysis</span>
                  </>
                )}
              </button>
            )}
          </div>

        </form>

      </div>
    </div>
  );
}
