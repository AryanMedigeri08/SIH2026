import React, { useState, useEffect } from 'react';
import { FileText, Printer, Download, X, Loader2, CheckCircle2 } from 'lucide-react';
import { fetchDprDocument } from '../services/api';

export function DprModal({ isOpen, onClose, reportId, reportData }) {
  const [format, setFormat] = useState('html');
  const [dprContent, setDprContent] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen || !reportId) return;

    async function loadDpr() {
      setLoading(true);
      try {
        const res = await fetchDprDocument(reportId, format);
        setDprContent(res);
      } catch (err) {
        setDprContent(`<div style="padding:20px; color:#f43f5e;">Could not load Bank DPR: ${err.message}</div>`);
      } finally {
        setLoading(false);
      }
    }
    loadDpr();
  }, [isOpen, reportId, format]);

  if (!isOpen) return null;

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/85 backdrop-blur-md">
      <div className="bg-[#0b1120] border border-indigo-500/30 rounded-2xl w-full max-w-5xl h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Modal Top Bar */}
        <div className="bg-slate-900/90 px-6 py-4 border-b border-indigo-500/20 flex flex-wrap items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
              <FileText className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-base sm:text-lg font-outfit font-bold text-white">
                Official 7-Section Statutory Bank DPR
              </h2>
              <p className="text-[11px] text-slate-400 font-mono">
                Report Ref ID: {reportId}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Format toggle */}
            <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
              <button
                onClick={() => setFormat('html')}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  format === 'html' ? 'bg-cyan-500 text-black font-semibold shadow-glow-cyan' : 'text-slate-400 hover:text-white'
                }`}
              >
                Printable HTML
              </button>
              <button
                onClick={() => setFormat('markdown')}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  format === 'markdown' ? 'bg-cyan-500 text-black font-semibold shadow-glow-cyan' : 'text-slate-400 hover:text-white'
                }`}
              >
                Markdown Memo
              </button>
            </div>

            {/* Print action button */}
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 px-3.5 py-1.5 rounded-xl shadow-glow transition"
            >
              <Printer className="w-4 h-4" />
              <span>Print / Save PDF</span>
            </button>

            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Document Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-950">
          {loading ? (
            <div className="h-full flex items-center justify-center text-slate-400 gap-2 text-sm">
              <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
              Compiling 7-Section Bank Memorandum...
            </div>
          ) : format === 'html' ? (
            <div 
              className="bg-white text-slate-900 rounded-xl p-6 sm:p-10 shadow-lg max-w-4xl mx-auto overflow-x-auto print:p-0 print:shadow-none"
              dangerouslySetInnerHTML={{ __html: dprContent }}
            />
          ) : (
            <pre className="font-mono text-xs text-slate-300 p-6 bg-slate-900 rounded-xl border border-slate-800 whitespace-pre-wrap max-w-4xl mx-auto overflow-x-auto">
              {typeof dprContent === 'string' ? dprContent : JSON.stringify(dprContent, null, 2)}
            </pre>
          )}
        </div>

      </div>
    </div>
  );
}
