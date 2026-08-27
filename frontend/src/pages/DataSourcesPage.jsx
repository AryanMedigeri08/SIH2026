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
      <div className="glass-panel p-6 border-l-4 border-indigo-500 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1 flex items-center gap-1.5">
            <Database className="w-4 h-4" />
            <span>Architecture & Data Lineage Explorer</span>
          </div>
          <h1 className="text-2xl font-outfit font-extrabold text-white">
            Verified Ground-Truth Data Sources & Schema Catalog
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Every figure displayed in Udyam Saathi is strictly grounded in official statutory tables, national census indices, Open Government Data, and supervised ML models. No arbitrary values.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 hover:text-white hover:border-slate-600 transition-all shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          <span>Refresh Live Status</span>
        </button>
      </div>

      {/* System Status Summary Ribbon */}
      {systemStats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            <span className="text-slate-400 text-[11px] block">Database Subsystem</span>
            <strong className="text-white font-mono text-sm mt-0.5 block">{systemStats.database_mode}</strong>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            <span className="text-slate-400 text-[11px] block">AI Synthesis Engine</span>
            <strong className="text-emerald-400 font-mono text-sm mt-0.5 block">{systemStats.ai_synthesis_mode}</strong>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            <span className="text-slate-400 text-[11px] block">Supported Languages</span>
            <strong className="text-cyan-400 font-mono text-sm mt-0.5 block">6 Indic (EN, HI, MR, TA, TE, KN)</strong>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            <span className="text-slate-400 text-[11px] block">Pipeline Architecture</span>
            <strong className="text-indigo-300 font-mono text-sm mt-0.5 block">4-Tier Decoupled</strong>
          </div>
        </div>
      )}

      {/* Search and Tier Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        
        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search data sources, tables, authority..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
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
                  ? 'bg-cyan-500 text-black font-bold shadow-glow-cyan'
                  : 'bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

      </div>

      {/* Data Sources Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-xs">
          <div className="w-8 h-8 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          Loading data sources and live status...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSources.map((ds) => (
            <div
              key={ds.id}
              className="glass-panel p-5 space-y-3.5 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
                    {ds.tier}
                  </span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    {ds.status}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-sm text-white">{ds.name}</h3>
                  <div className="text-[11px] font-mono text-cyan-400 mt-1 flex items-center gap-1.5">
                    <span>Table / Object:</span>
                    <code className="bg-slate-950 px-1.5 py-0.5 rounded text-indigo-300 border border-slate-800">
                      {ds.table_or_file}
                    </code>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">
                  {ds.description}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800/80 space-y-1.5 text-[11px]">
                <div className="flex justify-between text-slate-400">
                  <span>Storage / Type:</span>
                  <span className="text-slate-200 font-medium">{ds.type}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Record Count / Sizing:</span>
                  <span className="text-emerald-400 font-mono font-semibold">
                    {typeof ds.record_count === 'number' ? ds.record_count.toLocaleString('en-IN') : ds.record_count} records
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Query Latency SLA:</span>
                  <span className="text-cyan-300 font-mono">{ds.latency_sla}</span>
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
