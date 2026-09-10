import React, { useState, useEffect } from 'react';
import { 
  Database, 
  FileText, 
  ShieldAlert, 
  Search, 
  Filter, 
  CheckCircle2, 
  XCircle, 
  RotateCw, 
  Download,
  Trash2,
  Check,
  Globe,
  Layers
} from 'lucide-react';
import { 
  getDatasetItems, 
  getEvidenceItems, 
  getReviewItems, 
  getSources, 
  handleReviewAction, 
  toggleSource,
  getDatasetStats 
} from '../services/api';

export default function DataExplorerModal() {
  const [subTab, setSubTab] = useState('dataset'); // 'dataset' | 'evidence' | 'rejected' | 'sources'
  const [search, setSearch] = useState('');
  const [labelFilter, setLabelFilter] = useState('');
  const [items, setItems] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchStats = async () => {
    try {
      const s = await getDatasetStats();
      setStats(s);
    } catch (e) {
      console.warn('Stats load error', e);
    }
  };

  const fetchItems = async () => {
    setLoading(true);
    try {
      if (subTab === 'dataset') {
        const res = await getDatasetItems({ search, label: labelFilter, limit: 50 });
        setItems(res.items || []);
        setTotalCount(res.total || 0);
      } else if (subTab === 'evidence') {
        const res = await getEvidenceItems({ search, limit: 50 });
        setItems(res.items || []);
        setTotalCount(res.total || 0);
      } else if (subTab === 'rejected') {
        const res = await getReviewItems({ search, limit: 50 });
        setItems(res.items || []);
        setTotalCount(res.total || 0);
      } else if (subTab === 'sources') {
        const res = await getSources();
        setItems(res.sources || []);
        setTotalCount(res.total || 0);
      }
    } catch (e) {
      console.warn('Items fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    fetchItems();
  }, [subTab, search, labelFilter]);

  const handleApproveRejected = async (itemId) => {
    try {
      await handleReviewAction({ action: 'approve', item_id: itemId });
      await fetchItems();
      await fetchStats();
    } catch (err) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleDeleteRejected = async (itemId) => {
    try {
      await handleReviewAction({ action: 'delete', item_id: itemId });
      await fetchItems();
      await fetchStats();
    } catch (err) {
      alert(`Delete error: ${err.message}`);
    }
  };

  const handleToggleSource = async (srcId, currentEnabled) => {
    try {
      await toggleSource(srcId, !currentEnabled);
      await fetchItems();
    } catch (err) {
      alert(`Toggle error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-5 max-w-7xl mx-auto p-4 sm:p-6 text-slate-100 font-sans">
      {/* Top Header & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-5 rounded-2xl bg-dark-900/80 border border-slate-800">
        <div>
          <h2 className="text-xl font-bold font-mono text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-indigo-400" />
            Dataset & Evidence Repository
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Explore authoritative training datasets, canonical evidence pool, rejected items, and registered sources
          </p>
        </div>

        {stats && (
          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="px-3 py-1.5 rounded-lg bg-dark-950 border border-slate-800">
              <span className="text-slate-400">Dataset: </span>
              <span className="text-teal-300 font-bold">{stats.total_count}</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-dark-950 border border-slate-800">
              <span className="text-slate-400">Evidence: </span>
              <span className="text-blue-300 font-bold">{stats.evidence_count}</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-dark-950 border border-slate-800">
              <span className="text-slate-400">Rejected: </span>
              <span className="text-amber-300 font-bold">{stats.rejected_count}</span>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto font-mono text-xs">
        <button
          onClick={() => { setSubTab('dataset'); setSearch(''); }}
          className={`px-4 py-2 rounded-xl flex items-center gap-2 font-medium transition-all ${
            subTab === 'dataset'
              ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40'
              : 'text-slate-400 hover:text-slate-200 hover:bg-dark-900'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Training Dataset ({stats?.total_count ?? 0})</span>
        </button>

        <button
          onClick={() => { setSubTab('evidence'); setSearch(''); }}
          className={`px-4 py-2 rounded-xl flex items-center gap-2 font-medium transition-all ${
            subTab === 'evidence'
              ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40'
              : 'text-slate-400 hover:text-slate-200 hover:bg-dark-900'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>Evidence Pool ({stats?.evidence_count ?? 0})</span>
        </button>

        <button
          onClick={() => { setSubTab('rejected'); setSearch(''); }}
          className={`px-4 py-2 rounded-xl flex items-center gap-2 font-medium transition-all ${
            subTab === 'rejected'
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
              : 'text-slate-400 hover:text-slate-200 hover:bg-dark-900'
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Rejected Review Queue ({stats?.rejected_count ?? 0})</span>
        </button>

        <button
          onClick={() => { setSubTab('sources'); setSearch(''); }}
          className={`px-4 py-2 rounded-xl flex items-center gap-2 font-medium transition-all ${
            subTab === 'sources'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
              : 'text-slate-400 hover:text-slate-200 hover:bg-dark-900'
          }`}
        >
          <Globe className="w-3.5 h-3.5" />
          <span>Source Registry ({stats?.sources_count ?? 0})</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Search ${subTab}...`}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-dark-900 border border-slate-800 text-xs text-slate-200 focus:border-blue-500 font-sans"
          />
        </div>

        {subTab === 'dataset' && (
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Label:</span>
            <button
              onClick={() => setLabelFilter('')}
              className={`px-2.5 py-1 rounded-lg ${labelFilter === '' ? 'bg-blue-600 text-white' : 'bg-dark-900 text-slate-400'}`}
            >
              All
            </button>
            <button
              onClick={() => setLabelFilter('SUPPORTS')}
              className={`px-2.5 py-1 rounded-lg ${labelFilter === 'SUPPORTS' ? 'bg-emerald-600 text-white' : 'bg-dark-900 text-slate-400'}`}
            >
              SUPPORTS
            </button>
            <button
              onClick={() => setLabelFilter('REFUTES')}
              className={`px-2.5 py-1 rounded-lg ${labelFilter === 'REFUTES' ? 'bg-rose-600 text-white' : 'bg-dark-900 text-slate-400'}`}
            >
              REFUTES
            </button>
          </div>
        )}

        <div className="flex items-center gap-2">
          <button
            onClick={fetchItems}
            className="p-2 rounded-xl bg-dark-900 hover:bg-slate-800 border border-slate-800 text-slate-400"
            title="Refresh"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Content Renderers */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 font-mono text-xs">Loading {subTab} items...</div>
      ) : items.length === 0 ? (
        <div className="p-12 text-center text-slate-400 font-sans text-xs bg-dark-900/40 rounded-2xl border border-slate-800">
          No records found for current criteria.
        </div>
      ) : (
        <div className="space-y-3">
          {/* DATASET TABLE */}
          {subTab === 'dataset' && (
            <div className="space-y-2.5">
              {items.map((item, idx) => {
                const isSup = item.Label === 'SUPPORTS';
                return (
                  <div
                    key={item.ID || idx}
                    className="p-4 rounded-xl bg-dark-900/70 border border-slate-800/80 space-y-2 hover:border-slate-700 transition-all text-xs font-sans"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-400">{item.ID}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          isSup ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        }`}>
                          {item.Label}
                        </span>
                      </div>
                    </div>
                    <div>
                      <strong className="text-slate-300 block font-mono text-[11px] mb-0.5">CLAIM:</strong>
                      <p className="text-slate-200 font-medium">{item.Text}</p>
                    </div>
                    <div>
                      <strong className="text-slate-400 block font-mono text-[11px] mb-0.5">EVIDENCE:</strong>
                      <p className="text-slate-400 text-[11px] leading-relaxed">{item.Evidence}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* EVIDENCE POOL */}
          {subTab === 'evidence' && (
            <div className="space-y-2.5">
              {items.map((item, idx) => (
                <div
                  key={item.ID || idx}
                  className="p-4 rounded-xl bg-dark-900/70 border border-slate-800/80 space-y-1.5 text-xs font-sans"
                >
                  <div className="flex items-center justify-between font-mono text-[11px] text-blue-400 font-bold">
                    <span>{item.ID}</span>
                  </div>
                  <p className="text-slate-300 leading-relaxed text-xs">{item.Evidence}</p>
                </div>
              ))}
            </div>
          )}

          {/* REJECTED REVIEW QUEUE */}
          {subTab === 'rejected' && (
            <div className="space-y-2.5">
              {items.map((item, idx) => (
                <div
                  key={item.ID || idx}
                  className="p-4 rounded-xl bg-dark-900/70 border border-slate-800/80 space-y-2 text-xs font-sans"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-amber-400">{item.ID}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/15 text-amber-300 border border-amber-500/30">
                        Reason: {item.Reason}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleApproveRejected(item.ID)}
                        className="px-2.5 py-1 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-[11px] font-mono flex items-center gap-1"
                        title="Approve and move to train_subtask1.json"
                      >
                        <Check className="w-3 h-3" />
                        <span>Approve</span>
                      </button>
                      <button
                        onClick={() => handleDeleteRejected(item.ID)}
                        className="p-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30"
                        title="Permanently Delete"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  <div>
                    <strong className="text-slate-300 block font-mono text-[11px] mb-0.5">CANDIDATE CLAIM:</strong>
                    <p className="text-slate-200">{item.Text || '(Empty Claim)'}</p>
                  </div>

                  <div>
                    <strong className="text-slate-400 block font-mono text-[11px] mb-0.5">CANDIDATE EVIDENCE:</strong>
                    <p className="text-slate-400 text-[11px]">{item.Evidence || '(Empty Evidence)'}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* SOURCE REGISTRY */}
          {subTab === 'sources' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-sans">
              {items.map((src, idx) => (
                <div
                  key={src.source_id || idx}
                  className="p-4 rounded-xl bg-dark-900/70 border border-slate-800/80 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="font-mono font-bold text-slate-200">{src.source_name}</div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-slate-300">
                      {src.source_type}
                    </span>
                  </div>

                  <div className="text-[11px] text-blue-400 font-mono truncate">{src.base_url}</div>
                  <p className="text-[11px] text-slate-400">{src.description}</p>

                  <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono">
                    <span className="text-slate-400">Reliability: {(src.reliability_score * 100).toFixed(0)}%</span>
                    <button
                      onClick={() => handleToggleSource(src.source_id, src.enabled)}
                      className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                        src.enabled
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {src.enabled ? 'Enabled' : 'Disabled'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
