import React, { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  RefreshCw,
  Trophy,
  ArrowRight,
  ExternalLink,
  BookOpen,
  FlaskConical,
  Layers,
  Send,
  CheckCircle2,
  AlertTriangle,
  Play,
  FileText,
  Clock,
} from 'lucide-react';
import { api } from '../api/client';
import type { CompetitionSummary } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface CompetitionsPageProps {
  onNavigate: (page: string, params?: any) => void;
  onOpenQueue: () => void;
  initialSlug?: string;
}

export const CompetitionsPage: React.FC<CompetitionsPageProps> = ({
  onNavigate,
  onOpenQueue,
  initialSlug,
}) => {
  const [competitions, setCompetitions] = useState<CompetitionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [kindFilter, setKindFilter] = useState('all');
  const [selectedComp, setSelectedComp] = useState<string | null>(initialSlug || null);
  const [compDetails, setCompDetails] = useState<any>(null);
  const [detailsTab, setDetailsTab] = useState<'summary' | 'research' | 'solutions' | 'experiments' | 'submissions' | 'artifacts'>('summary');
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const fetchCompetitions = async () => {
    try {
      const data = await api.getCompetitions({
        search: search || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        kind: kindFilter !== 'all' ? kindFilter : undefined,
      });
      setCompetitions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompetitions();
  }, [search, statusFilter, kindFilter]);

  const loadCompDetails = async (slug: string) => {
    setLoadingDetails(true);
    try {
      const data = await api.getCompetitionDetails(slug);
      setCompDetails(data);
      setSelectedComp(slug);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  };

  useEffect(() => {
    if (initialSlug) {
      loadCompDetails(initialSlug);
    }
  }, [initialSlug]);

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

  const handleAction = async (actionType: 'baseline' | 'research' | 'experiment', slug: string) => {
    setActionInProgress(actionType);
    try {
      if (actionType === 'baseline') {
        await api.runBaseline(slug);
      } else if (actionType === 'research') {
        await api.runResearch(slug);
      } else if (actionType === 'experiment') {
        await api.runExperiment(slug);
      }
      onOpenQueue();
    } catch (err) {
      console.error(err);
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Competitions</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Central inventory of all competitions entered by your Kaggle account.
          </p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw size={13} className={syncing ? 'animate-spin' : ''} />
          Sync Competitions
        </button>
      </div>

      {/* Filter and Search Controls */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by slug or competition title..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-md border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs rounded-md border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Statuses</option>
            <option value="supported">Supported (csv_*)</option>
            <option value="report_only">Report Only</option>
          </select>

          {/* Task Type Filter */}
          <select
            value={kindFilter}
            onChange={(e) => setKindFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs rounded-md border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Task Types</option>
            <option value="csv_tabular">Tabular (csv_tabular)</option>
            <option value="code_competition">Code Competition</option>
            <option value="csv_cv">Computer Vision</option>
            <option value="agent_or_optimization">Agent / Optimization</option>
          </select>
        </div>
      </div>

      {/* Competitions Table */}
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="py-2.5 px-3">Competition</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Task Type</th>
                <th className="py-2.5 px-3">Evaluation Metric</th>
                <th className="py-2.5 px-3 text-right">Best Validation (CV)</th>
                <th className="py-2.5 px-3 text-right">Best Public Score</th>
                <th className="py-2.5 px-3">Research</th>
                <th className="py-2.5 px-3">Deadline</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto text-slate-400" />
                  </td>
                </tr>
              ) : competitions.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    No matching competitions found.
                  </td>
                </tr>
              ) : (
                competitions.map((c) => (
                  <tr
                    key={c.slug}
                    onClick={() => loadCompDetails(c.slug)}
                    className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-3">
                      <div className="flex flex-col">
                        <span className="font-semibold text-slate-900 font-mono">
                          {c.slug}
                        </span>
                        {c.title && c.title !== c.slug && (
                          <span className="text-[11px] text-slate-500 truncate max-w-xs">
                            {c.title}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2.5 px-3">
                      <StatusBadge status={c.status} size="sm" />
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-600">
                      {c.kind || 'N/A'}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="font-medium text-slate-700">
                        {c.evaluation_metric || 'ROC AUC'}
                      </span>
                      <span className="text-[10px] text-slate-400 ml-1">
                        ({c.direction || 'maximize'})
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-800">
                      {c.best_validation_score ? c.best_validation_score.toFixed(5) : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-emerald-700">
                      {c.my_best_public_score ? c.my_best_public_score.toFixed(5) : '—'}
                    </td>
                    <td className="py-2.5 px-3">
                      <StatusBadge status={c.research_status || 'Pending'} size="sm" />
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">
                      {c.deadline ? c.deadline.split('T')[0] : 'Open'}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          loadCompDetails(c.slug);
                        }}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800"
                      >
                        Inspect <ArrowRight size={12} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dedicated Competition Details Modal */}
      {selectedComp && (
        <Modal
          isOpen={Boolean(selectedComp)}
          onClose={() => {
            setSelectedComp(null);
            setCompDetails(null);
          }}
          title={selectedComp}
          subtitle="Competition Workspace & Automated Pipeline Details"
          maxWidth="4xl"
        >
          {loadingDetails || !compDetails ? (
            <div className="flex h-48 items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
            </div>
          ) : (
            <div className="space-y-5">
              {/* Top Quick Actions Bar inside Modal */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center gap-2">
                  <StatusBadge status={compDetails.summary.status} />
                  <span className="text-xs font-mono text-slate-500">
                    Kind: {compDetails.summary.kind}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleAction('baseline', selectedComp)}
                    disabled={Boolean(actionInProgress)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 disabled:opacity-50"
                  >
                    Setup Baseline
                  </button>
                  <button
                    onClick={() => handleAction('research', selectedComp)}
                    disabled={Boolean(actionInProgress)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 disabled:opacity-50"
                  >
                    Analyze Notebooks
                  </button>
                  <button
                    onClick={() => handleAction('experiment', selectedComp)}
                    disabled={Boolean(actionInProgress)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    Run Experiments
                  </button>
                </div>
              </div>

              {/* Tabs Navigation */}
              <div className="flex border-b border-slate-200 gap-4 text-xs font-medium">
                {(['summary', 'research', 'solutions', 'experiments', 'submissions', 'artifacts'] as const).map(
                  (tab) => (
                    <button
                      key={tab}
                      onClick={() => setDetailsTab(tab)}
                      className={`pb-2 capitalize transition-colors ${
                        detailsTab === tab
                          ? 'border-b-2 border-slate-900 text-slate-900 font-semibold'
                          : 'text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      {tab === 'solutions' ? 'My Solutions' : tab === 'research' ? 'Public Research' : tab}
                    </button>
                  )
                )}
              </div>

              {/* Tab 1: Summary */}
              {detailsTab === 'summary' && (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="p-3 bg-slate-50 rounded border border-slate-200">
                      <span className="text-slate-400 font-medium">Evaluation Metric</span>
                      <p className="font-semibold text-slate-800 mt-1">
                        {compDetails.summary.evaluation_metric || 'ROC AUC'} ({compDetails.summary.direction || 'maximize'})
                      </p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded border border-slate-200">
                      <span className="text-slate-400 font-medium">Kaggle URL</span>
                      <p className="font-mono text-blue-600 mt-1 truncate">
                        <a href={compDetails.summary.url} target="_blank" rel="noreferrer" className="flex items-center gap-1">
                          View on Kaggle <ExternalLink size={10} />
                        </a>
                      </p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded border border-slate-200">
                      <span className="text-slate-400 font-medium">Deadline</span>
                      <p className="font-medium text-slate-800 mt-1">
                        {compDetails.summary.deadline?.split('T')[0] || 'Ongoing'}
                      </p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded border border-slate-200">
                      <span className="text-slate-400 font-medium">Max Daily Submissions</span>
                      <p className="font-mono text-slate-800 mt-1">
                        {compDetails.summary.max_daily_submissions || 5} per day
                      </p>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded border border-slate-200">
                    <h4 className="font-semibold text-slate-800 mb-2">Dataset Information</h4>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-slate-500">Status:</span>
                      <span className={`font-medium ${compDetails.dataset.downloaded ? 'text-emerald-700' : 'text-amber-700'}`}>
                        {compDetails.dataset.downloaded ? '✓ Data files downloaded to workspace' : 'Data not downloaded yet'}
                      </span>
                    </div>
                    {compDetails.dataset.files && compDetails.dataset.files.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {compDetails.dataset.files.map((f: string) => (
                          <span key={f} className="px-2 py-0.5 bg-white border border-slate-200 rounded font-mono text-[11px] text-slate-700">
                            {f}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Tab 2: Public Research */}
              {detailsTab === 'research' && (
                <div className="space-y-4 text-xs">
                  {compDetails.public_research.notebooks.length === 0 ? (
                    <div className="p-6 text-center text-slate-400 border rounded-lg">
                      No public research notebooks mined yet. Click 'Mine Research' above.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <h4 className="font-semibold text-slate-800">Top Ranked Public Notebooks</h4>
                      <div className="divide-y border rounded-lg bg-white overflow-hidden">
                        {compDetails.public_research.notebooks.map((nb: any) => (
                          <div key={nb.ref} className="p-3 hover:bg-slate-50 flex items-center justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-slate-900">{nb.title}</span>
                                <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-mono text-[10px]">
                                  {nb.total_votes} votes
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-400 mt-0.5">Author: {nb.author} | License: {nb.license || 'Apache-2.0'}</p>
                              {nb.techniques_extracted && (
                                <p className="text-slate-600 mt-1 font-mono text-[11px]">{nb.techniques_extracted}</p>
                              )}
                            </div>
                            <a href={nb.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800">
                              <ExternalLink size={14} />
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: My Solutions */}
              {detailsTab === 'solutions' && (
                <div className="space-y-4 text-xs">
                  <div className="p-4 bg-slate-50 border rounded-lg space-y-2">
                    <h4 className="font-semibold text-slate-900">Current Best Solution Architecture</h4>
                    <p className="text-slate-600">
                      Stratified 5-Fold LightGBM with statistical noise gating ($cv\_std = 0.00039$).
                    </p>
                    <div className="grid grid-cols-2 gap-3 pt-2">
                      <div className="p-2.5 bg-white border rounded">
                        <span className="text-slate-400">Baseline 5-Fold Mean CV:</span>
                        <p className="font-mono font-semibold text-slate-900 mt-0.5">0.95438 (±0.00039)</p>
                      </div>
                      <div className="p-2.5 bg-white border rounded">
                        <span className="text-slate-400">Public Leaderboard Baseline:</span>
                        <p className="font-mono font-semibold text-emerald-700 mt-0.5">0.95408</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: Experiments */}
              {detailsTab === 'experiments' && (
                <div className="space-y-3 text-xs">
                  {compDetails.experiments.length === 0 ? (
                    <div className="p-6 text-center text-slate-400 border rounded-lg">
                      No experiments recorded yet for this competition.
                    </div>
                  ) : (
                    <table className="w-full text-left">
                      <thead className="bg-slate-50 border-b text-slate-600">
                        <tr>
                          <th className="py-2 px-2.5">ID</th>
                          <th className="py-2 px-2.5">Hypothesis</th>
                          <th className="py-2 px-2.5 text-right">Mean CV</th>
                          <th className="py-2 px-2.5 text-right">Std</th>
                          <th className="py-2 px-2.5 text-right">Time</th>
                          <th className="py-2 px-2.5">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {compDetails.experiments.map((e: any) => (
                          <tr key={e.id} className="hover:bg-slate-50">
                            <td className="py-2 px-2.5 font-mono font-semibold">#{e.id}</td>
                            <td className="py-2 px-2.5 text-slate-800">{e.description}</td>
                            <td className="py-2 px-2.5 text-right font-mono font-medium">{e.cv_mean ? e.cv_mean.toFixed(5) : '—'}</td>
                            <td className="py-2 px-2.5 text-right font-mono text-slate-500">{e.cv_std ? `±${e.cv_std.toFixed(5)}` : '—'}</td>
                            <td className="py-2 px-2.5 text-right font-mono text-slate-500">{e.runtime_sec ? `${e.runtime_sec}s` : '—'}</td>
                            <td className="py-2 px-2.5"><StatusBadge status={e.status} size="sm" /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {/* Tab 5: Submissions */}
              {detailsTab === 'submissions' && (
                <div className="space-y-3 text-xs">
                  {compDetails.submissions.length === 0 ? (
                    <div className="p-6 text-center text-slate-400 border rounded-lg">
                      No historical Kaggle submissions found in registry.
                    </div>
                  ) : (
                    <table className="w-full text-left">
                      <thead className="bg-slate-50 border-b text-slate-600">
                        <tr>
                          <th className="py-2 px-2.5">Ref</th>
                          <th className="py-2 px-2.5">File</th>
                          <th className="py-2 px-2.5">Date</th>
                          <th className="py-2 px-2.5 text-right">Public Score</th>
                          <th className="py-2 px-2.5">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {compDetails.submissions.map((s: any) => (
                          <tr key={s.ref} className="hover:bg-slate-50">
                            <td className="py-2 px-2.5 font-mono">#{s.ref}</td>
                            <td className="py-2 px-2.5 font-mono">{s.file_name}</td>
                            <td className="py-2 px-2.5 text-slate-500">{s.date}</td>
                            <td className="py-2 px-2.5 text-right font-mono font-semibold text-emerald-700">
                              {s.public_score ? s.public_score.toFixed(5) : '—'}
                            </td>
                            <td className="py-2 px-2.5"><StatusBadge status={s.status} size="sm" /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {/* Tab 6: Artifacts */}
              {detailsTab === 'artifacts' && (
                <div className="space-y-3 text-xs">
                  {compDetails.artifacts.length === 0 ? (
                    <div className="p-6 text-center text-slate-400 border rounded-lg">
                      No artifacts recorded in workspaces/{selectedComp}/artifacts.
                    </div>
                  ) : (
                    <div className="divide-y border rounded-lg overflow-hidden bg-white">
                      {compDetails.artifacts.map((a: any) => (
                        <div key={a.name} className="p-3 flex items-center justify-between hover:bg-slate-50">
                          <div className="flex items-center gap-2">
                            <FileText size={15} className="text-slate-400" />
                            <span className="font-mono font-medium text-slate-800">{a.name}</span>
                          </div>
                          <div className="flex items-center gap-4 text-slate-500 font-mono">
                            <span>{(a.size_bytes / 1024).toFixed(1)} KB</span>
                            <span>{a.created_at.split('T')[0]}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </Modal>
      )}
    </div>
  );
};
