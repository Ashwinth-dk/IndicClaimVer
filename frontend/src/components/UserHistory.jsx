import React, { useState } from 'react';
import { History, Search, Trash2, CheckCircle2, XCircle, AlertCircle, ArrowRight } from 'lucide-react';

export default function UserHistory({ history = [], onSelectHistoryItem, onClearHistory, onDeleteHistoryItem }) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredHistory = history.filter((item) =>
    (item.claim || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-5 rounded-2xl bg-dark-900/70 border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-blue-600/15 border border-blue-500/20 text-blue-400">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white font-sans">Verification History</h2>
            <p className="text-xs text-slate-400 font-sans">
              Your previous fact-checking assessments ({history.length} saved)
            </p>
          </div>
        </div>

        {history.length > 0 && (
          <button
            onClick={onClearHistory}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-mono text-rose-400 hover:text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 transition-all self-start sm:self-auto"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Search Input */}
      {history.length > 0 && (
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search past verified claims..."
            className="w-full pl-10 pr-4 py-3 rounded-xl bg-dark-950 border border-slate-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm font-sans text-slate-200"
          />
        </div>
      )}

      {/* History Items List */}
      <div className="space-y-3">
        {filteredHistory.length > 0 ? (
          filteredHistory.map((item, idx) => {
            const isSupports = item.verdict === 'SUPPORTS';
            const isRefutes = item.verdict === 'REFUTES';

            return (
              <div
                key={item.id || idx}
                onClick={() => onSelectHistoryItem && onSelectHistoryItem(item)}
                className="p-4 sm:p-5 rounded-2xl bg-dark-900/60 hover:bg-dark-900 border border-slate-800/80 hover:border-slate-700 transition-all cursor-pointer group flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2.5 py-0.5 rounded-lg text-[10px] font-mono font-bold flex items-center gap-1 ${
                        isSupports
                          ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                          : isRefutes
                          ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                      }`}
                    >
                      {isSupports ? (
                        <CheckCircle2 className="w-3 h-3" />
                      ) : isRefutes ? (
                        <XCircle className="w-3 h-3" />
                      ) : (
                        <AlertCircle className="w-3 h-3" />
                      )}
                      <span>{item.verdict}</span>
                    </span>

                    {item.confidence && (
                      <span className="text-[11px] font-mono text-slate-400">
                        {Math.round(item.confidence * 100)}% reliability
                      </span>
                    )}

                    <span className="text-[11px] text-slate-400 font-sans ml-auto sm:ml-0">
                      {item.timestamp || item.date || 'Recent'}
                    </span>
                  </div>

                  <p className="text-xs sm:text-sm font-sans text-slate-200 group-hover:text-blue-300 transition-colors line-clamp-2">
                    "{item.claim}"
                  </p>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <span className="text-xs text-blue-400 font-sans group-hover:translate-x-1 transition-transform flex items-center gap-1">
                    <span>View Result</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            );
          })
        ) : (
          <div className="p-8 rounded-2xl bg-dark-900/40 border border-slate-800 text-center space-y-2">
            <p className="text-sm font-sans text-slate-400">No previous verifications found.</p>
            <p className="text-xs text-slate-400 font-sans">
              Enter a claim on the Fact Verifier tab to begin.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
