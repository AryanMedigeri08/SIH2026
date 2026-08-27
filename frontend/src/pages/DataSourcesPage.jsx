import React, { useState, useEffect } from 'react';
import { 
  Database, Server, ShieldCheck, CheckCircle2, RefreshCw, 
  Search, ExternalLink, Layers, Activity, AlertCircle 
} from 'lucide-react';
import { fetchDataSources, fetchSystemStats } from '../services/api';

export function DataSourcesPage() {
  const [dataSources, setDataSources] = useState([]);
  const [systemStats, setSystemStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTier, setSelectedTier] = useState('ALL');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sources, stats] = await Promise.all([
        fetchDataSources(),
        fetchSystemStats(),
      ]);
      setDataSources(sources || []);
      setSystemStats(stats);
    } catch (e) {
      console.error("Failed to load data sources:", e);
    } finally {
      setLoading(false);
    }
  };

  const filteredSources = dataSources.filter(s => {
    const matchesSearch = 
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.table_or_file.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.source_authority.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (selectedTier === 'ALL') return matchesSearch;
    if (selectedTier === 'TIER1') return matchesSearch && s.tier.includes('Tier 1');
    if (selectedTier === 'TIER2') return matchesSearch && s.tier.includes('Tier 2');
    if (selectedTier === 'TIER3') return matchesSearch && s.tier.includes('Tier 3');
    return matchesSearch;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-sovereign-800 bg-white shadow-card border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-sovereign-700 mb-1 flex items-center gap-1.5">
            <Database className="w-4 h-4" />
            <span>Architecture & Data Lineage Explorer</span>
          </div>
          <h1 className="text-2xl font-outfit font-extrabold text-slate-900">
            Verified Ground-Truth Data Sources & Schema Catalog
          </h1>
          <p className="text-xs text-slate-600 mt-1 max-w-2xl font-medium">
            Every figure displayed in Udyam Saathi is strictly grounded in official statutory tables, national census indices, Open Government Data, and supervised ML models. No arbitrary values.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-slate-100 border border-slate-300 text-slate-800 hover:bg-slate-200 transition-all shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sovereign-800' : ''}`} />
          <span>Refresh Live Status</span>
        </button>
      </div>

      {/* System Status Summary Ribbon */}
      {systemStats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
            <span className="text-slate-500 text-[11px] block font-medium">Database Subsystem</span>
            <strong className="text-slate-900 font-mono text-sm mt-0.5 block font-bold">{systemStats.database_mode}</strong>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
            <span className="text-slate-500 text-[11px] block font-medium">AI Synthesis Engine</span>
            <strong className="text-emerald-700 font-mono text-sm mt-0.5 block font-bold">{systemStats.ai_synthesis_mode}</strong>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
            <span className="text-slate-500 text-[11px] block font-medium">Supported Languages</span>
            <strong className="text-sovereign-800 font-mono text-sm mt-0.5 block font-bold">6 Indic (EN, HI, MR, TA, TE, KN)</strong>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
            <span className="text-slate-500 text-[11px] block font-medium">Pipeline Architecture</span>
            <strong className="text-blue-900 font-mono text-sm mt-0.5 block font-bold">4-Tier Decoupled</strong>
          </div>
        </div>
      )}

      {/* Search and Tier Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
        
        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search data sources, tables, authority..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sovereign-600 font-medium"
          />
        </div>

        {/* Tier Filters */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
          {[
            { id: 'ALL', label: 'All Sources' },
            { id: 'TIER1', label: 'Tier 1: Math & Demographics' },
            { id: 'TIER2', label: 'Tier 2: Amenities & ML' },
            { id: 'TIER3', label: 'Tier 3: Groq LLM' },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setSelectedTier(t.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                selectedTier === t.id
                  ? 'bg-sovereign-800 text-white font-bold shadow-sm'
                  : 'bg-white text-slate-700 hover:text-slate-900 border border-slate-200 shadow-subtle'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

      </div>

      {/* Data Sources Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-500 text-xs">
          <div className="w-8 h-8 border-3 border-sovereign-800 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          Loading data sources and live status...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSources.map((ds) => (
            <div
              key={ds.id}
              className="glass-panel p-5 space-y-3.5 bg-white border border-slate-200 shadow-card hover:border-slate-300 transition-all flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
                    {ds.tier}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
                    {ds.status}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-sm text-slate-900">{ds.name}</h3>
                  <div className="text-[11px] font-mono text-slate-600 mt-1 flex items-center gap-1.5">
                    <span>Source:</span>
                    <code className="bg-slate-50 px-1.5 py-0.5 rounded text-sovereign-900 border border-slate-200 font-bold">
                      {ds.table_or_file}
                    </code>
                  </div>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed font-normal">
                  {ds.description}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-200 space-y-1.5 text-[11px]">
                <div className="flex justify-between text-slate-600 font-medium">
                  <span>Storage / Type:</span>
                  <span className="text-slate-900 font-bold">{ds.type}</span>
                </div>
                <div className="flex justify-between text-slate-600 font-medium">
                  <span>Record Count / Sizing:</span>
                  <span className="text-emerald-700 font-mono font-bold">
                    {typeof ds.record_count === 'number' ? ds.record_count.toLocaleString('en-IN') : ds.record_count} records
                  </span>
                </div>
                <div className="flex justify-between text-slate-600 font-medium">
                  <span>Query Latency SLA:</span>
                  <span className="text-sovereign-800 font-mono font-bold">{ds.latency_sla}</span>
                </div>
                <div className="text-[10px] text-slate-500 pt-1 italic">
                  Authority: {ds.source_authority}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}
export default DataSourcesPage;
