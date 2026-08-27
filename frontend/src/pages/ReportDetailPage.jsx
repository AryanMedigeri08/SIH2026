import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Dashboard } from '../components/Dashboard/Dashboard';
import { DprModal } from '../components/DprModal';
import { fetchFeasibilityReport } from '../services/api';
import { ArrowLeft, AlertCircle, RefreshCw } from 'lucide-react';

export function ReportDetailPage({ onOpenWizard }) {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDprOpen, setIsDprOpen] = useState(false);

  useEffect(() => {
    async function loadReport() {
      if (!reportId) return;
      setLoading(true);
      setError(null);
      try {
        const data = await fetchFeasibilityReport(reportId);
        setReportData(data);
      } catch (err) {
        setError(err.message || `Failed to retrieve report ${reportId}`);
      } finally {
        setLoading(false);
      }
    }
    loadReport();
  }, [reportId]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto py-24 px-4 text-center">
        <div className="inline-block p-4 rounded-2xl bg-slate-900 border border-cyan-500/30 shadow-glow mb-4">
          <div className="w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
        </div>
        <h3 className="text-lg font-bold font-outfit text-white">
          Retrieving Feasibility Report <code className="font-mono text-cyan-400">{reportId}</code>...
        </h3>
      </div>
    );
  }

  if (error || !reportData) {
    return (
      <div className="max-w-xl mx-auto py-20 px-4 text-center">
        <div className="glass-panel p-8 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-rose-500/10 text-rose-400 mx-auto flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white">Report Not Found</h2>
          <p className="text-xs text-slate-400">
            {error || `Could not find any cached feasibility assessment under ID ${reportId}.`}
          </p>
          <div className="flex justify-center gap-3 pt-2">
            <button
              onClick={() => navigate('/')}
              className="text-xs font-semibold px-4 py-2 rounded-xl bg-slate-800 text-slate-200 hover:text-white"
            >
              Back to Dashboard
            </button>
            <button
              onClick={() => navigate('/wizard')}
              className="text-xs font-semibold px-4 py-2 rounded-xl bg-cyan-500 text-black hover:bg-cyan-400 font-bold"
            >
              New Assessment
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Return navigation bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
        <button
          onClick={() => navigate('/')}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Assessments</span>
        </button>
      </div>

      <Dashboard
        reportData={reportData}
        onOpenDpr={() => setIsDprOpen(true)}
        onOpenWizard={onOpenWizard}
      />

      <DprModal
        isOpen={isDprOpen}
        onClose={() => setIsDprOpen(false)}
        reportId={reportId}
        reportData={reportData}
      />
    </div>
  );
}
