import React, { useState, useEffect } from 'react';
import { Loader2, Database, Cpu, Search, Sparkles, Filter, Check } from 'lucide-react';

const STAGES = [
  { label: 'Understanding claim semantics & language...', duration: 1200, icon: Search },
  { label: 'Searching multilingual vector evidence database (50k+ passages)...', duration: 2500, icon: Database },
  { label: 'Ranking and selecting Top-5 relevant evidence candidates...', duration: 1500, icon: Filter },
  { label: 'Running fine-tuned MuRIL sequence classification on (claim, evidence) pairs...', duration: 3000, icon: Cpu },
  { label: 'Synthesizing weighted confidence scores and generating verdict...', duration: 1500, icon: Sparkles },
];

export default function LoadingAnalysis({ claim = '' }) {
  const [currentStageIdx, setCurrentStageIdx] = useState(0);

  useEffect(() => {
    let timeout;
    if (currentStageIdx < STAGES.length - 1) {
      timeout = setTimeout(() => {
        setCurrentStageIdx((prev) => Math.min(prev + 1, STAGES.length - 1));
      }, STAGES[currentStageIdx].duration);
    }
    return () => clearTimeout(timeout);
  }, [currentStageIdx]);

  return (
    <div className="w-full max-w-3xl mx-auto rounded-2xl bg-dark-900/90 border border-blue-500/30 p-6 shadow-glass space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/40">
            <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 font-mono tracking-tight">
              Executing IndicClaimVer Pipeline
            </h4>
            <p className="text-xs text-slate-400">
              Retrieving evidence & running neural verification
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-950/60 border border-blue-500/30 text-xs font-mono text-blue-300">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          <span>Stage {currentStageIdx + 1} of {STAGES.length}</span>
        </div>
      </div>

      {/* Target Claim preview */}
      <div className="rounded-lg bg-dark-950/80 border border-slate-800/80 p-3.5 text-xs text-slate-300">
        <span className="font-mono text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
          Evaluating Claim:
        </span>
        <p className="font-sans italic line-clamp-2 text-slate-200">
          "{claim}"
        </p>
      </div>

      {/* Progressive Step Checklist */}
      <div className="space-y-2.5">
        {STAGES.map((stage, idx) => {
          const isDone = idx < currentStageIdx;
          const isActive = idx === currentStageIdx;
          const isPending = idx > currentStageIdx;
          const Icon = stage.icon;

          return (
            <div
              key={idx}
              className={`flex items-center justify-between p-3 rounded-lg border text-xs transition-all ${
                isActive
                  ? 'bg-blue-950/30 border-blue-500/50 text-blue-200 shadow-glow-blue'
                  : isDone
                  ? 'bg-slate-900/40 border-slate-800/60 text-slate-400'
                  : 'bg-dark-950/40 border-slate-900/60 text-slate-400 opacity-60'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`p-1.5 rounded-md ${isActive ? 'bg-blue-500/20 text-blue-300' : isDone ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <span className={`font-medium ${isActive ? 'text-slate-100 font-semibold' : 'text-slate-300'}`}>
                  {stage.label}
                </span>
              </div>

              <div className="font-mono text-[11px]">
                {isDone && (
                  <span className="flex items-center gap-1 text-emerald-400">
                    <Check className="w-3.5 h-3.5" />
                    <span>Completed</span>
                  </span>
                )}
                {isActive && (
                  <span className="flex items-center gap-1 text-blue-400">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Processing</span>
                  </span>
                )}
                {isPending && (
                  <span className="text-slate-400">Queued</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
