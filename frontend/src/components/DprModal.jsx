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
        setDprContent(`<div style="padding:20px; color:#dc2626;">Could not load Bank DPR: ${err.message}</div>`);
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-5xl h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Modal Top Bar */}
        <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-sovereign-50 text-sovereign-800 border border-sovereign-200">
              <FileText className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-base sm:text-lg font-outfit font-bold text-slate-900">
                Official 7-Section Statutory Bank DPR
              </h2>
              <p className="text-[11px] text-slate-500 font-mono font-medium">
                Report Ref ID: {reportId}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Format toggle */}
            <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
              <button
                onClick={() => setFormat('html')}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  format === 'html' ? 'bg-sovereign-800 text-white shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Printable HTML
              </button>
              <button
                onClick={() => setFormat('markdown')}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  format === 'markdown' ? 'bg-sovereign-800 text-white shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Markdown Memo
              </button>
            </div>

            {/* Print action button */}
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 text-xs font-bold text-white bg-sovereign-800 hover:bg-sovereign-700 px-3.5 py-1.5 rounded-xl shadow-sm transition"
            >
              <Printer className="w-4 h-4" />
              <span>Print / Save PDF</span>
            </button>

            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Document Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-100/70">
          {loading ? (
            <div className="h-full flex items-center justify-center text-slate-600 gap-2 text-sm font-medium">
              <Loader2 className="w-5 h-5 animate-spin text-sovereign-700" />
              Compiling 7-Section Bank Memorandum...
            </div>
          ) : format === 'html' ? (
            <div 
              className="bg-white text-slate-900 rounded-xl p-6 sm:p-10 shadow-card max-w-4xl mx-auto overflow-x-auto border border-slate-200 print:p-0 print:shadow-none"
              dangerouslySetInnerHTML={{ __html: dprContent }}
            />
          ) : (
            <pre className="font-mono text-xs text-slate-800 p-6 bg-white rounded-xl border border-slate-200 whitespace-pre-wrap max-w-4xl mx-auto overflow-x-auto shadow-card">
              {typeof dprContent === 'string' ? dprContent : JSON.stringify(dprContent, null, 2)}
            </pre>
          )}
        </div>

      </div>
    </div>
  );
}
export default DprModal;
