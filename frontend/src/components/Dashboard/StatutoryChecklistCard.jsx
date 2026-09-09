import React, { useState } from 'react';
import { ClipboardCheck, CheckSquare, Square, FileText } from 'lucide-react';
import { TranslatedText } from '../TranslatedText';

export function StatutoryChecklistCard() {
  const [checkedItems, setCheckedItems] = useState({
    doc1: true,
    doc2: true,
    doc3: false,
    doc4: false,
    doc5: false,
    doc6: false,
  });

  const toggle = (id) => setCheckedItems(prev => ({ ...prev, [id]: !prev[id] }));

  const docs = [
    { id: 'doc1', title: 'Promoter KYC (Aadhaar & PAN Card)', desc: 'Mandatory identity and residence proof for all loan appraisal files.' },
    { id: 'doc2', title: 'Udyam MSME Registration Certificate', desc: 'Required for statutory priority-sector MSME classification.' },
    { id: 'doc3', title: 'Detailed Machinery Invoices / Supplier Quotations', desc: '3 independent vendor quotations for plant, machinery and equipment.' },
    { id: 'doc4', title: 'Site Lease Deed / Land Ownership Proof', desc: 'Registered lease agreement (min 5 years) or title deed for manufacturing site.' },
    { id: 'doc5', title: 'FSSAI License / Industry NOC (If Food/Manufacturing)', desc: 'Statutory quality or pollution board clearances as applicable to sector.' },
    { id: 'doc6', title: '6-Month Bank Account Statements', desc: 'Primary bank account statements verifying existing turnover/solvency.' },
  ];

  const completedCount = Object.values(checkedItems).filter(Boolean).length;

  return (
    <div className="glass-panel p-4 sm:p-6 bg-white shadow-card border border-slate-200">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
            <ClipboardCheck className="w-3.5 h-3.5" />
            <TranslatedText text="Statutory Banking Compliance" />
          </div>
          <h3 className="text-lg font-outfit font-bold text-slate-900">
            <TranslatedText text="Commercial Bank Loan Submission Checklist" />
          </h3>
          <p className="text-xs text-slate-600 mt-0.5">
            <TranslatedText text="Mandatory statutory compliance checklist required prior to formal bank credit sanction." />
          </p>
        </div>

        <span className="text-xs font-bold px-3 py-1 rounded-full bg-sovereign-50 border border-sovereign-200 text-sovereign-800 self-start sm:self-auto shrink-0">
          {completedCount} <TranslatedText text="of" /> {docs.length} <TranslatedText text="Documents Ready" />
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {docs.map((d) => {
          const isChecked = checkedItems[d.id];
          return (
            <div 
              key={d.id}
              onClick={() => toggle(d.id)}
              className={`p-3.5 rounded-xl border cursor-pointer select-none transition-all flex items-start gap-3 ${
                isChecked 
                  ? 'bg-emerald-50 border-emerald-200 shadow-subtle' 
                  : 'bg-white border-slate-200 hover:border-slate-300 shadow-subtle'
              }`}
            >
              <div className="mt-0.5">
                {isChecked ? (
                  <CheckSquare className="w-4 h-4 text-emerald-600" />
                ) : (
                  <Square className="w-4 h-4 text-slate-400" />
                )}
              </div>

              <div>
                <div className={`text-xs font-bold ${isChecked ? 'text-emerald-900' : 'text-slate-900'}`}>
                  <TranslatedText text={d.title} />
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5 font-medium">
                  <TranslatedText text={d.desc} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
export default StatutoryChecklistCard;
