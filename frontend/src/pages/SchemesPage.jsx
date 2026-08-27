import React, { useState, useEffect } from 'react';
import { 
  Award, CheckCircle, Search, Filter, ShieldCheck, 
  ExternalLink, Layers, Building2, UserCheck, AlertCircle 
} from 'lucide-react';
import { fetchSchemesCatalog } from '../services/api';

export function SchemesPage() {
  const [schemes, setSchemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSector, setSelectedSector] = useState('all');

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const list = await fetchSchemesCatalog();
        setSchemes(list || []);
      } catch (e) {
        console.error("Failed to load schemes:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filteredSchemes = schemes.filter(s => {
    const matchesSearch = 
      s.scheme_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.administering_body.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.notes && s.notes.toLowerCase().includes(searchQuery.toLowerCase()));

    if (selectedSector === 'all') return matchesSearch;
    return matchesSearch && (s.target_sectors?.includes(selectedSector) || s.target_sectors?.includes('all'));
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-amber-500 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-1 flex items-center gap-1.5">
            <Award className="w-4 h-4" />
            <span>Statutory MSME Schemes Master Catalog</span>
          </div>
          <h1 className="text-2xl font-outfit font-extrabold text-white">
            Central & State MSME Credit-Linked Subsidy Matrix
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Explore active government credit schemes, capital subsidy slabs, collateral-free credit limits, and statutory eligibility criteria codified from official Ministry circulars.
          </p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-3 rounded-xl text-xs space-y-1 shrink-0">
          <span className="text-slate-400 text-[11px] block">Codified Schemes</span>
          <strong className="text-amber-400 font-mono text-sm block">10 Active Central/State Slabs</strong>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search scheme (e.g. PMEGP, PMFME, MUDRA)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Sector Filter Buttons */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
          {[
            { id: 'all', label: 'All Sectors' },
            { id: 'manufacturing', label: 'Manufacturing' },
            { id: 'service', label: 'Services / Repair' },
            { id: 'food_processing', label: 'Food Processing' },
          ].map(sec => (
            <button
              key={sec.id}
              onClick={() => setSelectedSector(sec.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                selectedSector === sec.id
                  ? 'bg-amber-500 text-black font-bold shadow-glow'
                  : 'bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {sec.label}
            </button>
          ))}
        </div>

      </div>

      {/* Schemes Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-xs">
          <div className="w-8 h-8 border-3 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          Loading statutory schemes catalog...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSchemes.map((s, idx) => (
            <div
              key={s.scheme_id || idx}
              className="glass-panel p-5 space-y-4 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-outfit font-black text-base text-white">
                    {s.scheme_id}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                    {s.administering_body || 'Ministry of MSME'}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-xs text-slate-200">{s.full_name}</h3>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Applicable: {s.target_sectors?.join(', ') || 'All Sectors'}
                  </div>
                </div>

                {/* Sizing & Cap Matrix */}
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Max Project Cost:</span>
                    <strong className="font-mono text-cyan-300">
                      {s.max_project_cost ? `₹${(s.max_project_cost.manufacturing || s.max_project_cost.service || 0).toLocaleString('en-IN')}` : 'No Strict Ceiling'}
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Promoter Margin:</span>
                    <strong className="font-mono text-white">
                      {s.promoter_contribution_pct ? `${((s.promoter_contribution_pct.special || 0.05) * 100).toFixed(0)}% to ${((s.promoter_contribution_pct.general || 0.10) * 100).toFixed(0)}%` : '10%'}
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Collateral Free Up To:</span>
                    <strong className="font-mono text-emerald-400">
                      {s.collateral_free_limit ? `₹${s.collateral_free_limit.toLocaleString('en-IN')}` : 'CGTMSE'}
                    </strong>
                  </div>
                </div>

                {s.notes && (
                  <p className="text-[11px] text-slate-300 leading-relaxed italic bg-slate-900/40 p-2 rounded-lg border border-slate-800/60">
                    {s.notes}
                  </p>
                )}
              </div>

              <div className="pt-3 border-t border-slate-800/80 text-[10px] text-slate-500 flex justify-between">
                <span>Rule Matrix Source:</span>
                <span className="font-mono text-cyan-400">government_schemes.json</span>
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}
