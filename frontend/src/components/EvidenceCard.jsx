import React, { useState } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  Copy, 
  Check, 
  FileText, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  Sparkles,
  Percent
} from 'lucide-react';

export default function EvidenceCard({
  rank = 1,
  id = 'EV_UNKNOWN',
  text = '',
  retrievalScore = 0,
  prediction = 'SUPPORTS',
  confidence = 0,
}) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const isSupports = prediction === 'SUPPORTS';
  const isRefutes = prediction === 'REFUTES';

  const relPercent = Math.round(retrievalScore * 100);
  const confPercent = Math.round(confidence * 100);

  // Snippet length
  const isLong = text.length > 220;
  const displayText = expanded || !isLong ? text : text.slice(0, 220) + '...';

  const handleCopy = (e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div 
      className={`group rounded-xl border transition-all duration-200 ${
        expanded 
          ? 'bg-dark-850/95 border-blue-500/40 shadow-glass' 
          : 'bg-dark-900/70 hover:bg-dark-850/80 border-slate-800/80 hover:border-slate-700/80'
      }`}
    >
      {/* Top Bar / Summary */}
      <div 
        onClick={() => setExpanded(!expanded)}
        className="flex flex-wrap items-center justify-between gap-3 p-4 cursor-pointer select-none"
      >
        {/* Left: Rank & ID */}
        <div className="flex items-center gap-2.5">
          <span className="flex items-center justify-center w-6 h-6 rounded-md bg-blue-500/10 border border-blue-500/20 text-blue-400 font-mono text-xs font-bold">
            #{rank}
          </span>
          <span className="font-mono text-xs text-slate-400 font-medium">
            {id}
          </span>
          <span className="hidden sm:inline-block text-slate-600">•</span>
          
          {/* Relevance Badge */}
          <div className="flex items-center gap-1 text-xs font-mono text-slate-300 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700/60">
            <span className="text-slate-400">Relevance:</span>
            <span className="text-blue-400 font-semibold">{relPercent}%</span>
          </div>
        </div>

        {/* Right: Model Prediction & Confidence + Actions */}
        <div className="flex items-center gap-2.5">
          {/* Prediction Tag */}
          <div className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border font-mono ${
            isSupports
              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40'
              : isRefutes
              ? 'bg-rose-950/60 text-rose-300 border-rose-500/40'
              : 'bg-slate-800 text-slate-300 border-slate-700'
          }`}>
            {isSupports ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : isRefutes ? (
              <XCircle className="w-3 h-3 text-rose-400" />
            ) : null}
            <span>{prediction}</span>
            <span className="text-slate-400 font-normal">({confPercent}%)</span>
          </div>

          {/* Copy Button */}
          <button
            type="button"
            onClick={handleCopy}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Copy evidence passage"
            aria-label="Copy evidence passage"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>

          {/* Expand Toggle */}
          <button
            type="button"
            className="p-1 text-slate-400 group-hover:text-slate-200 transition-colors"
            aria-label={expanded ? 'Collapse evidence details' : 'Expand evidence details'}
          >
            {expanded ? (
              <ChevronUp className="w-4 h-4 text-blue-400" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Passage Text Body */}
      <div className="px-4 pb-4 pt-1">
        <p className="text-sm text-slate-200 leading-relaxed font-sans whitespace-pre-wrap selection:bg-blue-500/20">
          {displayText}
        </p>

        {isLong && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="mt-2 text-xs font-mono font-medium text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1"
          >
            {expanded ? (
              <>
                <span>Show Less</span>
                <ChevronUp className="w-3 h-3" />
              </>
            ) : (
              <>
                <span>Show More</span>
                <ChevronDown className="w-3 h-3" />
              </>
            )}
          </button>
        )}
      </div>

      {/* Expanded Metadata Footer */}
      {expanded && (
        <div className="px-4 py-2.5 border-t border-slate-800/80 bg-dark-950/40 rounded-b-xl flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-slate-400">
          <div className="flex items-center gap-3">
            <span>Cosine Relevance: <strong className="text-slate-300">{retrievalScore.toFixed(4)}</strong></span>
            <span>MuRIL Confidence: <strong className="text-slate-300">{confidence.toFixed(4)}</strong></span>
          </div>
          <div className="text-[11px] text-slate-400">
            Source: Evidence Database ({id})
          </div>
        </div>
      )}
    </div>
  );
}
