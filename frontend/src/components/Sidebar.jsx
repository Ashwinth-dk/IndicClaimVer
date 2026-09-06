import React from 'react';
import { 
  ShieldCheck, 
  PlusCircle, 
  History, 
  Trash2, 
  Database, 
  Cpu, 
  Search, 
  Filter, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle,
  X,
  ExternalLink,
  Info,
  Layers
} from 'lucide-react';

export default function Sidebar({
  isOpen = true,
  onClose,
  onNewVerification,
  history = [],
  onSelectHistoryItem,
  onClearHistory,
  onDeleteHistoryItem,
  healthStatus = {},
}) {
  const isApiConnected = healthStatus.connected;
  const evidenceCount = healthStatus.evidence_count || 0;

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 lg:hidden transition-opacity"
        />
      )}

      {/* Main Sidebar Panel */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-72 flex flex-col justify-between bg-dark-900 border-r border-slate-800/80 transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Top Header & Actions */}
        <div className="p-4 space-y-4 flex-shrink-0">
          {/* Brand Logo & Title */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 p-0.5 shadow-glow-blue flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-base font-bold font-mono tracking-tight text-white flex items-center gap-1.5">
                  IndicClaimVer
                </h2>
                <p className="text-[11px] text-slate-400 font-sans">
                  AI-Powered Evidence Verification
                </p>
              </div>
            </div>

            {/* Mobile close button */}
            <button
              type="button"
              onClick={onClose}
              className="lg:hidden p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* New Verification Action */}
          <button
            type="button"
            onClick={() => {
              onNewVerification();
              if (window.innerWidth < 1024) onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 hover:border-blue-500/50 text-xs font-mono font-semibold transition-all shadow-sm active:scale-98"
          >
            <PlusCircle className="w-4 h-4 text-blue-400" />
            <span>New Verification</span>
          </button>
        </div>

        {/* Scrollable Middle: History & Pipeline Info */}
        <div className="flex-1 overflow-y-auto px-4 space-y-5 text-xs">
          {/* Verification History Section */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-slate-400 font-mono text-[11px] uppercase tracking-wider px-1">
              <span className="flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-slate-400" />
                History ({history.length})
              </span>
              {history.length > 0 && (
                <button
                  type="button"
                  onClick={onClearHistory}
                  className="text-slate-400 hover:text-red-400 transition-colors p-0.5"
                  title="Clear all verification history"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {history.length === 0 ? (
              <div className="p-3 rounded-lg bg-dark-950/60 border border-slate-800/60 text-center text-slate-400 font-sans text-xs">
                No past verifications in current session.
              </div>
            ) : (
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {history.map((item, idx) => {
                  const isSup = item.verdict === 'SUPPORTS';
                  const isRef = item.verdict === 'REFUTES';
                  return (
                    <div
                      key={item.id || idx}
                      onClick={() => {
                        onSelectHistoryItem(item);
                        if (window.innerWidth < 1024) onClose();
                      }}
                      className="group flex items-start justify-between p-2.5 rounded-lg bg-dark-950/70 hover:bg-dark-850 border border-slate-800/80 hover:border-blue-500/30 cursor-pointer transition-all"
                    >
                      <div className="space-y-1 flex-1 min-w-0 pr-2">
                        <div className="flex items-center gap-1.5">
                          {isSup ? (
                            <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                          ) : isRef ? (
                            <XCircle className="w-3 h-3 text-rose-400 flex-shrink-0" />
                          ) : (
                            <AlertTriangle className="w-3 h-3 text-amber-400 flex-shrink-0" />
                          )}
                          <span className="font-mono font-medium text-[11px] text-slate-200">
                            {item.verdict}
                          </span>
                          <span className="font-mono text-[10px] text-slate-400">
                            ({Math.round((item.confidence || 0) * 100)}%)
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 truncate font-sans">
                          {item.claim}
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteHistoryItem(item.id || idx);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-400 p-1 transition-opacity"
                        title="Delete from history"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Compact Pipeline Architecture Section */}
          <div className="p-3.5 rounded-xl bg-dark-950/80 border border-slate-800/80 space-y-2.5">
            <div className="flex items-center gap-1.5 text-slate-300 font-mono text-[11px] uppercase tracking-wider font-semibold">
              <Info className="w-3.5 h-3.5 text-blue-400" />
              <span>Pipeline Architecture</span>
            </div>

            <div className="space-y-2 font-mono text-[11px] text-slate-400">
              <div className="flex items-center gap-2">
                <Search className="w-3 h-3 text-blue-400 flex-shrink-0" />
                <span>1. Claim Preprocessing</span>
              </div>
              <div className="flex items-center gap-2">
                <Database className="w-3 h-3 text-indigo-400 flex-shrink-0" />
                <span>2. Vector Retrieval (Top-20)</span>
              </div>
              <div className="flex items-center gap-2">
                <Filter className="w-3 h-3 text-teal-400 flex-shrink-0" />
                <span>3. Ranking & Top-5 Selection</span>
              </div>
              <div className="flex items-center gap-2">
                <Cpu className="w-3 h-3 text-purple-400 flex-shrink-0" />
                <span>4. MuRIL Sequence Inference</span>
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                <span>5. Relevance-Weighted Verdict</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom System Status Section */}
        <div className="p-4 border-t border-slate-800/80 bg-dark-950/60 flex-shrink-0 space-y-2 text-xs font-mono">
          <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
            System Status
          </div>

          <div className="space-y-1.5 text-[11px]">
            <div className="flex items-center justify-between text-slate-300">
              <span className="text-slate-400">Model:</span>
              <span className="font-semibold text-blue-300">MuRIL Base</span>
            </div>

            <div className="flex items-center justify-between text-slate-300">
              <span className="text-slate-400">Evidence Pool:</span>
              <span className="text-slate-200">
                {evidenceCount > 0 ? `${evidenceCount.toLocaleString()} Loaded` : '50k+ Ready'}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400">Backend API:</span>
              <span className="flex items-center gap-1.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    isApiConnected ? 'bg-emerald-400 shadow-glow-green' : 'bg-rose-500'
                  }`}
                />
                <span className={isApiConnected ? 'text-emerald-400 font-semibold' : 'text-rose-400'}>
                  {isApiConnected ? 'Connected' : 'Disconnected'}
                </span>
              </span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
