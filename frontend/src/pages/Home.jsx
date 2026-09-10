import React, { useState, useEffect } from 'react';
import UserHeader from '../components/UserHeader';
import UserVerifier from '../components/UserVerifier';
import UserHistory from '../components/UserHistory';
import UserAbout from '../components/UserAbout';
import DeveloperPortal from '../components/DeveloperPortal';
import DeveloperAuthModal from '../components/DeveloperAuthModal';
import { isAdminAuthenticated } from '../services/api';
import { ShieldCheck, Terminal, Heart } from 'lucide-react';

const STORAGE_KEY = 'indicclaim_user_history_v2';

export default function Home() {
  const [activeTab, setActiveTab] = useState('verifier'); // 'verifier' | 'history' | 'about' | 'developer'
  const [history, setHistory] = useState([]);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isDevAuth, setIsDevAuth] = useState(false);

  // Load history & auth state on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        setHistory(JSON.parse(saved));
      }
    } catch (e) {
      console.warn('Failed to parse history from localStorage', e);
    }
    setIsDevAuth(isAdminAuthenticated());
  }, []);

  const saveHistory = (item) => {
    const updated = [item, ...history.filter(h => h.claim !== item.claim).slice(0, 49)];
    setHistory(updated);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.warn('Failed to save history', e);
    }
  };

  const handleClearHistory = () => {
    setHistory([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {}
  };

  const handleDeleteHistoryItem = (id) => {
    const updated = history.filter(item => item.id !== id);
    setHistory(updated);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {}
  };

  const handleSelectHistoryItem = (item) => {
    setActiveTab('verifier');
  };

  const handleOpenDevPortal = () => {
    if (isAdminAuthenticated()) {
      setIsDevAuth(true);
      setActiveTab('developer');
    } else {
      setIsAuthModalOpen(true);
    }
  };

  const handleAuthSuccess = () => {
    setIsDevAuth(true);
    setActiveTab('developer');
  };

  const handleExitDevMode = () => {
    setActiveTab('verifier');
    setIsDevAuth(isAdminAuthenticated());
  };

  // If in Developer Mode, render Developer Portal
  if (activeTab === 'developer') {
    return <DeveloperPortal onExitDevMode={handleExitDevMode} />;
  }

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col font-sans selection:bg-blue-500/30 selection:text-blue-200">
      {/* User Navigation Header */}
      <UserHeader
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenDevPortal={handleOpenDevPortal}
        isDevAuth={isDevAuth}
      />

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-10">
        {activeTab === 'verifier' && <UserVerifier onSaveHistory={saveHistory} />}
        {activeTab === 'history' && (
          <UserHistory
            history={history}
            onSelectHistoryItem={handleSelectHistoryItem}
            onClearHistory={handleClearHistory}
            onDeleteHistoryItem={handleDeleteHistoryItem}
          />
        )}
        {activeTab === 'about' && <UserAbout />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-dark-950 py-6 text-slate-400 text-xs font-sans">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            <span className="font-semibold text-slate-300">IndicClaim</span>
            <span>— Multi-Source Fact Verification</span>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setActiveTab('about')}
              className="hover:text-slate-200 transition-colors"
            >
              Methodology
            </button>
            <button
              onClick={handleOpenDevPortal}
              className="flex items-center gap-1.5 text-slate-400 hover:text-indigo-400 transition-colors font-mono text-[11px]"
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Developer Portal</span>
            </button>
          </div>
        </div>
      </footer>

      {/* Developer Auth Modal */}
      <DeveloperAuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={handleAuthSuccess}
      />
    </div>
  );
}
