import React, { useCallback, useEffect, useState } from 'react';
import { rolesApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export function ApplicationMessages() {
  const { token, userProfile } = useAuth();
  const [applications, setApplications] = useState([]);
  const [selected, setSelected] = useState('');
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const list = await rolesApi.listApplications(token);
      setApplications(list);
      setSelected((current) => list.some((item) => item.application_id === current) ? current : list[0]?.application_id || '');
      setError('');
    } catch (err) { setError(err.message || 'Could not load applications.'); }
  }, [token]);

  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => {
    let cancelled = false;
    if (!selected || !token) { setMessages([]); return () => { cancelled = true; }; }
    rolesApi.messages(token, selected).then((list) => { if (!cancelled) setMessages(list); })
      .catch((err) => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [selected, token]);

  const send = async (event) => {
    event.preventDefault();
    if (!draft.trim() || !selected) return;
    setBusy(true); setError('');
    try {
      const message = await rolesApi.sendMessage(token, selected, draft.trim());
      setMessages((current) => [...current, message]);
      setDraft('');
    } catch (err) { setError(err.message || 'Could not send message.'); }
    finally { setBusy(false); }
  };

  return <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-bold text-slate-900">Messages</h2><p className="text-sm text-slate-600">Conversations stay attached to each submitted DPR.</p></div><button type="button" onClick={refresh} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold">Refresh</button></div>
    {error && <p role="alert" className="mb-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
    {applications.length === 0 ? <p className="rounded-xl bg-slate-50 p-6 text-sm text-slate-600">No DPR conversations yet.</p> : <div className="grid gap-5 md:grid-cols-[15rem_1fr]">
      <div className="space-y-2" aria-label="DPR conversations">{applications.map((item) => <button key={item.application_id} type="button" onClick={() => setSelected(item.application_id)} className={`w-full rounded-xl border p-3 text-left text-sm ${selected === item.application_id ? 'border-sky-500 bg-sky-50' : 'border-slate-200 bg-white'}`}><span className="block font-bold text-slate-900">{item.business_name || item.application_id}</span><span className="text-xs text-slate-600">{item.village_name || 'Village'} · {item.status}</span></button>)}</div>
      <div><div className="min-h-56 max-h-96 space-y-3 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-4">{messages.length === 0 ? <p className="text-sm text-slate-500">No messages for this application yet.</p> : messages.map((item) => <div key={item.message_id} className={`max-w-[85%] rounded-xl p-3 text-sm ${item.sender_uid === userProfile?.firebase_uid ? 'ml-auto bg-sky-900 text-white' : 'bg-white text-slate-900 shadow-sm'}`}><p className="whitespace-pre-wrap break-words">{item.body}</p><time className="mt-1 block text-[11px] opacity-70">{new Date(item.created_at).toLocaleString()}</time></div>)}</div>
      <form onSubmit={send} className="mt-3 flex gap-2"><input aria-label="Message" className="min-w-0 flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm" value={draft} onChange={(event) => setDraft(event.target.value)} maxLength={2000} placeholder="Write a message…" /><button disabled={busy || !draft.trim()} className="rounded-xl bg-sky-900 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">Send</button></form></div>
    </div>}
  </section>;
}
