import React from 'react';
import { ShieldCheck, History, Info, Sparkles, Lock, Terminal } from 'lucide-react';

export default function UserHeader({ activeTab, setActiveTab, onOpenDevPortal, isDevAuth }) {
  return (
    <header className="border-b border-slate-800/80 bg-dark-950/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <div 
          onClick={() => setActiveTab('verifier')} 
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 p-0.5 shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-dark-950 rounded-[10px] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-blue-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-black tracking-tight text-white font-mono">
                Indic<span className="text-blue-400">Claim</span>
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-sans tracking-wide">AI-Powered Fact Verification</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => setActiveTab('verifier')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold font-sans transition-all ${
              activeTab === 'verifier'
                ? 'bg-blue-600/15 text-blue-300 border border-blue-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Fact Verifier</span>
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold font-sans transition-all ${
              activeTab === 'history'
                ? 'bg-blue-600/15 text-blue-300 border border-blue-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
            }`}
          >
            <History className="w-4 h-4" />
            <span>History</span>
          </button>

          <button
            onClick={() => setActiveTab('about')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold font-sans transition-all ${
              activeTab === 'about'
                ? 'bg-blue-600/15 text-blue-300 border border-blue-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
            }`}
          >
            <Info className="w-4 h-4" />
            <span>About</span>
          </button>

          {/* Discrete Developer Portal Trigger */}
          <div className="pl-2 border-l border-slate-800 ml-1">
            <button
              onClick={onOpenDevPortal}
              title={isDevAuth ? 'Open Developer Dashboard' : 'Developer Access'}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-mono text-slate-400 hover:text-indigo-300 hover:bg-indigo-950/40 border border-transparent hover:border-indigo-800/40 transition-all"
            >
              {isDevAuth ? (
                <>
                  <Terminal className="w-3.5 h-3.5 text-indigo-400" />
                  <span className="hidden sm:inline">Developer</span>
                </>
              ) : (
                <>
                  <Lock className="w-3 h-3 text-slate-400" />
                  <span className="hidden md:inline">Dev Mode</span>
                </>
              )}
            </button>
          </div>
        </nav>
      </div>
    </header>
  );
}
