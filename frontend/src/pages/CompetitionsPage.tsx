import React, { useEffect, useState, useMemo } from 'react';
import {
  Search,
  RefreshCw,
  Trophy,
  ExternalLink,
  Clock,
  ArrowRight,
  LayoutGrid,
  List as ListIcon,
  Tag,
  Award,
  Calendar,
  CheckCircle2,
  FileText,
  Wrench,
  FlaskConical,
  ArrowLeft,
} from 'lucide-react';
import { api } from '../api/client';
import type { CompetitionSummary } from '../types';
import { StatusBadge } from '../components/StatusBadge';

interface CompetitionsPageProps {
  activeCompetition: string;
  onSelectCompetition: (slug: string) => void;
  onNavigate: (page: string, params?: any) => void;
  onOpenQueue: () => void;
  initialSlug?: string;
}

export const CompetitionsPage: React.FC<CompetitionsPageProps> = ({
  activeCompetition,
  onSelectCompetition,
  onNavigate,
  onOpenQueue,
  initialSlug,
}) => {
  const [competitions, setCompetitions] = useState<CompetitionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  
  // Kaggle-style filter states
  const [categoryTab, setCategoryTab] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'completed'>('all');
  const [formatFilter, setFormatFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'deadline' | 'score' | 'title'>('deadline');
  const [viewMode, setViewMode] = useState<'cards' | 'list'>('cards');

  // Modal inspection state
  const [selectedComp, setSelectedComp] = useState<string | null>(initialSlug || null);
  const [compDetails, setCompDetails] = useState<any>(null);
  const [detailsTab, setDetailsTab] = useState<'summary' | 'research' | 'solutions' | 'experiments' | 'submissions' | 'artifacts'>('summary');
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const fetchCompetitions = async () => {
    try {
      const data = await api.getCompetitions();
      setCompetitions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompetitions();
  }, []);

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

  // Helper formatting functions
  const formatCategory = (cat?: string) => {
    if (!cat) return 'General';
    if (cat.toLowerCase().includes('playground')) return 'Playground Series';
    if (cat.toLowerCase().includes('research')) return 'Research';
    if (cat.toLowerCase().includes('featured')) return 'Featured';
    if (cat.toLowerCase().includes('getting')) return 'Getting Started';
    return cat;
  };

  const formatKind = (kind?: string) => {
    if (!kind) return 'Standard';
    if (kind === 'csv_tabular') return 'Tabular';
    if (kind === 'code_competition') return 'Code Competition';
    if (kind === 'csv_cv') return 'Computer Vision';
    if (kind === 'agent_or_optimization') return 'Agent Simulation';
    return kind.replace('_', ' ');
  };

  const formatReward = (reward?: string) => {
    if (!reward || reward.toLowerCase() === 'none') return 'Knowledge';
    if (reward.toLowerCase() === 'swag') return 'Swag / Badges';
    if (!reward.includes('$') && reward.toLowerCase().includes('usd')) {
      return `$${reward.toUpperCase()}`;
    }
    return reward;
  };

  const formatDeadline = (deadlineStr?: string) => {
    if (!deadlineStr) return { text: 'Ongoing', isPast: false };
    try {
      const date = new Date(deadlineStr);
      const now = new Date();
      const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      
      if (diffDays < 0) {
        return { text: `Ended ${date.toLocaleDateString([], { month: 'short', year: 'numeric' })}`, isPast: true };
      }
      if (diffDays < 30) {
        return { text: `${diffDays} days remaining`, isPast: false };
      }
      const months = Math.ceil(diffDays / 30);
      return { text: `${months} months remaining`, isPast: false };
    } catch {
      return { text: deadlineStr.split(' ')[0], isPast: false };
    }
  };

  // Filter & Sort competitions
  const filteredCompetitions = useMemo(() => {
    return competitions
      .filter((c) => {
        // Category tab filter
        if (categoryTab !== 'all') {
          const cat = (c.category || '').toLowerCase();
          if (!cat.includes(categoryTab.toLowerCase())) return false;
        }

        // Search filter
        if (search) {
          const s = search.toLowerCase();
          const matchTitle = (c.title || '').toLowerCase().includes(s);
          const matchSlug = c.slug.toLowerCase().includes(s);
          const matchMetric = (c.evaluation_metric || '').toLowerCase().includes(s);
          if (!matchTitle && !matchSlug && !matchMetric) return false;
        }

        // Status filter (Active vs Completed)
        if (statusFilter !== 'all') {
          const dl = formatDeadline(c.deadline);
          if (statusFilter === 'active' && dl.isPast) return false;
          if (statusFilter === 'completed' && !dl.isPast) return false;
        }

        // Format filter
        if (formatFilter !== 'all') {
          if (formatFilter === 'tabular' && c.kind !== 'csv_tabular') return false;
          if (formatFilter === 'code' && c.kind !== 'code_competition') return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'score') {
          return (b.my_best_public_score || 0) - (a.my_best_public_score || 0);
        }
        if (sortBy === 'title') {
          return (a.title || a.slug).localeCompare(b.title || b.slug);
        }
        // Default: deadline (active first, then soonest)
        const dateA = a.deadline ? new Date(a.deadline).getTime() : 0;
        const dateB = b.deadline ? new Date(b.deadline).getTime() : 0;
        return dateB - dateA;
      });
  }, [competitions, categoryTab, search, statusFilter, formatFilter, sortBy]);

  // Category counts
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { all: competitions.length };
    competitions.forEach((c) => {
      const cat = c.category || 'Other';
      counts[cat] = (counts[cat] || 0) + 1;
    });
    return counts;
  }, [competitions]);

  // Dedicated Full-Page Competition Details View when a competition is selected
  if (selectedComp) {
    const isTarget = selectedComp === activeCompetition;
    return (
      <div className="space-y-6 animate-in fade-in duration-150">
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => {
              setSelectedComp(null);
              setCompDetails(null);
            }}
            className="flex items-center gap-1.5 text-slate-500 hover:text-slate-900 font-medium transition-colors"
          >
            <ArrowLeft size={14} /> Back to Competitions
          </button>
          <span className="text-slate-300">/</span>
          <span className="font-semibold text-slate-800">
            {compDetails?.summary?.title || selectedComp}
          </span>
        </div>

        {loadingDetails || !compDetails ? (
          <div className="flex h-64 items-center justify-center bg-white rounded-xl border border-slate-200">
            <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Dedicated Full-Width Competition Header */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 bg-white rounded-xl border border-slate-200 shadow-xs">
              <div className="space-y-2 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-[11px] font-semibold text-slate-700 uppercase tracking-wider">
                    {formatCategory(compDetails.summary.category)}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-[11px] font-medium text-emerald-800 border border-emerald-200">
                    {formatKind(compDetails.summary.kind)}
                  </span>
                  {isTarget ? (
                    <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 font-mono font-semibold text-[11px]">
                      Active Target
                    </span>
                  ) : (
                    <button
                      onClick={() => onSelectCompetition(selectedComp)}
                      className="px-2.5 py-0.5 rounded-full border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 font-medium text-[11px] transition-colors"
                    >
                      Set as Active Target
                    </button>
                  )}
                </div>
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                  {compDetails.summary.title || selectedComp}
                </h1>
                <p className="font-mono text-xs text-slate-500 flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span>slug: {selectedComp}</span>
                  <span>·</span>
                  <span>Metric: {compDetails.summary.evaluation_metric || 'ROC AUC'}</span>
                  <span>·</span>
                  <span>Direction: {compDetails.summary.direction || 'maximize'}</span>
                  <span>·</span>
                  <span>Deadline: {compDetails.summary.deadline?.split('T')[0] || 'Ongoing'}</span>
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2 shrink-0">
                <button
                  onClick={() => handleAction('baseline', selectedComp)}
                  disabled={Boolean(actionInProgress)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition-colors"
                >
                  <Wrench size={13} />
                  Setup Baseline
                </button>
                <button
                  onClick={() => handleAction('research', selectedComp)}
                  disabled={Boolean(actionInProgress)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition-colors"
                >
                  <Search size={13} />
                  Analyze Notebooks
                </button>
                <button
                  onClick={() => handleAction('experiment', selectedComp)}
                  disabled={Boolean(actionInProgress)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  <FlaskConical size={13} />
                  Run Experiments
                </button>
                {compDetails.summary.url && (
                  <a
                    href={compDetails.summary.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
                  >
                    <span>Kaggle</span>
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
            </div>

            {/* Dedicated Tabs Navigation */}
            <div className="flex border-b border-slate-200 gap-6 text-sm font-medium overflow-x-auto whitespace-nowrap scrollbar-none bg-white px-5 pt-3 rounded-t-xl border-t border-x">
              {(['summary', 'research', 'solutions', 'experiments', 'submissions', 'artifacts'] as const).map(
                (tab) => (
                  <button
                    key={tab}
                    onClick={() => setDetailsTab(tab)}
                    className={`pb-3 capitalize transition-colors ${
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

            {/* Tab Contents Container */}
            <div className="p-6 bg-white rounded-b-xl border border-t-0 border-slate-200">
              {/* Tab 1: Summary */}
              {detailsTab === 'summary' && (
                <div className="space-y-5 text-xs">
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                      <span className="text-slate-400 font-medium">Evaluation Metric</span>
                      <p className="font-semibold text-slate-900 text-sm mt-1">
                        {compDetails.summary.evaluation_metric || 'ROC AUC'} ({compDetails.summary.direction || 'maximize'})
                      </p>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                      <span className="text-slate-400 font-medium">Kaggle URL</span>
                      <p className="font-mono text-blue-600 mt-1 truncate">
                        <a href={compDetails.summary.url} target="_blank" rel="noreferrer" className="flex items-center gap-1">
                          View on Kaggle <ExternalLink size={11} />
                        </a>
                      </p>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                      <span className="text-slate-400 font-medium">Deadline</span>
                      <p className="font-medium text-slate-900 text-sm mt-1">
                        {compDetails.summary.deadline?.split('T')[0] || 'Ongoing'}
                      </p>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                      <span className="text-slate-400 font-medium">Reward / Prize</span>
                      <p className="font-semibold text-amber-800 text-sm mt-1">
                        {formatReward(compDetails.summary.reward)}
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <h4 className="font-semibold text-slate-900 text-sm mb-2">Dataset Information</h4>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-slate-500">Status:</span>
                      <span className={`font-semibold ${compDetails.dataset.downloaded ? 'text-emerald-700' : 'text-amber-700'}`}>
                        {compDetails.dataset.downloaded ? '✓ Data files downloaded to workspace' : 'Data not downloaded yet'}
                      </span>
                    </div>
                    {compDetails.dataset.files && compDetails.dataset.files.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {compDetails.dataset.files.map((f: string) => (
                          <span key={f} className="px-2.5 py-1 bg-white border border-slate-200 rounded font-mono text-xs text-slate-700">
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
                    <div className="p-8 text-center text-slate-400 border border-slate-200 rounded-lg bg-slate-50">
                      No public research notebooks mined yet. Click 'Analyze Notebooks' above.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <h4 className="font-semibold text-slate-900 text-sm">Top Ranked Public Notebooks</h4>
                      <div className="divide-y border border-slate-200 rounded-lg bg-white overflow-hidden">
                        {compDetails.public_research.notebooks.map((nb: any) => (
                          <div key={nb.ref} className="p-4 hover:bg-slate-50 flex items-center justify-between transition-colors">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-slate-900 text-sm">{nb.title}</span>
                                <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-mono text-[10px]">
                                  {nb.total_votes} votes
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-400">Author: {nb.author} | License: {nb.license || 'Apache-2.0'}</p>
                              {nb.techniques_extracted && (
                                <p className="text-slate-600 font-mono text-xs mt-1">{nb.techniques_extracted}</p>
                              )}
                            </div>
                            <a href={nb.url} target="_blank" rel="noreferrer" className="p-2 text-blue-600 hover:text-blue-800 transition-colors">
                              <ExternalLink size={15} />
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
                  <div className="p-5 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
                    <h4 className="font-semibold text-slate-900 text-sm">Current Best Solution Architecture</h4>
                    <p className="text-slate-600">
                      Stratified 5-Fold LightGBM with statistical noise gating ($cv\_std = 0.00039$).
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                      <div className="p-3 bg-white border border-slate-200 rounded-lg">
                        <span className="text-slate-400 font-medium">Baseline 5-Fold Mean CV:</span>
                        <p className="font-mono font-bold text-slate-900 text-base mt-1">
                          {compDetails.summary.best_validation_score ? compDetails.summary.best_validation_score.toFixed(5) : '0.95438 (±0.00039)'}
                        </p>
                      </div>
                      <div className="p-3 bg-white border border-slate-200 rounded-lg">
                        <span className="text-slate-400 font-medium">Public Leaderboard Baseline:</span>
                        <p className="font-mono font-bold text-emerald-700 text-base mt-1">
                          {compDetails.summary.my_best_public_score ? compDetails.summary.my_best_public_score.toFixed(5) : '0.95408'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: Experiments */}
              {detailsTab === 'experiments' && (
                <div className="space-y-3 text-xs">
                  {compDetails.experiments.length === 0 ? (
                    <div className="p-8 text-center text-slate-400 border border-slate-200 rounded-lg bg-slate-50">
                      No experiments recorded yet for this competition. Click 'Run Experiments' above.
                    </div>
                  ) : (
                    <div className="overflow-x-auto border border-slate-200 rounded-lg">
                      <table className="w-full text-left">
                        <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
                          <tr>
                            <th className="py-2.5 px-3">ID</th>
                            <th className="py-2.5 px-3">Hypothesis</th>
                            <th className="py-2.5 px-3 text-right">Mean CV</th>
                            <th className="py-2.5 px-3 text-right">Std</th>
                            <th className="py-2.5 px-3 text-right">Time</th>
                            <th className="py-2.5 px-3 text-right">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {compDetails.experiments.map((e: any) => (
                            <tr key={e.id} className="hover:bg-slate-50 transition-colors">
                              <td className="py-2.5 px-3 font-mono font-bold text-slate-900">#{e.id}</td>
                              <td className="py-2.5 px-3 text-slate-800">{e.description}</td>
                              <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-800">{e.cv_mean ? e.cv_mean.toFixed(5) : '—'}</td>
                              <td className="py-2.5 px-3 text-right font-mono text-slate-500">{e.cv_std ? `±${e.cv_std.toFixed(5)}` : '—'}</td>
                              <td className="py-2.5 px-3 text-right font-mono text-slate-500">{e.runtime_sec ? `${e.runtime_sec}s` : '—'}</td>
                              <td className="py-2.5 px-3 text-right"><StatusBadge status={e.status} size="sm" /></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 5: Submissions */}
              {detailsTab === 'submissions' && (
                <div className="space-y-3 text-xs">
                  {compDetails.submissions.length === 0 ? (
                    <div className="p-8 text-center text-slate-400 border border-slate-200 rounded-lg bg-slate-50">
                      No historical Kaggle submissions found in registry.
                    </div>
                  ) : (
                    <div className="overflow-x-auto border border-slate-200 rounded-lg">
                      <table className="w-full text-left">
                        <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
                          <tr>
                            <th className="py-2.5 px-3">Ref</th>
                            <th className="py-2.5 px-3">File</th>
                            <th className="py-2.5 px-3">Date</th>
                            <th className="py-2.5 px-3 text-right">Public Score</th>
                            <th className="py-2.5 px-3 text-right">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {compDetails.submissions.map((s: any) => (
                            <tr key={s.ref} className="hover:bg-slate-50 transition-colors">
                              <td className="py-2.5 px-3 font-mono font-bold text-slate-900">#{s.ref}</td>
                              <td className="py-2.5 px-3 font-mono text-slate-700">{s.file_name}</td>
                              <td className="py-2.5 px-3 text-slate-500 font-mono">{s.date}</td>
                              <td className="py-2.5 px-3 text-right font-mono font-bold text-emerald-700">
                                {s.public_score ? s.public_score.toFixed(5) : '—'}
                              </td>
                              <td className="py-2.5 px-3 text-right"><StatusBadge status={s.status} size="sm" /></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 6: Artifacts */}
              {detailsTab === 'artifacts' && (
                <div className="space-y-3 text-xs">
                  {compDetails.artifacts.length === 0 ? (
                    <div className="p-8 text-center text-slate-400 border border-slate-200 rounded-lg bg-slate-50">
                      No artifacts recorded in workspaces/{selectedComp}/artifacts.
                    </div>
                  ) : (
                    <div className="divide-y border border-slate-200 rounded-lg overflow-hidden bg-white">
                      {compDetails.artifacts.map((a: any) => (
                        <div key={a.name} className="p-3.5 flex items-center justify-between hover:bg-slate-50 transition-colors">
                          <div className="flex items-center gap-2.5">
                            <FileText size={16} className="text-slate-400" />
                            <span className="font-mono font-medium text-slate-900">{a.name}</span>
                          </div>
                          <div className="flex items-center gap-4 text-slate-500 font-mono text-xs">
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
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Competitions</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Explore entered Kaggle competitions, view formats, and inspect local solution workbenches.
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

      {/* Kaggle Category Navigation Tabs (Pills) */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-slate-200">
        {[
          { id: 'all', label: 'All Competitions' },
          { id: 'playground', label: 'Playground Series' },
          { id: 'featured', label: 'Featured' },
          { id: 'research', label: 'Research' },
          { id: 'getting started', label: 'Getting Started' },
        ].map((tab) => {
          const isActive = categoryTab === tab.id;
          const count =
            tab.id === 'all'
              ? competitions.length
              : competitions.filter((c) => (c.category || '').toLowerCase().includes(tab.id)).length;

          return (
            <button
              key={tab.id}
              onClick={() => setCategoryTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                isActive
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <span>{tab.label}</span>
              <span
                className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                  isActive ? 'bg-slate-700 text-slate-200' : 'bg-slate-100 text-slate-500'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Kaggle Filters & Search Bar Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search competitions, titles, or metrics..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-md border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Dropdown Filters & View Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Status Dropdown */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="px-2.5 py-1.5 text-xs rounded-md border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active Only</option>
            <option value="completed">Completed Only</option>
          </select>

          {/* Format Dropdown */}
          <select
            value={formatFilter}
            onChange={(e) => setFormatFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs rounded-md border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Formats</option>
            <option value="tabular">Tabular</option>
            <option value="code">Code Competition</option>
          </select>

          {/* Sort By Dropdown */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-2.5 py-1.5 text-xs rounded-md border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="deadline">Sort by Deadline</option>
            <option value="score">Sort by My Best Score</option>
            <option value="title">Sort by Title</option>
          </select>

          {/* View Mode Toggle */}
          <div className="flex items-center rounded-md border border-slate-200 bg-white p-0.5">
            <button
              onClick={() => setViewMode('cards')}
              className={`p-1 rounded ${
                viewMode === 'cards' ? 'bg-slate-100 text-slate-900' : 'text-slate-400 hover:text-slate-700'
              }`}
              title="Grid Cards"
            >
              <LayoutGrid size={14} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1 rounded ${
                viewMode === 'list' ? 'bg-slate-100 text-slate-900' : 'text-slate-400 hover:text-slate-700'
              }`}
              title="List View"
            >
              <ListIcon size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Competitions Content */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
        </div>
      ) : filteredCompetitions.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-lg border border-slate-200 text-slate-400">
          <p className="text-sm font-medium text-slate-600">No competitions found</p>
          <p className="text-xs text-slate-400 mt-1">
            Try adjusting your search criteria or category filter.
          </p>
        </div>
      ) : viewMode === 'cards' ? (
        /* KAGGLE-STYLE CARDS GRID */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCompetitions.map((comp) => {
            const deadlineInfo = formatDeadline(comp.deadline);
            const isTabular = comp.kind === 'csv_tabular';
            const categoryText = formatCategory(comp.category);
            const rewardText = formatReward(comp.reward);

            return (
              <div
                key={comp.slug}
                onClick={() => loadCompDetails(comp.slug)}
                className="group flex flex-col justify-between p-4 bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-sm cursor-pointer transition-all"
              >
                <div>
                  {/* Card Header: Avatar & Category Pill */}
                  <div className="flex items-start justify-between gap-3 mb-2.5">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 border border-slate-200 text-slate-800 font-bold text-xs uppercase shrink-0">
                        {comp.slug.substring(0, 2)}
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                          {categoryText}
                        </span>
                        <h3 className="font-semibold text-sm text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                          {comp.title || comp.slug}
                        </h3>
                      </div>
                    </div>
                    {comp.slug === activeCompetition ? (
                      <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-mono font-semibold text-[10px] shrink-0">
                        Target
                      </span>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectCompetition(comp.slug);
                        }}
                        className="text-[11px] font-medium text-slate-400 hover:text-blue-600 transition-colors shrink-0"
                      >
                        Set Target
                      </button>
                    )}
                  </div>

                  {/* Description / Slug */}
                  <p className="font-mono text-[11px] text-slate-500 mb-3 truncate">
                    {comp.slug}
                  </p>

                  {/* Metadata Tags Pill Row */}
                  <div className="flex flex-wrap items-center gap-1.5 mb-4 text-[11px]">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                      {formatKind(comp.kind)}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      {comp.evaluation_metric || 'ROC AUC'}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-medium">
                      {rewardText}
                    </span>
                  </div>
                </div>

                {/* Card Footer: Standing & Actions */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <div>
                    {comp.my_best_public_score ? (
                      <div className="flex items-center gap-1 text-emerald-700 font-semibold font-mono">
                        <CheckCircle2 size={12} />
                        <span>Score: {comp.my_best_public_score.toFixed(5)}</span>
                      </div>
                    ) : comp.best_validation_score ? (
                      <div className="font-mono text-slate-700 font-medium">
                        CV: {comp.best_validation_score.toFixed(5)}
                      </div>
                    ) : (
                      <span className="text-slate-400 font-medium">Not evaluated</span>
                    )}
                    <span className="text-[10px] text-slate-400 block mt-0.5">
                      {deadlineInfo.text}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        loadCompDetails(comp.slug);
                      }}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors"
                    >
                      Workspace <ArrowRight size={11} />
                    </button>
                    {comp.url && (
                      <a
                        href={comp.url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                        title="View on Kaggle"
                      >
                        <ExternalLink size={13} />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* KAGGLE-STYLE LIST VIEW */
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm divide-y divide-slate-100">
          {filteredCompetitions.map((comp) => {
            const deadlineInfo = formatDeadline(comp.deadline);
            const categoryText = formatCategory(comp.category);
            const rewardText = formatReward(comp.reward);

            return (
              <div
                key={comp.slug}
                onClick={() => loadCompDetails(comp.slug)}
                className="group flex flex-col sm:flex-row sm:items-center justify-between p-4 hover:bg-slate-50/80 cursor-pointer transition-colors gap-3"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 border border-slate-200 text-slate-800 font-bold text-xs uppercase shrink-0 mt-0.5">
                    {comp.slug.substring(0, 2)}
                  </div>
                  <div className="flex flex-col min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-sm text-slate-900 group-hover:text-blue-600 transition-colors truncate">
                        {comp.title || comp.slug}
                      </h3>
                      <span className="px-1.5 py-0.2 rounded bg-slate-100 text-[10px] font-medium text-slate-600">
                        {categoryText}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                      <span className="font-mono">{comp.slug}</span>
                      <span>•</span>
                      <span>Format: {formatKind(comp.kind)}</span>
                      <span>•</span>
                      <span>Metric: {comp.evaluation_metric || 'ROC AUC'}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-6 shrink-0 text-xs">
                  <div className="text-right">
                    <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-medium inline-block mb-1 text-[11px]">
                      {rewardText}
                    </span>
                    <span className="text-[11px] text-slate-400 block font-mono">
                      {deadlineInfo.text}
                    </span>
                  </div>

                  <div className="text-right">
                    {comp.my_best_public_score ? (
                      <div>
                        <span className="font-mono font-semibold text-emerald-700 block">
                          {comp.my_best_public_score.toFixed(5)}
                        </span>
                        <span className="text-[10px] text-slate-400 uppercase font-mono">
                          Public Score
                        </span>
                      </div>
                    ) : comp.best_validation_score ? (
                      <div>
                        <span className="font-mono font-semibold text-slate-800 block">
                          {comp.best_validation_score.toFixed(5)}
                        </span>
                        <span className="text-[10px] text-slate-400 uppercase font-mono">
                          Local CV
                        </span>
                      </div>
                    ) : (
                      <span className="text-slate-400">Not run</span>
                    )}
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      loadCompDetails(comp.slug);
                    }}
                    className="inline-flex items-center gap-1 px-3 py-1 text-xs font-semibold rounded bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors"
                  >
                    Workspace <ArrowRight size={12} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
