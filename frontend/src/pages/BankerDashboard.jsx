import React, { useCallback, useEffect, useState } from 'react';
import { Dashboard } from '../components/Dashboard/Dashboard';
import { ApplicationMessages } from '../components/ApplicationMessages';
import { StaffShell } from '../components/StaffShell';
import { rolesApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export function BankerDashboard() {
  const { token } = useAuth();
  const [tab, setTab] = useState('overview');
  const [applications, setApplications] = useState([]);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!token) return;
    try { setApplications(await rolesApi.listApplications(token)); setError(''); }
    catch (err) { setError(err.message); }
  }, [token]);
  useEffect(() => { void refresh(); }, [refresh]);

  const scrutinize = async (applicationId) => {
    setBusy(true); setError('');
    try { setSelected(await rolesApi.application(token, applicationId)); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };
  const updateStatus = async (status) => {
    if (!selected) return;
    setBusy(true); setError('');
    try {
      await rolesApi.updateStatus(token, selected.application.application_id, status);
      setSelected((current) => ({ ...current, application: { ...current.application, status } }));
      await refresh();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };
  const downloadDpr = () => {
    const dpr = selected?.project?.analysis_result?.dpr;
    if (!dpr) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(dpr, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = `${selected.application.application_id}-DPR.json`; link.click(); URL.revokeObjectURL(url);
  };

  return <StaffShell title="Banker / Auditor dashboard" subtitle="Review DPR applications submitted to your village and talk with applicants.">
    <div className="mb-5 flex gap-2"><button onClick={() => setTab('overview')} className={`rounded-xl px-4 py-2 text-sm font-bold ${tab === 'overview' ? 'bg-sky-900 text-white' : 'bg-white text-slate-700'}`}>Overview</button><button onClick={() => setTab('messages')} className={`rounded-xl px-4 py-2 text-sm font-bold ${tab === 'messages' ? 'bg-sky-900 text-white' : 'bg-white text-slate-700'}`}>Messages</button></div>
    {error && <p role="alert" className="mb-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
    {tab === 'messages' ? <ApplicationMessages /> : <div className="space-y-5">
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-bold">Received DPR applications ({applications.length})</h2><button onClick={refresh} className="text-sm font-semibold text-sky-800 underline">Refresh</button></div>
        {applications.length === 0 ? <p className="text-sm text-slate-600">No DPR applications received for your village yet.</p> : <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{applications.map((item) => <article key={item.application_id} className="rounded-2xl border border-slate-200 p-4"><h3 className="font-bold">{item.business_name || item.project_id}</h3><p className="mt-1 text-xs text-slate-600">{item.village_name}, {item.district_name}</p><p className="mt-1 text-xs font-semibold text-sky-800">{item.status}</p><button disabled={busy} onClick={() => scrutinize(item.application_id)} className="mt-3 rounded-lg bg-slate-900 px-3 py-2 text-xs font-bold text-white">Scrutinize</button></article>)}</div>}
      </section>
      {selected && <section className="space-y-4"><div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-sky-200 bg-white p-4"><div><h2 className="font-bold">Scrutinizing {selected.project.business_name}</h2><p className="text-xs text-slate-600">{selected.application.application_id} · {selected.application.status}</p></div><div className="flex flex-wrap gap-2"><select aria-label="Application status" value={selected.application.status} onChange={(event) => updateStatus(event.target.value)} className="rounded-lg border border-slate-200 px-3 py-2 text-sm"><option value="submitted">Submitted</option><option value="under_review">Under review</option><option value="needs_information">Needs information</option><option value="approved">Approved</option><option value="declined">Declined</option></select><button onClick={downloadDpr} className="rounded-lg bg-sky-900 px-3 py-2 text-sm font-bold text-white">Download DPR</button><button onClick={() => setSelected(null)} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">Close</button></div></div><Dashboard reportData={selected.project.analysis_result?.report} onOpenDpr={downloadDpr} /></section>}
    </div>}
  </StaffShell>;
}
