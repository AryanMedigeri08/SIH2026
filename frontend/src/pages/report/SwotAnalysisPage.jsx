import React from 'react';
import { SwotMatrixCard } from '../../components/Dashboard/SwotMatrixCard';
import { Grid3X3, Target, ShieldCheck } from 'lucide-react';

export function SwotAnalysisPage({ reportData }) {
  if (!reportData) return null;

  const swot = reportData.swot_matrix || {};

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-amber-600 bg-white shadow-card border border-slate-200">
        <div className="text-xs font-bold uppercase tracking-wider text-amber-700 mb-1 flex items-center gap-1.5">
          <Grid3X3 className="w-4 h-4" />
          <span>Dimension 6 • Domain-Grounded Strategic Evaluation</span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900">
          Grounded SWOT Analysis Matrix
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium">
          Comprehensive strategic appraisal derived from Census 2011 demographic growth, MSME saturation density, and supervised XGBoost viability factors.
        </p>
      </div>

      {/* SWOT 4-Quadrant Card Component */}
      <SwotMatrixCard swotData={swot} />

    </div>
  );
}
export default SwotAnalysisPage;
