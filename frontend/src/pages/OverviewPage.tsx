import React, { useEffect, useState } from 'react';
import {
  RefreshCw,
  Search,
  Cpu,
  ArrowRight,
  FlaskConical,
  Trophy,
  Send,
  Wrench,
  CheckCircle2,
  ExternalLink,
  Tag,
  Shield,
  Layers,
} from 'lucide-react';
import { api } from '../api/client';
import type { OverviewMetrics, CompetitionSummary, ExperimentRecord, SubmissionRecord, QueueTask } from '../types';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';

interface OverviewPageProps {
  activeCompetition: string;
  onNavigate: (page: string, params?: any) => void;
  onOpenQueue: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  activeCompetition,
  onNavigate,
  onOpenQueue,
}) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [syncing, setSyncing] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const res = await api.getOverview(activeCompetition);
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, [activeCompetition]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.syncCompetitions();
      onOpenQueue();
    } catch (err) {
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  const handleAction = async (actionType: 'baseline' | 'research' | 'experiment') => {
    setActionInProgress(actionType);
    try {
      if (actionType === 'baseline') {
        await api.runBaseline(activeCompetition);
      } else if (actionType === 'research') {
        await api.runResearch(activeCompetition);
      } else if (actionType === 'experiment') {
        await api.runExperiment(activeCompetition);
      }
      onOpenQueue();
    } catch (err) {
      console.error(err);
    } finally {
      setActionInProgress(null);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  const target = data?.target_competition || {};
  const metrics = data?.metrics;
  const activeResearch = data?.active_research;
  const classifications = data?.classifications || {};
  const bestImp = metrics?.best_validation_improvement;

  const formatKindBadge = (kind?: string) => {
    if (kind === 'csv_tabular') return 'Tabular (Supported)';
    if (kind === 'code_competition') return 'Code Competition (Report Only)';
    if (kind === 'csv_cv') return 'Computer Vision (Report Only)';
    if (kind === 'agent_or_optimization') return 'Agent Simulation (Report Only)';
    return 'Custom Format (Report Only)';
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Overview</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Competition classification, active target monitoring, and submission performance.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw size={13} className={syncing ? 'animate-spin' : ''} />
            Sync Competitions
          </button>
          <button
            onClick={() => onNavigate('research', { slug: activeCompetition })}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition-colors"
          >
            <Search size={13} />
            Extract Research
          </button>
          <button
            onClick={onOpenQueue}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-sm transition-colors"
          >
            <Cpu size={13} />
            Execution Queue
          </button>
        </div>
      </div>

      {/* Competition Classification Breakdown Section */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Competition Inventory Classification
          </span>
          <button
            onClick={() => onNavigate('competitions')}
            className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            Browse in Competitions <ArrowRight size={12} />
          </button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-white rounded-lg border border-slate-200 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900">Tabular ML</span>
              <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono text-[10px] font-semibold">
                Supported
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Standard CSV data, automated baseline & keep/revert</p>
            <span className="text-xl font-bold font-mono text-slate-900 mt-2">
              {classifications.tabular?.count || 0} <span className="text-xs font-normal text-slate-400">competitions</span>
            </span>
          </div>

          <div className="p-3 bg-white rounded-lg border border-slate-200 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900">Code Competitions</span>
              <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-mono">
                Report Only
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Offline kernels, submission notebook evaluation</p>
            <span className="text-xl font-bold font-mono text-slate-900 mt-2">
              {classifications.code_competition?.count || 0} <span className="text-xs font-normal text-slate-400">competitions</span>
            </span>
          </div>

          <div className="p-3 bg-white rounded-lg border border-slate-200 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900">Agent Simulation</span>
              <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-mono">
                Report Only
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Game environments, reinforcement learning & math agents</p>
            <span className="text-xl font-bold font-mono text-slate-900 mt-2">
              {classifications.agent_simulation?.count || 0} <span className="text-xs font-normal text-slate-400">competitions</span>
            </span>
          </div>

          <div className="p-3 bg-white rounded-lg border border-slate-200 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900">Computer Vision</span>
              <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-mono">
                Report Only
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Image & volumetric CT segmentation datasets</p>
            <span className="text-xl font-bold font-mono text-slate-900 mt-2">
              {classifications.computer_vision?.count || 0} <span className="text-xs font-normal text-slate-400">competitions</span>
            </span>
          </div>
        </div>
      </div>

      {/* Target Competition Active Workbench Card */}
      <div className="p-4 bg-slate-50/80 rounded-xl border border-slate-200 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Active Target:
              </span>
              <h2 className="text-base font-bold text-slate-900">
                {target.title || target.slug}
              </h2>
              <span className="px-2 py-0.5 rounded bg-white border border-slate-200 font-mono text-[11px] text-slate-700">
                {target.slug}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Classification: <span className="font-medium text-slate-700">{formatKindBadge(target.kind)}</span> | Metric: <span className="font-medium text-slate-700">{target.metric}</span> ({target.direction})
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleAction('baseline')}
              disabled={Boolean(actionInProgress)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 disabled:opacity-50"
            >
              <Wrench size={13} />
              Setup Baseline
            </button>
            <button
              onClick={() => handleAction('research')}
              disabled={Boolean(actionInProgress)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 disabled:opacity-50"
            >
              <Search size={13} />
              Analyze Notebooks
            </button>
            <button
              onClick={() => handleAction('experiment')}
              disabled={Boolean(actionInProgress)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              <FlaskConical size={13} />
              Run Experiments
            </button>
          </div>
        </div>

        {/* Target Key Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
          <MetricCard
            label="My Best Leaderboard Score"
            value={target.best_public_score ? target.best_public_score.toFixed(5) : 'Not scored'}
            subValue="Verified on Kaggle"
            mono
          />
          <MetricCard
            label="Local 5-Fold Baseline (CV)"
            value={target.baseline_cv ? target.baseline_cv.toFixed(5) : 'Not run'}
            subValue={target.baseline_cv ? 'Stratified CV' : 'Click Setup Baseline'}
            mono
          />
          <MetricCard
            label="Target Experiments"
            value={metrics?.target_experiments_count ?? 0}
            subValue="Keep/revert trials"
            mono
          />
          <MetricCard
            label="Daily Submissions Quota"
            value={`${target.quota_remaining ?? 5} / ${target.daily_cap ?? 5}`}
            subValue="Remaining today"
            mono
          />
        </div>
      </div>

      {/* Active Research Banner (if running) */}
      {activeResearch && (
        <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
                <FlaskConical size={16} />
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-semibold text-slate-900">{activeResearch.name}</h3>
                  <StatusBadge status={activeResearch.stage} size="sm" />
                </div>
                <p className="text-xs text-slate-500 font-mono mt-0.5">
                  Target: {activeResearch.competition_slug} | {activeResearch.resource_allocation}
                </p>
              </div>
            </div>
            <button
              onClick={onOpenQueue}
              className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-800"
            >
              Open Queue Details <ArrowRight size={13} />
            </button>
          </div>
          {activeResearch.logs.length > 0 && (
            <div className="mt-3 bg-slate-900 text-slate-200 rounded p-2 text-xs font-mono truncate">
              {activeResearch.logs[activeResearch.logs.length - 1]}
            </div>
          )}
        </div>
      )}

      {/* Grid: Competition Activity & Target Experiments */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section: Competition Activity */}
        <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <div className="flex flex-wrap items-center gap-2">
              <Trophy size={16} className="text-slate-500" />
              <h2 className="text-sm font-semibold text-slate-900">Competition Activity</h2>
            </div>
            <button
              onClick={() => onNavigate('competitions')}
              className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              View all ({metrics?.joined_competitions ?? 0}) <ArrowRight size={12} />
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {(data?.recent_competitions || []).map((comp: any) => (
              <div
                key={comp.slug}
                onClick={() => onNavigate('competitions', { slug: comp.slug })}
                className="flex items-center justify-between p-3 hover:bg-slate-50/80 cursor-pointer transition-colors"
              >
                <div className="flex flex-col min-w-0 pr-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-slate-900 truncate">
                      {comp.title || comp.slug}
                    </span>
                    {comp.slug === activeCompetition && (
                      <span className="px-1.5 py-0.2 rounded bg-blue-100 text-blue-800 font-mono text-[9px] font-semibold">
                        Target
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {comp.slug} • {comp.evaluation_metric || 'ROC AUC'}
                  </span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right">
                    <div className="text-xs font-mono font-medium text-slate-800">
                      {comp.my_best_public_score ? comp.my_best_public_score.toFixed(5) : '—'}
                    </div>
                    <div className="text-[10px] text-slate-400 uppercase font-mono">Public Score</div>
                  </div>
                  <StatusBadge status={comp.status} size="sm" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Section: Target Recent Experiments */}
        <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <div className="flex flex-wrap items-center gap-2">
              <FlaskConical size={16} className="text-slate-500" />
              <h2 className="text-sm font-semibold text-slate-900">
                Experiments for {target.slug}
              </h2>
            </div>
            <button
              onClick={() => onNavigate('experiments')}
              className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              View all ({metrics?.experiments_completed ?? 0}) <ArrowRight size={12} />
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {(data?.recent_experiments || []).length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                No experiments recorded yet for {target.slug}. Click 'Run Experiments' above to execute iterations.
              </div>
            ) : (
              (data.recent_experiments || []).map((exp: any) => (
                <div
                  key={exp.id}
                  onClick={() => onNavigate('experiments', { expId: exp.id })}
                  className="flex items-center justify-between p-3 hover:bg-slate-50/80 cursor-pointer transition-colors"
                >
                  <div className="flex flex-col min-w-0 pr-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-mono font-semibold text-slate-700">
                        #{exp.id}
                      </span>
                      <span className="text-xs font-medium text-slate-900 truncate">
                        {exp.description || 'LightGBM baseline'}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 font-mono mt-0.5">
                      Hash: {exp.commit_hash?.substring(0, 7) || 'HEAD'} | Time: {exp.runtime_sec ? `${exp.runtime_sec}s` : '—'}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right">
                      <div className="text-xs font-mono font-medium text-slate-800">
                        {exp.cv_mean ? exp.cv_mean.toFixed(5) : '—'}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {exp.cv_std ? `±${exp.cv_std.toFixed(5)}` : '5-Fold'}
                      </div>
                    </div>
                    <StatusBadge status={exp.status} size="sm" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Section: Submissions */}
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
          <div className="flex flex-wrap items-center gap-2">
            <Send size={16} className="text-slate-500" />
            <h2 className="text-sm font-semibold text-slate-900">
              Leaderboard Submissions for {target.slug}
            </h2>
          </div>
          <button
            onClick={() => onNavigate('submissions')}
            className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            Submissions Workspace <ArrowRight size={12} />
          </button>
        </div>
        <div className="divide-y divide-slate-100">
          {(data?.recent_submissions || []).length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400">
              No submissions recorded yet for {target.slug}.
            </div>
          ) : (
            (data.recent_submissions || []).map((sub: any) => (
              <div
                key={sub.ref}
                className="flex items-center justify-between p-3 hover:bg-slate-50/80 transition-colors"
              >
                <div className="flex flex-col min-w-0 pr-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-mono font-semibold text-slate-700">
                      Ref #{sub.ref}
                    </span>
                    <span className="text-xs font-medium text-slate-900 truncate">
                      {sub.file_name}
                    </span>
                    {sub.is_baseline ? (
                      <span className="px-1.5 py-0.2 rounded bg-slate-100 text-[10px] font-mono text-slate-600">
                        Baseline
                      </span>
                    ) : null}
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {sub.description || 'Kaggle submission'} | Date: {sub.date || 'Today'}
                  </span>
                </div>
                <div className="flex items-center gap-4 shrink-0">
                  <div className="text-right">
                    <div className="text-xs font-mono font-semibold text-emerald-700">
                      {sub.public_score ? sub.public_score.toFixed(5) : 'Pending'}
                    </div>
                    <div className="text-[10px] text-slate-400 uppercase font-mono">Public Score</div>
                  </div>
                  <StatusBadge status={sub.status || 'Scored'} size="sm" />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
