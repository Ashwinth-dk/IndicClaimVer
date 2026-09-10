import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Layers, 
  AlertTriangle, 
  Search, 
  Filter, 
  Download, 
  Check, 
  Trash2, 
  Edit3, 
  CheckCircle2, 
  RotateCw, 
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Globe
} from 'lucide-react';
import { 
  getDatasetItems, 
  getEvidenceItems, 
  getReviewItems, 
  getSources, 
  handleReviewAction, 
  getDatasetStats 
} from '../services/api';

export default function DeveloperDataset() {
  const [activeTab, setActiveTab] = useState('training'); // 'training' | 'evidence' | 'rejected' | 'sources'
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(25);
  const [search, setSearch] = useState('');
  const [labelFilter, setLabelFilter] = useState('');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState('');

  const fetchStats = async () => {
    try {
      const data = await getDatasetStats();
      setStats(data);
    } catch (e) {
      console.warn('Failed to fetch dataset stats:', e);
    }
  };

  const fetchTabItems = async () => {
    setLoading(true);
    try {
      if (activeTab === 'training') {
        const res = await getDatasetItems({ search, label: labelFilter, offset, limit });
        setItems(res.items || []);
        setTotal(res.total || 0);
      } else if (activeTab === 'evidence') {
        const res = await getEvidenceItems({ search, offset, limit });
        setItems(res.items || []);
        setTotal(res.total || 0);
      } else if (activeTab === 'rejected') {
        const res = await getReviewItems({ search, offset, limit });
        setItems(res.items || []);
        setTotal(res.total || 0);
      } else if (activeTab === 'sources') {
        const res = await getSources();
        setItems(res.sources || []);
        setTotal(res.total || 0);
      }
    } catch (e) {
      console.warn('Failed to load tab items:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    setOffset(0);
    fetchTabItems();
  }, [activeTab, search, labelFilter]);

  useEffect(() => {
    fetchTabItems();
  }, [offset, limit]);

  const handleApprove = async (itemId, label) => {
    try {
      await handleReviewAction({ item_id: itemId, action: 'approve', label });
      setActionMsg(`Approved item ${itemId} as ${label}`);
      fetchTabItems();
      fetchStats();
      setTimeout(() => setActionMsg(''), 3000);
    } catch (e) {
      alert(`Approval error: ${e.message}`);
    }
  };

  const handleDelete = async (itemId) => {
    try {
      await handleReviewAction({ item_id: itemId, action: 'delete' });
      setActionMsg(`Deleted review item ${itemId}`);
      fetchTabItems();
      fetchStats();
      setTimeout(() => setActionMsg(''), 3000);
    } catch (e) {
      alert(`Delete error: ${e.message}`);
    }
  };

  return (
    <div className="space-y-6 text-slate-100 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-dark-900/70 border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-black font-mono text-white">Data Repository & Quality Manager</h2>
            <p className="text-xs text-slate-400 font-sans">
              Inspect canonical datasets, deduplicated evidence pool, and moderate ambiguous review records.
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1.5 p-1 bg-dark-950 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('training')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
              activeTab === 'training'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Training Dataset ({stats?.total_count || 0})
          </button>

          <button
            onClick={() => setActiveTab('evidence')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
              activeTab === 'evidence'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Evidence Pool ({stats?.evidence_count || 0})
          </button>

          <button
            onClick={() => setActiveTab('rejected')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
              activeTab === 'rejected'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Rejected Records ({stats?.rejected_count || 0})
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-2xl bg-dark-900/60 border border-slate-800">
        <div className="relative flex-1 w-full sm:w-auto">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Search ${activeTab}...`}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-dark-950 border border-slate-800 text-xs font-mono text-slate-200"
          />
        </div>

        {activeTab === 'training' && (
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={labelFilter}
              onChange={(e) => setLabelFilter(e.target.value)}
              className="px-3 py-2 rounded-xl bg-dark-950 border border-slate-800 text-xs font-mono text-slate-200"
            >
              <option value="">All Labels</option>
              <option value="SUPPORTS">SUPPORTS</option>
              <option value="REFUTES">REFUTES</option>
            </select>
          </div>
        )}

        <button
          onClick={fetchTabItems}
          className="p-2.5 rounded-xl bg-dark-950 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-colors"
          title="Refresh table"
        >
          <RotateCw className="w-4 h-4" />
        </button>
      </div>

      {/* Table Content */}
      <div className="p-4 rounded-2xl bg-dark-900/60 border border-slate-800 overflow-x-auto">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs font-mono">
            Loading data records...
          </div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs font-mono">
            No records match the current filter.
          </div>
        ) : activeTab === 'training' ? (
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 pb-2">
                <th className="p-3">ID</th>
                <th className="p-3">Claim (Text)</th>
                <th className="p-3">Evidence Passage</th>
                <th className="p-3">Label</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {items.map((item, idx) => (
                <tr key={idx} className="hover:bg-dark-950/60 transition-colors">
                  <td className="p-3 text-slate-400 font-bold">{item.ID}</td>
                  <td className="p-3 text-slate-200 max-w-xs">{item.Text}</td>
                  <td className="p-3 text-slate-300 max-w-md font-sans text-xs">{item.Evidence}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      item.Label === 'SUPPORTS'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    }`}>
                      {item.Label}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : activeTab === 'evidence' ? (
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 pb-2">
                <th className="p-3 w-28">ID</th>
                <th className="p-3">Evidence Text</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {items.map((item, idx) => (
                <tr key={idx} className="hover:bg-dark-950/60 transition-colors">
                  <td className="p-3 text-indigo-400 font-bold">{item.ID}</td>
                  <td className="p-3 text-slate-300 font-sans text-xs">{item.Evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 pb-2">
                <th className="p-3">ID</th>
                <th className="p-3">Claim</th>
                <th className="p-3">Evidence</th>
                <th className="p-3">Rejection Reason</th>
                <th className="p-3 text-right">Moderation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {items.map((item, idx) => (
                <tr key={idx} className="hover:bg-dark-950/60 transition-colors">
                  <td className="p-3 text-amber-400 font-bold">{item.ID}</td>
                  <td className="p-3 text-slate-200 max-w-xs">{item.Text}</td>
                  <td className="p-3 text-slate-300 max-w-xs font-sans text-xs">{item.Evidence}</td>
                  <td className="p-3 text-amber-300/90 max-w-xs">{item.Reason}</td>
                  <td className="p-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => handleApprove(item.ID, 'SUPPORTS')}
                        className="px-2 py-1 rounded bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600/30 text-[10px] font-bold"
                        title="Approve as SUPPORTS"
                      >
                        +S
                      </button>
                      <button
                        onClick={() => handleApprove(item.ID, 'REFUTES')}
                        className="px-2 py-1 rounded bg-rose-600/20 text-rose-300 hover:bg-rose-600/30 text-[10px] font-bold"
                        title="Approve as REFUTES"
                      >
                        +R
                      </button>
                      <button
                        onClick={() => handleDelete(item.ID)}
                        className="p-1 rounded bg-slate-800 text-slate-400 hover:text-rose-400"
                        title="Dismiss/Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between text-xs font-mono text-slate-400">
        <span>Showing {total === 0 ? 0 : offset + 1} - {Math.min(offset + limit, total)} of {total} records</span>
        <div className="flex items-center gap-2">
          <button
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - limit))}
            className="p-2 rounded-xl bg-dark-950 border border-slate-800 disabled:opacity-40"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            disabled={offset + limit >= total}
            onClick={() => setOffset(offset + limit)}
            className="p-2 rounded-xl bg-dark-950 border border-slate-800 disabled:opacity-40"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
