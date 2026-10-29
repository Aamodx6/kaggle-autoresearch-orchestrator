import React, { useEffect, useState } from 'react';
import {
  RefreshCw,
  Search,
  Cpu,
  ArrowRight,
  TrendingUp,
  FlaskConical,
  Trophy,
  Send,
  AlertCircle,
  Play,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../api/client';
import type { OverviewMetrics, CompetitionSummary, ExperimentRecord, SubmissionRecord, QueueTask } from '../types';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';

interface OverviewPageProps {
  onNavigate: (page: string, params?: any) => void;
  onOpenQueue: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigate, onOpenQueue }) => {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<OverviewMetrics | null>(null);
  const [activeResearch, setActiveResearch] = useState<QueueTask | null>(null);
  const [competitions, setCompetitions] = useState<CompetitionSummary[]>([]);
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [submissions, setSubmissions] = useState<SubmissionRecord[]>([]);
  const [syncing, setSyncing] = useState(false);

  const loadData = async () => {
    try {
      const data = await api.getOverview();
      setMetrics(data.metrics);
      setActiveResearch(data.active_research);
      setCompetitions(data.recent_competitions);
      setExperiments(data.recent_experiments);
      setSubmissions(data.recent_submissions);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

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

  if (loading && !metrics) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  const bestImp = metrics?.best_validation_improvement;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Overview</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Monitor competitions, experiments, and submission performance.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw size={13} className={syncing ? 'animate-spin' : ''} />
            Sync Competitions
          </button>
          <button
            onClick={() => onNavigate('research', { slug: 'playground-series-s6e2' })}
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
            View Execution Queue
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <MetricCard
          label="Joined Competitions"
          value={metrics?.joined_competitions ?? 0}
          subValue={`${metrics?.supported_competitions ?? 0} tabular supported`}
        />
        <MetricCard
          label="Active Research Runs"
          value={metrics?.active_research_runs ?? 0}
          subValue={metrics?.active_research_runs ? 'Processing task' : 'Queue idle'}
        />
        <MetricCard
          label="Experiments Completed"
          value={metrics?.experiments_completed ?? 0}
          subValue="Audited in results.tsv"
          mono
        />
        <MetricCard
          label="Best Validation (CV)"
          value={bestImp ? `${bestImp.current_value.toFixed(5)}` : 'N/A'}
          mono
          delta={
            bestImp
              ? {
                  value: `${bestImp.delta >= 0 ? '+' : ''}${bestImp.delta.toFixed(5)}`,
                  positive: bestImp.delta > 0,
                  label: bestImp.metric_name,
                }
              : undefined
          }
          subValue={bestImp ? `Baseline: ${bestImp.original_value.toFixed(5)}` : undefined}
        />
        <MetricCard
          label="Pending Submissions"
          value={`${metrics?.pending_submissions ?? 5} / ${metrics?.daily_cap ?? 5}`}
          subValue="Daily quota remaining"
          mono
        />
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
                <div className="flex items-center gap-2">
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

      {/* Grid: Competitions Activity & Experiments */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section: Competition Activity */}
        <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
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
            {competitions.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">No competitions found.</div>
            ) : (
              competitions.map((comp) => (
                <div
                  key={comp.slug}
                  onClick={() => onNavigate('competitions', { slug: comp.slug })}
                  className="flex items-center justify-between p-3 hover:bg-slate-50/80 cursor-pointer transition-colors"
                >
                  <div className="flex flex-col min-w-0 pr-4">
                    <span className="text-xs font-semibold text-slate-900 truncate">
                      {comp.title || comp.slug}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {comp.slug} • {comp.evaluation_metric || 'ROC AUC'}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right">
                      <div className="text-xs font-mono font-medium text-slate-800">
                        {comp.my_best_public_score ? comp.my_best_public_score.toFixed(5) : '—'}
                      </div>
                      <div className="text-[10px] text-slate-400 uppercase">Public Score</div>
                    </div>
                    <StatusBadge status={comp.status} size="sm" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Section: Recent Experiments */}
        <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <FlaskConical size={16} className="text-slate-500" />
              <h2 className="text-sm font-semibold text-slate-900">Recent Experiments</h2>
            </div>
            <button
              onClick={() => onNavigate('experiments')}
              className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              View all ({metrics?.experiments_completed ?? 0}) <ArrowRight size={12} />
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {experiments.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">
                No experiments recorded yet. Click 'AutoResearch Loop' to start.
              </div>
            ) : (
              experiments.map((exp) => (
                <div
                  key={exp.id}
                  onClick={() => onNavigate('experiments', { expId: exp.id })}
                  className="flex items-center justify-between p-3 hover:bg-slate-50/80 cursor-pointer transition-colors"
                >
                  <div className="flex flex-col min-w-0 pr-4">
                    <div className="flex items-center gap-2">
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

      {/* Section: Recent Submissions */}
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Send size={16} className="text-slate-500" />
            <h2 className="text-sm font-semibold text-slate-900">Recent Leaderboard Submissions</h2>
          </div>
          <button
            onClick={() => onNavigate('submissions')}
            className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            View Submissions <ArrowRight size={12} />
          </button>
        </div>
        <div className="divide-y divide-slate-100">
          {submissions.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-400">No submissions recorded yet.</div>
          ) : (
            submissions.map((sub) => (
              <div
                key={sub.ref}
                className="flex items-center justify-between p-3 hover:bg-slate-50/80 transition-colors"
              >
                <div className="flex flex-col min-w-0 pr-4">
                  <div className="flex items-center gap-2">
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
                    <div className="text-[10px] text-slate-400 uppercase">Public Score</div>
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
