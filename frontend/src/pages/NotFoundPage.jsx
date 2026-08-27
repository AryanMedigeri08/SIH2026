import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, AlertCircle } from 'lucide-react';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="max-w-md mx-auto py-24 px-4 text-center">
      <div className="glass-panel p-8 space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 text-cyan-400 mx-auto flex items-center justify-center text-3xl font-bold">
          404
        </div>
        <h2 className="text-xl font-bold font-outfit text-white">Page Not Found</h2>
        <p className="text-xs text-slate-400">
          The requested page or route does not exist.
        </p>
        <button
          onClick={() => navigate('/')}
          className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-cyan-500 text-black hover:bg-cyan-400 font-bold shadow-glow"
        >
          <Home className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </button>
      </div>
    </div>
  );
}
