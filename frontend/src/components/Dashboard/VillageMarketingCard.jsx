import React, { useState } from 'react';
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
  Calendar
} from 'lucide-react';
import { TranslatedText } from '../TranslatedText';

export function VillageMarketingCard({ reportData }) {
  const p = reportData?.input_parameters || {};
  const enterpriseName = p.enterprise_name || "Gramin Enterprise";
  const sector = (p.sector || "general").toLowerCase();
  const village = p.village_name || "Local Village";
  const district = p.district_name || "District";
  const promoter = p.promoter_name || "Entrepreneur";

  const [copiedTab, setCopiedTab] = useState(null);
  const [activePromoTab, setActivePromoTab] = useState('whatsapp');

  // Sector-tailored promotional copy
  const sectorDetails = sector.includes('dairy') 
    ? { product: 'Pure, Unadulterated Buffalo & Cow Milk & Fresh Paneer', tag: 'Direct from Village Farm to Your Kitchen' }
    : sector.includes('food') 
    ? { product: 'Freshly Ground Spices, Pickles & Flour', tag: 'Traditional Village Taste, 100% Hygienic' }
    : sector.includes('repair') 
    ? { product: 'Fast Mobile & Electronics Repair with Warranty', tag: 'Same-day genuine part replacement' }
    : sector.includes('apparel') || sector.includes('textile')
    ? { product: 'Custom Tailored Ethnic Wear & Ready Garments', tag: 'Affordable village rates, modern styles' }
    : { product: 'Quality Village Products & Services', tag: 'Trusted, local, and guaranteed satisfaction' };

  const whatsappMessage = `🙏 Namaste from ${enterpriseName}!

We are proud to serve our village ${village}, ${district} with ${sectorDetails.product}.

✨ Why choose us?
• 100% Quality & Hygiene Guaranteed
• Fair, honest village pricing
• ${sectorDetails.tag}

📍 Location: ${village} Centre (Near Panchayat Office)
📞 Contact / Orders: ${promoter}

Support your local village enterprise! Share this with your friends & family. Dhanyawad! 🙏`;

  const haatPitch = `🏆 Weekly Haat & Village Market Stall Strategy:
1. Stall Location: Set up near the central intersection or main grocery section of ${village} Weekly Haat.
2. Signage: Display a large, clear Hindi/Regional banner: "${enterpriseName} — ${sectorDetails.tag}".
3. Free Tasting/Demo: Offer small free samples/trials during the morning 8 AM - 11 AM peak footfall.
4. Combo Discounts: "Buy 2 units get ₹10 off" to encourage bulk purchases by families.`;

  const munadiScript = `📢 Village Auto-Rickshaw / Loudspeaker Announcement Script (Munadi):

"Suno suno suno! Gram Panchayat ${village} ke sabhi bhai-behno ke liye khush-khabri!
Ab aapke apne gaanv mein shuru ho gaya hai ${enterpriseName}!
Paiye ${sectorDetails.product}, wo bhi sabse kifayati daamo mein!
Bahar sheher jaane ki zaroorat nahi! Aaj hi padharein ${village} mein!"`;

  const handleCopy = (text, tabKey) => {
    navigator.clipboard.writeText(text);
    setCopiedTab(tabKey);
    setTimeout(() => setCopiedTab(null), 2500);
  };

  return (
    <div className="glass-panel p-4 sm:p-6 bg-white border border-slate-200/90 rounded-2xl shadow-card space-y-5 transition-all">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="p-2.5 rounded-xl bg-sky-50 text-sky-800 border border-sky-200 shadow-xs">
            <Megaphone className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base sm:text-lg font-outfit font-bold text-slate-900">
                <TranslatedText text="Village Customer Outreach & Ad Kit" />
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-sky-100 text-sky-900 border border-sky-300">
                <TranslatedText text="Grassroots GTM" />
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">
              <TranslatedText text="Field-proven rural marketing channels to acquire your first 100 paying customers" />
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
          <Store className="w-4 h-4 text-slate-400" />
          <span>{village}, {district}</span>
        </div>
      </div>

      {/* Channel Switcher Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-100 pb-2">
        <button
          type="button"
          onClick={() => setActivePromoTab('whatsapp')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
            activePromoTab === 'whatsapp'
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span><TranslatedText text="WhatsApp Promo Message" /></span>
        </button>

        <button
          type="button"
          onClick={() => setActivePromoTab('haat')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
            activePromoTab === 'haat'
              ? 'bg-sovereign-800 text-white shadow-xs'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          <span><TranslatedText text="Weekly Haat Stall Pitch" /></span>
        </button>

        <button
          type="button"
          onClick={() => setActivePromoTab('munadi')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
            activePromoTab === 'munadi'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <Volume2 className="w-3.5 h-3.5" />
          <span><TranslatedText text="Loudspeaker Munadi Script" /></span>
        </button>

        <button
          type="button"
          onClick={() => setActivePromoTab('b2b')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
            activePromoTab === 'b2b'
              ? 'bg-indigo-700 text-white shadow-xs'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span><TranslatedText text="Local B2B Buyer Tie-Ups" /></span>
        </button>
      </div>

      {/* Tab Content 1: WhatsApp Promo */}
      {activePromoTab === 'whatsapp' && (
        <div className="space-y-3 animate-in fade-in duration-200">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
              <span><TranslatedText text="Ready-to-Send WhatsApp Announcement" /></span>
            </span>
            <button
              type="button"
              onClick={() => handleCopy(whatsappMessage, 'whatsapp')}
              className="flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-3 py-1 rounded-lg border border-emerald-200 transition"
            >
              {copiedTab === 'whatsapp' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedTab === 'whatsapp' ? 'Copied to Clipboard!' : 'Copy Text'}</span>
            </button>
          </div>

          <div className="p-4 rounded-xl bg-emerald-50/40 border border-emerald-200/80 font-mono text-xs text-slate-800 whitespace-pre-wrap leading-relaxed shadow-subtle">
            {whatsappMessage}
          </div>
          <p className="text-[11px] text-slate-500 italic">
            <TranslatedText text="Tip: Forward this message to local village WhatsApp groups, Self-Help Group (SHG) networks, and youth circles." />
          </p>
        </div>
      )}

      {/* Tab Content 2: Weekly Haat Pitch */}
      {activePromoTab === 'haat' && (
        <div className="space-y-3 animate-in fade-in duration-200">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <Store className="w-3.5 h-3.5 text-sovereign-700" />
              <span><TranslatedText text="Weekly Haat (हफ़्ते का बाज़ार) Conversion Plan" /></span>
            </span>
            <button
              type="button"
              onClick={() => handleCopy(haatPitch, 'haat')}
              className="flex items-center gap-1 text-xs font-bold text-sovereign-800 bg-sovereign-50 hover:bg-sovereign-100 px-3 py-1 rounded-lg border border-sovereign-200 transition"
            >
              {copiedTab === 'haat' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedTab === 'haat' ? 'Copied!' : 'Copy Plan'}</span>
            </button>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 font-sans text-xs text-slate-800 whitespace-pre-wrap leading-relaxed space-y-2">
            {haatPitch}
          </div>
        </div>
      )}

      {/* Tab Content 3: Munadi Audio Script */}
      {activePromoTab === 'munadi' && (
        <div className="space-y-3 animate-in fade-in duration-200">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <Volume2 className="w-3.5 h-3.5 text-amber-600" />
              <span><TranslatedText text="Loudspeaker Rickshaw Announcement Script (मुनादी)" /></span>
            </span>
            <button
              type="button"
              onClick={() => handleCopy(munadiScript, 'munadi')}
              className="flex items-center gap-1 text-xs font-bold text-amber-800 bg-amber-50 hover:bg-amber-100 px-3 py-1 rounded-lg border border-amber-200 transition"
            >
              {copiedTab === 'munadi' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedTab === 'munadi' ? 'Copied!' : 'Copy Script'}</span>
            </button>
          </div>

          <div className="p-4 rounded-xl bg-amber-50/50 border border-amber-200 font-sans text-xs text-amber-950 whitespace-pre-wrap leading-relaxed">
            {munadiScript}
          </div>
        </div>
      )}

      {/* Tab Content 4: B2B Buyer Tie-Ups */}
      {activePromoTab === 'b2b' && (
        <div className="space-y-3 animate-in fade-in duration-200">
          <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5 text-indigo-600" />
            <span><TranslatedText text="Primary B2B Distribution Channels in Your Block" /></span>
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <strong className="text-slate-900 block font-bold">1. Local Retail Kirana Stores</strong>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                <TranslatedText text="Offer 8-10% wholesale trade discount for upfront cash payment or 7-day credit cycle." />
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <strong className="text-slate-900 block font-bold">2. Village Tea Stalls & Eateries</strong>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                <TranslatedText text="Secure daily recurring orders (e.g. morning milk, eggs, bread, or packaging supplies)." />
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <strong className="text-slate-900 block font-bold">3. Weekly Haats (5-10 km radius)</strong>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                <TranslatedText text="Rotate between 3 neighboring village haats on Wednesday, Friday, and Sunday." />
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <strong className="text-slate-900 block font-bold">4. Institutional Canteens & Schools</strong>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                <TranslatedText text="Register on GeM portal or local panchayat mid-day meal procurement for bulk supply." />
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default VillageMarketingCard;
