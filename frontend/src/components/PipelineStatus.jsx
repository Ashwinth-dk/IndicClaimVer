import React from 'react';
import { Check, Loader2, CircleDot, Database, Cpu, Search, Sparkles, Filter } from 'lucide-react';

const STEPS = [
  { id: 'claim', label: 'Understanding Claim', icon: Search },
  { id: 'retrieval', label: 'Searching Evidence', icon: Database },
  { id: 'ranking', label: 'Ranking Evidence', icon: Filter },
  { id: 'muril', label: 'MuRIL Verification', icon: Cpu },
  { id: 'verdict', label: 'Generating Verdict', icon: Sparkles },
];

export default function PipelineStatus({ activeStep = 5, isComplete = true }) {
  return (
    <div className="w-full rounded-xl bg-dark-900/60 border border-slate-800/80 p-3.5 sm:p-4">
      <div className="flex items-center justify-between mb-3 text-xs font-mono text-slate-400">
        <span className="flex items-center gap-1.5 font-medium text-slate-300">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          Verification Pipeline
        </span>
        <span className="text-[11px] text-slate-400">
          {isComplete ? 'All stages completed' : `Stage ${activeStep} of ${STEPS.length}`}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
        {STEPS.map((step, idx) => {
          const stepNum = idx + 1;
          const isDone = isComplete || stepNum < activeStep;
          const isCurrent = !isComplete && stepNum === activeStep;
          const isPending = !isComplete && stepNum > activeStep;
          const Icon = step.icon;

          let stateBg = 'bg-slate-900/40 border-slate-800/60 text-slate-400';
          let iconColor = 'text-slate-400';
          let statusBadge = 'Pending';

          if (isDone) {
            stateBg = 'bg-blue-950/20 border-blue-500/30 text-blue-200';
            iconColor = 'text-blue-400';
            statusBadge = 'Completed';
          } else if (isCurrent) {
            stateBg = 'bg-blue-900/30 border-blue-400/60 text-blue-100 shadow-glow-blue animate-pulse-subtle';
            iconColor = 'text-blue-300';
            statusBadge = 'Processing';
          }

          return (
            <div
              key={step.id}
              className={`flex sm:flex-col items-center sm:items-start justify-between sm:justify-center p-2.5 rounded-lg border text-xs transition-all ${stateBg}`}
            >
              <div className="flex items-center gap-2">
                <div className="p-1 rounded bg-slate-800/50">
                  <Icon className={`w-3.5 h-3.5 ${iconColor}`} />
                </div>
                <span className="font-medium text-slate-200 text-[11px] sm:text-xs truncate">
                  {step.label}
                </span>
              </div>

              <div className="mt-0 sm:mt-2 flex items-center gap-1 font-mono text-[10px]">
                {isDone ? (
                  <span className="flex items-center gap-1 text-emerald-400">
                    <Check className="w-3 h-3" />
                    <span>Done</span>
                  </span>
                ) : isCurrent ? (
                  <span className="flex items-center gap-1 text-blue-300">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Active</span>
                  </span>
                ) : (
                  <span className="text-slate-400 flex items-center gap-1">
                    <CircleDot className="w-2.5 h-2.5" />
                    <span>Queued</span>
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
