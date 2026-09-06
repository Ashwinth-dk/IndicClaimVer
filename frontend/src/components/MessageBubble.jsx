import React from 'react';
import { User, ShieldCheck, Database, Layers, Sparkles, AlertOctagon } from 'lucide-react';
import VerdictCard from './VerdictCard';
import EvidenceCard from './EvidenceCard';
import PipelineStatus from './PipelineStatus';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isError = message.isError;

  if (isUser) {
    return (
      <div className="flex justify-end my-4 animate-in fade-in duration-300">
        <div className="flex items-start gap-3 max-w-2xl">
          <div className="rounded-2xl rounded-tr-sm bg-gradient-to-br from-blue-600 to-indigo-700 px-4 py-3 text-white shadow-lg border border-blue-400/20">
            <div className="flex items-center gap-1.5 text-[11px] font-mono text-blue-200 uppercase tracking-wider mb-1">
              <span>Submitted Claim</span>
            </div>
            <p className="text-sm font-normal leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          </div>
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
            <User className="w-4 h-4 text-blue-400" />
          </div>
        </div>
      </div>
    );
  }

  // Error Message
  if (isError) {
    return (
      <div className="flex justify-start my-4">
        <div className="flex items-start gap-3 max-w-3xl">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-950/60 border border-red-500/40 flex items-center justify-center text-red-400">
            <AlertOctagon className="w-4 h-4" />
          </div>
          <div className="rounded-2xl rounded-tl-sm bg-rose-950/30 border border-rose-500/30 p-4 text-sm text-rose-200 space-y-1">
            <div className="font-semibold text-rose-400 flex items-center gap-1.5 text-xs uppercase tracking-wider">
              Verification Pipeline Error
            </div>
            <p className="text-slate-300 text-sm leading-relaxed">
              {message.content}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const data = message.data || {};
  const evidenceList = data.evidence || [];

  return (
    <div className="flex justify-start my-6 animate-in fade-in duration-300">
      <div className="flex items-start gap-3.5 w-full max-w-4xl">
        {/* Assistant Avatar */}
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 p-0.5 shadow-glow-blue">
          <div className="w-full h-full rounded-[10px] bg-dark-950 flex items-center justify-center">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
          </div>
        </div>

        {/* Message Card Container */}
        <div className="flex-1 space-y-4">
          {/* Conversational Natural Language Header */}
          {data.summary && (
            <div className="rounded-xl bg-dark-900/90 border border-slate-800/80 p-4 shadow-glass">
              <div className="flex items-center gap-2 mb-2 text-xs font-mono text-blue-400">
                <Sparkles className="w-3.5 h-3.5" />
                <span className="font-semibold uppercase tracking-wider">Analysis Summary</span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed font-sans">
                {data.summary}
              </p>
            </div>
          )}

          {/* Pipeline Stage Bar */}
          <PipelineStatus isComplete={true} activeStep={5} />

          {/* Prominent Verdict Card */}
          <VerdictCard
            verdict={data.verdict || 'SUPPORTS'}
            confidence={data.confidence || 0}
            supportsScore={data.supports_score || 0}
            refutesScore={data.refutes_score || 0}
            evidenceCount={evidenceList.length}
            modelName={data.model_name || 'MuRIL'}
          />

          {/* Evidence Analysis Section */}
          {evidenceList.length > 0 && (
            <div className="space-y-2.5 pt-2">
              <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-blue-400" />
                  <h4 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-300">
                    Retrieved Evidence Analysis ({evidenceList.length})
                  </h4>
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  Ranked by semantic cosine similarity
                </span>
              </div>

              <div className="space-y-2">
                {evidenceList.map((item) => (
                  <EvidenceCard
                    key={item.id || item.rank}
                    rank={item.rank}
                    id={item.id}
                    text={item.text}
                    retrievalScore={item.retrieval_score}
                    prediction={item.prediction}
                    confidence={item.confidence}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Footer Timestamp / Model info */}
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1 pt-1 border-t border-slate-900">
            <span>Verified via MuRIL Fine-Tuned Sequence Classifier</span>
            <span>{message.timestamp || new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
