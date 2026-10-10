import React, { useCallback, useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { StaffShell } from '../components/StaffShell';
import { rolesApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export function AdminDashboard() {
  const { token } = useAuth();
  const [tab, setTab] = useState('overview');
  const [users, setUsers] = useState([]);
  const [applications, setApplications] = useState([]);
  const [activity, setActivity] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [bankRequests, setBankRequests] = useState([]);
  const [bankForm, setBankForm] = useState({ state_name: '', district_name: '', village_name: '', available: true, evidence: '' });
  const [selectedUser, setSelectedUser] = useState(null);
  const [userProjects, setUserProjects] = useState([]);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [form, setForm] = useState({ email: '', name: '', role: 'banker', state_name: '', district_name: '', village_name: '' });
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const [nextUsers, nextApplications, nextActivity, nextStatus, nextRequests] = await Promise.all([
        rolesApi.adminUsers(token), rolesApi.adminApplications(token), rolesApi.adminActivity(token),
        rolesApi.adminSystemStatus(token), rolesApi.adminBankVerificationRequests(token),
      ]);
      setUsers(nextUsers); setApplications(nextApplications); setActivity(nextActivity);
      setSystemStatus(nextStatus); setBankRequests(nextRequests); setError('');
    } catch (err) { setError(err.message || 'Could not load administration data.'); }
  }, [token]);
  useEffect(() => { void refresh(); }, [refresh]);

  const createStaff = async (event) => {
    event.preventDefault(); setBusy(true); setError(''); setNotice('');
    try {
      const result = await rolesApi.createStaff(token, form);
      setNotice(`${result.created ? 'Created' : 'Found existing'} ${form.role} account: ${result.email}. Share the temporary password through a secure channel.`);
      setForm({ email: '', name: '', role: 'banker', state_name: '', district_name: '', village_name: '' });
      await refresh();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const inspectUser = async (user) => {
    setError(''); setSelectedUser(user); setSelectedApplication(null);
    try { setUserProjects(await rolesApi.adminUserProjects(token, user.firebase_uid)); }
    catch (err) { setError(err.message); }
  };
  const inspectApplication = async (id) => {
    setError(''); setSelectedUser(null);
    try { setSelectedApplication(await rolesApi.adminApplication(token, id)); }
    catch (err) { setError(err.message); }
  };

  const saveBankVerification = async (event) => {
    event.preventDefault(); setBusy(true); setError(''); setNotice('');
    try {
      await rolesApi.saveBankVerification(token, bankForm);
      setNotice(`Bank availability for ${bankForm.village_name} was recorded with administrator evidence.`);
      setBankForm({ state_name: '', district_name: '', village_name: '', available: true, evidence: '' });
      await refresh();
    } catch (err) { setError(err.message || 'Could not save bank verification.'); }
    finally { setBusy(false); }
  };
  const roleCounts = Object.entries(users.reduce((counts, user) => {
    const role = user.role || 'entrepreneur'; counts[role] = (counts[role] || 0) + 1; return counts;
  }, {})).map(([name, value]) => ({ name, value }));
  const applicationCounts = Object.entries(applications.reduce((counts, item) => {
    counts[item.status] = (counts[item.status] || 0) + 1; return counts;
  }, {})).map(([name, count]) => ({ name, count }));

  return <StaffShell title="SuperAdmin dashboard" subtitle="Role-restricted account, DPR and activity oversight.">
    {error && <p role="alert" className="mb-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
    {notice && <p role="status" className="mb-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}
    <nav aria-label="SuperAdmin dashboard sections" className="mb-6 flex flex-wrap gap-2">{[['overview', 'Overview'], ['users', 'Users & staff'], ['applications', 'DPR applications'], ['banks', 'Bank verification'], ['system', 'System status']].map(([id, label]) => <button key={id} type="button" onClick={() => setTab(id)} aria-current={tab === id ? 'page' : undefined} className={`rounded-xl px-4 py-2.5 text-sm font-bold ${tab === id ? 'bg-sky-900 text-white shadow-md' : 'border border-slate-200 bg-white text-slate-700 hover:bg-sky-50'}`}>{label}</button>)}</nav>
    {tab === 'overview' && <>
    <div className="mb-6 grid gap-4 sm:grid-cols-3">{[['Users shown', users.length], ['Bank DPR applications shown', applications.length], ['Recent events shown', activity.length]].map(([label, value]) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-3xl font-black text-sky-950">{value}</p></div>)}</div>
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-bold">User roles</h2><p className="mb-3 text-xs text-slate-500">Breakdown of the most recent {users.length} users shown.</p>{roleCounts.length ? <div role="img" aria-label="Pie chart showing user roles" className="h-72"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={roleCounts} dataKey="value" nameKey="name" cx="50%" cy="45%" outerRadius={80} label>{roleCounts.map((item, index) => <Cell key={item.name} fill={['#0369a1', '#7c3aed', '#0d9488', '#ea580c'][index % 4]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></div> : <p className="text-sm text-slate-500">No users to chart.</p>}</section>
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-bold">DPR application status</h2><p className="mb-3 text-xs text-slate-500">Status of the most recent {applications.length} applications shown.</p>{applicationCounts.length ? <div role="img" aria-label="Bar chart showing DPR application status" className="h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={applicationCounts}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="count" name="Applications" fill="#0284c7" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></div> : <p className="text-sm text-slate-500">No applications to chart.</p>}</section>
    </div>
    </>}
    {tab === 'users' && <>
    <section className="mb-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Provision staff account</h2><p className="mt-1 text-xs text-slate-500">Entrepreneurs register publicly; banker and government accounts are restricted to administration. Village bankers are also created automatically on the first eligible DPR submission.</p><form onSubmit={createStaff} className="mt-4 grid gap-3 sm:grid-cols-2"><input className="rounded-xl border p-3" type="text" placeholder="Staff email or village@udyam" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /><input className="rounded-xl border p-3" placeholder="Full name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /><select className="rounded-xl border p-3" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}><option value="banker">Banker / Auditor</option><option value="government">Government Official</option></select>{form.role === 'banker' && <><input className="rounded-xl border p-3" placeholder="State" value={form.state_name} onChange={(e) => setForm({ ...form, state_name: e.target.value })} required /><input className="rounded-xl border p-3" placeholder="District" value={form.district_name} onChange={(e) => setForm({ ...form, district_name: e.target.value })} required /><input className="rounded-xl border p-3" placeholder="Village" value={form.village_name} onChange={(e) => setForm({ ...form, village_name: e.target.value })} required /></>}<button disabled={busy} className="rounded-xl bg-sky-900 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">Create staff login</button></form></section>
    </>}
    {tab === 'users' && <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Users (most recent {users.length})</h2><div className="mt-3 grid max-h-[36rem] gap-3 overflow-auto sm:grid-cols-2">{users.map((user) => <div key={user.firebase_uid} className="rounded-xl bg-slate-50 p-3 text-sm"><strong>{user.name}</strong><span className="ml-2 rounded bg-sky-100 px-2 py-0.5 text-xs">{user.role || 'entrepreneur'}</span><p className="break-all text-xs text-slate-600">{user.email || user.phone || user.firebase_uid}</p><button type="button" onClick={() => inspectUser(user)} className="mt-2 text-xs font-bold text-sky-800 underline">View enterprises</button></div>)}</div></section>}
    {tab === 'applications' && <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">DPR applications</h2><div className="mt-3 grid max-h-[36rem] gap-3 overflow-auto sm:grid-cols-2">{applications.map((item) => <div key={item.application_id} className="rounded-xl bg-slate-50 p-3 text-sm"><strong>{item.application_id}</strong> · {item.status}<p className="break-all text-xs text-slate-600">Project {item.project_id}</p><button type="button" onClick={() => inspectApplication(item.application_id)} className="mt-2 text-xs font-bold text-sky-800 underline">Inspect application and messages</button></div>)}{!applications.length && <p className="text-sm text-slate-500">No submissions yet.</p>}</div></section>}
    {tab === 'users' && selectedUser && <section className="mt-6 rounded-3xl border border-sky-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">{selectedUser.name}: saved enterprises</h2><p className="mt-1 text-xs text-slate-500">Read-only view of persisted project records.</p><div className="mt-3 grid gap-3 sm:grid-cols-2">{userProjects.map((project) => <div key={project.project_id} className="rounded-xl bg-slate-50 p-4"><strong>{project.business_name}</strong><p className="text-xs text-slate-600">{project.village_name}, {project.district_name} · {project.status}</p><p className="text-xs text-slate-500">{project.project_id}</p></div>)}{!userProjects.length && <p className="text-sm text-slate-500">No enterprises saved.</p>}</div></section>}
    {tab === 'applications' && selectedApplication && <section className="mt-6 rounded-3xl border border-sky-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Application {selectedApplication.application.application_id}</h2><p className="mt-2 text-sm">{selectedApplication.project?.business_name || selectedApplication.application.project_id} · {selectedApplication.application.status}</p><p className="mt-1 text-xs text-slate-500">{selectedApplication.project?.village_name}, {selectedApplication.project?.district_name}</p><h3 className="mt-5 font-bold">Conversation ({selectedApplication.messages.length})</h3><div className="mt-2 max-h-64 space-y-2 overflow-auto">{selectedApplication.messages.map((message) => <p key={message.message_id} className="rounded-xl bg-slate-50 p-3 text-sm">{message.body}</p>)}{!selectedApplication.messages.length && <p className="text-sm text-slate-500">No messages yet.</p>}</div></section>}
    {tab === 'banks' && <div className="grid gap-6 xl:grid-cols-2">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Village bank verification requests</h2><p className="mt-1 text-xs text-slate-500">Verify against credible branch evidence before enabling DPR handoff. Never mark a branch available solely from regional averages.</p><div className="mt-4 max-h-[30rem] space-y-2 overflow-auto">{bankRequests.map((request) => <div key={request.project_id} className="rounded-xl bg-slate-50 p-3 text-sm"><strong>{request.business_name || request.project_id}</strong><p className="text-xs text-slate-600">{request.village_name}, {request.district_name}, {request.state_name}</p><p className="mt-1 text-xs font-semibold text-sky-800">{request.verification.verified ? request.verification.available ? 'Bank verified' : 'No bank verified' : 'Awaiting verification'}</p><button type="button" onClick={() => setBankForm({ state_name: request.state_name, district_name: request.district_name, village_name: request.village_name, available: true, evidence: '' })} className="mt-2 text-xs font-bold text-sky-800 underline">Review location</button></div>)}{!bankRequests.length && <p className="text-sm text-slate-500">No verification requests yet.</p>}</div></section>
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Record branch verification</h2><p className="mt-1 text-xs text-slate-500">This audited decision controls whether a village DPR can be sent. Provide a branch name, address, or source reference as evidence.</p><form onSubmit={saveBankVerification} className="mt-4 space-y-3"><input className="w-full rounded-xl border p-3" placeholder="State" value={bankForm.state_name} onChange={(e) => setBankForm({ ...bankForm, state_name: e.target.value })} required /><input className="w-full rounded-xl border p-3" placeholder="District" value={bankForm.district_name} onChange={(e) => setBankForm({ ...bankForm, district_name: e.target.value })} required /><input className="w-full rounded-xl border p-3" placeholder="Village" value={bankForm.village_name} onChange={(e) => setBankForm({ ...bankForm, village_name: e.target.value })} required /><select className="w-full rounded-xl border p-3" value={String(bankForm.available)} onChange={(e) => setBankForm({ ...bankForm, available: e.target.value === 'true' })}><option value="true">Bank branch confirmed</option><option value="false">No bank branch confirmed</option></select><textarea className="w-full rounded-xl border p-3" placeholder="Verification evidence (branch name, address or source URL)" minLength={8} maxLength={500} value={bankForm.evidence} onChange={(e) => setBankForm({ ...bankForm, evidence: e.target.value })} required /><button disabled={busy} className="rounded-xl bg-sky-900 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">Save verification</button></form></section>
    </div>}
    {tab === 'system' && <>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[
        ['API', systemStatus?.api || 'unknown'],
        ['Database', systemStatus?.database?.status || 'unknown'],
        ['Database engine', systemStatus?.database?.engine || 'unknown'],
        ['DB query latency', systemStatus?.database?.latency_ms != null ? `${systemStatus.database.latency_ms} ms` : 'unknown'],
        ['Free disk space', systemStatus?.disk_free_mb != null ? `${systemStatus.disk_free_mb} MB` : 'unknown'],
        ['ML model file', systemStatus?.services?.ml_model_file_present ? 'present' : 'missing'],
        ['LLM configuration', systemStatus?.services?.llm_configured ? 'configured' : 'not configured'],
        ['Speech configuration', systemStatus?.services?.speech_configured ? 'configured' : 'not configured'],
      ].map(([label, value]) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-bold uppercase text-slate-500">{label}</p><p className="mt-2 break-all text-lg font-black text-sky-950">{value}</p></div>)}</div>
      <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Service details</h2><p className="mt-2 text-sm text-slate-700">Firebase Admin configuration: {systemStatus?.authentication?.configured ? 'configured' : 'not configured'} (remote connectivity is not tested here).</p><p className="mt-1 text-sm text-slate-700">Database fallback: {systemStatus?.database?.fallback_active ? 'Neon configured, but SQLite fallback is active — investigate connectivity' : 'not active'}.</p><p className="mt-1 text-sm text-slate-700">Uptime: {systemStatus?.uptime_seconds ?? '—'} seconds · Checked: {systemStatus?.checked_at ? new Date(systemStatus.checked_at).toLocaleString() : '—'}</p><button type="button" onClick={() => void refresh()} className="mt-4 rounded-xl border border-sky-300 px-4 py-2 text-sm font-bold text-sky-900">Refresh status</button></section>
      <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-bold">Recent account and application events</h2><div className="mt-3 max-h-72 space-y-2 overflow-auto">{activity.map((event) => <div key={event.event_id} className="flex flex-wrap justify-between gap-2 rounded-xl bg-slate-50 p-3 text-xs"><span><strong>{event.action.replaceAll('_', ' ')}</strong> · {event.actor_uid}</span><time>{new Date(event.created_at).toLocaleString()}</time></div>)}{!activity.length && <p className="text-sm text-slate-500">No events recorded yet.</p>}</div></section>
    </>}
  </StaffShell>;
}
