import React, { useState, useEffect } from 'react';
import { 
  Building2, MapPin, User, Coins, Clock, FileText, CheckCircle2, 
  ChevronRight, ChevronLeft, Sparkles, X, Loader2, Compass, 
  AlertCircle, Info, ShieldCheck, Languages, Check
} from 'lucide-react';
import { fetchStates, fetchDistricts, fetchBlocks, fetchVillages, fetchOdopProduct } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

/**
 * Statutory Promoter Margin Equity Requirement Rule:
 * General Category = 10% (0.10)
 * Special/Reserved Category (Women, SC, ST, OBC, Artisan, etc.) = 5% (0.05)
 */
export const getMarginPct = (category) => {
  return category && category.toLowerCase() !== "general" ? 0.05 : 0.10;
};

export function FeasibilityWizard({ isOpen, onClose, onSubmit, isSubmitting, initialData }) {
  const { userProfile } = useAuth() || {};
  const { language: appLanguage, setLanguage, languages, t } = useLanguage();
  const [currentStep, setCurrentStep] = useState(1);
  const [odopHint, setOdopHint] = useState(null);
  const [formData, setFormData] = useState(() => {
    const initCat = initialData?.promoter_category || "general";
    const marginPct = getMarginPct(initCat);
    const cost = initialData?.project_cost !== undefined ? initialData.project_cost : 900000;
    const margin = initialData?.margin_capital !== undefined 
      ? initialData.margin_capital 
      : Math.round(cost * marginPct);

    return {
      enterprise_name: "Joypur Fresh Dairy Processing Unit",
      business_category: "manufacturing",
      sector: "dairy",
      promoter_name: userProfile?.name || "Dipankar Ghosh",
      promoter_category: initCat,
      gender: userProfile?.gender && userProfile.gender !== "Unspecified" ? userProfile.gender : "Male",
      state_name: "West Bengal",
      district_name: "Bankura",
      block_name: "Joypur",
      village_name: "Joypur",
      is_rural: true,
      margin_capital: margin,
      project_cost: cost,
      annual_turnover_estimate: 950000,
      tenure_years: 7,
      moratorium_months: 6,
      additional_business_details: "",
      monthly_net_operating_income_override: "",
      language: "en",
      ...initialData,
    };
  });

  // LGD Dropdown states
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [blocks, setBlocks] = useState([]);
  const [villages, setVillages] = useState([]);
  const [loadingLgd, setLoadingLgd] = useState(false);

  // Geolocation detection state
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);
  const [locationDetectError, setLocationDetectError] = useState(null);
  const [locationSuccessMsg, setLocationSuccessMsg] = useState(null);

  useEffect(() => {
    if (initialData) {
      setFormData(prev => {
        const cat = initialData.promoter_category || prev.promoter_category || "general";
        const marginPct = getMarginPct(cat);
        const cost = initialData.project_cost !== undefined ? initialData.project_cost : (prev.project_cost || 900000);
        const margin = initialData.margin_capital !== undefined 
          ? initialData.margin_capital 
          : Math.round(cost * marginPct);
        return {
          ...prev,
          ...initialData,
          margin_capital: margin,
          project_cost: cost,
        };
      });
    }
  }, [initialData]);

  // If user profile is available, pre-fill promoter name if empty or default
  useEffect(() => {
    if (userProfile?.name && (!formData.promoter_name || formData.promoter_name === "Dipankar Ghosh")) {
      setFormData(prev => ({ ...prev, promoter_name: userProfile.name }));
    }
  }, [userProfile]);

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

  // Sync ODOP data for selected district
  useEffect(() => {
    if (!formData.district_name) {
      setOdopHint(null);
      return;
    }
    let isCurrent = true;
    async function checkOdop() {
      const data = await fetchOdopProduct(formData.state_name, formData.district_name);
      if (isCurrent && data?.has_odop_record) {
        setOdopHint(data);
      } else if (isCurrent) {
        setOdopHint(null);
      }
    }
    checkOdop();
    return () => { isCurrent = false; };
  }, [formData.state_name, formData.district_name]);

  // Browser Geolocation Auto-Detection
  const handleDetectLocation = () => {
    if (!navigator.geolocation) {
      setLocationDetectError("Geolocation is not supported by your browser.");
      return;
    }

    setIsDetectingLocation(true);
    setLocationDetectError(null);
    setLocationSuccessMsg(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          // Reverse geocode via OpenStreetMap Nominatim
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json&addressdetails=1`
          );
          
          if (!response.ok) {
            throw new Error(`Reverse geocoding HTTP ${response.status}`);
          }
          
          const data = await response.json();
          const addr = data.address || {};

          const detectedState = addr.state || "";
          const detectedDistrict = addr.state_district || addr.district || addr.county || "";
          const detectedBlock = addr.county || addr.suburb || addr.town || addr.city_district || addr.municipality || "";
          const detectedVillage = addr.village || addr.suburb || addr.neighbourhood || addr.hamlet || addr.town || addr.city || "";

          // Match against available states
          let matchedState = states.find(s => 
            s.state_name?.toLowerCase() === detectedState.toLowerCase() ||
            detectedState.toLowerCase().includes(s.state_name?.toLowerCase()) ||
            s.state_name?.toLowerCase().includes(detectedState.toLowerCase())
          );
          
          const targetState = matchedState ? matchedState.state_name : (detectedState || formData.state_name);
          
          // Fetch districts for targetState
          let loadedDistricts = [];
          if (targetState) {
            loadedDistricts = await fetchDistricts(targetState) || [];
            setDistricts(loadedDistricts);
          }

          let matchedDistrict = loadedDistricts.find(d => 
            d.district_name?.toLowerCase() === detectedDistrict.toLowerCase() ||
            detectedDistrict.toLowerCase().includes(d.district_name?.toLowerCase()) ||
            d.district_name?.toLowerCase().includes(detectedDistrict.toLowerCase())
          );

          const targetDistrict = matchedDistrict ? matchedDistrict.district_name : (detectedDistrict || (loadedDistricts[0]?.district_name || ""));

          let loadedBlocks = [];
          let loadedVillages = [];
          if (targetDistrict) {
            const [b, v] = await Promise.all([
              fetchBlocks(targetDistrict),
              fetchVillages(targetDistrict),
            ]);
            loadedBlocks = b || [];
            loadedVillages = v || [];
            setBlocks(loadedBlocks);
            setVillages(loadedVillages);
          }

          let matchedBlock = loadedBlocks.find(b => 
            b.development_block_name?.toLowerCase() === detectedBlock.toLowerCase() ||
            detectedBlock.toLowerCase().includes(b.development_block_name?.toLowerCase()) ||
            b.development_block_name?.toLowerCase().includes(detectedBlock.toLowerCase())
          );
          const targetBlock = matchedBlock ? matchedBlock.development_block_name : (loadedBlocks[0]?.development_block_name || detectedBlock || "Main Block");

          let matchedVillage = loadedVillages.find(v => 
            v.village_name?.toLowerCase() === detectedVillage.toLowerCase() ||
            detectedVillage.toLowerCase().includes(v.village_name?.toLowerCase()) ||
            v.village_name?.toLowerCase().includes(detectedVillage.toLowerCase())
          );
          const targetVillage = matchedVillage ? matchedVillage.village_name : (loadedVillages[0]?.village_name || detectedVillage || "Main Village");

          // Update formData with resolved LGD fields
          // IMPORTANT: Leaves the area classification radio button (is_rural) untouched as requested!
          setFormData(prev => ({
            ...prev,
            state_name: targetState,
            district_name: targetDistrict,
            block_name: targetBlock,
            village_name: targetVillage,
          }));

          setLocationSuccessMsg(`Location Auto-Detected: ${targetVillage}, ${targetBlock}, ${targetDistrict}, ${targetState}`);
        } catch (err) {
          console.warn("GPS Reverse Geocoding note:", err);
          setLocationDetectError("GPS position retrieved, but address resolution was limited. Please confirm selections in dropdowns.");
        } finally {
          setIsDetectingLocation(false);
        }
      },
      (err) => {
        setIsDetectingLocation(false);
        if (err.code === 1) {
          setLocationDetectError("Location access was denied. Please allow location permissions in your browser or select manually.");
        } else {
          setLocationDetectError("Unable to acquire GPS coordinates. Please select your LGD location manually.");
        }
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
    );
  };

  const addNarrativeSnippet = (snippet) => {
    setFormData(prev => {
      const current = prev.additional_business_details || "";
      if (current.includes(snippet)) return prev;
      const separator = current.trim().length > 0 ? "; " : "";
      return {
        ...prev,
        additional_business_details: (current + separator + snippet).slice(0, 1000)
      };
    });
  };

  if (!isOpen) return null;

  const steps = [
    { num: 1, title: 'Enterprise', icon: Building2 },
    { num: 2, title: 'LGD Location', icon: MapPin },
    { num: 3, title: 'Promoter', icon: User },
    { num: 4, title: 'Capital & Sales', icon: Coins },
    { num: 5, title: 'Loan Terms', icon: Clock },
    { num: 6, title: 'Additional Details', icon: FileText },
    { num: 7, title: 'Review & Run', icon: CheckCircle2 },
  ];

  const handleNext = () => setCurrentStep(prev => Math.min(prev + 1, 7));
  const handleBack = () => setCurrentStep(prev => Math.max(prev - 1, 1));

  const handleSubmit = (e) => {
    e.preventDefault();
    const submissionPayload = {
      ...formData,
      monthly_net_operating_income_override: formData.monthly_net_operating_income_override 
        ? Number(formData.monthly_net_operating_income_override) 
        : undefined,
      additional_business_details: formData.additional_business_details?.trim() || undefined,
    };
    onSubmit(submissionPayload);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden my-4 sm:my-8 transform transition-all duration-300">
        
        {/* Header */}
        <div className="bg-slate-50 px-4 sm:px-6 py-3.5 sm:py-5 border-b border-slate-200 flex justify-between items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-sovereign-50 text-sovereign-800 border border-sovereign-200 shadow-sm animate-pulse">
                <Sparkles className="w-5 h-5" />
              </span>
              <h2 className="font-outfit text-xl font-bold text-slate-900">
                7-Step Enterprise Feasibility Appraisal Wizard
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 font-medium">
              Multi-Tier LGD demographic mapping, financial solvency & credit synthesis engine.
            </p>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-2 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Stepper Progress Bar */}
        <div className="bg-slate-100/70 px-3 sm:px-6 py-2.5 sm:py-3 border-b border-slate-200 flex items-center justify-start sm:justify-between overflow-x-auto gap-2 sm:gap-3 scroll-touch-x no-scrollbar">
          {steps.map((s, idx) => {
            const Icon = s.icon;
            const isDone = s.num < currentStep;
            const isCurrent = s.num === currentStep;
            return (
              <div key={s.num} className="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  onClick={() => setCurrentStep(s.num)}
                  className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-200 ${
                    isDone 
                      ? 'bg-emerald-600 text-white shadow-sm hover:bg-emerald-500' 
                      : isCurrent 
                      ? 'bg-sovereign-800 text-white ring-4 ring-sovereign-100 shadow-md scale-105' 
                      : 'bg-slate-200 text-slate-500 hover:bg-slate-300'
                  }`}
                  title={s.title}
                >
                  {isDone ? <Check className="w-3.5 h-3.5" /> : <Icon className="w-3.5 h-3.5" />}
                </button>
                <span className={`text-[11px] sm:text-xs font-semibold hidden md:inline transition-colors ${
                  isCurrent ? 'text-sovereign-900 font-bold' : isDone ? 'text-slate-700' : 'text-slate-400'
                }`}>
                  {s.title}
                </span>
                {idx < steps.length - 1 && (
                  <div className="w-2 sm:w-4 lg:w-6 h-0.5 bg-slate-200 mx-0.5 hidden sm:block" />
                )}
              </div>
            );
          })}
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-4 sm:p-8 space-y-4 sm:space-y-6">
          
          {/* Step 1: Enterprise Profile */}
          {currentStep === 1 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-sovereign-700" />
                Step 1: Enterprise Identity & Industry Classification
              </h3>
              
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Enterprise Commercial Name</label>
                <input
                  type="text"
                  required
                  value={formData.enterprise_name}
                  onChange={e => setFormData({ ...formData, enterprise_name: e.target.value })}
                  placeholder="e.g. Joypur Fresh Dairy Processing Unit"
                  className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 transition shadow-subtle"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Business Type</label>
                  <select
                    value={formData.business_category}
                    onChange={e => setFormData({ ...formData, business_category: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                  >
                    <option value="manufacturing">Manufacturing (Production / Processing)</option>
                    <option value="service">Service (Repair, Retail, Digital)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Industry Sector</label>
                  <select
                    value={formData.sector}
                    onChange={e => setFormData({ ...formData, sector: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                  >
                    <option value="dairy">Dairy & Milk Processing</option>
                    <option value="food_processing">Food Processing & Agro Milling</option>
                    <option value="repair">Auto, Mobile & Electronics Repair</option>
                    <option value="apparel">Apparel, Tailoring & Handloom</option>
                    <option value="fabrication">Light Engineering & Metal Fabrication</option>
                    <option value="artisan_trades">Artisan & Craft Trades</option>
                    <option value="general">General Commercial MSME</option>
                  </select>
                  {odopHint?.odop_product && (
                    <div className="mt-2 text-[11px] font-medium flex items-center gap-1.5 text-amber-900 bg-amber-50 border border-amber-200/80 px-2.5 py-1.5 rounded-lg">
                      <Sparkles className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                      <span>
                        <strong>{formData.district_name || "District"} ODOP:</strong> {odopHint.odop_product}
                        {odopHint.matching_sectors?.includes(formData.sector) && (
                          <span className="ml-1.5 font-bold text-emerald-800 bg-emerald-100/90 border border-emerald-300 px-1.5 py-0.5 rounded text-[10px]">
                            ✓ Matches District ODOP!
                          </span>
                        )}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: LGD Location Hierarchy + Geolocation Detection */}
          {currentStep === 2 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-sovereign-700" />
                  Step 2: Local Government Directory (LGD) Hierarchy
                </h3>
                
                {/* Geolocation Auto-Detect Button */}
                <button
                  type="button"
                  onClick={handleDetectLocation}
                  disabled={isDetectingLocation}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-50 hover:bg-sky-100 border border-sky-200 text-sky-800 text-xs font-bold transition-all shadow-subtle hover:shadow disabled:opacity-60 group"
                  title="Detect GPS coordinates and auto-fill LGD state, district, block, and village"
                >
                  <Compass className={`w-3.5 h-3.5 text-sky-600 ${isDetectingLocation ? 'animate-spin' : 'group-hover:rotate-45 transition-transform'}`} />
                  <span>{isDetectingLocation ? "Detecting GPS..." : "Auto-Detect My Location"}</span>
                </button>
              </div>

              {/* Status messages for Geolocation */}
              {locationDetectError && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-start gap-2 animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <span>{locationDetectError}</span>
                </div>
              )}

              {locationSuccessMsg && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-start gap-2 animate-in fade-in">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="font-medium">{locationSuccessMsg}</span>
                </div>
              )}

              {loadingLgd && (
                <div className="text-xs text-sovereign-700 flex items-center gap-1.5 font-medium">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading LGD directory subunits...
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">1. State / UT</label>
                  <select
                    value={formData.state_name}
                    onChange={e => setFormData({ ...formData, state_name: e.target.value, district_name: '', block_name: '', village_name: '' })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                  >
                    {states.map(s => (
                      <option key={s.state_code || s.state_name} value={s.state_name}>{s.state_name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">2. District</label>
                  <select
                    value={formData.district_name}
                    onChange={e => setFormData({ ...formData, district_name: e.target.value, block_name: '', village_name: '' })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                  >
                    <option value="">-- Select District --</option>
                    {districts.map(d => (
                      <option key={d.district_code || d.district_name} value={d.district_name}>{d.district_name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">3. Development Block</label>
                  <select
                    value={formData.block_name}
                    onChange={e => setFormData({ ...formData, block_name: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                  >
                    <option value="">-- Select Block --</option>
                    {blocks.map(b => (
                      <option key={b.development_block_code || b.development_block_name} value={b.development_block_name}>{b.development_block_name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">4. Gram Panchayat / Village</label>
                  <select
                    value={formData.village_name}
                    onChange={e => setFormData({ ...formData, village_name: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                  >
                    <option value="">-- Select Village --</option>
                    {villages.map(v => (
                      <option key={v.village_code || v.village_name} value={v.village_name}>{v.village_name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Real-Time ODOP Cluster Discovery Banner */}
              {odopHint && (
                <div className="p-3.5 rounded-xl bg-gradient-to-r from-amber-50 via-sky-50/40 to-amber-50 border border-amber-200 shadow-xs flex items-start gap-2.5 text-xs text-amber-950 animate-in fade-in">
                  <div className="p-1.5 rounded-lg bg-amber-100 text-amber-800 shrink-0 mt-0.5">
                    <Sparkles className="w-4 h-4 text-amber-700" />
                  </div>
                  <div className="space-y-1 w-full">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-md bg-amber-600 text-white font-bold text-[10px] font-mono uppercase tracking-wider">
                          One District One Product (ODOP)
                        </span>
                        <span className="font-bold text-slate-900 text-xs sm:text-sm">{odopHint.odop_product}</span>
                      </div>
                      {odopHint.pmfme_eligible && (
                        <span className="px-2 py-0.5 rounded-full bg-emerald-100 border border-emerald-300 text-emerald-800 text-[10px] font-bold">
                          35% PMFME Subsidy
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      Statutory cluster identified under MoFPI & DPIIT. Enterprises in this cluster receive <strong>priority bank sanction</strong>, GeM ODOP corridor access, and testing lab subsidies.
                    </p>
                  </div>
                </div>
              )}

              {/* Area Classification (Kept as user confirmation choice, untouched by GPS) */}
              <div className="pt-3 border-t border-slate-100">
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Area Classification (Determines PMEGP 25% vs 35% Subsidy Slab)
                </label>
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer font-medium p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 transition">
                    <input
                      type="radio"
                      name="is_rural"
                      checked={formData.is_rural === true}
                      onChange={() => setFormData({ ...formData, is_rural: true })}
                      className="accent-sovereign-700"
                    />
                    <span>Rural Catchment (Up to 35% PMEGP Capital Subsidy)</span>
                  </label>
                  <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer font-medium p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 transition">
                    <input
                      type="radio"
                      name="is_rural"
                      checked={formData.is_rural === false}
                      onChange={() => setFormData({ ...formData, is_rural: false })}
                      className="accent-sovereign-700"
                    />
                    <span>Urban / Semi-Urban Catchment (15% Subsidy)</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Promoter Details */}
          {currentStep === 3 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <User className="w-4 h-4 text-sovereign-700" />
                Step 3: Promoter Identity & Social Beneficiary Category
              </h3>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Promoter Full Legal Name</label>
                <input
                  type="text"
                  required
                  value={formData.promoter_name}
                  onChange={e => setFormData({ ...formData, promoter_name: e.target.value })}
                  placeholder="e.g. Dipankar Ghosh"
                  className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Social / Statutory Category</label>
                  <select
                    value={formData.promoter_category}
                    onChange={e => {
                      const newCat = e.target.value;
                      const newMarginPct = getMarginPct(newCat);
                      const currentMargin = Number(formData.margin_capital) || Math.round((Number(formData.project_cost) || 900000) * getMarginPct(formData.promoter_category));
                      const derivedCost = newMarginPct > 0 ? Math.round(currentMargin / newMarginPct) : currentMargin * 10;
                      setFormData(prev => ({
                        ...prev,
                        promoter_category: newCat,
                        margin_capital: currentMargin,
                        project_cost: derivedCost,
                      }));
                    }}
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                  >
                    <option value="general">General Category (10% Promoter Margin)</option>
                    <option value="women">Women Entrepreneur (5% Margin • Special Slab)</option>
                    <option value="sc">Scheduled Caste (SC) (5% Margin)</option>
                    <option value="st">Scheduled Tribe (ST) (5% Margin)</option>
                    <option value="obc">Other Backward Class (OBC) (5% Margin)</option>
                    <option value="artisan">Artisan / Traditional Craftsman (5% Margin)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Gender</label>
                  <select
                    value={formData.gender}
                    onChange={e => setFormData({ ...formData, gender: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
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
          {currentStep === 4 && (() => {
            const cost = Number(formData.project_cost) || 0;
            const sales = Number(formData.annual_turnover_estimate) || 0;
            const marginVal = Number(formData.margin_capital) || 0;
            const turnoverRatio = cost > 0 ? (sales / cost) : 0;
            
            // Sector benchmark margin helper
            const sec = String(formData.sector || "").toLowerCase();
            const sectorMargin = sec.includes("service") || sec.includes("repair") ? 0.38 
              : sec.includes("apparel") || sec.includes("textile") || sec.includes("craft") ? 0.32
              : sec.includes("trading") || sec.includes("retail") ? 0.22 
              : 0.30;
            
            // Fast EMI approximation for instant underwriting preview
            const loanPrincipal = Math.max(1000, (cost * 0.65) - Math.min(marginVal, cost * 0.10));
            const monthlyRate = 0.095 / 12;
            const tenureMonths = Math.max(12, (Number(formData.tenure_years) || 5) * 12);
            const quickEmi = (loanPrincipal * monthlyRate * Math.pow(1 + monthlyRate, tenureMonths)) / 
              Math.max(0.0001, (Math.pow(1 + monthlyRate, tenureMonths) - 1));
            
            const monthlyNoi = (sales * sectorMargin) / 12;
            const preDscr = quickEmi > 0 ? (monthlyNoi / quickEmi) : 0;

            const isLowSales = turnoverRatio > 0 && (turnoverRatio < 0.50 || preDscr < 1.0);
            const isHighSales = turnoverRatio > 5.0;
            const isOptimal = turnoverRatio >= 0.80 && turnoverRatio <= 3.50 && preDscr >= 1.33;

            return (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <Coins className="w-4 h-4 text-sovereign-700" />
                    Step 4: Available Margin Capital & Sales Revenue
                  </h3>
                  <span className="text-[11px] font-bold text-sovereign-800 bg-sovereign-50 border border-sovereign-200 px-2.5 py-1 rounded-lg self-start sm:self-auto">
                    Statutory Equity: {(getMarginPct(formData.promoter_category) * 100).toFixed(0)}% ({formData.promoter_category?.toUpperCase()})
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center justify-between">
                      <span>Available Margin Capital (₹)</span>
                      <span className="text-[10px] text-emerald-600 font-semibold">User Equity Input</span>
                    </label>
                    <input
                      type="number"
                      required
                      min={2500}
                      step={2500}
                      value={formData.margin_capital !== undefined ? formData.margin_capital : ""}
                      onChange={e => {
                        const rawVal = e.target.value;
                        const margin = rawVal === "" ? "" : Number(rawVal);
                        const numMargin = Number(margin) || 0;
                        const marginPct = getMarginPct(formData.promoter_category);
                        const derivedCost = marginPct > 0 ? Math.round(numMargin / marginPct) : numMargin * 10;
                        setFormData(prev => ({
                          ...prev,
                          margin_capital: margin,
                          project_cost: derivedCost,
                        }));
                      }}
                      placeholder="e.g. 90000"
                      className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                    />
                    <p className="text-[11px] text-slate-500 mt-1">Personal cash/equity capital you are willing to invest</p>

                    {/* Derived Project Sizing Readout Card */}
                    <div className="mt-3 p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5 shadow-subtle">
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-500 font-medium">Derived Project Outlay:</span>
                        <strong className="text-emerald-700 font-mono font-bold text-sm">
                          ₹{Number(formData.project_cost || 0).toLocaleString('en-IN')}
                        </strong>
                      </div>
                      <div className="flex justify-between items-center text-[11px]">
                        <span className="text-slate-500">Gross Implied Bank Loan:</span>
                        <span className="text-slate-800 font-mono font-semibold">
                          ₹{Number(Math.max(0, (formData.project_cost || 0) - (Number(formData.margin_capital) || 0))).toLocaleString('en-IN')}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-200 flex items-center gap-1">
                        <Info className="w-3 h-3 text-sovereign-600 shrink-0" />
                        <span>Back-solved: Margin ÷ {(getMarginPct(formData.promoter_category) * 100).toFixed(0)}% statutory equity requirement</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between items-center mb-1.5">
                        <label className="block text-xs font-bold text-slate-700">Estimated Annual Gross Sales (₹)</label>
                        {cost > 0 && (
                          <span className="text-[10px] text-slate-500 font-medium">
                            Range: ₹{(cost * 0.8).toLocaleString('en-IN')} – ₹{(cost * 3.0).toLocaleString('en-IN')}
                          </span>
                        )}
                      </div>
                      <input
                        type="number"
                        required
                        min={25000}
                        step={5000}
                        value={formData.annual_turnover_estimate}
                        onChange={e => setFormData({ ...formData, annual_turnover_estimate: Number(e.target.value) })}
                        className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                      />
                      <p className="text-[11px] text-slate-500 mt-1">Projected 100% capacity annual sales revenue</p>

                      {/* 1-Click Quick Preset Turnover Buttons */}
                      {cost > 0 && (
                        <div className="mt-2 flex flex-wrap items-center gap-1.5">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mr-1">Presets:</span>
                          <button
                            type="button"
                            onClick={() => setFormData(prev => ({
                              ...prev,
                              annual_turnover_estimate: Math.round((cost * 1.0) / 5000) * 5000
                            }))}
                            className={`text-[10px] px-2 py-1 rounded-md font-semibold border transition ${
                              Math.abs(turnoverRatio - 1.0) < 0.1
                                ? 'bg-sovereign-100 border-sovereign-400 text-sovereign-900'
                                : 'bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200'
                            }`}
                          >
                            1.0x Conservative
                          </button>
                          <button
                            type="button"
                            onClick={() => setFormData(prev => ({
                              ...prev,
                              annual_turnover_estimate: Math.round((cost * 1.5) / 5000) * 5000
                            }))}
                            className={`text-[10px] px-2 py-1 rounded-md font-semibold border transition ${
                              Math.abs(turnoverRatio - 1.5) < 0.1
                                ? 'bg-emerald-100 border-emerald-400 text-emerald-900 shadow-xs'
                                : 'bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-100'
                            }`}
                          >
                            ★ 1.5x Realistic (Optimal)
                          </button>
                          <button
                            type="button"
                            onClick={() => setFormData(prev => ({
                              ...prev,
                              annual_turnover_estimate: Math.round((cost * 2.2) / 5000) * 5000
                            }))}
                            className={`text-[10px] px-2 py-1 rounded-md font-semibold border transition ${
                              Math.abs(turnoverRatio - 2.2) < 0.1
                                ? 'bg-sovereign-100 border-sovereign-400 text-sovereign-900'
                                : 'bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200'
                            }`}
                          >
                            2.2x High Capacity
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Live Underwriting Diagnostics Preview Card */}
                    <div className="p-3 bg-gradient-to-br from-slate-50 to-sovereign-50/30 border border-slate-200 rounded-xl space-y-2 shadow-subtle">
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-600 font-medium">Turnover to Capital Leverage:</span>
                        <strong className="text-sovereign-900 font-mono font-bold text-sm">
                          {turnoverRatio.toFixed(2)}x
                        </strong>
                      </div>
                      <div className="grid grid-cols-2 gap-2 pt-1.5 border-t border-slate-200/80 text-[11px]">
                        <div>
                          <span className="text-slate-500 block">Est. Monthly Cash Surplus:</span>
                          <span className="text-slate-800 font-mono font-semibold">
                            ₹{Math.round(monthlyNoi).toLocaleString('en-IN')}/mo
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Est. Bank EMI:</span>
                          <span className="text-slate-800 font-mono font-semibold">
                            ₹{Math.round(quickEmi).toLocaleString('en-IN')}/mo
                          </span>
                        </div>
                      </div>

                      {/* Dynamic Solvency Pre-Check Indicator */}
                      <div className="pt-1.5 border-t border-slate-200/80 flex items-center justify-between text-[11px]">
                        <span className="text-slate-500">Instant Pre-DSCR:</span>
                        {isOptimal ? (
                          <span className="inline-flex items-center gap-1 font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded text-[10px]">
                            <CheckCircle2 className="w-3 h-3" />
                            {preDscr.toFixed(2)}x (Prime Bankable)
                          </span>
                        ) : isLowSales ? (
                          <span className="inline-flex items-center gap-1 font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded text-[10px]">
                            <AlertCircle className="w-3 h-3" />
                            {preDscr.toFixed(2)}x (Insolvent Cash Deficit)
                          </span>
                        ) : isHighSales ? (
                          <span className="inline-flex items-center gap-1 font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded text-[10px]">
                            <AlertCircle className="w-3 h-3" />
                            {turnoverRatio.toFixed(1)}x (High Machine Load)
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 font-bold text-slate-700 bg-slate-200 px-2 py-0.5 rounded text-[10px]">
                            {preDscr.toFixed(2)}x (Acceptable)
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Step 5: Loan Terms & Moratorium */}
          {currentStep === 5 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-4 h-4 text-sovereign-700" />
                Step 5: Commercial Bank Loan Repayment & Grace Terms
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Requested Repayment Tenure (Years)</label>
                  <input
                    type="number"
                    min={1}
                    max={15}
                    step={0.5}
                    value={formData.tenure_years}
                    onChange={e => setFormData({ ...formData, tenure_years: Number(e.target.value) })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">Standard MSME bank term loan tenure: 5 to 7 years</p>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Moratorium Grace Period (Months)</label>
                  <input
                    type="number"
                    min={0}
                    max={24}
                    value={formData.moratorium_months}
                    onChange={e => setFormData({ ...formData, moratorium_months: Number(e.target.value) })}
                    className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">Repayment begins after operational stabilization</p>
                </div>
              </div>
            </div>
          )}

          {/* Step 6: Supplementary Business Context & Operational Overrides (NEW STEP) */}
          {currentStep === 6 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-sovereign-700" />
                  Step 6: Supplementary Business Context & Operational Overrides
                </h3>
                <span className="text-[11px] text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded-full">
                  Optional Details
                </span>
              </div>

              {/* Informational Banner */}
              <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-200 text-xs text-blue-900 flex items-start gap-2.5">
                <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <div className="leading-relaxed">
                  <strong>Enterprise Narrative & Grounding:</strong> Adding operational background provides richer domain color in your generated Bank DPR and guides the AI synthesis engine. It will <strong>never alter</strong> deterministic regulatory ₹ subsidies or RBI banking solvency formulas.
                </div>
              </div>

              {/* Narrative Context Field */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-bold text-slate-700">
                    Supplementary Business Background & Operational Strengths
                  </label>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {(formData.additional_business_details || "").length} / 1000 chars
                  </span>
                </div>
                <textarea
                  rows={4}
                  maxLength={1000}
                  value={formData.additional_business_details || ""}
                  onChange={e => setFormData({ ...formData, additional_business_details: e.target.value })}
                  placeholder="e.g. 5 years of family experience in dairy processing; active procurement tie-up with 45 local farmers cooperative; existing cold storage facility equipped with solar backup..."
                  className="w-full bg-white border border-slate-300 rounded-xl p-3 text-xs text-slate-900 leading-relaxed placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle transition"
                />

                {/* Quick Snippet Helpers */}
                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  <span className="text-[10px] text-slate-500 font-semibold">Quick add:</span>
                  {[
                    "+ 5+ Yrs Industry Experience",
                    "+ Local Cooperative Tie-Up",
                    "+ Cold Chain Storage Available",
                    "+ Solar Powered Unit",
                    "+ Direct B2B Distribution"
                  ].map((tag, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => addNarrativeSnippet(tag.replace("+ ", ""))}
                      className="text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-0.5 rounded-md font-medium transition"
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>

              {/* Monthly Net Operating Income Override & Language in a 2-col grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    Monthly Net Operating Income Override (₹)
                  </label>
                  <input
                    type="number"
                    min={0}
                    step={1000}
                    value={formData.monthly_net_operating_income_override || ""}
                    onChange={e => setFormData({ ...formData, monthly_net_operating_income_override: e.target.value })}
                    placeholder="Leave empty for auto-calculation"
                    className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-xs text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-sovereign-600 focus:border-sovereign-600 shadow-subtle"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">Optional override if audited monthly cash surplus is known</p>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center gap-1">
                    <Languages className="w-3.5 h-3.5 text-sovereign-700" />
                    {t('appraisalLanguage') || 'Credit Appraisal Language'}
                  </label>
                  <div className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 font-semibold flex items-center justify-between shadow-xs">
                    <span>English (EN)</span>
                    <span className="text-[10px] font-bold text-sovereign-800 bg-sovereign-100/80 px-2 py-0.5 rounded-md font-mono">Global Default</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">Multi-language dynamic translation is accessible from the top dashboard navigation</p>
                </div>
              </div>
            </div>
          )}

          {/* Step 7: Review & Final Verification */}
          {currentStep === 7 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-sovereign-700" />
                Step 7: Appraisal Review & Statutory Pipeline Execution
              </h3>

              {/* Summary card */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-3 shadow-subtle">
                <div className="font-bold text-sovereign-900 uppercase tracking-wider text-[11px] flex items-center justify-between">
                  <span>Pre-Execution Parameter Summary:</span>
                  <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 text-[10px]">
                    Ready for Multi-Tier Underwriting
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-700">
                  <div className="p-2.5 bg-white rounded-lg border border-slate-200">
                    <div className="text-[10px] text-slate-400 font-bold uppercase">Enterprise & Sector</div>
                    <div className="font-bold text-slate-900 mt-0.5">{formData.enterprise_name}</div>
                    <div className="text-slate-500 uppercase text-[10px] mt-0.5">{formData.business_category} • {formData.sector}</div>
                  </div>

                  <div className="p-2.5 bg-white rounded-lg border border-slate-200">
                    <div className="text-[10px] text-slate-400 font-bold uppercase">LGD Hierarchy</div>
                    <div className="font-bold text-slate-900 mt-0.5">{formData.village_name}, {formData.block_name}</div>
                    <div className="text-slate-500 text-[10px] mt-0.5">{formData.district_name}, {formData.state_name} ({formData.is_rural ? 'Rural' : 'Urban'})</div>
                  </div>

                  <div className="p-2.5 bg-white rounded-lg border border-slate-200">
                    <div className="text-[10px] text-slate-400 font-bold uppercase">Promoter Profile</div>
                    <div className="font-bold text-slate-900 mt-0.5">{formData.promoter_name}</div>
                    <div className="text-slate-500 text-[10px] mt-0.5">{formData.promoter_category?.toUpperCase()} • {formData.gender}</div>
                  </div>

                  <div className="p-2.5 bg-white rounded-lg border border-slate-200">
                    <div className="text-[10px] text-slate-400 font-bold uppercase">Margin Capital & Sizing</div>
                    <div className="font-mono font-bold text-emerald-700 mt-0.5">
                      ₹{Number(formData.margin_capital !== undefined ? formData.margin_capital : Math.round(formData.project_cost * getMarginPct(formData.promoter_category))).toLocaleString('en-IN')} Margin ({(getMarginPct(formData.promoter_category) * 100).toFixed(0)}%)
                    </div>
                    <div className="font-mono text-slate-700 text-[10px] mt-0.5">
                      ₹{Number(formData.project_cost).toLocaleString('en-IN')} Derived Outlay • ₹{Number(formData.annual_turnover_estimate).toLocaleString('en-IN')} Sales
                    </div>
                  </div>
                </div>

                {formData.additional_business_details && (
                  <div className="p-2.5 bg-white rounded-lg border border-slate-200">
                    <div className="text-[10px] text-slate-400 font-bold uppercase">Supplementary Context</div>
                    <div className="text-slate-700 text-xs italic mt-0.5 line-clamp-2">
                      "{formData.additional_business_details}"
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between text-[11px] text-slate-600 pt-1 border-t border-slate-200">
                  <span>Language: <strong className="text-slate-900 uppercase">{formData.language}</strong></span>
                  <span>Tenure: <strong className="text-slate-900">{formData.tenure_years} Years ({formData.moratorium_months}m grace)</strong></span>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Controls */}
          <div className="flex justify-between items-center gap-2 pt-4 border-t border-slate-200">
            {currentStep > 1 ? (
              <button
                type="button"
                onClick={handleBack}
                className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 px-3 sm:px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-50 transition shadow-subtle shrink-0"
              >
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
            ) : <div />}

            {currentStep < 7 ? (
              <button
                type="button"
                onClick={handleNext}
                className="flex items-center gap-1.5 text-xs font-bold text-white bg-sovereign-800 hover:bg-sovereign-700 px-4 sm:px-5 py-2.5 rounded-xl shadow-sm transition group shrink-0"
              >
                <span>Next Step</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center justify-center gap-2 text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-600 px-4 sm:px-6 py-2.5 rounded-xl shadow-md shadow-emerald-900/15 transition-all duration-200 hover:scale-[1.02] disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Executing Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-emerald-200 shrink-0" />
                    <span className="truncate">Run Bank Appraisal</span>
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

export default FeasibilityWizard;
