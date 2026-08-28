import React, { useState, useEffect } from 'react';
import { StatutoryChecklistCard } from '../../components/Dashboard/StatutoryChecklistCard';
import { fetchDprDocument } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { FileText, Printer, Download, Copy, Check, Loader2, CheckCircle2, ShieldCheck, Sparkles, Landmark, IndianRupee, PieChart, TrendingUp } from 'lucide-react';

export function BankDprPage({ reportData }) {
  const { token } = useAuth();
  const [format, setFormat] = useState('html');
  const [dprContent, setDprContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const reportId = reportData?.report_id;
  const p = reportData?.input_parameters || {};
  const fin = reportData?.financial_analysis || {};
  const schemes = reportData?.scheme_optimization || [];
  const topScheme = schemes.find(s => s.eligible) || schemes[0] || {};

  const projectCost = Number(p.project_cost) || 0;
  const subsidyAmount = topScheme.subsidy_grant_amount || 0;
  const promoterMargin = fin.promoter_margin_amount || (projectCost * 0.10);
  const termLoan = fin.loan_principal || Math.max(projectCost - subsidyAmount - promoterMargin, 0);
  const monthlyEmi = fin.amortization?.monthly_emi || 0;
  const dscr = fin.dscr?.dscr ?? 1.33;

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

  const handleCopy = () => {
    const textToCopy = format === 'html' 
      ? dprContent.replace(/<[^>]+>/g, '') // plain text strip for html
      : dprContent;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([dprContent], { type: format === 'html' ? 'text/html' : 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Bank_DPR_${p.enterprise_name ? p.enterprise_name.replace(/\s+/g, '_') : 'Enterprise'}_${reportId}.${format === 'html' ? 'html' : 'md'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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

        <div className="flex flex-wrap items-center gap-2 shrink-0">
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

          {/* Copy action */}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 px-3 py-2 rounded-xl shadow-xs border border-slate-200 transition"
            title="Copy memorandum text to clipboard"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4 text-slate-500" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {/* Download action */}
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 px-3 py-2 rounded-xl shadow-xs border border-slate-200 transition"
            title="Download DPR file"
          >
            <Download className="w-4 h-4 text-slate-500" />
            <span>Download</span>
          </button>

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

      {/* Credit Appraisal Summary Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <PieChart className="w-3 h-3 text-sovereign-700" />
            <span>Total Outlay</span>
          </div>
          <strong className="text-base font-mono font-extrabold text-slate-900 block mt-1">
            ₹{(projectCost / 100000).toFixed(2)}L
          </strong>
          <span className="text-[10px] text-slate-500 font-medium">100% Sourced</span>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-emerald-600" />
            <span>Capital Grant</span>
          </div>
          <strong className="text-base font-mono font-extrabold text-emerald-700 block mt-1">
            ₹{(subsidyAmount / 100000).toFixed(2)}L
          </strong>
          <span className="text-[10px] text-emerald-700 font-semibold">{topScheme.scheme_id || 'Scheme'} Subsidy</span>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <Landmark className="w-3 h-3 text-amber-700" />
            <span>Term Loan</span>
          </div>
          <strong className="text-base font-mono font-extrabold text-amber-900 block mt-1">
            ₹{(termLoan / 100000).toFixed(2)}L
          </strong>
          <span className="text-[10px] text-amber-700 font-semibold">@ {fin.amortization?.annual_rate_pct || 11}% p.a.</span>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <IndianRupee className="w-3 h-3 text-indigo-700" />
            <span>Monthly EMI</span>
          </div>
          <strong className="text-base font-mono font-extrabold text-indigo-900 block mt-1">
            ₹{Math.round(monthlyEmi).toLocaleString('en-IN')}
          </strong>
          <span className="text-[10px] text-slate-500 font-medium">60 Mo Amortized</span>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all col-span-2 sm:col-span-1">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-sovereign-700" />
            <span>DSCR Solvency</span>
          </div>
          <strong className="text-base font-mono font-extrabold text-sovereign-900 block mt-1">
            {dscr.toFixed(2)}x
          </strong>
          <span className={`text-[10px] font-bold ${dscr >= 1.33 ? 'text-emerald-700' : 'text-amber-700'}`}>
            {dscr >= 1.33 ? 'RBI Benchmark Met' : 'Below 1.33'}
          </span>
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
