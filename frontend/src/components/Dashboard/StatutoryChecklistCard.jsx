import React, { useState } from 'react';
import { ClipboardCheck, CheckSquare, Square, FileText } from 'lucide-react';

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
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ClipboardCheck className="w-4 h-4 text-cyan-400" />
            Statutory Commercial Bank Loan Submission Checklist
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Mandatory statutory compliance checklist required prior to formal bank credit sanction.
          </p>
        </div>

        <span className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-cyan-300">
          {completedCount} of {docs.length} Documents Ready
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
                  ? 'bg-emerald-950/15 border-emerald-500/30' 
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="mt-0.5 text-cyan-400">
                {isChecked ? (
                  <CheckSquare className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Square className="w-4 h-4 text-slate-500" />
                )}
              </div>

              <div>
                <div className={`text-xs font-semibold ${isChecked ? 'text-emerald-300' : 'text-white'}`}>
                  {d.title}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {d.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
