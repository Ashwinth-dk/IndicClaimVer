import React, { useState } from 'react';
import { 
  Sparkles, 
  Search, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Globe, 
  Check, 
  Loader2, 
  FileText, 
  ArrowRight,
  ExternalLink,
  Copy,
  RotateCcw,
  BookOpen
} from 'lucide-react';
import { verifyClaim } from '../services/api';

const SAMPLE_CLAIMS = [
  'COVID-19 vaccination is mandatory for domestic flights in India.',
  'Karnataka High Court set aside life sentence in murder case due to contradictory eyewitness testimony.',
  'The Ministry of Health clarified COVID-19 vaccination is strictly voluntary.',
  'Supreme Court issued fresh guidelines on bail reform under PMLA.',
  'RBI decided to keep repo rate unchanged in latest monetary policy meeting.',
];

export default function UserVerifier({ onSaveHistory }) {
  const [claimText, setClaimText] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(0); // 0: Finding info, 1: Collecting evidence, 2: Verifying claim, 3: Preparing result
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [copied, setCopied] = useState(false);

  const steps = [
    { label: 'Finding relevant information', desc: 'Searching verified knowledge bases' },
    { label: 'Collecting evidence', desc: 'Filtering authoritative sources' },
    { label: 'Verifying claim', desc: 'Analyzing factual consistency' },
    { label: 'Preparing result', desc: 'Synthesizing evidence verdict' },
  ];

  const handleVerify = async (e, mode = 'standard') => {
    e?.preventDefault();
    if (!claimText.trim() || loading) return;

    setErrorMsg('');
    setResult(null);
    setLoading(true);
    setActiveStep(0);

    // Progressive step simulation for a smooth user experience
    const stepInterval = setInterval(() => {
      setActiveStep((prev) => (prev < 3 ? prev + 1 : prev));
    }, 700);

    try {
      const responseData = await verifyClaim(claimText.trim());
      clearInterval(stepInterval);
      setActiveStep(3);
      
      // Delay slightly for smooth completion
      setTimeout(() => {
        setResult(responseData);
        setLoading(false);

        if (onSaveHistory) {
          onSaveHistory({
            id: Date.now().toString(),
            claim: claimText.trim(),
            verdict: responseData.verdict,
            confidence: responseData.confidence,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            date: new Date().toLocaleDateString(),
            data: responseData,
          });
        }
      }, 400);
    } catch (err) {
      clearInterval(stepInterval);
      setLoading(false);
      setErrorMsg(err.message || 'Verification could not be completed. Please try again.');
    }
  };

  const handleCopyResult = () => {
    if (!result) return;
    const text = `IndicClaim Verification:\nClaim: "${result.claim}"\nVerdict: ${result.verdict} (${Math.round((result.confidence || 0) * 100)}% Confidence)\nSummary: ${result.summary}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    setClaimText('');
    setResult(null);
    setErrorMsg('');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Hero Welcome Card */}
      {!result && !loading && (
        <div className="text-center space-y-3 pt-4 pb-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Multi-Source Fact Verification</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white font-sans">
            Verify Any Claim in Seconds
          </h1>
          <p className="text-sm sm:text-base text-slate-400 max-w-xl mx-auto font-sans leading-relaxed">
            Enter a news claim, government policy statement, or legal development. IndicClaim automatically cross-references verified evidence to determine its authenticity.
          </p>
        </div>
      )}

      {/* Main Input Form */}
      <div className="p-5 sm:p-7 rounded-3xl bg-dark-900/80 border border-slate-800 shadow-2xl backdrop-blur-xl space-y-4">
        <form onSubmit={(e) => handleVerify(e, 'standard')} className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 flex items-center justify-between">
              <span>What would you like to verify?</span>
              <span className="text-[11px] text-slate-400 font-sans normal-case">News, policy statements, or viral claims</span>
            </label>
            <div className="relative">
              <textarea
                rows={3}
                value={claimText}
                onChange={(e) => setClaimText(e.target.value)}
                placeholder="e.g. COVID-19 vaccination was made mandatory for domestic flights in India..."
                disabled={loading}
                className="w-full p-4 rounded-2xl bg-dark-950 border border-slate-700/80 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/15 text-slate-100 placeholder-slate-500 text-sm sm:text-base font-sans leading-relaxed transition-all resize-none disabled:opacity-60"
              />
            </div>
          </div>

          {/* Preset Suggestions */}
          {!loading && !result && (
            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] font-mono text-slate-400">Popular claims to try:</span>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_CLAIMS.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setClaimText(sample)}
                    className="text-left text-xs px-3 py-1.5 rounded-xl bg-slate-800/60 hover:bg-blue-900/30 text-slate-300 hover:text-blue-200 border border-slate-700/60 hover:border-blue-500/30 transition-all font-sans"
                  >
                    {sample.length > 60 ? `${sample.slice(0, 57)}...` : sample}
                  </button>
                ))}
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="p-3.5 rounded-2xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={loading || !claimText.trim()}
              className="w-full sm:w-auto flex-1 flex items-center justify-center gap-2 px-8 py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-indigo-500 text-white font-sans font-bold text-sm shadow-lg shadow-blue-500/25 transition-all active:scale-98 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analyzing Claim...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Verify Claim</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={(e) => handleVerify(e, 'research')}
              disabled={loading || !claimText.trim()}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl bg-dark-950 hover:bg-slate-800 text-slate-200 border border-slate-700/80 font-sans font-semibold text-xs transition-all active:scale-98 disabled:opacity-50"
            >
              <Globe className="w-4 h-4 text-indigo-400" />
              <span>Research & Verify</span>
            </button>

            {(result || claimText) && !loading && (
              <button
                type="button"
                onClick={handleReset}
                className="p-3.5 rounded-2xl bg-dark-950 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-colors"
                title="Reset and verify another claim"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Step-by-Step Progress Display */}
      {loading && (
        <div className="p-6 rounded-3xl bg-dark-900/90 border border-blue-500/30 shadow-xl space-y-4 animate-fade-in">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-blue-400 font-bold">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Analyzing Your Claim</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {steps.map((st, i) => {
              const isDone = activeStep > i;
              const isCurrent = activeStep === i;
              return (
                <div
                  key={i}
                  className={`p-3.5 rounded-2xl border flex items-center gap-3 transition-all ${
                    isDone
                      ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                      : isCurrent
                      ? 'bg-blue-950/40 border-blue-500/50 text-blue-200 shadow-glow-blue animate-pulse-subtle'
                      : 'bg-dark-950/40 border-slate-800 text-slate-400'
                  }`}
                >
                  <div
                    className={`w-7 h-7 rounded-xl flex items-center justify-center text-xs font-bold ${
                      isDone
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : isCurrent
                        ? 'bg-blue-500/30 text-blue-300'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {isDone ? <Check className="w-4 h-4" /> : i + 1}
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold">{st.label}</h4>
                    <p className="text-[11px] opacity-70 font-sans">{st.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Final Verification Result Card */}
      {result && !loading && (
        <div className="space-y-5 animate-fade-in">
          {/* Verdict Banner */}
          <div
            className={`p-6 sm:p-8 rounded-3xl border shadow-2xl relative overflow-hidden ${
              result.verdict === 'SUPPORTS'
                ? 'bg-gradient-to-br from-emerald-950/60 via-dark-900 to-teal-950/40 border-emerald-500/40'
                : result.verdict === 'REFUTES'
                ? 'bg-gradient-to-br from-rose-950/60 via-dark-900 to-pink-950/40 border-rose-500/40'
                : 'bg-gradient-to-br from-amber-950/60 via-dark-900 to-yellow-950/40 border-amber-500/40'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
              <div className="flex items-center gap-3">
                <div
                  className={`p-3 rounded-2xl ${
                    result.verdict === 'SUPPORTS'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-glow-emerald'
                      : result.verdict === 'REFUTES'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30 shadow-glow-rose'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {result.verdict === 'SUPPORTS' ? (
                    <CheckCircle2 className="w-7 h-7" />
                  ) : result.verdict === 'REFUTES' ? (
                    <XCircle className="w-7 h-7" />
                  ) : (
                    <AlertCircle className="w-7 h-7" />
                  )}
                </div>
                <div>
                  <span className="text-[11px] font-mono uppercase tracking-widest text-slate-400 block">
                    Verification Verdict
                  </span>
                  <h2
                    className={`text-2xl sm:text-3xl font-black font-mono tracking-tight ${
                      result.verdict === 'SUPPORTS'
                        ? 'text-emerald-300'
                        : result.verdict === 'REFUTES'
                        ? 'text-rose-300'
                        : 'text-amber-300'
                    }`}
                  >
                    {result.verdict}
                  </h2>
                </div>
              </div>

              {/* Confidence / Reliability Rating */}
              <div className="flex items-center gap-3 bg-dark-950/80 px-4 py-2.5 rounded-2xl border border-slate-800">
                <div className="text-right">
                  <span className="text-[10px] font-mono uppercase text-slate-400 block">Reliability Score</span>
                  <span className="text-base font-bold font-mono text-white">
                    {Math.round((result.confidence || 0) * 100)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Plain-Language Summary Explanation */}
            <div className="pt-4 space-y-2">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                Summary Assessment
              </h3>
              <p className="text-sm sm:text-base text-slate-200 font-sans leading-relaxed">
                {result.summary || (
                  result.verdict === 'SUPPORTS'
                    ? 'The verified evidence consistently supports the facts stated in this claim.'
                    : result.verdict === 'REFUTES'
                    ? 'The verified evidence directly contradicts or debunks the facts in this claim.'
                    : 'Insufficient authoritative evidence was found to confirm or disprove this claim.'
                )}
              </p>
            </div>

            {/* Footer Action */}
            <div className="pt-4 flex items-center justify-between border-t border-slate-800/80 mt-4">
              <span className="text-xs text-slate-400 font-sans">
                Evidence verified across {result.evidence?.length || 0} authoritative sources
              </span>
              <button
                onClick={handleCopyResult}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-xs font-mono text-slate-300 hover:text-white transition-all"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>{copied ? 'Copied!' : 'Copy Summary'}</span>
              </button>
            </div>
          </div>

          {/* Evidence Used List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-bold flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-blue-400" />
                <span>Evidence Used for Verification ({result.evidence?.length || 0})</span>
              </h3>
            </div>

            <div className="space-y-3">
              {result.evidence && result.evidence.length > 0 ? (
                result.evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-4 sm:p-5 rounded-2xl bg-dark-900/70 border border-slate-800/90 space-y-2 hover:border-slate-700 transition-all"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="px-2.5 py-0.5 rounded-lg bg-blue-500/10 text-blue-300 font-mono text-[11px] border border-blue-500/20 font-semibold">
                        Source #{idx + 1}
                      </span>
                      <span className="text-slate-400 font-mono text-[11px]">
                        Relevance: {Math.round((ev.retrieval_score || 0) * 100)}%
                      </span>
                    </div>

                    <p className="text-xs sm:text-sm text-slate-300 font-sans leading-relaxed">
                      "{ev.text}"
                    </p>
                  </div>
                ))
              ) : (
                <div className="p-4 rounded-2xl bg-dark-900/40 border border-slate-800 text-center text-xs text-slate-400">
                  No specific evidence passages were indexed for this query.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
