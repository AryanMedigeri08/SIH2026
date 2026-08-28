import React, { useState, useEffect } from 'react';
import { StatutoryChecklistCard } from '../../components/Dashboard/StatutoryChecklistCard';
import { fetchDprDocument } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { FileText, Printer, Download, Loader2, CheckCircle2, ShieldCheck, Sparkles } from 'lucide-react';

export function BankDprPage({ reportData }) {
  const { token } = useAuth();
  const [format, setFormat] = useState('html');
  const [dprContent, setDprContent] = useState('');
  const [loading, setLoading] = useState(false);

  const reportId = reportData?.report_id;

  useEffect(() => {
    if (!reportId) return;

    async function loadDpr() {
      setLoading(true);
      try {
        const res = await fetchDprDocument(reportId, format, token);
        setDprContent(res);
      } catch (err) {
        setDprContent(`<div style="padding:20px; color:#dc2626;">Could not load Bank DPR: ${err.message}</div>`);
      } finally {
        setLoading(false);
      }
    }
    loadDpr();
  }, [reportId, format, token]);

  if (!reportData) return null;

  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      window.print();
      return;
    }
    printWindow.document.write(dprContent);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
    }, 250);
  };

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-purple-600 bg-gradient-to-r from-white via-purple-50/20 to-white shadow-card border border-slate-200/90 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-purple-700 mb-1 flex items-center gap-1.5">
            <FileText className="w-4 h-4 text-purple-600" />
            <span>Dimension 7 • Statutory Bank Detailed Project Report (DPR)</span>
          </div>
          <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
            Official 7-Section Bank DPR & Sanction Memorandum
          </h1>
          <p className="text-xs text-slate-600 mt-1 max-w-2xl font-medium leading-relaxed">
            Compiled in accordance with standard commercial bank credit underwriting norms, containing full means of finance, 5-year amortization, demographic validation, and risk mitigation schedules.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Format toggle */}
          <div className="flex bg-slate-100/90 p-1 rounded-xl border border-slate-200 text-xs shadow-inner">
            <button
              onClick={() => setFormat('html')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                format === 'html' ? 'bg-gradient-to-r from-sovereign-800 to-indigo-900 text-white shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Printable HTML
            </button>
            <button
              onClick={() => setFormat('markdown')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                format === 'markdown' ? 'bg-gradient-to-r from-sovereign-800 to-indigo-900 text-white shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Markdown Memo
            </button>
          </div>

          {/* Print action button */}
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 text-xs font-bold text-white bg-gradient-to-r from-sovereign-800 to-sky-700 hover:from-sovereign-700 hover:to-sky-600 px-4 py-2 rounded-xl shadow-md shadow-sovereign-900/15 border border-sky-400/20 transition"
          >
            <Printer className="w-4 h-4 text-sky-200" />
            <span>Print / PDF</span>
          </button>
        </div>
      </div>

      {/* Statutory Bank Checklist */}
      <StatutoryChecklistCard />

      {/* Embedded 7-Section DPR Paper Container */}
      <div className="glass-panel p-6 bg-slate-50/70 border border-slate-200/90 shadow-card rounded-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-6">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Statutory 7-Section Bank Memorandum Output
            </span>
          </div>
          <span className="text-xs font-mono font-bold text-sovereign-900 bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-subtle">
            Report Ref: {reportId}
          </span>
        </div>

        {loading ? (
          <div className="py-24 flex items-center justify-center text-slate-600 gap-2 text-sm font-medium">
            <Loader2 className="w-5 h-5 animate-spin text-sovereign-800" />
            Compiling Official 7-Section Bank Memorandum...
          </div>
        ) : format === 'html' ? (
          <div 
            className="bg-white text-slate-900 rounded-xl p-6 sm:p-10 shadow-card max-w-4xl mx-auto overflow-x-auto border border-slate-200/90 print:p-0 print:shadow-none"
            dangerouslySetInnerHTML={{ __html: dprContent }}
          />
        ) : (
          <pre className="font-mono text-xs text-slate-800 p-6 bg-white rounded-xl border border-slate-200/90 whitespace-pre-wrap max-w-4xl mx-auto overflow-x-auto shadow-card">
            {typeof dprContent === 'string' ? dprContent : JSON.stringify(dprContent, null, 2)}
          </pre>
        )}
      </div>

    </div>
  );
}
export default BankDprPage;
