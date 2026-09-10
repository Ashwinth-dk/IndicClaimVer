import React, { useState, useEffect } from 'react';
import { Terminal, Clock, RotateCw, CheckCircle2, AlertTriangle, XCircle, Search } from 'lucide-react';
import { getCrawlStatus, getCrawlHistory } from '../services/api';

export default function DeveloperLogs() {
  const [liveStatus, setLiveStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);

  const fetchLogs = async () => {
    try {
      const [st, hist] = await Promise.all([
        getCrawlStatus(),
        getCrawlHistory()
      ]);
      setLiveStatus(st);
      setHistory(hist || []);
    } catch (e) {
      console.warn('Failed to fetch logs:', e);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, []);

  const liveLogs = liveStatus?.crawl_status?.logs || [];
  const filteredLiveLogs = liveLogs.filter((l) =>
    (l.message || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 text-slate-100 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between p-5 rounded-2xl bg-dark-900/70 border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
            <Terminal className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-black font-mono text-white">System & Pipeline Execution Logs</h2>
            <p className="text-xs text-slate-400 font-sans">
              Stream live crawler events, Quality Gate verification, and historical batch execution records.
            </p>
          </div>
        </div>

        <button
          onClick={fetchLogs}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-dark-950 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-mono transition-colors"
        >
          <RotateCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Live Stream Terminal */}
      <div className="p-5 rounded-2xl bg-black/90 border border-slate-800 space-y-3 font-mono text-xs shadow-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800 text-slate-400">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-200 font-bold uppercase tracking-wider">Live Execution Stream</span>
            <span className="text-[10px] text-slate-400">({filteredLiveLogs.length} events)</span>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter logs..."
              className="pl-8 pr-3 py-1 rounded-lg bg-dark-950 border border-slate-800 text-[11px] text-slate-200"
            />
          </div>
        </div>

        <div className="max-h-80 overflow-y-auto space-y-1 pr-2 font-mono text-[11px]">
          {filteredLiveLogs.length > 0 ? (
            filteredLiveLogs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2 py-0.5 leading-relaxed">
                <span className="text-slate-400 flex-shrink-0">[{log.timestamp}]</span>
                <span
                  className={
                    log.level === 'SUCCESS'
                      ? 'text-emerald-400'
                      : log.level === 'WARN'
                      ? 'text-amber-400'
                      : log.level === 'ERROR'
                      ? 'text-rose-400'
                      : 'text-slate-300'
                  }
                >
                  {log.message}
                </span>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-slate-400">
              {liveStatus?.is_running
                ? 'Waiting for next crawler log event...'
                : 'Pipeline is idle. Click START PIPELINE to initiate new run.'}
            </div>
          )}
        </div>
      </div>

      {/* Historical Runs */}
      {history.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-400" />
            <span>Past Execution History ({history.length} runs)</span>
          </h3>

          <div className="space-y-2">
            {history.map((run, i) => (
              <div
                key={i}
                className="p-4 rounded-xl bg-dark-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white">Job ID: {run.job_id}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        run.stage === 'COMPLETED'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : run.stage === 'FAILED'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {run.stage}
                    </span>
                  </div>
                  <p className="text-slate-400 font-sans text-xs">{run.stage_details}</p>
                </div>

                <div className="text-right text-[11px] text-slate-400 font-sans">
                  {run.started_at && <span>{new Date(run.started_at).toLocaleString()}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
