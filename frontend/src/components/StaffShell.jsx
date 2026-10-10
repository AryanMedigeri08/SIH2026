import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LanguageSelector } from './LanguageSelector';
import { useAuth } from '../context/AuthContext';

export function StaffShell({ title, subtitle, children }) {
  const { userProfile, logout } = useAuth();
  const navigate = useNavigate();
  const signOut = async () => { await logout(); navigate('/login', { replace: true }); };
  return <div className="min-h-screen bg-gradient-to-br from-slate-50 via-sky-50 to-violet-50 text-slate-900">
    <header className="border-b border-slate-200 bg-white/90 px-4 py-4 shadow-sm backdrop-blur sm:px-8"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3"><Link to="/" className="text-lg font-black text-sky-950">Udyam Saathi</Link><div className="flex items-center gap-3"><LanguageSelector /><span className="hidden text-sm font-semibold text-slate-600 sm:block">{userProfile?.name}</span><button onClick={signOut} className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-bold hover:bg-slate-50">Sign out</button></div></div></header>
    <main className="mx-auto max-w-7xl px-4 py-7 sm:px-8"><div className="mb-7"><p className="text-xs font-bold uppercase tracking-widest text-sky-700">Role-based workspace</p><h1 className="mt-2 text-3xl font-black">{title}</h1><p className="mt-1 text-sm text-slate-600">{subtitle}</p></div>{children}</main>
  </div>;
}
