import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, AlertCircle } from 'lucide-react';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="max-w-md mx-auto py-24 px-4 text-center">
      <div className="glass-panel p-8 space-y-4 bg-white shadow-card border border-slate-200 rounded-2xl">
        <div className="w-16 h-16 rounded-2xl bg-sovereign-50 border border-sovereign-200 text-sovereign-800 mx-auto flex items-center justify-center text-2xl font-bold font-mono">
          404
        </div>
        <h2 className="text-xl font-bold font-outfit text-slate-900">Page Not Found</h2>
        <p className="text-xs text-slate-600 font-medium">
          The requested page or route does not exist.
        </p>
        <button
          onClick={() => navigate('/dashboard')}
          className="inline-flex items-center gap-2 text-xs font-bold px-4 py-2.5 rounded-xl bg-sovereign-800 text-white hover:bg-sovereign-700 shadow-sm transition"
        >
          <Home className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </button>
      </div>
    </div>
  );
}
export default NotFoundPage;
