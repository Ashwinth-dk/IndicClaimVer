import React, { useState } from 'react';
import { 
  Activity, 
  Globe, 
  Cpu, 
  Database, 
  Terminal, 
  Layers, 
  LogOut, 
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  Menu,
  X
} from 'lucide-react';
import DeveloperDashboard from './DeveloperDashboard';
import DeveloperPipeline from './DeveloperPipeline';
import DeveloperTraining from './DeveloperTraining';
import DeveloperModels from './DeveloperModels';
import DeveloperDataset from './DeveloperDataset';
import DeveloperLogs from './DeveloperLogs';
import DeveloperArchitecture from './DeveloperArchitecture';
import { clearAdminKey } from '../services/api';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: Activity, desc: 'Overview & System Status' },
  { id: 'pipeline', label: 'Crawler & Pipeline', icon: Globe, desc: 'Automated Crawl & Train' },
  { id: 'training', label: 'Training & Quality', icon: Cpu, desc: 'Quality Gate & Class Balance' },
  { id: 'models', label: 'Models Registry', icon: Sparkles, desc: 'Checkpoints & Hot-Reload' },
  { id: 'dataset', label: 'Dataset & Evidence', icon: Database, desc: 'Repository & Review Queue' },
  { id: 'logs', label: 'System Logs', icon: Terminal, desc: 'Live Execution Stream' },
  { id: 'architecture', label: 'Architecture', icon: Layers, desc: 'Pipeline Internals' },
];

export default function DeveloperPortal({ onExitDevMode }) {
  const [activeSection, setActiveSection] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleLogout = () => {
    clearAdminKey();
    onExitDevMode && onExitDevMode();
  };

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col md:flex-row font-sans">
      {/* Mobile Top Bar */}
      <div className="md:hidden flex items-center justify-between p-4 border-b border-slate-800 bg-dark-900/90 sticky top-0 z-30">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-indigo-400" />
          <span className="font-mono font-bold text-sm text-white">IndicClaim DevPortal</span>
        </div>
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="p-2 rounded-xl bg-dark-950 border border-slate-800 text-slate-300"
        >
          {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Developer Sidebar */}
      <aside
        className={`w-full md:w-64 bg-dark-900/95 border-r border-slate-800/90 flex flex-col justify-between p-4 space-y-4 fixed md:sticky top-0 h-auto md:h-screen z-40 transition-transform ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="space-y-6">
          {/* Developer Header */}
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
                <Terminal className="w-4 h-4" />
              </div>
              <div>
                <span className="font-mono font-black text-sm text-white tracking-tight block">
                  Indic<span className="text-indigo-400">Claim</span> DEV
                </span>
                <span className="text-[10px] font-mono text-indigo-300 uppercase tracking-wider block">
                  Admin & Diagnostics
                </span>
              </div>
            </div>
          </div>

          {/* Nav List */}
          <nav className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeSection === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveSection(item.id);
                    setIsSidebarOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-mono transition-all text-left ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 font-bold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <div>
                    <span>{item.label}</span>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-slate-800 space-y-2">
          <button
            onClick={onExitDevMode}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-slate-850 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/60 text-xs font-mono transition-all"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to User App</span>
          </button>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 text-[11px] font-mono transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Lock Dev Session</span>
          </button>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 p-4 sm:p-8 max-w-7xl mx-auto overflow-y-auto w-full">
        {activeSection === 'dashboard' && <DeveloperDashboard onNavigate={setActiveSection} />}
        {activeSection === 'pipeline' && <DeveloperPipeline />}
        {activeSection === 'training' && <DeveloperTraining />}
        {activeSection === 'models' && <DeveloperModels />}
        {activeSection === 'dataset' && <DeveloperDataset />}
        {activeSection === 'logs' && <DeveloperLogs />}
        {activeSection === 'architecture' && <DeveloperArchitecture />}
      </main>
    </div>
  );
}
