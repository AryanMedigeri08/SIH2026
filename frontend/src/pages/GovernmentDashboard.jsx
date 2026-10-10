import React, { useCallback, useEffect, useState } from 'react';
import { StaffShell } from '../components/StaffShell';
import { rolesApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

const money = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value) || 0);

export function GovernmentDashboard() {
  const { token } = useAuth();
  const [summary, setSummary] = useState(null);
  const [schemes, setSchemes] = useState([]);
  const [schemeForm, setSchemeForm] = useState({ name: '', description: '', administering_body: '', benefit_amount: '' });
  const [paymentForm, setPaymentForm] = useState({ scheme_name: '', beneficiary_uid: '', amount: '' });
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const [nextSummary, nextSchemes] = await Promise.all([rolesApi.governmentSummary(token), rolesApi.governmentSchemes(token)]);
      setSummary(nextSummary); setSchemes(nextSchemes); setError('');
    } catch (err) { setError(err.message || 'Could not load government data.'); }
  }, [token]);
  useEffect(() => { void refresh(); }, [refresh]);

  const addScheme = async (event) => {
    event.preventDefault(); setBusy(true); setError(''); setNotice('');
    try {
      await rolesApi.addGovernmentScheme(token, { ...schemeForm, benefit_amount: schemeForm.benefit_amount ? Number(schemeForm.benefit_amount) : null });
      setSchemeForm({ name: '', description: '', administering_body: '', benefit_amount: '' });
      setNotice('Scheme added to the administrative catalog. It is not automatically treated as a verified benefit in existing DPRs.');
      await refresh();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };
  const recordPayment = async (event) => {
    event.preventDefault(); setBusy(true); setError(''); setNotice('');
    try {
      await rolesApi.recordDisbursement(token, { ...paymentForm, amount: Number(paymentForm.amount) });
      setPaymentForm({ scheme_name: '', beneficiary_uid: '', amount: '' });
      setNotice('Reimbursement recorded. The total below now reflects this actual entry.');
      await refresh();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  return <StaffShell title="Government dashboard" subtitle="Track verified scheme reimbursements and manage the administrative scheme catalog.">
    {error && <p role="alert" className="mb-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
    {notice && <p role="status" className="mb-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}
    <div className="mb-6 grid gap-4 sm:grid-cols-3">{[
      ['Registered users', summary?.registered_users ?? '—'],
      ['Bank DPR applications', summary?.bank_applications ?? '—'],
      ['Total reimbursed', money(summary?.total_reimbursed)],
    ].map(([label, value]) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-black text-sky-950">{value}</p></div>)}</div>
    <section className="mb-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Potential scheme reach from DPRs</h2><p className="mt-1 text-xs text-slate-500">These are eligibility recommendations in saved DPRs, not approved claims or paid benefits.</p><div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{summary?.scheme_interest?.length ? summary.scheme_interest.map((item) => <div key={item.scheme_name} className="rounded-xl bg-sky-50 p-4"><strong className="text-sm text-sky-950">{item.scheme_name}</strong><p className="mt-1 text-xs text-slate-700">{item.entrepreneurs} entrepreneur(s) · {item.eligible_projects} DPR(s)</p></div>) : <p className="text-sm text-slate-600">No eligible recommendations in saved DPRs yet.</p>}</div></section>
    <div className="grid gap-6 lg:grid-cols-2"><section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Scheme-by-scheme performance</h2><p className="mt-1 text-xs text-slate-500">Only recorded reimbursements are counted; DPR subsidy estimates are not payments.</p><div className="mt-5 space-y-3">{summary?.schemes?.length ? summary.schemes.map((item) => <div key={item.scheme_name} className="rounded-xl bg-slate-50 p-3"><div className="flex justify-between gap-2 text-sm"><strong>{item.scheme_name}</strong><span>{money(item.reimbursed)}</span></div><p className="mt-1 text-xs text-slate-600">{item.beneficiaries} recorded reimbursement(s)</p><div className="mt-2 h-2 rounded-full bg-slate-200"><div className="h-2 rounded-full bg-sky-600" style={{ width: `${Math.max(3, (item.reimbursed / Math.max(summary.total_reimbursed, 1)) * 100)}%` }} /></div></div>) : <p className="text-sm text-slate-600">No reimbursements have been recorded yet.</p>}</div></section>
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Record a reimbursement</h2><p className="mt-1 text-xs text-slate-500">Only enter a payment after it has actually been reimbursed.</p><form onSubmit={recordPayment} className="mt-4 space-y-3"><input className="w-full rounded-xl border p-3" placeholder="Scheme name" value={paymentForm.scheme_name} onChange={(e) => setPaymentForm({ ...paymentForm, scheme_name: e.target.value })} required /><input className="w-full rounded-xl border p-3" placeholder="Beneficiary user ID" value={paymentForm.beneficiary_uid} onChange={(e) => setPaymentForm({ ...paymentForm, beneficiary_uid: e.target.value })} required /><input className="w-full rounded-xl border p-3" type="number" min="1" step="0.01" placeholder="Amount reimbursed (₹)" value={paymentForm.amount} onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })} required /><button disabled={busy} className="rounded-xl bg-sky-900 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">Record reimbursement</button></form></section></div>
    <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Add a new scheme</h2><p className="mt-1 text-xs text-slate-500">New administrative schemes appear here; eligibility and financial models remain unchanged until separately validated.</p><form onSubmit={addScheme} className="mt-4 grid gap-3 sm:grid-cols-2"><input className="rounded-xl border p-3" placeholder="Scheme name" value={schemeForm.name} onChange={(e) => setSchemeForm({ ...schemeForm, name: e.target.value })} required /><input className="rounded-xl border p-3" placeholder="Administering body" value={schemeForm.administering_body} onChange={(e) => setSchemeForm({ ...schemeForm, administering_body: e.target.value })} /><input className="rounded-xl border p-3" type="number" min="0" placeholder="Benefit amount (optional)" value={schemeForm.benefit_amount} onChange={(e) => setSchemeForm({ ...schemeForm, benefit_amount: e.target.value })} /><textarea className="rounded-xl border p-3 sm:col-span-2" placeholder="Eligibility and benefit description" value={schemeForm.description} onChange={(e) => setSchemeForm({ ...schemeForm, description: e.target.value })} minLength={10} required /><button disabled={busy} className="rounded-xl bg-violet-900 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">Add scheme</button></form><div className="mt-5 space-y-2">{schemes.map((scheme) => <div key={scheme.scheme_id} className="rounded-xl bg-slate-50 p-3"><strong className="text-sm">{scheme.name}</strong><p className="text-xs text-slate-600">{scheme.description}</p></div>)}</div></section>
  </StaffShell>;
}
