import React, { useState, useEffect } from 'react';
import { Cpu, CheckCircle2, Archive, Sparkles, TrendingUp, Clock, ShieldCheck, RotateCw, Check, Undo2 } from 'lucide-react';
import { getModelsList, getActiveModelInfo, activateModelVersion, rollbackModelVersion } from '../services/api';

export default function DeveloperModels() {
  const [models, setModels] = useState([]);
  const [activeInfo, setActiveInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [actionMsg, setActionMsg] = useState(null);

  const fetchModels = async () => {
    try {
      const [res, active] = await Promise.all([
        getModelsList(),
        getActiveModelInfo()
      ]);
      setModels(res.models || []);
      setActiveInfo(active);
    } catch (e) {
      console.warn('Failed to fetch models list:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleActivate = async (version) => {
    if (!window.confirm(`Activate model version '${version}' as the live inference model?`)) return;
    setActionLoading(version);
    setActionMsg(null);
    try {
      await activateModelVersion(version);
      setActionMsg({ type: 'success', text: `Model version '${version}' is now active and hot-reloaded.` });
      await fetchModels();
    } catch (e) {
      setActionMsg({ type: 'error', text: e.message });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRollback = async (version) => {
    if (!window.confirm(`Rollback live inference model to version '${version}'?`)) return;
    setActionLoading(version);
    setActionMsg(null);
    try {
      await rollbackModelVersion(version);
      setActionMsg({ type: 'success', text: `Successfully rolled back active model to '${version}'.` });
      await fetchModels();
    } catch (e) {
      setActionMsg({ type: 'error', text: e.message });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6 text-slate-100 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between p-5 rounded-2xl bg-dark-900/70 border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-emerald-600/20 border border-emerald-500/30 text-emerald-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-black font-mono text-white">MuRIL Models & Version Registry</h2>
            <p className="text-xs text-slate-400 font-sans">
              Versioned model checkpoints with test accuracy, F1 scores, hot-reload promotion, and one-click rollback.
            </p>
          </div>
        </div>

        <button
          onClick={fetchModels}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-dark-950 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-mono transition-colors"
        >
          <RotateCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {actionMsg && (
        <div className={`p-4 rounded-xl text-xs font-mono flex items-center justify-between border ${
          actionMsg.type === 'error'
            ? 'bg-rose-950/40 border-rose-500/40 text-rose-300'
            : 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
        }`}>
          <span>{actionMsg.text}</span>
          <button onClick={() => setActionMsg(null)} className="text-slate-400 hover:text-white">&times;</button>
        </div>
      )}

      {/* Active Model Spotlight */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-emerald-950/30 via-dark-900 to-teal-950/30 border border-emerald-500/40 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>LIVE ACTIVE PREDICTION MODEL</span>
            </span>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Version: <strong className="text-emerald-300 font-bold">{activeInfo?.active_version || 'baseline'}</strong>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs font-mono pt-1">
          <div className="p-3.5 rounded-xl bg-dark-950/80 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-400 block uppercase">Checkpoint Version</span>
            <span className="text-sm font-bold text-emerald-400 block truncate">
              {activeInfo?.active_version || 'baseline'}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-dark-950/80 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-400 block uppercase">Test Accuracy</span>
            <span className="text-sm font-bold text-white block">
              {Math.round((activeInfo?.metrics?.test_accuracy || 0.79) * 100)}%
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-dark-950/80 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-400 block uppercase">Macro F1 Score</span>
            <span className="text-sm font-bold text-blue-300 block">
              {activeInfo?.metrics?.macro_f1 || 0.77}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-dark-950/80 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-400 block uppercase">Activation Date</span>
            <span className="text-sm font-bold text-slate-200 block truncate">
              {activeInfo?.trained_at ? new Date(activeInfo.trained_at).toLocaleDateString() : 'Baseline'}
            </span>
          </div>
        </div>
      </div>

      {/* Models List */}
      <div className="space-y-3">
        <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
          Available Model Checkpoints ({models.length})
        </h3>

        <div className="space-y-3">
          {models.map((m, idx) => (
            <div
              key={idx}
              className={`p-5 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                m.is_active
                  ? 'bg-dark-900/90 border-emerald-500/40 shadow-glow-emerald'
                  : 'bg-dark-900/50 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <span className="text-sm font-bold font-mono text-white">{m.model_name || m.version}</span>
                  <span
                    className={`px-2.5 py-0.5 rounded-md text-[10px] font-mono font-bold ${
                      m.is_active
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {m.status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono truncate max-w-md">
                  Path: {m.model_path}
                </p>
              </div>

              <div className="flex items-center gap-4 text-xs font-mono self-end sm:self-auto">
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block">Accuracy</span>
                  <span className="font-bold text-slate-200">
                    {Math.round((m.accuracy || 0.79) * 100)}%
                  </span>
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block">F1</span>
                  <span className="font-bold text-slate-200">
                    {m.macro_f1 || 0.77}
                  </span>
                </div>

                <div className="pl-2">
                  {m.is_active ? (
                    <span className="px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-xs font-mono font-bold flex items-center gap-1">
                      <Check className="w-3.5 h-3.5" />
                      <span>Active</span>
                    </span>
                  ) : (
                    <button
                      onClick={() => handleRollback(m.version)}
                      disabled={actionLoading === m.version}
                      className="px-3 py-1.5 rounded-xl bg-dark-950 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 text-xs font-mono font-bold flex items-center gap-1.5 transition"
                    >
                      <Undo2 className="w-3.5 h-3.5 text-amber-400" />
                      <span>{actionLoading === m.version ? 'Switching...' : 'Rollback to this'}</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
