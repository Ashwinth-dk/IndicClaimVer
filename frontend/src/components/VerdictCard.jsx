import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck, Database, Layers } from 'lucide-react';
import ConfidenceBar from './ConfidenceBar';

export default function VerdictCard({
  verdict = 'SUPPORTS',
  confidence = 0,
  supportsScore = 0,
  refutesScore = 0,
  evidenceCount = 0,
  modelName = 'MuRIL',
}) {
  const isSupports = verdict === 'SUPPORTS';
  const isRefutes = verdict === 'REFUTES';
  const isInsufficient = verdict === 'INSUFFICIENT_EVIDENCE';

  // Visual theming based on verdict
  let containerBg = 'bg-slate-900/80 border-slate-800';
  let badgeBg = 'bg-slate-800 text-slate-300 border-slate-700';
  let badgeIcon = <ShieldCheck className="w-5 h-5" />;
  let verdictTitle = 'UNKNOWN';
  let verdictDesc = 'No conclusive verdict reached.';

  if (isSupports) {
    containerBg = 'bg-emerald-950/20 border-emerald-500/30 shadow-glow-green';
    badgeBg = 'bg-emerald-900/50 text-emerald-300 border-emerald-500/40';
    badgeIcon = <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
    verdictTitle = 'SUPPORTS';
    verdictDesc = 'Retrieved evidence aligns with and verifies the factual claim.';
  } else if (isRefutes) {
    containerBg = 'bg-rose-950/20 border-rose-500/30 shadow-glow-red';
    badgeBg = 'bg-rose-900/50 text-rose-300 border-rose-500/40';
    badgeIcon = <XCircle className="w-5 h-5 text-rose-400" />;
    verdictTitle = 'REFUTES';
    verdictDesc = 'Retrieved evidence contradicts or disproves the factual claim.';
  } else if (isInsufficient) {
    containerBg = 'bg-amber-950/20 border-amber-500/30';
    badgeBg = 'bg-amber-900/50 text-amber-300 border-amber-500/40';
    badgeIcon = <AlertTriangle className="w-5 h-5 text-amber-400" />;
    verdictTitle = 'INSUFFICIENT EVIDENCE';
    verdictDesc = 'Relevant factual passages in the corpus are insufficient for decisive verification.';
  }

  const confPercent = Math.round(confidence * 100);
  const supPercent = Math.round(supportsScore * 100);
  const refPercent = Math.round(refutesScore * 100);

  return (
    <div className={`w-full rounded-xl border p-5 transition-all ${containerBg}`}>
      {/* Header Section: Tag & Evidence Metric */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-2.5">
          <span className="text-xs font-mono font-medium uppercase tracking-wider text-slate-400">
            Model Verdict
          </span>
          <div className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1 text-sm font-bold tracking-wide ${badgeBg}`}>
            {badgeIcon}
            <span>{verdictTitle}</span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
          <div className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-blue-400" />
            <span>{evidenceCount} Evidence {evidenceCount === 1 ? 'Passage' : 'Passages'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Model:</span>
            <span className="text-slate-300">{modelName.split(' ')[0]}</span>
          </div>
        </div>
      </div>

      {/* Main Verdict Content */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        {/* Left 2 Cols: Confidence Bar & Description */}
        <div className="md:col-span-2 space-y-3">
          <p className="text-sm text-slate-300 leading-relaxed font-normal">
            {verdictDesc}
          </p>
          <ConfidenceBar confidence={confidence} verdict={verdict} />
        </div>

        {/* Right Col: Aggregate Scores Breakdown */}
        <div className="rounded-lg bg-dark-900/80 border border-slate-800/80 p-3.5 font-mono text-xs space-y-2">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-sans font-medium">
            Aggregation Scores
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Supports:
            </span>
            <span className="font-semibold text-emerald-400">{supPercent}%</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-400" />
              Refutes:
            </span>
            <span className="font-semibold text-rose-400">{refPercent}%</span>
          </div>
          <div className="pt-1.5 border-t border-slate-800 text-[10px] text-slate-400 font-sans">
            Weighted by semantic relevance
          </div>
        </div>
      </div>
    </div>
  );
}
