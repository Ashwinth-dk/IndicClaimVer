import React, { useEffect, useRef } from 'react';
import { 
  ShieldCheck, 
  Sparkles, 
  Search, 
  Database, 
  Cpu, 
  ArrowRight, 
  FileCheck2,
  Globe2,
  HelpCircle
} from 'lucide-react';
import MessageBubble from './MessageBubble';
import LoadingAnalysis from './LoadingAnalysis';

const EXAMPLE_CLAIMS = [
  {
    topic: 'Health & Policy',
    language: 'English',
    text: 'Tamil Nadu government extended Covid curbs till January 31 and maintained night curfew.',
  },
  {
    topic: 'Judicial & Governance',
    language: 'Hindi',
    text: 'सुप्रीम कोर्ट ने सर्दियों में शहरी गरीबों के लिए आश्रय गृहों की मांग पर विस्तृत हलफनामा मांगा।',
  },
  {
    topic: 'Omicron Variant Data',
    language: 'English',
    text: 'Odisha reported 14 new cases of the Omicron variant of COVID-19.',
  },
  {
    topic: 'Relief & Governance',
    language: 'Bengali',
    text: 'করোনা মহামারি মোকাবিলায় প্রধানমন্ত্রীর ত্রাণ তহবিলে অর্থ দান করেছেন হীরাবেন।',
  },
  {
    topic: 'Political Analysis',
    language: 'English',
    text: 'Arun Jaitley emphasized that the Delhi BJP unit needs to enhance its grassroots credibility.',
  },
  {
    topic: 'Judicial Rulings',
    language: 'Hindi',
    text: 'सुप्रीम कोर्ट ने कहा कि मोटर दुर्घटना दावा मामलों में संभाव्यता की प्रधानता लागू होनी चाहिए।',
  },
];

export default function ChatWindow({
  messages = [],
  isLoading = false,
  activeClaim = '',
  onSelectExample,
}) {
  const scrollEndRef = useRef(null);

  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-6">
      {isEmpty ? (
        <div className="max-w-3xl mx-auto py-8 sm:py-12 space-y-8 animate-in fade-in duration-500">
          {/* Hero Welcome Header */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-950/70 border border-blue-500/30 text-blue-300 text-xs font-mono mb-2 shadow-glow-blue">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>Multi-Evidence Neural Claim Verification</span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
              Verify a <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-teal-300 bg-clip-text text-transparent">Factual Claim</span>
            </h1>

            <p className="text-sm sm:text-base text-slate-400 max-w-xl mx-auto leading-relaxed">
              Enter a factual claim in English or Indic languages. IndicClaimVer retrieves relevant passages from the evidence database and uses fine-tuned <strong>MuRIL</strong> to verify factuality.
            </p>
          </div>

          {/* Quick Architecture Highlights */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-xl bg-dark-900/60 border border-slate-800/80 space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono text-blue-400 font-semibold">
                <Database className="w-4 h-4" />
                <span>Evidence Pool</span>
              </div>
              <p className="text-xs text-slate-400">
                Indexed semantic embeddings across 50,000+ factual news and public records.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-dark-900/60 border border-slate-800/80 space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono text-indigo-400 font-semibold">
                <Cpu className="w-4 h-4" />
                <span>Fine-Tuned MuRIL</span>
              </div>
              <p className="text-xs text-slate-400">
                Multilingual Representations for Indian Languages for sequence classification.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-dark-900/60 border border-slate-800/80 space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono text-teal-400 font-semibold">
                <FileCheck2 className="w-4 h-4" />
                <span>Weighted Aggregation</span>
              </div>
              <p className="text-xs text-slate-400">
                Transparent multi-evidence combination weighted by cosine similarity.
              </p>
            </div>
          </div>

          {/* Example Claims Section */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-1">
              <span className="flex items-center gap-1.5 uppercase tracking-wider font-semibold text-slate-300">
                <HelpCircle className="w-3.5 h-3.5 text-blue-400" />
                Suggested Claims to Test
              </span>
              <span>Click to load</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {EXAMPLE_CLAIMS.map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onSelectExample(example.text)}
                  className="group text-left p-4 rounded-xl bg-dark-900/70 hover:bg-dark-850/90 border border-slate-800/80 hover:border-blue-500/40 transition-all duration-200 shadow-sm hover:shadow-glass flex flex-col justify-between space-y-2"
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="text-[11px] font-mono text-blue-400 font-medium bg-blue-950/50 px-2 py-0.5 rounded border border-blue-500/20">
                      {example.topic}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {example.language}
                    </span>
                  </div>

                  <p className="text-xs text-slate-200 group-hover:text-white leading-relaxed line-clamp-2 font-sans">
                    "{example.text}"
                  </p>

                  <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400 group-hover:text-blue-400 transition-colors pt-1">
                    <span>Verify claim</span>
                    <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Active Live Analysis Spinner & Pipeline Card */}
          {isLoading && <LoadingAnalysis claim={activeClaim} />}
        </div>
      )}

      <div ref={scrollEndRef} className="h-4" />
    </div>
  );
}
