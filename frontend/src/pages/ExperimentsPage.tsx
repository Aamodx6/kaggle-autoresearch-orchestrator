import React, { useEffect, useState } from 'react';
import {
  FlaskConical,
  Play,
  RefreshCw,
  GitCommit,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  XCircle,
  FileCode,
  Terminal,
  Cpu,
  Layers,
} from 'lucide-react';
import { api } from '../api/client';
import type { ExperimentRecord } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface ExperimentsPageProps {
  onOpenQueue: () => void;
  initialExpId?: number;
}

export const ExperimentsPage: React.FC<ExperimentsPageProps> = ({
  onOpenQueue,
  initialExpId,
}) => {
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningLoop, setRunningLoop] = useState(false);
  const [selectedExpId, setSelectedExpId] = useState<number | null>(initialExpId || null);
  const [expDetails, setExpDetails] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const fetchExperiments = async () => {
    try {
      const data = await api.getExperiments();
      setExperiments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiments();
  }, []);

  const loadDetails = async (id: number) => {
    setLoadingDetails(true);
    setSelectedExpId(id);
    try {
      const data = await api.getExperimentDetails(id);
      setExpDetails(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  };

  useEffect(() => {
    if (initialExpId) {
      loadDetails(initialExpId);
    }
  }, [initialExpId]);

  const handleRunLoop = async () => {
    setRunningLoop(true);
    try {
      await api.runExperiment('playground-series-s6e2');
      onOpenQueue();
    } catch (err) {
      console.error(err);
    } finally {
      setRunningLoop(false);
    }
  };

  const baselineScore = 0.95438;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">AutoResearch Experiments</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Karpathy-style keep/revert hypothesis optimization with strict statistical noise gating.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchExperiments}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-sm transition-colors"
          >
            <RefreshCw size={13} />
            Refresh
          </button>
          <button
            onClick={handleRunLoop}
            disabled={runningLoop}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition-colors disabled:opacity-50"
          >
            <FlaskConical size={13} className={runningLoop ? 'animate-spin' : ''} />
            Run AutoResearch Loop
          </button>
        </div>
      </div>

      {/* Experiments Table */}
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="py-2.5 px-3">Exp ID</th>
                <th className="py-2.5 px-3">Competition</th>
                <th className="py-2.5 px-3">Hypothesis / Description</th>
                <th className="py-2.5 px-3 font-mono">Git Hash</th>
                <th className="py-2.5 px-3 text-right">Mean CV</th>
                <th className="py-2.5 px-3 text-right">Noise (±Std)</th>
                <th className="py-2.5 px-3 text-right">Δ vs Base</th>
                <th className="py-2.5 px-3 text-right">Runtime</th>
                <th className="py-2.5 px-3 text-right">Decision / Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto text-slate-400" />
                  </td>
                </tr>
              ) : experiments.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    No experiments executed yet. Click 'Run AutoResearch Loop' to start the cycle.
                  </td>
                </tr>
              ) : (
                experiments.map((exp) => {
                  const delta = exp.cv_mean ? exp.cv_mean - baselineScore : 0;
                  const isImproved = exp.status === 'improved';
                  return (
                    <tr
                      key={exp.id}
                      onClick={() => loadDetails(exp.id)}
                      className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                    >
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-900">
                        #{exp.id}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-600">
                        {exp.competition_slug}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-slate-900 max-w-sm truncate">
                        {exp.description || 'LightGBM experiment'}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-500">
                        {exp.commit_hash?.substring(0, 7) || 'HEAD'}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-semibold text-slate-900">
                        {exp.cv_mean ? exp.cv_mean.toFixed(5) : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                        {exp.cv_std ? `±${exp.cv_std.toFixed(5)}` : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-medium">
                        {exp.cv_mean ? (
                          <span
                            className={
                              delta > 0.00039
                                ? 'text-emerald-700'
                                : delta > 0
                                ? 'text-amber-600'
                                : 'text-slate-500'
                            }
                          >
                            {delta >= 0 ? '+' : ''}
                            {delta.toFixed(5)}
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-500">
                        {exp.runtime_sec ? `${exp.runtime_sec}s` : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <StatusBadge status={exp.status} size="sm" />
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Experiment Details Modal */}
      {selectedExpId && (
        <Modal
          isOpen={Boolean(selectedExpId)}
          onClose={() => {
            setSelectedExpId(null);
            setExpDetails(null);
          }}
          title={`Experiment #${selectedExpId}`}
          subtitle={expDetails?.experiment?.description || 'Experiment Inspection'}
          maxWidth="2xl"
        >
          {loadingDetails || !expDetails ? (
            <div className="flex h-36 items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
            </div>
          ) : (
            <div className="space-y-4 text-xs">
              {/* Statistical Evaluation Box */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Statistical Hypothesis Verification
                </span>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <span className="text-slate-400">Baseline Score:</span>
                    <p className="font-mono font-semibold text-slate-800 mt-0.5">
                      {expDetails.evaluation.baseline_score.toFixed(5)}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400">Candidate Score:</span>
                    <p className="font-mono font-semibold text-slate-800 mt-0.5">
                      {expDetails.evaluation.candidate_score
                        ? expDetails.evaluation.candidate_score.toFixed(5)
                        : '—'}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400">Fold Noise Floor (σ):</span>
                    <p className="font-mono font-semibold text-slate-800 mt-0.5">
                      ±{expDetails.evaluation.noise_floor.toFixed(5)}
                    </p>
                  </div>
                </div>
                <div className="pt-2 border-t border-slate-200 flex items-center justify-between">
                  <span className="text-slate-600 font-medium">Statistical Significance Gate:</span>
                  <span
                    className={`font-semibold ${
                      expDetails.evaluation.meets_significance
                        ? 'text-emerald-700'
                        : 'text-rose-700'
                    }`}
                  >
                    {expDetails.evaluation.meets_significance
                      ? '✓ Passed (Δ > σ_CV)'
                      : '✗ Failed (Δ ≤ σ_CV)'}
                  </span>
                </div>
              </div>

              {/* Decision Box */}
              <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900">Decision Outcome</span>
                  <StatusBadge status={expDetails.decision.status} size="sm" />
                </div>
                <p className="text-slate-600">{expDetails.decision.reason}</p>
              </div>

              {/* Code Changes Diff */}
              <div className="space-y-1">
                <span className="font-semibold text-slate-900 flex items-center gap-1.5">
                  <FileCode size={13} className="text-slate-500" />
                  Code Changes Diff (train.py)
                </span>
                <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg font-mono text-[11px] overflow-x-auto">
                  {expDetails.artifacts.diff}
                </pre>
              </div>

              {/* Resources & Execution Info */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 grid grid-cols-2 gap-2 text-slate-600 font-mono text-[11px]">
                <div>Runtime: {expDetails.resources.runtime_sec} seconds</div>
                <div>Memory: {expDetails.resources.memory_mb} MB</div>
                <div>GPU: RTX 4050 Laptop</div>
                <div>CV Strategy: 5-Fold Stratified</div>
              </div>
            </div>
          )}
        </Modal>
      )}
    </div>
  );
};
