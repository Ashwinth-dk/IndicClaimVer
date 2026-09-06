import React from 'react';

/**
 * ConfidenceBar renders a sleek visual indicator of model confidence
 * with appropriate verdict-based color accenting.
 */
export default function ConfidenceBar({ confidence = 0, verdict = 'SUPPORTS', className = '' }) {
  const percent = Math.min(100, Math.max(0, Math.round(confidence * 100)));

  // Determine bar color according to verdict
  let barGradient = 'from-blue-600 to-blue-400';
  let textColor = 'text-blue-400';

  if (verdict === 'SUPPORTS') {
    barGradient = 'from-emerald-600 via-emerald-500 to-teal-400';
    textColor = 'text-emerald-400';
  } else if (verdict === 'REFUTES') {
    barGradient = 'from-rose-600 via-red-500 to-pink-500';
    textColor = 'text-red-400';
  } else if (verdict === 'INSUFFICIENT_EVIDENCE') {
    barGradient = 'from-amber-600 via-amber-500 to-yellow-400';
    textColor = 'text-amber-400';
  }

  // Qualitative confidence label
  let quality = 'Low';
  if (percent >= 85) quality = 'High Certainty';
  else if (percent >= 65) quality = 'Moderate Certainty';
  else quality = 'Marginal / Uncertain';

  return (
    <div className={`w-full space-y-1.5 ${className}`}>
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-slate-400">Confidence Metric</span>
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-[11px] font-sans">{quality}</span>
          <span className={`font-semibold ${textColor}`}>{percent}%</span>
        </div>
      </div>
      
      {/* Background Track */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-900 border border-slate-800">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${barGradient} transition-all duration-700 ease-out`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
