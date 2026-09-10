import React from 'react';
import { ShieldCheck, BookOpen, Search, CheckCircle2, Globe, Scale, FileText } from 'lucide-react';

export default function UserAbout() {
  return (
    <div className="max-w-4xl mx-auto space-y-6 text-slate-200">
      {/* Overview Hero */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-blue-950/30 via-dark-900 to-indigo-950/30 border border-blue-900/40 space-y-3">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-white font-sans">About IndicClaim</h1>
            <p className="text-xs sm:text-sm text-blue-300 font-sans">
              AI-Powered Fact Verification for Indian Context & Governance
            </p>
          </div>
        </div>

        <p className="text-sm sm:text-base text-slate-300 font-sans leading-relaxed pt-2">
          IndicClaim is an intelligent, evidence-grounded fact-checking platform engineered specifically for the Indian information ecosystem. It allows citizens, researchers, and professionals to verify claims against authoritative government, legal, and news archives.
        </p>
      </div>

      {/* How It Works */}
      <div className="p-6 sm:p-7 rounded-3xl bg-dark-900/70 border border-slate-800 space-y-4">
        <h2 className="text-base font-bold text-white font-sans flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-blue-400" />
          <span>How Verification Works</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
          <div className="p-4 rounded-2xl bg-dark-950/80 border border-slate-800 space-y-2">
            <div className="w-8 h-8 rounded-xl bg-blue-500/15 border border-blue-500/30 text-blue-400 flex items-center justify-center text-xs font-bold font-mono">
              1
            </div>
            <h3 className="text-sm font-bold text-slate-100 font-sans">Evidence Discovery</h3>
            <p className="text-xs text-slate-400 font-sans leading-relaxed">
              When a claim is submitted, IndicClaim locates the most relevant verified excerpts across official archives and public records.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950/80 border border-slate-800 space-y-2">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 flex items-center justify-center text-xs font-bold font-mono">
              2
            </div>
            <h3 className="text-sm font-bold text-slate-100 font-sans">Factual Analysis</h3>
            <p className="text-xs text-slate-400 font-sans leading-relaxed">
              The engine compares the exact factual assertions in the claim against the context provided by authentic evidence.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950/80 border border-slate-800 space-y-2">
            <div className="w-8 h-8 rounded-xl bg-purple-500/15 border border-purple-500/30 text-purple-400 flex items-center justify-center text-xs font-bold font-mono">
              3
            </div>
            <h3 className="text-sm font-bold text-slate-100 font-sans">Transparent Verdict</h3>
            <p className="text-xs text-slate-400 font-sans leading-relaxed">
              A transparent verdict (SUPPORTS / REFUTES) is rendered alongside exact source excerpts so you can verify the truth yourself.
            </p>
          </div>
        </div>
      </div>

      {/* Authoritative Sources Covered */}
      <div className="p-6 sm:p-7 rounded-3xl bg-dark-900/70 border border-slate-800 space-y-4">
        <h2 className="text-base font-bold text-white font-sans flex items-center gap-2">
          <Globe className="w-4 h-4 text-emerald-400" />
          <span>Authoritative Sources Covered</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 text-xs">
          <div className="p-4 rounded-2xl bg-dark-950 border border-slate-800 flex items-start gap-3">
            <Scale className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-bold text-slate-200">Legal Judgments</h4>
              <p className="text-slate-400 text-[11px] mt-0.5">Supreme Court of India, High Courts, and Indian Kanoon legal repositories.</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950 border border-slate-800 flex items-start gap-3">
            <FileText className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-bold text-slate-200">Government Notifications</h4>
              <p className="text-slate-400 text-[11px] mt-0.5">Press Information Bureau (PIB), Ministry of Health, DGCA, and official gazettes.</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950 border border-slate-800 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-bold text-slate-200">Verified News Portals</h4>
              <p className="text-slate-400 text-[11px] mt-0.5">Reputable national news agencies, fact-checking desks, and public interest journalism.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
