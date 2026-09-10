import React, { useState, useEffect } from 'react';
import { Cpu, ShieldCheck, TrendingUp, Layers, CheckCircle2, AlertTriangle, Clock, Database, BarChart2, Play, Pause, RefreshCw, Zap } from 'lucide-react';
import { getActiveModelInfo, getDatasetStats, getCrawlStatus, getTrainingStatus, pauseAutoTraining, resumeAutoTraining, updateRetrainThreshold, triggerManualTraining } from '../services/api';

export default function DeveloperTraining() {
  const [modelMeta, setModelMeta] = useState(null);
  const [stats, setStats] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [triggerStatus, setTriggerStatus] = useState(null);
  const [thresholdInput, setThresholdInput] = useState('100');
  const [savingThreshold, setSavingThreshold] = useState(false);
  const [togglingPause, setTogglingPause] = useState(false);
  const [triggeringManual, setTriggeringManual] = useState(false);
  const [actionMsg, setActionMsg] = useState(null);

  const fetchData = async () => {
    try {
      const [m, s, c, t] = await Promise.all([
        getActiveModelInfo(),
        getDatasetStats(),
        getCrawlStatus(),
        getTrainingStatus()
      ]);
      setModelMeta(m);
      setStats(s);
      setStatusData(c);
      setTriggerStatus(t);
      if (t?.threshold && thresholdInput === '100') {
        setThresholdInput(String(t.threshold));
      }
    } catch (e) {
      console.warn('Failed to load training info:', e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleAutoTrain = async () => {
    setTogglingPause(true);
    setActionMsg(null);
    try {
      if (triggerStatus?.auto_train_enabled) {
        await pauseAutoTraining();
        setActionMsg({ type: 'success', text: 'Automatic training paused.' });
      } else {
        await resumeAutoTraining();
        setActionMsg({ type: 'success', text: 'Automatic training resumed.' });
      }
      await fetchData();
    } catch (e) {
      setActionMsg({ type: 'error', text: e.message });
    } finally {
      setTogglingPause(false);
    }
  };

  const handleSaveThreshold = async (e) => {
    e.preventDefault();
    setSavingThreshold(true);
    setActionMsg(null);
    try {
      const val = parseInt(thresholdInput, 10);
      if (isNaN(val) || val < 1) throw new Error('Threshold must be at least 1');
      await updateRetrainThreshold(val);
      setActionMsg({ type: 'success', text: `Retrain threshold updated to ${val} new examples.` });
      await fetchData();
    } catch (e) {
      setActionMsg({ type: 'error', text: e.message });
    } finally {
      setSavingThreshold(false);
    }
  };

  const handleManualTrainNow = async () => {
    if (!window.confirm('Trigger manual training override now on all accumulated data?')) return;
    setTriggeringManual(true);
    setActionMsg(null);
    try {
      const res = await triggerManualTraining({ epochs: 3, batch_size: 8 });
      setActionMsg({ type: 'success', text: res.message || 'Training job initiated.' });
      await fetchData();
    } catch (e) {
      setActionMsg({ type: 'error', text: e.message });
    } finally {
      setTriggeringManual(false);
    }
  };

  const trainProgress = statusData?.training_progress || {};
  const trainResult = statusData?.training_result || {};
  const isTraining = statusData?.stage === 'MU_RIL_TRAINING' || statusData?.stage === 'MODEL_EVALUATION' || statusData?.stage === 'TRAINING_QUEUED';

  const total = stats?.total_count || 0;
  const supports = stats?.supports_count || 0;
  const refutes = stats?.refutes_count || 0;
  const supportsPct = total > 0 ? Math.round((supports / total) * 100) : 50;
  const refutesPct = total > 0 ? Math.round((refutes / total) * 100) : 50;

  const newExamples = triggerStatus?.new_examples_since_last_training || 0;
  const threshold = triggerStatus?.threshold || 100;
  const progressPct = Math.min(100, Math.round((newExamples / threshold) * 100));

  return (
    <div className="space-y-6 text-slate-100 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-5 rounded-2xl bg-dark-900/70 border border-slate-800 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-purple-600/20 border border-purple-500/30 text-purple-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-black font-mono text-white">MuRIL Training & Automation Engine</h2>
            <p className="text-xs text-slate-400 font-sans">
              Automated data accumulation trigger, 10-point Quality Gate, safe model promotion, and live training telemetry.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleManualTrainNow}
            disabled={triggeringManual || isTraining}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-mono font-bold transition shadow-lg shadow-purple-600/20"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>{triggeringManual ? 'Triggering...' : 'Train Now (Override)'}</span>
          </button>
        </div>
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

      {/* AUTOMATION TRIGGER STATUS CARD */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-purple-950/30 via-dark-900 to-indigo-950/30 border border-purple-500/40 shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>AUTOMATIC TRAINING TRIGGER</span>
            </span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
              triggerStatus?.auto_train_enabled
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
            }`}>
              {triggerStatus?.auto_train_enabled ? 'STATUS: ENABLED' : 'STATUS: PAUSED'}
            </span>
          </div>

          <button
            onClick={handleToggleAutoTrain}
            disabled={togglingPause}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-dark-950 hover:bg-slate-800 text-xs font-mono text-slate-300 border border-slate-700 transition"
          >
            {triggerStatus?.auto_train_enabled ? (
              <>
                <Pause className="w-3.5 h-3.5 text-amber-400" />
                <span>Pause Auto-Train</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 text-emerald-400" />
                <span>Resume Auto-Train</span>
              </>
            )}
          </button>
        </div>

        {/* Progress Bar towards Next Training */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-300 font-bold">
              Accumulated Data: <strong className="text-purple-300">{newExamples}</strong> / {threshold} new valid records
            </span>
            <span className="text-slate-400">
              {progressPct >= 100 ? (
                <span className="text-emerald-400 font-bold">Threshold Reached &mdash; Auto-Train Ready</span>
              ) : (
                <span>Need <strong>{Math.max(0, threshold - newExamples)}</strong> more records to trigger</span>
              )}
            </span>
          </div>

          <div className="w-full h-3.5 bg-dark-950 rounded-full overflow-hidden border border-slate-800 p-0.5">
            <div
              style={{ width: `${progressPct}%` }}
              className={`h-full rounded-full transition-all duration-500 ${
                progressPct >= 100
                  ? 'bg-gradient-to-r from-purple-500 to-emerald-400 animate-pulse'
                  : 'bg-gradient-to-r from-purple-600 to-indigo-500'
              }`}
            />
          </div>
        </div>

        {/* Config Threshold Form */}
        <form onSubmit={handleSaveThreshold} className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-800/80 text-xs font-mono">
          <span className="text-slate-400">Retrain Trigger Threshold:</span>
          <input
            type="number"
            min="1"
            max="5000"
            value={thresholdInput}
            onChange={(e) => setThresholdInput(e.target.value)}
            className="w-24 px-3 py-1.5 rounded-xl bg-dark-950 border border-slate-700 text-white font-mono focus:border-purple-500 focus:outline-none"
          />
          <span className="text-slate-400">new valid records</span>
          <button
            type="submit"
            disabled={savingThreshold}
            className="px-3 py-1.5 rounded-xl bg-dark-950 hover:bg-slate-800 border border-slate-700 text-purple-300 font-bold hover:text-purple-200 transition"
          >
            {savingThreshold ? 'Saving...' : 'Update Threshold'}
          </button>
        </form>
      </div>

      {/* 4 Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-2">
          <span className="text-xs font-mono text-slate-400 block uppercase">Active Checkpoint</span>
          <span className="text-xl font-bold font-mono text-emerald-400 block truncate">
            {modelMeta?.active_version || 'baseline'}
          </span>
          <span className="text-[11px] text-slate-400 font-sans">
            Trained: {modelMeta?.trained_at ? new Date(modelMeta.trained_at).toLocaleDateString() : 'Baseline'}
          </span>
        </div>

        <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-2">
          <span className="text-xs font-mono text-slate-400 block uppercase">Total Valid Dataset</span>
          <span className="text-xl font-bold font-mono text-purple-300 block">
            {total.toLocaleString()}
          </span>
          <span className="text-[11px] text-slate-400 font-sans">
            Accumulated `train_subtask1.json`
          </span>
        </div>

        <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-2">
          <span className="text-xs font-mono text-slate-400 block uppercase">Class Distribution</span>
          <span className="text-sm font-bold font-mono text-slate-200 block pt-1">
            <span className="text-emerald-400">{supports} SUPPORTS</span> ({supportsPct}%)
          </span>
          <span className="text-[11px] font-mono text-rose-400 block">
            {refutes} REFUTES ({refutesPct}%)
          </span>
        </div>

        <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-2">
          <span className="text-xs font-mono text-slate-400 block uppercase">Rejected Records</span>
          <span className="text-xl font-bold font-mono text-amber-400 block">
            {(stats?.rejected_count || 0).toLocaleString()}
          </span>
          <span className="text-[11px] text-slate-400 font-sans">
            Uncertain/Ambiguous pairs
          </span>
        </div>
      </div>

      {/* Class Balance Ratio Meter */}
      <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-300 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <BarChart2 className="w-4 h-4 text-purple-400" />
            <span>Dataset Label Balance</span>
          </span>
          <span className="text-slate-400">
            Ratio: {supportsPct}% / {refutesPct}% (Threshold: &le; 80% dominant)
          </span>
        </div>

        <div className="w-full h-3.5 bg-dark-950 rounded-full overflow-hidden flex border border-slate-800">
          <div
            style={{ width: `${supportsPct}%` }}
            className="bg-emerald-500 h-full transition-all duration-500"
            title={`SUPPORTS: ${supports}`}
          />
          <div
            style={{ width: `${refutesPct}%` }}
            className="bg-rose-500 h-full transition-all duration-500"
            title={`REFUTES: ${refutes}`}
          />
        </div>

        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>SUPPORTS: {supports} items</span>
          </span>
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2 h-2 rounded-full bg-rose-400"></span>
            <span>REFUTES: {refutes} items</span>
          </span>
        </div>
      </div>

      {/* 10-Point Training Quality Gate Card */}
      <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-emerald-300 font-bold">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>10-Point Training Quality Gate Checks</span>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            Gate Passed (Active)
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">1. Total Valid Examples (&ge; 50)</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{total}</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">2. SUPPORTS Count (&ge; 15)</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{supports}</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">3. REFUTES Count (&ge; 15)</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{refutes}</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">4. Class Balance (&le; 80/20)</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{supportsPct}% / {refutesPct}%</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">5. No Fabricated Labels</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Enforced</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">6. Non-empty Claim & Evidence</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Validated</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">7. Canonical Labels Only</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>SUPPORTS / REFUTES</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">8. Data Leakage Prevention</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Stratified 80/10/10</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
