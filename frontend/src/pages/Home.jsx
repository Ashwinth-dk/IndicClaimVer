import React, { useState, useEffect } from 'react';
import { Menu, Sparkles, ShieldCheck, RefreshCw } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';
import { verifyClaim, getHealthStatus } from '../services/api';

const STORAGE_KEY = 'indicclaimver_history_v1';

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeClaim, setActiveClaim] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [history, setHistory] = useState([]);
  const [healthStatus, setHealthStatus] = useState({ connected: false, evidence_count: 0 });

  // Load history from localStorage on initial render
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        setHistory(JSON.parse(saved));
      }
    } catch (e) {
      console.warn('Failed to parse history from localStorage', e);
    }
  }, []);

  // Sync history to localStorage
  const saveHistory = (newHistory) => {
    setHistory(newHistory);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
    } catch (e) {
      console.warn('Failed to save history to localStorage', e);
    }
  };

  // Poll Backend Health Status
  const checkHealth = async () => {
    const status = await getHealthStatus();
    setHealthStatus(status);
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Start a fresh verification session
  const handleNewVerification = () => {
    setMessages([]);
    setActiveClaim('');
    setInputValue('');
  };

  // Select a suggestion or history item
  const handleSelectExample = (text) => {
    setInputValue(text);
  };

  const handleSelectHistoryItem = (item) => {
    // Reconstruct message stream from history record
    setMessages([
      {
        id: `user-${item.id}`,
        role: 'user',
        content: item.claim,
        timestamp: item.timestamp,
      },
      {
        id: `assistant-${item.id}`,
        role: 'assistant',
        data: item.data,
        timestamp: item.timestamp,
      },
    ]);
  };

  const handleClearHistory = () => {
    saveHistory([]);
  };

  const handleDeleteHistoryItem = (id) => {
    const updated = history.filter((item, idx) => (item.id || idx) !== id);
    saveHistory(updated);
  };

  // Primary verification submission handler
  const handleSendMessage = async (claimText) => {
    if (!claimText || isLoading) return;

    const queryId = Date.now().toString();
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // 1. Add User Claim to Message Stream
    const userMsg = {
      id: `user-${queryId}`,
      role: 'user',
      content: claimText,
      timestamp,
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setActiveClaim(claimText);
    setInputValue('');

    try {
      // 2. Call FastAPI Backend Verification Endpoint
      const responseData = await verifyClaim(claimText);

      // 3. Add Assistant Verification Response
      const assistantMsg = {
        id: `assistant-${queryId}`,
        role: 'assistant',
        data: responseData,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // 4. Record to History
      const historyRecord = {
        id: queryId,
        claim: claimText,
        verdict: responseData.verdict,
        confidence: responseData.confidence,
        timestamp,
        data: responseData,
      };

      saveHistory([historyRecord, ...history.slice(0, 49)]); // Keep last 50
    } catch (error) {
      console.error('Verification error:', error);
      const errorMsg = {
        id: `error-${queryId}`,
        role: 'assistant',
        isError: true,
        content: error.message || 'An unexpected error occurred during verification.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setActiveClaim('');
    }
  };

  return (
    <div className="flex h-screen bg-dark-950 text-slate-100 overflow-hidden">
      {/* Left Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onNewVerification={handleNewVerification}
        history={history}
        onSelectHistoryItem={handleSelectHistoryItem}
        onClearHistory={handleClearHistory}
        onDeleteHistoryItem={handleDeleteHistoryItem}
        healthStatus={healthStatus}
      />

      {/* Main Chat Interface */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Top Navbar */}
        <header className="h-14 border-b border-slate-800/80 bg-dark-900/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between flex-shrink-0 z-20">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              aria-label="Open sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <span className="font-mono font-bold text-sm tracking-tight text-white hidden sm:inline">
                IndicClaimVer
              </span>
              <span className="text-xs text-slate-400 hidden sm:inline">•</span>
              <span className="text-xs text-slate-400 truncate max-w-xs sm:max-w-md">
                AI Evidence Retrieval & MuRIL Verification
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick API status indicator on top bar */}
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] font-mono">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  healthStatus.connected ? 'bg-emerald-400' : 'bg-rose-400'
                }`}
              />
              <span className="text-slate-400 hidden sm:inline">Backend:</span>
              <span className={healthStatus.connected ? 'text-emerald-400' : 'text-rose-400'}>
                {healthStatus.connected ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        </header>

        {/* Chat Feed */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          activeClaim={activeClaim}
          onSelectExample={handleSelectExample}
        />

        {/* Bottom Fixed Chat Input */}
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          initialValue={inputValue}
        />
      </div>
    </div>
  );
}
