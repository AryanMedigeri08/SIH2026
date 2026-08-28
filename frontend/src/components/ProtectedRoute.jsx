/**
 * ProtectedRoute.jsx — Route Guard that verifies Firebase Authentication.
 * Redirects unauthenticated visitors to /login preserving target route in state.
 */

import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Loader2 } from "lucide-react";

export const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6">
        <div className="flex flex-col items-center gap-4 p-8 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-2xl backdrop-blur-md max-w-sm w-full text-center">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Loader2 className="w-7 h-7 animate-spin" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100 font-display">Verifying Sovereign Identity</h3>
            <p className="text-xs text-slate-400 mt-1">Authenticating encrypted token credentials...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
