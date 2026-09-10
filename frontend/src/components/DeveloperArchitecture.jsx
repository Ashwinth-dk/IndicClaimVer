import React, { useState, useEffect } from 'react';
import { Layers, Cpu, Database, Search, Sparkles, Scale, Server, ShieldCheck } from 'lucide-react';
import { getHealthStatus, getActiveModelInfo } from '../services/api';

export default function DeveloperArchitecture() {
  const [health, setHealth] = useState(null);
  const [modelMeta, setModelMeta] = useState(null);

  useEffect(() => {
    getHealthStatus().then(setHealth);
    getActiveModelInfo().then(setModelMeta);
  }, []);

  return (
    <div className="space-y-6 text-slate-100 font-sans">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 flex items-center gap-3">
        <div className="p-3 rounded-2xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
          <Layers className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-xl font-black font-mono text-white">System Architecture & Pipeline Internals</h2>
          <p className="text-xs text-slate-400 font-sans">
            Technical pipeline specification from vector cosine retrieval to MuRIL sequence classification.
          </p>
        </div>
      </div>

      {/* 5-Step Pipeline Architecture */}
      <div className="p-6 rounded-3xl bg-dark-900/70 border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-200">
          Core Claim Verification Pipeline
        </h3>

        <div className="space-y-3">
          <div className="p-4 rounded-2xl bg-dark-950/80 border border-slate-800 flex items-start gap-4">
            <div className="w-8 h-8 rounded-xl bg-blue-500/15 border border-blue-500/30 text-blue-400 flex items-center justify-center font-mono text-xs font-bold flex-shrink-0">
              01
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-bold font-mono text-white">Claim Preprocessing & Normalization</h4>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Cleans Indic & English script, removes zero-width characters, normalizes whitespace, and parses entity assertions.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950/80 border border-slate-800 flex items-start gap-4">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 flex items-center justify-center font-mono text-xs font-bold flex-shrink-0">
              02
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-bold font-mono text-white">Dense Vector Semantic Retrieval</h4>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Encodes claim using <code className="text-blue-300">paraphrase-multilingual-MiniLM-L12-v2</code> and performs vector cosine similarity search over 13,600+ indexed passages.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950/80 border border-slate-800 flex items-start gap-4">
            <div className="w-8 h-8 rounded-xl bg-purple-500/15 border border-purple-500/30 text-purple-400 flex items-center justify-center font-mono text-xs font-bold flex-shrink-0">
              03
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-bold font-mono text-white">Contextual Top-K Relevance Ranking</h4>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Ranks candidates using lexical term overlap, entity matches, and semantic relevance to select top-5 corroborating evidence passages.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950/80 border border-slate-800 flex items-start gap-4">
            <div className="w-8 h-8 rounded-xl bg-teal-500/15 border border-teal-500/30 text-teal-400 flex items-center justify-center font-mono text-xs font-bold flex-shrink-0">
              04
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-bold font-mono text-white">MuRIL Cross-Attention Sequence Inference</h4>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Feeds (Claim, Evidence) pair into fine-tuned <code className="text-teal-300">BertForSequenceClassification</code> (MuRIL) to compute logits for SUPPORTS vs REFUTES.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950/80 border border-slate-800 flex items-start gap-4">
            <div className="w-8 h-8 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center font-mono text-xs font-bold flex-shrink-0">
              05
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-bold font-mono text-white">Relevance-Weighted Verdict Synthesis</h4>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Aggregates evidence predictions weighted by retrieval cosine score to formulate final verdict and reliability confidence.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Runtime Configuration Table */}
      <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800 space-y-3">
        <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
          Runtime Configuration & Storage Paths
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex justify-between">
            <span className="text-slate-400">Device</span>
            <span className="text-blue-400 font-bold">{health?.device?.toUpperCase() || 'CPU'}</span>
          </div>

          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex justify-between">
            <span className="text-slate-400">Embedding Dimension</span>
            <span className="text-white font-bold">384</span>
          </div>

          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex justify-between">
            <span className="text-slate-400">Max Sequence Length</span>
            <span className="text-white font-bold">512</span>
          </div>

          <div className="p-3 rounded-xl bg-dark-950 border border-slate-800 flex justify-between">
            <span className="text-slate-400">Active Model</span>
            <span className="text-emerald-400 font-bold">{modelMeta?.active_version || 'baseline'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
