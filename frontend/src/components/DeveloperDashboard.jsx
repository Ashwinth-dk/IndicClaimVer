import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Cpu, 
  Database, 
  Layers, 
  TrendingUp, 
  ShieldCheck, 
  Globe, 
  Terminal, 
  RotateCw,
  Sparkles,
  ArrowUpRight,
  Clock
} from 'lucide-react';
import { getHealthStatus, getActiveModelInfo, getDatasetStats, getCrawlStatus } from '../services/api';

export default function DeveloperDashboard({ onNavigate }) {
  const [health, setHealth] = useState(null);
  const [modelMeta, setModelMeta] = useState(null);
  const [stats, setStats] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [h, m, s, p] = await Promise.all([
        getHealthStatus(),
        getActiveModelInfo(),
        getDatasetStats(),
        getCrawlStatus()
      ]);
      setHealth(h);
      setModelMeta(m);
      setStats(s);
      setPipelineStatus(p);
    } catch (e) {
      console.warn('Failed to load dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 6000);
    return () => clearInterval(interval);
  }, []);

  const isRunning = pipelineStatus?.is_running;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-dark-900 to-blue-950/40 border border-indigo-900/40 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
              <Activity className="w-5 h-5" />
            </div>
            <h1 className="text-xl sm:text-2xl font-black font-mono tracking-tight text-white">
              Developer & Admin Dashboard
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 font-sans">
            Real-time telemetry, automated crawl-to-train pipeline control, and model lifecycle management.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <button
            onClick={fetchDashboardData}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-dark-950 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-mono transition-colors"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* System Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Backend API Status */}
        <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>FastAPI Server</span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
          </div>
          <div className="space-y-1">
            <div className="text-xl font-bold font-mono text-white">
              {health?.connected ? 'CONNECTED' : 'DISCONNECTED'}
            </div>
            <p className="text-[11px] text-slate-400 font-sans">
              Device: <span className="font-mono text-blue-400">{health?.device?.toUpperCase() || 'CPU'}</span>
            </p>
          </div>
        </div>

        {/* Active Model Checkpoint */}
        <div 
          onClick={() => onNavigate && onNavigate('models')}
          className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-3 hover:border-slate-700 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Active MuRIL Model</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="space-y-1">
            <div className="text-xl font-bold font-mono text-emerald-300 truncate">
              {modelMeta?.active_version || 'baseline'}
            </div>
            <p className="text-[11px] text-slate-400 font-sans flex items-center justify-between">
              <span>Hot-Reload Active</span>
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-emerald-400 transition-colors" />
            </p>
          </div>
        </div>

        {/* Evidence Pool */}
        <div 
          onClick={() => onNavigate && onNavigate('dataset')}
          className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-3 hover:border-slate-700 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Evidence Pool</span>
            <Layers className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="space-y-1">
            <div className="text-xl font-bold font-mono text-indigo-300">
              {stats?.evidence_count?.toLocaleString() || '13,613'}
            </div>
            <p className="text-[11px] text-slate-400 font-sans flex items-center justify-between">
              <span>Indexed Passages</span>
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-400 transition-colors" />
            </p>
          </div>
        </div>

        {/* Training Dataset */}
        <div 
          onClick={() => onNavigate && onNavigate('training')}
          className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-3 hover:border-slate-700 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Training Dataset</span>
            <Database className="w-4 h-4 text-purple-400" />
          </div>
          <div className="space-y-1">
            <div className="text-xl font-bold font-mono text-purple-300">
              {stats?.total_count?.toLocaleString() || '2,474'}
            </div>
            <p className="text-[11px] text-slate-400 font-sans flex items-center justify-between">
              <span>S:{stats?.supports_count || 0} / R:{stats?.refutes_count || 0}</span>
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-purple-400 transition-colors" />
            </p>
          </div>
        </div>
      </div>

      {/* Live Pipeline State Widget */}
      <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-slate-200 font-bold">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span>Automated Crawl & Fine-Tuning Status</span>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-slate-400">Stage:</span>
            <span className={`px-2.5 py-0.5 rounded-full font-bold ${
              isRunning 
                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40 animate-pulse'
                : pipelineStatus?.stage === 'COMPLETED'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'bg-slate-800 text-slate-300'
            }`}>
              {pipelineStatus?.stage || 'IDLE'}
            </span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-dark-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
          <div className="space-y-1">
            <div className="text-slate-300 font-sans">
              <strong className="text-blue-400 font-mono">Details:</strong> {pipelineStatus?.stage_details || 'Pipeline is idle and ready to crawl.'}
            </div>
            {pipelineStatus?.started_at && (
              <div className="text-[11px] text-slate-400 font-sans flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                <span>Job Started: {new Date(pipelineStatus.started_at).toLocaleTimeString()}</span>
              </div>
            )}
          </div>

          <button
            onClick={() => onNavigate && onNavigate('pipeline')}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 text-xs font-mono font-bold transition-all self-start sm:self-auto"
          >
            <span>Open Pipeline Console</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Quick Access Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div 
          onClick={() => onNavigate && onNavigate('pipeline')}
          className="p-5 rounded-2xl bg-dark-900/60 hover:bg-dark-900/90 border border-slate-800/80 hover:border-blue-500/40 transition-all cursor-pointer group space-y-2"
        >
          <Globe className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-bold font-mono text-white group-hover:text-blue-300 transition-colors">
            1. Web Crawler & Auto-Train
          </h3>
          <p className="text-xs text-slate-400 font-sans">
            Initiate multi-source crawl and let the backend automatically validate and fine-tune MuRIL.
          </p>
        </div>

        <div 
          onClick={() => onNavigate && onNavigate('training')}
          className="p-5 rounded-2xl bg-dark-900/60 hover:bg-dark-900/90 border border-slate-800/80 hover:border-purple-500/40 transition-all cursor-pointer group space-y-2"
        >
          <Cpu className="w-5 h-5 text-purple-400" />
          <h3 className="text-sm font-bold font-mono text-white group-hover:text-purple-300 transition-colors">
            2. Training & Quality Gate
          </h3>
          <p className="text-xs text-slate-400 font-sans">
            Inspect the 10-point Quality Gate, class balance, split partitions, and validation metrics.
          </p>
        </div>

        <div 
          onClick={() => onNavigate && onNavigate('dataset')}
          className="p-5 rounded-2xl bg-dark-900/60 hover:bg-dark-900/90 border border-slate-800/80 hover:border-emerald-500/40 transition-all cursor-pointer group space-y-2"
        >
          <Database className="w-5 h-5 text-emerald-400" />
          <h3 className="text-sm font-bold font-mono text-white group-hover:text-emerald-300 transition-colors">
            3. Dataset & Review Queue
          </h3>
          <p className="text-xs text-slate-400 font-sans">
            Browse canonical training items (`train_subtask1.json`) and moderate rejected candidates.
          </p>
        </div>
      </div>
    </div>
  );
}
