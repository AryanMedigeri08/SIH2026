import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Megaphone,
  MessageSquare,
  Store,
  Share2,
  Copy,
  Check,
  Users,
  Sparkles,
  Volume2,
  Building2,
  Calendar,
  Printer,
  Target,
  CheckSquare,
  Square,
  Award,
  TrendingUp,
  MapPin,
  Phone,
  ExternalLink,
  ChevronRight,
  Landmark
} from 'lucide-react';
import { TranslatedText } from '../../components/TranslatedText';
import { useLanguage } from '../../context/LanguageContext';

export function MarketingPage({ reportData }) {
  if (!reportData) return null;

  const { t } = useLanguage();
  const p = reportData?.input_parameters || {};
  const enterpriseName = p.enterprise_name || 'Gramin Enterprise';
  const sector = (p.sector || 'dairy').toLowerCase();
  const village = p.village_name || 'Local Village';
  const block = p.block_name || 'Block';
  const district = p.district_name || 'District';
  const state = p.state_name || 'State';
  const promoter = p.promoter_name || 'Entrepreneur';

  // Demographics & TAM Catchment Data
  const popProj = reportData?.market_demographics?.population_projection || {};
  const tamData = reportData?.market_demographics?.tam || {};
  const compData = reportData?.market_demographics?.competition || {};
  const pricing = reportData?.pricing_recommendation || {};

  const pop = popProj.projected_population || 18240;
  const households = popProj.projected_households || Math.round(pop / 4.8) || 3800;
  const targetHouseholds = tamData.target_households || Math.round(households * 0.25) || 950;
  const unitPrice = Math.round(pricing.recommended_selling_price_band_low || pricing.unit_cost_floor * 1.15 || 55);

  // Daily target to break even / thrive
  const turnover = Number(p.annual_turnover_estimate) || 1200000;
  const dailyCustomersGoal = Math.max(15, Math.round(turnover / (unitPrice * 312)) || 25);
  const catchmentSharePct = ((dailyCustomersGoal / households) * 100).toFixed(1);

  // ODOP Cluster Alignment & Statutory Benefits
  const districtLower = (district || '').toLowerCase();
  const sectorLower = (sector || '').toLowerCase();
  let fallbackProduct = "District Specialty Product";
  let fallbackAligned = false;

  if (districtLower.includes('bankura')) {
    fallbackProduct = "Terracotta Pottery & Dokra Metal Craft";
    fallbackAligned = sectorLower === 'artisan_trades' || sectorLower === 'apparel';
  } else if (districtLower.includes('bulandshahr')) {
    fallbackProduct = "Khurja Glazed Pottery & Ceramic Ware";
    fallbackAligned = sectorLower === 'fabrication' || sectorLower === 'artisan_trades' || sectorLower === 'manufacturing';
  } else if (districtLower.includes('ujjain')) {
    fallbackProduct = "Bhairavgarh Batik Print Textiles";
    fallbackAligned = sectorLower === 'apparel' || sectorLower === 'artisan_trades';
  }

  const odop = reportData?.odop_alignment || {
    is_aligned: fallbackAligned,
    odop_product: fallbackProduct,
    district_name: district,
    state_name: state,
    category: fallbackAligned ? 'Food / Craft Processing (ODOP)' : 'Rural Commercial Enterprise',
    pmfme_eligible: fallbackAligned,
    gem_category: fallbackAligned ? 'ODOP Official Catalog' : 'General MSME Direct Procurement',
    cfc_available: true,
    key_benefits: fallbackAligned ? [
      'PMFME 35% credit-linked capital subsidy up to ₹10 Lakhs',
      'GeM ODOP seller corridor priority listing without tender',
      'Common Facility Centre (CFC) testing & cold-chain access',
      'District ODOP packaging seal authorization'
    ] : [
      'PMEGP 25%–35% rural capital subsidy via KVIC / DIC',
      'GeM MSME Public Procurement corridor (25% reserved quota)',
      'DIC District Industries Centre general enterprise support',
      'FSSAI & local Gram Panchayat provenance branding'
    ],
    branding_seal: fallbackAligned ? {
      seal_title: `District ODOP Certified Product — ${district}`,
      recommended_price_premium_pct: 18.0,
      labeling_compliance: 'FSSAI / Agmark / ODOP Registered Cluster',
      is_seal_eligible: true,
    } : {
      seal_title: `Local Rural Enterprise — ${district}`,
      recommended_price_premium_pct: 8.0,
      labeling_compliance: 'Standard FSSAI / Gram Panchayat Certified',
      is_seal_eligible: false,
    }
  };

  // Interactive Tab State
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') || 'whatsapp';
  const [activeTab, setActiveTab] = useState(initialTab);
  const [copiedKey, setCopiedKey] = useState(null);

  // Sync tab with URL search parameter if present
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && ['whatsapp', 'haat', 'munadi', 'b2b', 'odop'].includes(tab)) {
      setActiveTab(tab);
      setTimeout(() => {
        const el = document.getElementById('marketing-tabs-section');
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    }
  }, [searchParams]);

  // 30-Day Launch Checklist State (8 milestones)
  const [checklist, setChecklist] = useState({
    w1_1: true,
    w1_2: false,
    w2_1: false,
    w2_2: false,
    w3_1: false,
    w3_2: false,
    w4_1: false,
    w4_2: false,
  });

  const toggleChecklist = (key) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const completedCount = Object.values(checklist).filter(Boolean).length;
  const progressPct = Math.round((completedCount / 8) * 100);

  // Sector-tailored promotional copy
  const sectorCopy = sector.includes('dairy')
    ? {
        product: 'Pure, Unadulterated Cow & Buffalo Milk, Fresh Paneer & Ghee',
        tagline: 'Direct from Village Farm to Your Kitchen',
        benefit: '100% pure, daily morning fresh delivery, no mixing',
        b2b: 'Tea stalls, sweet shops (halwais), and morning milk buyers',
      }
    : sector.includes('food') || sector.includes('agro')
    ? {
        product: 'Freshly Milled Whole Wheat Flour, Cold-Pressed Mustard Oil & Spices',
        tagline: 'Traditional Village Stone-Ground Taste & Hygiene',
        benefit: 'Chemical-free, unadulterated, wholesome farm produce',
        b2b: 'Local grocery kirana stores, wedding caterers, and canteens',
      }
    : sector.includes('apparel') || sector.includes('textile')
    ? {
        product: 'Custom Tailored Dailywear, School Uniforms & Festival Attire',
        tagline: 'Durable Stitching, Modern Village Styles at Honest Rates',
        benefit: 'Perfect fit guarantee, fast 48-hour delivery',
        b2b: 'School uniform bulk orders and cloth merchants',
      }
    : sector.includes('repair') || sector.includes('electric')
    ? {
        product: 'Fast Mobile, Fan & Motor Repair with Genuine Parts',
        tagline: 'Trusted Same-Day Local Service with 30-Day Warranty',
        benefit: 'No need to travel to district town for minor repairs',
        b2b: 'Farmers with irrigation pumps and local workshops',
      }
    : {
        product: 'Quality Village Products & Guaranteed Direct Service',
        tagline: 'Trusted, Local & Honest Grassroots Quality',
        benefit: 'Affordable village pricing with personal accountability',
        b2b: 'Local village shops and neighborhood families',
      };

  // 1. WhatsApp Message Template
  const whatsappMessage = `🙏 *Namaste from ${enterpriseName}!*

We are proud to serve our village *${village} (${district})* with *${sectorCopy.product}*!

✨ *Why Choose Us?*
• 🌿 ${sectorCopy.tagline}
• 🛡️ ${sectorCopy.benefit}
• 💰 Honest, fair village price (Starting from ₹${unitPrice}/unit)
• 🤝 Direct from your neighbor, no middlemen

📍 *Location:* ${village} (Near Gram Panchayat Office)
📞 *Contact / Orders:* ${promoter}

Support your local village entrepreneur! Please share this with your village WhatsApp groups & family. Dhanyawad! 🙏`;

  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(whatsappMessage)}`;

  // 2. Munadi / Loudspeaker Script
  const munadiScript = `📢 [🔔 डंका / घंटी बजाएं — 3 बार]

"सुनो सुनो सुनो! ग्राम पंचायत ${village} के सभी भाइयों, बहनों और बुज़ुर्गों के लिए बड़ी खुशखबरी!

अब आपके अपने गाँव ${village} में शुरू हो गया है — *${enterpriseName}*!
अब आपको शहर जाने की कोई ज़रूरत नहीं!
पाइए *${sectorCopy.product}* — वो भी सबसे शुद्ध, सबसे ताज़ा और सबसे किफ़ायती गाँव के दामों में!

📍 हमारा पता: ग्राम पंचायत कार्यालय के पास, ${village}
📞 संपर्क करें: आपके अपने ${promoter} भाई!

आज ही पधारें और पहले 50 ग्राहकों के लिए विशेष छूट का लाभ उठाएं!
सुनो सुनो सुनो!"

[🔔 डंका बजाएं]`;

  // 3. Weekly Haat Strategy
  const haatStrategy = [
    {
      title: '1. Prime Stall Placement (सही जगह का चुनाव)',
      desc: `Set up your table near the central intersection or main grocery section of ${village} Weekly Haat, where families gather for weekly household supplies.`,
    },
    {
      title: '2. Golden Hours: 8:00 AM – 11:30 AM (सुबह का समय)',
      desc: 'Over 65% of weekly haat transactions occur in the first 3.5 hours. Ensure your display is fully stocked and staffed by 7:30 AM.',
    },
    {
      title: '3. Live Demonstration / Free Sampling (मुफ़्त चखना/जाँच)',
      desc: 'Provide small sample tastes or live demos to passing villagers. In rural haats, personal trust and tasting convert 4 out of 5 passersby into paying customers.',
    },
    {
      title: '4. Panchayat Combo Offer ("गाँव का बंडल पैक")',
      desc: `Offer a "Buy 2 units, get ₹10 instant off" family pack. Rural buyers appreciate bulk savings for their weekly household consumption.`,
    },
  ];

  // 4. B2B Tie-Ups Strategy
  const b2bPartners = [
    {
      title: 'Local Kirana Stores (राशन की दुकानें)',
      target: '3 to 5 stores in 5 km radius',
      terms: 'Offer 8% wholesale margin for weekly cash settlement',
      action: 'Place a small branded counter display near the billing desk.',
    },
    {
      title: 'Tea Stalls & Village Eateries (चाय और नाश्ते वाले)',
      target: 'Daily recurring morning delivery',
      terms: 'Fixed daily morning supply with 7-day payment cycle',
      action: 'Guarantees reliable baseline cash flow every morning.',
    },
    {
      title: 'Neighboring Village Haats (पड़ोसी हाट)',
      target: 'Rotate between 3 weekly markets',
      terms: 'Wed / Fri / Sun haat circuit in neighboring 10 km villages',
      action: 'Expands your customer base 3x without increasing rent.',
    },
    {
      title: 'Panchayat & School Canteens (सरकारी व स्कूल)',
      target: 'Mid-day meal or event catering',
      terms: 'Concessional bulk pricing against official panchayat voucher',
      action: 'Register enterprise details with the Gram Panchayat Secretary.',
    },
  ];

  const handleCopy = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2500);
  };

  return (
    <div className="space-y-6 pb-8">
      {/* Header Banner */}
      <div className="glass-panel p-4 sm:p-6 border-l-4 border-sky-600 bg-gradient-to-r from-white via-sky-50/25 to-white shadow-card border border-slate-200/90 rounded-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-sky-800 mb-1 flex items-center gap-1.5">
              <Megaphone className="w-4 h-4 text-sky-600" />
              <span><TranslatedText text="Module 1 • Grassroots Customer Acquisition Kit" /></span>
            </div>
            <h1 className="text-xl sm:text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
              <TranslatedText text="Village Outreach, WhatsApp Promo & Haat Stall Kit" />
            </h1>
            <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
              <TranslatedText text="Field-proven grassroots customer acquisition toolkit. Connect directly with households across your 5–10 km catchment, bypass middlemen, and build a recurring village customer base." />
            </p>
          </div>

          <div className="flex items-center gap-2 bg-sky-50 border border-sky-200 px-3 py-2 rounded-xl shrink-0">
            <Store className="w-5 h-5 text-sky-700 shrink-0" />
            <div>
              <span className="text-[10px] uppercase font-bold text-sky-800 block">
                <TranslatedText text="Primary Catchment" />
              </span>
              <span className="text-xs sm:text-sm font-bold text-slate-900">
                {village}, {district}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Catchment Funnel KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        {/* Metric 1: Total Village Households */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-subtle space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span><TranslatedText text="Catchment Households" /></span>
            <Users className="w-4 h-4 text-sky-600" />
          </div>
          <div className="text-2xl font-mono font-extrabold text-slate-900">
            {households.toLocaleString('en-IN')}
          </div>
          <p className="text-[10px] text-slate-500">
            <TranslatedText text="Census 2026 projected base within 5 km" />
          </p>
        </div>

        {/* Metric 2: Target Segment */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-subtle space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span><TranslatedText text="Target Buyer Families" /></span>
            <Target className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-mono font-extrabold text-emerald-700">
            {targetHouseholds.toLocaleString('en-IN')}
          </div>
          <p className="text-[10px] text-emerald-700 font-medium">
            <TranslatedText text="Core demographic sector consumers" />
          </p>
        </div>

        {/* Metric 3: Daily Target Customers */}
        <div className="p-4 rounded-2xl bg-gradient-to-br from-sky-600 to-indigo-700 text-white shadow-md space-y-1">
          <div className="flex items-center justify-between text-sky-100 text-xs font-medium">
            <span><TranslatedText text="Daily Sales Target" /></span>
            <TrendingUp className="w-4 h-4 text-sky-200" />
          </div>
          <div className="text-2xl font-mono font-extrabold">
            {dailyCustomersGoal} <span className="text-xs font-sans font-normal text-sky-100"><TranslatedText text="customers/day" /></span>
          </div>
          <p className="text-[10px] text-sky-100 font-medium">
            <TranslatedText text="Only" /> {catchmentSharePct}% <TranslatedText text="of village needed for full profit" />
          </p>
        </div>
      </div>

      {/* Visual Catchment Share Callout Bar */}
      <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
          <span className="text-emerald-950 font-medium">
            <strong><TranslatedText text="Low Village Competition Moat:" /></strong> <TranslatedText text="Capturing just" /> <strong>{catchmentSharePct}%</strong> <TranslatedText text="of local households completely meets your monthly bank loan repayment and family profit quota!" />
          </span>
        </div>
        <div className="flex items-center gap-1.5 font-bold text-emerald-900 bg-white px-2.5 py-1 rounded-lg border border-emerald-200 shadow-xs shrink-0 self-start sm:self-auto">
          <span>{compData.estimated_competitors_count || 2} <TranslatedText text="local competitors" /></span>
        </div>
      </div>

      {/* 4-Channel Grassroots Action Hub */}
      <div id="marketing-tabs-section" className="glass-panel p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-4">
        {/* Tab Headers */}
        <div className="flex flex-wrap gap-2 pb-3 border-b border-slate-100">
          <button
            type="button"
            onClick={() => setActiveTab('whatsapp')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'whatsapp'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span><TranslatedText text="WhatsApp Viral Broadcast" /></span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('haat')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'haat'
                ? 'bg-sovereign-800 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span><TranslatedText text="Weekly Haat Stall Playbook" /></span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('munadi')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'munadi'
                ? 'bg-amber-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Volume2 className="w-4 h-4" />
            <span><TranslatedText text="Loudspeaker Munadi Script" /></span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('b2b')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'b2b'
                ? 'bg-indigo-700 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span><TranslatedText text="Local B2B Buyer Tie-Ups" /></span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('odop')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'odop'
                ? odop.is_aligned
                  ? 'bg-gradient-to-r from-amber-600 to-amber-700 text-white shadow-xs'
                  : 'bg-gradient-to-r from-slate-700 to-slate-800 text-white shadow-xs'
                : odop.is_aligned
                ? 'bg-amber-50/90 text-amber-900 hover:bg-amber-100 border border-amber-200/80'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
            }`}
          >
            <Sparkles className={`w-4 h-4 ${odop.is_aligned ? 'text-amber-500 fill-amber-400' : 'text-sky-600'}`} />
            <span>
              {odop.is_aligned ? (
                <TranslatedText text="ODOP & GeM Marketplace" />
              ) : (
                <TranslatedText text="ODOP Synergy & GeM Hub" />
              )}
            </span>
          </button>
        </div>

        {/* Tab 1: WhatsApp Broadcast */}
        {activeTab === 'whatsapp' && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
              <div>
                <span className="font-bold text-slate-900 block">
                  <TranslatedText text="Personalized Village WhatsApp Promo Message" />
                </span>
                <span className="text-slate-500 text-[11px]">
                  <TranslatedText text="Forward directly to village groups, Self-Help Group (SHG) circles, and youth networks." />
                </span>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => handleCopy(whatsappMessage, 'whatsapp')}
                  className="flex items-center gap-1 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-xl border border-slate-200 transition"
                >
                  {copiedKey === 'whatsapp' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedKey === 'whatsapp' ? 'Copied!' : 'Copy Text'}</span>
                </button>

                <a
                  href={whatsappUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 px-3 py-1.5 rounded-xl shadow-xs transition"
                >
                  <Share2 className="w-3.5 h-3.5" />
                  <span><TranslatedText text="Open in WhatsApp" /></span>
                </a>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50/40 border border-emerald-200/80 font-mono text-xs text-slate-800 whitespace-pre-wrap leading-relaxed shadow-subtle">
              {whatsappMessage}
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-1">
              <strong>💡 <TranslatedText text="Grassroots Outreach Tactic:" /></strong>
              <p className="text-[11px]">
                <TranslatedText text="Ask the President of your village Self-Help Group (SHG / Mahila Mandal) to forward this note. SHG referrals generate a 70%+ repeat trial rate in rural India." />
              </p>
            </div>
          </div>
        )}

        {/* Tab 2: Weekly Haat Playbook */}
        {activeTab === 'haat' && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between text-xs pb-1">
              <div>
                <span className="font-bold text-slate-900 block">
                  <TranslatedText text="Weekly Haat (हफ़्ते का बाज़ार) Conversion Blueprint" />
                </span>
                <span className="text-slate-500 text-[11px]">
                  <TranslatedText text="Turn the weekly village market into your largest single-day revenue source." />
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {haatStrategy.map((step, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/90 space-y-1.5">
                  <span className="text-xs font-bold text-sovereign-900 block flex items-center gap-1">
                    <Store className="w-3.5 h-3.5 text-sovereign-700" />
                    {step.title}
                  </span>
                  <p className="text-[11px] text-slate-600 leading-relaxed font-medium">
                    {step.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Munadi Loudspeaker Script */}
        {activeTab === 'munadi' && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
              <div>
                <span className="font-bold text-slate-900 block">
                  <TranslatedText text="Rickshaw Loudspeaker Announcement Script (मुनादी प्रचार)" />
                </span>
                <span className="text-slate-500 text-[11px]">
                  <TranslatedText text="Hire a local e-rickshaw or loudspeaker for 2 hours during the evening market rush." />
                </span>
              </div>

              <button
                type="button"
                onClick={() => handleCopy(munadiScript, 'munadi')}
                className="flex items-center gap-1 text-xs font-bold text-amber-900 bg-amber-50 hover:bg-amber-100 px-3 py-1.5 rounded-xl border border-amber-200 transition shrink-0 self-start sm:self-auto"
              >
                {copiedKey === 'munadi' ? <Check className="w-3.5 h-3.5 text-amber-700" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedKey === 'munadi' ? 'Copied!' : 'Copy Script'}</span>
              </button>
            </div>

            <div className="p-4 rounded-xl bg-amber-50/50 border border-amber-200 font-sans text-xs text-amber-950 whitespace-pre-wrap leading-relaxed">
              {munadiScript}
            </div>

            <p className="text-[11px] text-slate-500">
              <TranslatedText text="Cost benchmark: A 2-hour auto-rickshaw broadcast in a rural Gram Panchayat typically costs ₹250–₹350, reaching all 5–7 tolas/hamlets." />
            </p>
          </div>
        )}

        {/* Tab 4: B2B Buyer Tie-Ups */}
        {activeTab === 'b2b' && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div>
              <span className="font-bold text-slate-900 text-xs block">
                <TranslatedText text="Local Commercial Accounts & Recurring Bulk Buyers" />
              </span>
              <span className="text-slate-500 text-[11px]">
                <TranslatedText text="Locking in 3 recurring wholesale clients guarantees steady baseline cash flow before retail sales." />
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {b2bPartners.map((b, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                  <div className="font-bold text-slate-900 flex items-center justify-between">
                    <span>{b.title}</span>
                    <span className="text-[10px] text-indigo-700 font-normal bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100">
                      {b.target}
                    </span>
                  </div>
                  <p className="text-slate-600 text-[11px] leading-relaxed">
                    <strong><TranslatedText text="Terms:" /></strong> {b.terms}
                  </p>
                  <p className="text-slate-500 text-[10px]">
                    <strong><TranslatedText text="Tactic:" /></strong> {b.action}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 5: ODOP & GeM Marketplace Linkage */}
        {activeTab === 'odop' && (
          odop.is_aligned ? (
            <div className="space-y-5 animate-in fade-in duration-200">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                <div>
                  <span className="font-bold text-slate-900 block text-sm font-outfit">
                    <TranslatedText text="One District One Product (ODOP) Branding & Government GeM Corridor" />
                  </span>
                  <span className="text-slate-500 text-[11px]">
                    <TranslatedText text="Leverage official district GI/ODOP credentials to command a 15–25% price premium and access direct institutional orders." />
                  </span>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-300 text-emerald-900 font-bold text-[10px] font-mono shrink-0 self-start sm:self-auto">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-600 fill-emerald-500" />
                  <span>ODOP Aligned: {district} {odop.odop_product}</span>
                </span>
              </div>

              {/* 4 Specialized ODOP Action Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                
                {/* Card 1: Official Packaging Seal & 18% Price Premium */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-amber-50/70 to-white border border-amber-200/90 shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-slate-900 font-outfit">
                      <div className="w-7 h-7 rounded-lg bg-amber-600 text-white flex items-center justify-center">
                        <Award className="w-4 h-4" />
                      </div>
                      <span><TranslatedText text="1. Official District Packaging Seal" /></span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold font-mono">
                      +18% <TranslatedText text="Price Premium" />
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    <TranslatedText text="By printing the official ODOP district emblem and FSSAI/Udyam license number on pouches and packaging, rural producers charge 15–25% higher prices in district towns, highway eateries, and tourist markets." />
                  </p>
                  <div className="p-3 rounded-xl bg-white border border-amber-200/80 text-[11px] font-mono text-slate-700 flex items-center justify-between">
                    <div>
                      <strong className="block text-slate-900 font-bold">"{district} ODOP Authentic {p.sector ? p.sector.toUpperCase() : 'PRODUCE'}"</strong>
                      <span className="text-[10px] text-slate-500">Tagline: Pure Local Origin • MoFPI Cluster Aligned</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleCopy(`Authentic ${district} ODOP Certified - Pure Local Quality`, 'seal_tag')}
                      className="p-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 transition shrink-0 ml-2"
                      title="Copy packaging seal tagline"
                    >
                      {copiedKey === 'seal_tag' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Card 2: Government e-Marketplace (GeM) ODOP Corridor */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-sky-50/70 to-white border border-sky-200/90 shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-slate-900 font-outfit">
                      <div className="w-7 h-7 rounded-lg bg-sky-700 text-white flex items-center justify-center">
                        <Store className="w-4 h-4" />
                      </div>
                      <span><TranslatedText text="2. GeM ODOP Onboarding" /></span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 text-[10px] font-bold font-mono">
                      <TranslatedText text="Direct B2G Orders" />
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    <TranslatedText text="Government departments, hostels, and public institutions can purchase ODOP products directly up to ₹5 Lakhs without tenders on the Government e-Marketplace (GeM) with guaranteed 10-day payment." />
                  </p>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-slate-500 font-mono">Category: {odop.gem_category || 'ODOP Catalog'}</span>
                    <a
                      href="https://gem.gov.in/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-sky-700 hover:text-sky-800 hover:underline"
                    >
                      <span><TranslatedText text="Visit GeM Portal" /></span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>

                {/* Card 3: District Common Facility Centre (CFC) */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-50/70 to-white border border-emerald-200/90 shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-slate-900 font-outfit">
                      <div className="w-7 h-7 rounded-lg bg-emerald-600 text-white flex items-center justify-center">
                        <Building2 className="w-4 h-4" />
                      </div>
                      <span><TranslatedText text="3. District CFC & Testing Labs" /></span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold font-mono">
                      75% <TranslatedText text="Govt Subsidized" />
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    <TranslatedText text="Access shared cold storage, modern vacuum packaging, and quality testing apparatus at your district's Common Facility Centre (CFC) without investing large capital in private equipment." />
                  </p>
                  <div className="text-[10px] text-emerald-900 bg-emerald-50/80 p-2 rounded-lg border border-emerald-200/60 font-medium">
                    ✓ <TranslatedText text="District Hub: Available via District Industries Centre (DIC) cluster facilitation." />
                  </div>
                </div>

                {/* Card 4: PMFME 35% Subsidy & DIC Linkage */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-indigo-50/70 to-white border border-indigo-200/90 shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-slate-900 font-outfit">
                      <div className="w-7 h-7 rounded-lg bg-indigo-700 text-white flex items-center justify-center">
                        <Sparkles className="w-4 h-4" />
                      </div>
                      <span><TranslatedText text="4. PMFME 35% Capital Grant" /></span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 text-[10px] font-bold font-mono">
                      Max ₹10L <TranslatedText text="Grant" />
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    <TranslatedText text="Submit your credit-linked DPR to the District Level Committee (DLC) headed by the District Collector to receive the back-ended 35% capital subsidy credited directly into your loan account." />
                  </p>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-slate-500 font-mono">Admin: MoFPI / DIC {district}</span>
                    <a
                      href="https://pmfme.mofpi.gov.in/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-700 hover:text-indigo-800 hover:underline"
                    >
                      <span><TranslatedText text="PMFME Portal" /></span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>

              </div>
            </div>
          ) : (
            <div className="space-y-5 animate-in fade-in duration-200">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                <div>
                  <span className="font-bold text-slate-900 block text-sm font-outfit">
                    <TranslatedText text="District ODOP Context, Synergies & GeM Institutional Sales" />
                  </span>
                  <span className="text-slate-500 text-[11px]">
                    <TranslatedText text={`While ${enterpriseName} operates in the ${(p.sector || 'dairy').toUpperCase()} sector (Non-ODOP), discover strategic local cluster packaging synergies with ${district}'s official ODOP item, institutional GeM sales, and PMEGP capital subsidies.`} />
                  </span>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 border border-slate-300 text-slate-700 font-bold text-[10px] font-mono shrink-0 self-start sm:self-auto">
                  <Landmark className="w-3.5 h-3.5 text-slate-500" />
                  <span>Non-ODOP Sector • District ODOP: {odop.odop_product}</span>
                </span>
              </div>

              {/* 4 Specialized Non-ODOP Strategic Action Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                
                {/* Card 1: Cluster Synergy Packaging Innovation */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-amber-50/70 to-white border border-amber-200/90 shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-slate-900 font-outfit">
                      <div className="w-7 h-7 rounded-lg bg-amber-700 text-white flex items-center justify-center">
                        <Award className="w-4 h-4" />
                      </div>
                      <span><TranslatedText text="1. Earthenware Cluster Packaging Synergy" /></span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold font-mono">
                      +15%–20% <TranslatedText text="Artisanal Premium" />
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    {districtLower.includes('bankura') ? (
                      <TranslatedText text="Partner with Bankura's famous Panchmura terracotta artisans (the district's notified ODOP craft) to package your curd (Mishti Doi), paneer, and ghee in authentic terracotta handis/matkas. Commands a 15–20% price premium over standard pouches while celebrating local GI heritage and 100% plastic-free sustainability." />
                    ) : (
                      <TranslatedText text="Collaborate with local artisanal packaging producers to provide eco-friendly, traditional container packaging that commands an authentic rural premium over industrial mass products while complying with FSSAI standards." />
                    )}
                  </p>
                  <div className="p-3 rounded-xl bg-white border border-amber-200/80 text-[11px] font-mono text-slate-700 flex items-center justify-between">
                    <div>
                      <strong className="block text-slate-900 font-bold">
                        {districtLower.includes('bankura') ? `"${enterpriseName} — Authentic Bankura Terracotta Packaged"` : `"${enterpriseName} — Pure Rural Origin • Authentic Local Quality"`}
                      </strong>
                      <span className="text-[10px] text-slate-500">
                        {districtLower.includes('bankura') ? "Eco-Friendly Earthen Matka • GI Cluster Synergy" : "FSSAI Registered • Natural Local Produce"}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleCopy(districtLower.includes('bankura') ? `${enterpriseName} - Handcrafted in Bankura Terracotta` : `${enterpriseName} - Pure Rural Origin`, 'synergy_tag')}
                      className="p-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 transition shrink-0 ml-2"
                      title="Copy packaging tagline"
                    >
                      {copiedKey === 'synergy_tag' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Card 2: Government e-Marketplace (GeM) MSME Direct Procurement */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-sky-50/70 to-white border border-sky-200/90 shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-slate-900 font-outfit">
                      <div className="w-7 h-7 rounded-lg bg-sky-700 text-white flex items-center justify-center">
                        <Store className="w-4 h-4" />
                      </div>
                      <span><TranslatedText text="2. GeM MSME Direct Procurement" /></span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 text-[10px] font-bold font-mono">
                      <TranslatedText text="25% Public Quota" />
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    <TranslatedText text="Under the Public Procurement Policy for MSEs, Central & State government departments, residential schools, hospitals, and Anganwadis must purchase 25% of annual supplies from micro enterprises. Micro dairy & agro units can supply up to ₹5 Lakhs directly without tender." />
                  </p>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-slate-500 font-mono">Corridor: GeM MSE Direct Purchase</span>
                    <a
                      href="https://gem.gov.in/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-sky-700 hover:text-sky-800 hover:underline"
                    >
                      <span><TranslatedText text="Visit GeM Portal" /></span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>

                {/* Card 3: District Industries Centre (DIC) Facilitation */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-50 to-white border border-slate-200/90 shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-slate-900 font-outfit">
                      <div className="w-7 h-7 rounded-lg bg-slate-800 text-white flex items-center justify-center">
                        <Building2 className="w-4 h-4" />
                      </div>
                      <span><TranslatedText text={`3. DIC ${district} Support Cell`} /></span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-800 text-[10px] font-bold font-mono">
                      <TranslatedText text="District Nodal Agency" />
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    <TranslatedText text={`While ${p.sector || 'dairy'} is not ${district}'s notified ODOP, the District Industries Centre (DIC) actively supports rural dairy processing and agro-enterprises through Udyam registration, FSSAI facilitation, power subsidy NOCs, and State Rural Livelihood linkages.`} />
                  </p>
                  <div className="text-[10px] text-slate-700 bg-slate-50 p-2 rounded-lg border border-slate-200 font-medium">
                    ✓ <TranslatedText text={`Office: General Manager, District Industries Centre (DIC), ${district}`} />
                  </div>
                </div>

                {/* Card 4: PMEGP 35% Capital Subsidy (Optimal Statutory Scheme) */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-50/70 to-white border border-emerald-200/90 shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-slate-900 font-outfit">
                      <div className="w-7 h-7 rounded-lg bg-emerald-700 text-white flex items-center justify-center">
                        <Sparkles className="w-4 h-4" />
                      </div>
                      <span><TranslatedText text="4. PMEGP 35% Rural Subsidy" /></span>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold font-mono">
                      <TranslatedText text="Up to ₹17.5 Lakhs" />
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    <TranslatedText text="PMEGP is the most financially advantageous statutory scheme for non-ODOP rural manufacturing and processing units. Qualified rural special category promoters receive a 35% non-repayable capital subsidy with only 5% promoter equity contribution required." />
                  </p>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-slate-500 font-mono">Admin: KVIC / KVIB / DIC</span>
                    <a
                      href="https://pmegp.msme.gov.in/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 hover:text-emerald-800 hover:underline"
                    >
                      <span><TranslatedText text="PMEGP Portal" /></span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>

              </div>
            </div>
          )
        )}
      </div>

      {/* Two Balanced Columns: "First 100 Customers" Roadmap + Printable Village Rate Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        
        {/* Left: 30-Day "First 100 Customers" Roadmap (7 cols) */}
        <div className="lg:col-span-7 glass-panel p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-emerald-700" />
                <h3 className="font-outfit font-bold text-slate-900 text-sm sm:text-base">
                  <TranslatedText text="30-Day 'First 100 Customers' Roadmap" />
                </h3>
              </div>
              <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                {completedCount}/8 <TranslatedText text="Done" /> ({progressPct}%)
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mt-3 mb-4">
              <div
                className="bg-gradient-to-r from-sky-500 to-emerald-600 h-full transition-all duration-300"
                style={{ width: `${progressPct}%` }}
              />
            </div>

            {/* Checklist Items */}
            <div className="space-y-2.5 text-xs">
              {/* Week 1 */}
              <div className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-200 space-y-2">
                <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider block text-sky-800">
                  <TranslatedText text="Week 1: Family, Friends & Sampling (Target: 25 Customers)" />
                </span>
                
                <button
                  type="button"
                  onClick={() => toggleChecklist('w1_1')}
                  className="flex items-start gap-2 text-left w-full cursor-pointer group"
                >
                  {checklist.w1_1 ? (
                    <CheckSquare className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-400 shrink-0 mt-0.5 group-hover:text-slate-600" />
                  )}
                  <span className={checklist.w1_1 ? 'line-through text-slate-400' : 'text-slate-700'}>
                    <TranslatedText text="Send WhatsApp launch message to 30 family members, neighbors & SHG contacts." />
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => toggleChecklist('w1_2')}
                  className="flex items-start gap-2 text-left w-full cursor-pointer group"
                >
                  {checklist.w1_2 ? (
                    <CheckSquare className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-400 shrink-0 mt-0.5 group-hover:text-slate-600" />
                  )}
                  <span className={checklist.w1_2 ? 'line-through text-slate-400' : 'text-slate-700'}>
                    <TranslatedText text="Provide free samples to 10 key village elders and Sarpanch / Ward members." />
                  </span>
                </button>
              </div>

              {/* Week 2 */}
              <div className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-200 space-y-2">
                <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider block text-emerald-800">
                  <TranslatedText text="Week 2: Weekly Haat Debut (Target: 50 Customers)" />
                </span>

                <button
                  type="button"
                  onClick={() => toggleChecklist('w2_1')}
                  className="flex items-start gap-2 text-left w-full cursor-pointer group"
                >
                  {checklist.w2_1 ? (
                    <CheckSquare className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-400 shrink-0 mt-0.5 group-hover:text-slate-600" />
                  )}
                  <span className={checklist.w2_1 ? 'line-through text-slate-400' : 'text-slate-700'}>
                    <TranslatedText text="Set up first physical stall at local weekly haat with 'Buy 2, Get ₹10 Off' combo." />
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => toggleChecklist('w2_2')}
                  className="flex items-start gap-2 text-left w-full cursor-pointer group"
                >
                  {checklist.w2_2 ? (
                    <CheckSquare className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-400 shrink-0 mt-0.5 group-hover:text-slate-600" />
                  )}
                  <span className={checklist.w2_2 ? 'line-through text-slate-400' : 'text-slate-700'}>
                    <TranslatedText text="Record mobile numbers of all first-day buyers in a notebook for repeat orders." />
                  </span>
                </button>
              </div>

              {/* Week 3 */}
              <div className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-200 space-y-2">
                <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider block text-indigo-800">
                  <TranslatedText text="Week 3: B2B Commercial Tie-Ups (Target: 75 Customers)" />
                </span>

                <button
                  type="button"
                  onClick={() => toggleChecklist('w3_1')}
                  className="flex items-start gap-2 text-left w-full cursor-pointer group"
                >
                  {checklist.w3_1 ? (
                    <CheckSquare className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-400 shrink-0 mt-0.5 group-hover:text-slate-600" />
                  )}
                  <span className={checklist.w3_1 ? 'line-through text-slate-400' : 'text-slate-700'}>
                    <TranslatedText text="Sign up 2 local Kirana shops or tea stalls for recurring daily supply." />
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => toggleChecklist('w3_2')}
                  className="flex items-start gap-2 text-left w-full cursor-pointer group"
                >
                  {checklist.w3_2 ? (
                    <CheckSquare className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-400 shrink-0 mt-0.5 group-hover:text-slate-600" />
                  )}
                  <span className={checklist.w3_2 ? 'line-through text-slate-400' : 'text-slate-700'}>
                    <TranslatedText text="Run 2-hour evening auto-rickshaw Munadi broadcast across all village hamlets." />
                  </span>
                </button>
              </div>

              {/* Week 4 */}
              <div className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-200 space-y-2">
                <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider block text-amber-800">
                  <TranslatedText text="Week 4: Retention & Loyalty (Target: 100 Recurring Customers)" />
                </span>

                <button
                  type="button"
                  onClick={() => toggleChecklist('w4_1')}
                  className="flex items-start gap-2 text-left w-full cursor-pointer group"
                >
                  {checklist.w4_1 ? (
                    <CheckSquare className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-400 shrink-0 mt-0.5 group-hover:text-slate-600" />
                  )}
                  <span className={checklist.w4_1 ? 'line-through text-slate-400' : 'text-slate-700'}>
                    <TranslatedText text="Distribute loyalty passes: '10th purchase gets 50% off' to lock in repeat weekly buyers." />
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => toggleChecklist('w4_2')}
                  className="flex items-start gap-2 text-left w-full cursor-pointer group"
                >
                  {checklist.w4_2 ? (
                    <CheckSquare className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-400 shrink-0 mt-0.5 group-hover:text-slate-600" />
                  )}
                  <span className={checklist.w4_2 ? 'line-through text-slate-400' : 'text-slate-700'}>
                    <TranslatedText text="Re-invest 5% of monthly profits into promotional materials and weekly haat banners." />
                  </span>
                </button>
              </div>
            </div>
          </div>

          <p className="text-[11px] text-slate-500 font-medium pt-2">
            <TranslatedText text="Tip: Ticking off these 8 milestones guarantees your enterprise clears its monthly bank loan EMI without stress." />
          </p>
        </div>

        {/* Right: Printable Village Notice Board Flyer Preview (5 cols) */}
        <div className="lg:col-span-5 glass-panel p-5 bg-white border border-slate-200 rounded-2xl shadow-card space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Printer className="w-4 h-4 text-sky-700" />
                <h3 className="font-outfit font-bold text-slate-900 text-sm sm:text-base">
                  <TranslatedText text="Village Pamphlet & Flyer Card" />
                </h3>
              </div>
              <button
                type="button"
                onClick={() => window.print()}
                className="flex items-center gap-1 text-xs font-bold text-sky-800 bg-sky-50 hover:bg-sky-100 px-2.5 py-1 rounded-lg border border-sky-200 transition cursor-pointer"
                title="Print this village notice card"
              >
                <Printer className="w-3.5 h-3.5" />
                <span><TranslatedText text="Print Flyer" /></span>
              </button>
            </div>

            {/* Flyer Card Mockup */}
            <div className="mt-3 p-4 rounded-xl border-2 border-dashed border-sky-300 bg-gradient-to-b from-sky-50/50 to-white space-y-3 text-center shadow-subtle">
              <div className="inline-block px-2.5 py-0.5 rounded-full bg-sky-100 text-sky-900 font-bold text-[10px] uppercase tracking-wider border border-sky-200">
                🏛️ <TranslatedText text="Udyam Saathi Verified Enterprise" />
              </div>

              <div className="space-y-1">
                <h4 className="font-outfit font-extrabold text-lg text-slate-900 leading-tight">
                  {enterpriseName}
                </h4>
                <p className="text-xs text-emerald-800 font-bold">
                  {sectorCopy.tagline}
                </p>
              </div>

              <div className="p-2.5 rounded-lg bg-white border border-slate-200 text-xs text-slate-700 text-left space-y-1">
                <div className="font-bold text-slate-900 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  <span>{sectorCopy.product}</span>
                </div>
                <div className="text-[11px] text-slate-600">
                  • 100% Shuddh, Taza aur Bharosemand
                </div>
                <div className="text-[11px] text-emerald-700 font-bold">
                  • Starting at only ₹{unitPrice}/unit
                </div>
              </div>

              <div className="text-[11px] text-slate-600 space-y-1 text-left pt-1 border-t border-slate-100">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                  <span>{village}, Near Gram Panchayat ({district})</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Proprietor: {promoter}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-950 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-600 shrink-0" />
            <p className="text-[11px] leading-relaxed">
              <TranslatedText text="Paste this pamphlet on the Gram Panchayat Notice Board, Dairy Cooperative milk collection center, and primary school gate." />
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}

export default MarketingPage;
