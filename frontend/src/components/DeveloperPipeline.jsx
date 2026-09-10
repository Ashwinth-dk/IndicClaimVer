import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Square, 
  RotateCw, 
  Sparkles, 
  Cpu, 
  Database, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Layers, 
  Clock, 
  Check, 
  Loader2, 
  ShieldCheck, 
  Filter, 
  Globe, 
  Activity, 
  TrendingUp, 
  Terminal,
  Info
} from 'lucide-react';
import { startCrawlPipeline, getCrawlStatus, stopCrawlPipeline, getCrawlHistory, getActiveModelInfo } from '../services/api';

const PIPELINE_STAGES = [
  { id: 'CRAWLING', label: '1. Web Crawling', desc: 'Fetching articles from authoritative sources', icon: Globe },
  { id: 'PROCESSING', label: '2. Extraction & Cleaning', desc: 'Extracting factual claims, normalizing evidence', icon: Filter },
  { id: 'DATASET_BUILDING', label: '3. Dataset Consolidation', desc: 'Deduplicating and accumulating into canonical pool', icon: Database },
  { id: 'DATA_QUALITY_VALIDATION', label: '4. Quality Gate', desc: '10-point check: count, balance, leaks, validity', icon: ShieldCheck },
  { id: 'MU_RIL_TRAINING', label: '5. MuRIL Fine-Tuning', desc: 'Automatic training if Quality Gate passes', icon: Cpu },
  { id: 'MODEL_EVALUATION', label: '6. Model Evaluation', desc: 'Computing test accuracy and F1 safety thresholds', icon: TrendingUp },
  { id: 'MODEL_ACTIVATION', label: '7. Model Activation', desc: 'Activating version & hot-reloading inference', icon: Sparkles },
];

export default function DeveloperPipeline() {
  const [topic, setTopic] = useState('COVID vaccination mandatory domestic flights India');
  const [targetCount, setTargetCount] = useState(100);
  const [epochs, setEpochs] = useState(3);
  const [batchSize, setBatchSize] = useState(8);
  const [learningRate, setLearningRate] = useState(2e-5);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [statusData, setStatusData] = useState(null);
  const [activeModel, setActiveModel] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const PRESET_TOPICS = [
    'COVID vaccination mandatory domestic flights India',
    'Karnataka High Court murder conviction set aside eyewitness',
    'Ministry of Health vaccine guidelines India',
    'Supreme Court bail reform guidelines PMLA',
    'ISRO Chandrayaan mission launch announcements',
    'RBI repo rate inflation decision',
  ];

  const refreshStatus = async () => {
    try {
      const data = await getCrawlStatus();
      setStatusData(data);
    } catch (e) {
      console.warn('Failed to fetch pipeline status:', e);
    }
  };

  const refreshMetaAndHistory = async () => {
    try {
      const [modelMeta, hist] = await Promise.all([
        getActiveModelInfo(),
        getCrawlHistory()
      ]);
      setActiveModel(modelMeta);
      setHistory(hist || []);
    } catch (e) {
      console.warn('Failed to fetch history or model meta:', e);
    }
  };

  useEffect(() => {
    refreshStatus();
    refreshMetaAndHistory();
    const interval = setInterval(() => {
      refreshStatus();
      if (!statusData?.is_running) {
        refreshMetaAndHistory();
      }
    }, statusData?.is_running ? 1500 : 5000);
    return () => clearInterval(interval);
  }, [statusData?.is_running]);

  const handleStartPipeline = async (e) => {
    e?.preventDefault();
    if (!topic.trim()) return;
    setErrorMsg('');
    setLoading(true);

    try {
      await startCrawlPipeline({
        topic: topic.trim(),
        target_count: parseInt(targetCount, 10) || 100,
        auto_train: true, // Backend automatically executes Quality Gate -> Training -> Evaluation -> Activation
        epochs: parseInt(epochs, 10) || 3,
        batch_size: parseInt(batchSize, 10) || 8,
        learning_rate: parseFloat(learningRate) || 2e-5,
      });
      await refreshStatus();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to start automated pipeline');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      await stopCrawlPipeline();
      await refreshStatus();
    } catch (err) {
      alert(`Stop error: ${err.message}`);
    }
  };

  const isRunning = statusData?.is_running;
  const currentStage = statusData?.stage || 'QUEUED';
  const crawlStatus = statusData?.crawl_status || {};
  const trainResult = statusData?.training_result || {};
  const isTrainingSkipped = trainResult?.training_status === 'SKIPPED' || trainResult?.status === 'skipped' || currentStage === 'TRAINING_SKIPPED';
  const isModelActivated = trainResult?.training_status === 'ACTIVATED' || trainResult?.status === 'activated';

  // Compute stage status index
  const stageIndexMap = {
    QUEUED: 0,
    CRAWLING: 0,
    PROCESSING: 1,
    DATASET_BUILDING: 2,
    DATA_QUALITY_VALIDATION: 3,
    MU_RIL_TRAINING: 4,
    MODEL_EVALUATION: 5,
    MODEL_ACTIVATION: 6,
    TRAINING_SKIPPED: 3,
    COMPLETED: 7,
    FAILED: -1,
    STOPPED: -1,
  };

  const currentIdx = stageIndexMap[currentStage] ?? 0;

  return (
    <div className="space-y-6 text-slate-100 font-sans">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-blue-950/40 via-dark-900 to-indigo-950/40 border border-blue-900/40 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <h1 className="text-xl sm:text-2xl font-black font-mono tracking-tight text-white">
              Automated Crawler & MuRIL Fine-Tuning Pipeline
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 font-sans">
            Single Entry Point: START CRAWL triggers async crawl $\rightarrow$ extraction $\rightarrow$ quality gate $\rightarrow$ auto training $\rightarrow$ evaluation $\rightarrow$ hot-reloaded activation.
          </p>
        </div>

        {/* Active Model Badge */}
        <div className="flex items-center gap-3 bg-dark-950/80 px-4 py-2.5 rounded-xl border border-slate-800 self-start md:self-auto">
          <Cpu className="w-4 h-4 text-emerald-400" />
          <div className="text-xs">
            <span className="text-slate-400 block text-[10px] uppercase font-mono tracking-wider">Active Model</span>
            <span className="font-mono font-bold text-emerald-300">
              {activeModel?.active_version ? `MuRIL (${activeModel.active_version})` : 'MuRIL Baseline'}
            </span>
          </div>
        </div>
      </div>

      {/* Input Control Card */}
      <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800/80 backdrop-blur-sm space-y-4">
        <form onSubmit={handleStartPipeline} className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 flex items-center justify-between">
              <span>Target Topic / Search Query</span>
              <span className="text-[11px] text-blue-400 normal-case font-sans">Topic-aware multi-source crawl</span>
            </label>
            <div className="relative">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. COVID vaccination mandatory domestic flights India"
                disabled={isRunning}
                className="w-full px-4 py-3 rounded-xl bg-dark-950 border border-slate-700/80 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-slate-100 text-sm font-sans transition-all disabled:opacity-60"
              />
            </div>
          </div>

          {/* Preset Pill Suggestions */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-mono text-slate-400">Suggestions:</span>
            {PRESET_TOPICS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                disabled={isRunning}
                onClick={() => setTopic(preset)}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/70 hover:bg-blue-900/40 text-slate-300 hover:text-blue-200 border border-slate-700/60 hover:border-blue-500/30 transition-all font-sans"
              >
                {preset}
              </button>
            ))}
          </div>

          {/* Advanced Hyperparameters Toggle */}
          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-[11px] font-mono text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              <span>{showAdvanced ? '▼ Hide Training Hyperparameters' : '▶ Show Training Hyperparameters'}</span>
            </button>

            {showAdvanced && (
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-3 mt-2 border-t border-slate-800">
                <div className="space-y-1">
                  <label className="text-[11px] font-mono text-slate-400">Target Examples</label>
                  <input
                    type="number"
                    min="10"
                    max="2000"
                    value={targetCount}
                    onChange={(e) => setTargetCount(e.target.value)}
                    disabled={isRunning}
                    className="w-full px-3 py-2 rounded-lg bg-dark-950 border border-slate-800 text-xs font-mono text-slate-200"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-mono text-slate-400">Fine-Tuning Epochs</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={epochs}
                    onChange={(e) => setEpochs(e.target.value)}
                    disabled={isRunning}
                    className="w-full px-3 py-2 rounded-lg bg-dark-950 border border-slate-800 text-xs font-mono text-slate-200"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-mono text-slate-400">Batch Size</label>
                  <input
                    type="number"
                    min="1"
                    max="64"
                    value={batchSize}
                    onChange={(e) => setBatchSize(e.target.value)}
                    disabled={isRunning}
                    className="w-full px-3 py-2 rounded-lg bg-dark-950 border border-slate-800 text-xs font-mono text-slate-200"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-mono text-slate-400">Learning Rate</label>
                  <input
                    type="text"
                    value={learningRate}
                    onChange={(e) => setLearningRate(e.target.value)}
                    disabled={isRunning}
                    className="w-full px-3 py-2 rounded-lg bg-dark-950 border border-slate-800 text-xs font-mono text-slate-200"
                  />
                </div>
              </div>
            )}
          </div>

          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-3 pt-2">
            {!isRunning ? (
              <button
                type="submit"
                disabled={loading || !topic.trim()}
                className="flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-indigo-500 text-white font-mono font-bold text-sm uppercase tracking-wider shadow-lg shadow-blue-500/25 transition-all active:scale-98 disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5 fill-current" />}
                <span>START PIPELINE</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleStop}
                className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 font-mono font-bold text-xs uppercase tracking-wider transition-all active:scale-98"
              >
                <Square className="w-4 h-4 fill-current" />
                <span>STOP PIPELINE</span>
              </button>
            )}

            <button
              type="button"
              onClick={refreshStatus}
              className="p-3.5 rounded-xl bg-dark-950 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-colors"
              title="Refresh Pipeline Status"
            >
              <RotateCw className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>

      {/* Quality Gate / Pipeline Status Notification Banner */}
      {isTrainingSkipped && (
        <div className="p-4 rounded-2xl bg-amber-950/30 border border-amber-500/40 text-amber-200 text-xs space-y-1">
          <div className="flex items-center gap-2 font-mono font-bold uppercase tracking-wider text-amber-300">
            <Info className="w-4 h-4" />
            <span>Training Skipped — Quality Gate Enforced</span>
          </div>
          <p className="font-sans text-amber-200/90">
            Training skipped — insufficient reliable training data ({trainResult?.reason || 'Quality gate requirements not met'}). Active model ({trainResult?.active_model || activeModel?.active_version || 'baseline'}) preserved safely.
          </p>
        </div>
      )}

      {isModelActivated && (
        <div className="p-4 rounded-2xl bg-emerald-950/30 border border-emerald-500/40 text-emerald-200 text-xs space-y-1">
          <div className="flex items-center gap-2 font-mono font-bold uppercase tracking-wider text-emerald-300">
            <CheckCircle2 className="w-4 h-4" />
            <span>New MuRIL Model Activated Successfully!</span>
          </div>
          <p className="font-sans text-emerald-200/90">
            Model version <strong>{trainResult.version}</strong> passed all evaluation criteria (Test Accuracy: {Math.round((trainResult.metrics?.test_accuracy || 0) * 100)}%) and is now the live active verification model.
          </p>
        </div>
      )}

      {/* 7-Stage Pipeline Visualizer */}
      <div className="p-5 rounded-2xl bg-dark-900/70 border border-slate-800/80 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-slate-300 font-semibold">
            <Activity className="w-4 h-4 text-blue-400" />
            <span>Automated 7-Stage Execution Flow</span>
          </div>
          <div className="font-mono text-xs text-slate-400">
            Stage: <span className="text-blue-400 font-bold">{currentStage}</span>
          </div>
        </div>

        {/* Stage Progress Tracker */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2.5">
          {PIPELINE_STAGES.map((st, idx) => {
            let isCompleted = false;
            let isActive = false;
            let isSkipped = false;

            if (idx <= 3) {
              if (currentStage === 'COMPLETED' || currentIdx > idx) {
                isCompleted = true;
              } else if (isRunning && currentIdx === idx) {
                isActive = true;
              }
            } else {
              if (isTrainingSkipped) {
                isSkipped = true;
              } else if (isModelActivated && currentStage === 'COMPLETED') {
                isCompleted = true;
              } else if (currentIdx > idx && currentStage !== 'FAILED') {
                isCompleted = true;
              } else if (isRunning && currentIdx === idx) {
                isActive = true;
              }
            }

            const Icon = st.icon;

            let cardBg = 'bg-dark-950/60 border-slate-800/80 text-slate-400';
            let iconBg = 'bg-slate-800/60 text-slate-400';

            if (isCompleted) {
              cardBg = 'bg-blue-950/20 border-blue-500/30 text-slate-200';
              iconBg = 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
            } else if (isActive) {
              cardBg = 'bg-blue-900/30 border-blue-400/60 text-blue-100 shadow-glow-blue animate-pulse-subtle';
              iconBg = 'bg-blue-500/30 text-blue-300 border border-blue-400/40';
            } else if (isSkipped) {
              cardBg = 'bg-amber-950/10 border-amber-500/20 text-slate-400';
              iconBg = 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
            }

            return (
              <div
                key={st.id}
                className={`p-3 rounded-xl border flex flex-col justify-between space-y-2 transition-all ${cardBg}`}
              >
                <div className="flex items-start justify-between gap-1">
                  <div className={`p-1.5 rounded-lg ${iconBg}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="font-mono text-[10px] text-slate-400">#{idx + 1}</span>
                </div>

                <div>
                  <h4 className="text-xs font-mono font-bold text-slate-100">{st.label}</h4>
                  <p className="text-[10px] text-slate-400 mt-0.5 line-clamp-2">{st.desc}</p>
                </div>

                <div className="pt-1 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono">
                  <span className="text-slate-400">Status:</span>
                  {isCompleted ? (
                    <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                      <Check className="w-3 h-3" />
                      <span>Done</span>
                    </span>
                  ) : isActive ? (
                    <span className="flex items-center gap-1 text-blue-300 font-semibold">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      <span>Active</span>
                    </span>
                  ) : isSkipped ? (
                    <span className="text-amber-400 font-semibold">Skipped</span>
                  ) : (
                    <span className="text-slate-400">Queued</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Live Details Sub-banner */}
        <div className="p-3 rounded-xl bg-dark-950/80 border border-slate-800 text-xs font-mono flex items-center justify-between text-slate-300">
          <span className="truncate max-w-xl">
            <strong className="text-blue-400">Details:</strong> {statusData?.stage_details || 'Ready to start'}
          </span>
          {statusData?.started_at && (
            <span className="text-[11px] text-slate-400 font-sans flex items-center gap-1">
              <Clock className="w-3 h-3" /> Started: {new Date(statusData.started_at).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Live Telemetry & Quality Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 rounded-xl bg-dark-900/60 border border-slate-800/80 space-y-1">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Pages Crawled</div>
          <div className="text-xl font-bold font-mono text-blue-400">
            {crawlStatus.urls_crawled ?? 0}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-dark-900/60 border border-slate-800/80 space-y-1">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Evidence Candidates</div>
          <div className="text-xl font-bold font-mono text-indigo-400">
            {crawlStatus.evidence_candidates ?? crawlStatus.collected_count ?? 0}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-dark-900/60 border border-slate-800/80 space-y-1">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Training Items</div>
          <div className="text-xl font-bold font-mono text-teal-400">
            {crawlStatus.collected_count ?? 0}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-dark-900/60 border border-slate-800/80 space-y-1">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Class Breakdown</div>
          <div className="text-sm font-bold font-mono flex items-center gap-1.5 pt-1">
            <span className="text-emerald-400">S:{crawlStatus.supports_count ?? 0}</span>
            <span className="text-slate-400">/</span>
            <span className="text-rose-400">R:{crawlStatus.refutes_count ?? 0}</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-dark-900/60 border border-slate-800/80 space-y-1">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Rejected Records</div>
          <div className="text-xl font-bold font-mono text-amber-400">
            {crawlStatus.rejected_count ?? 0}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-dark-900/60 border border-slate-800/80 space-y-1">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Active Checkpoint</div>
          <div className="text-sm font-bold font-mono text-purple-300 truncate pt-1">
            {activeModel?.active_version || 'baseline'}
          </div>
        </div>
      </div>

      {/* Live Terminal Logs */}
      {crawlStatus.logs && crawlStatus.logs.length > 0 && (
        <div className="p-4 rounded-2xl bg-black/90 border border-slate-800 space-y-2 font-mono text-xs">
          <div className="flex items-center justify-between text-slate-400 pb-1 border-b border-slate-800">
            <span className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-slate-300">
              <Terminal className="w-3.5 h-3.5 text-blue-400" />
              Live Execution Stream
            </span>
            <span className="text-[10px] text-slate-400">{crawlStatus.logs.length} entries</span>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-1 font-mono text-[11px] pr-1">
            {crawlStatus.logs.map((l, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-slate-400 flex-shrink-0">[{l.timestamp}]</span>
                <span className={
                  l.level === 'SUCCESS' ? 'text-emerald-400' :
                  l.level === 'WARN' ? 'text-amber-400' :
                  l.level === 'ERROR' ? 'text-rose-400' : 'text-slate-300'
                }>
                  {l.message}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
