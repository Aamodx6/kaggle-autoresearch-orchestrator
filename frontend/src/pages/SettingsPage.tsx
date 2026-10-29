import React, { useEffect, useState } from 'react';
import {
  Settings,
  ShieldCheck,
  Cpu,
  FlaskConical,
  Send,
  HardDrive,
  RefreshCw,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../api/client';
import type { SettingsData } from '../types';
import { StatusBadge } from '../components/StatusBadge';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  const fetchSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  if (loading || !settings) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">System Settings</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure authentication, resource boundaries, AutoResearch budgets, and submission policies.
          </p>
        </div>
        <button
          onClick={handleSave}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition-colors"
        >
          {saved ? <CheckCircle2 size={13} /> : null}
          {saved ? 'Saved' : 'Save Changes'}
        </button>
      </div>

      <div className="space-y-6 text-xs">
        {/* Section 1: Kaggle Connection */}
        <div className="p-5 bg-white rounded-lg border border-slate-200 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <ShieldCheck size={16} className="text-emerald-600" />
            <h2 className="text-sm font-semibold text-slate-900">Kaggle Authentication & Access</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span className="text-slate-500 font-medium block">Authenticated Username</span>
              <p className="font-mono font-semibold text-slate-800 mt-1">{settings.kaggle.username}</p>
            </div>
            <div>
              <span className="text-slate-500 font-medium block">CLI Version & Protocol</span>
              <p className="font-mono text-slate-800 mt-1">Kaggle CLI v{settings.kaggle.cli_version} (kagglesdk)</p>
            </div>
            <div>
              <span className="text-slate-500 font-medium block">Credential Location</span>
              <p className="font-mono text-slate-600 mt-1">{settings.kaggle.token_path}</p>
            </div>
            <div>
              <span className="text-slate-500 font-medium block">Account Status</span>
              <div className="mt-1">
                <StatusBadge status="Authenticated" size="sm" />
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Research & Experimentation */}
        <div className="p-5 bg-white rounded-lg border border-slate-200 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <FlaskConical size={16} className="text-blue-600" />
            <h2 className="text-sm font-semibold text-slate-900">AutoResearch Keep/Revert Parameters</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="text-slate-600 font-medium block">Timeout per Experiment (s)</label>
              <input
                type="number"
                value={settings.research.timeout_seconds}
                readOnly
                className="mt-1 w-full px-2.5 py-1.5 rounded border border-slate-200 bg-slate-50 font-mono text-slate-700"
              />
            </div>
            <div>
              <label className="text-slate-600 font-medium block">Max Experiments per Run</label>
              <input
                type="number"
                value={settings.research.max_experiments}
                readOnly
                className="mt-1 w-full px-2.5 py-1.5 rounded border border-slate-200 bg-slate-50 font-mono text-slate-700"
              />
            </div>
            <div>
              <label className="text-slate-600 font-medium block">Early Stopping Patience</label>
              <input
                type="number"
                value={settings.research.patience}
                readOnly
                className="mt-1 w-full px-2.5 py-1.5 rounded border border-slate-200 bg-slate-50 font-mono text-slate-700"
              />
            </div>
          </div>
          <p className="text-[11px] text-slate-400">
            * Statistical Noise Gate: Candidates are kept only if CV improvement exceeds fold standard deviation (Δ &gt; σ_CV).
          </p>
        </div>

        {/* Section 3: Compute & Hardware */}
        <div className="p-5 bg-white rounded-lg border border-slate-200 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <Cpu size={16} className="text-purple-600" />
            <h2 className="text-sm font-semibold text-slate-900">Hardware & Execution Sandbox</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span className="text-slate-500 font-medium block">Detected GPU</span>
              <p className="font-mono font-semibold text-slate-800 mt-1">{settings.compute.gpu}</p>
            </div>
            <div>
              <span className="text-slate-500 font-medium block">CPU Cores Allocated</span>
              <p className="font-mono text-slate-800 mt-1">{settings.compute.cpu_cores} Threads</p>
            </div>
            <div>
              <span className="text-slate-500 font-medium block">Max Concurrency</span>
              <p className="font-mono text-slate-800 mt-1">{settings.compute.max_concurrent_runs} Task Worker</p>
            </div>
            <div>
              <span className="text-slate-500 font-medium block">Git Worktree Sandbox</span>
              <div className="mt-1">
                <StatusBadge status="Active" size="sm" />
              </div>
            </div>
          </div>
        </div>

        {/* Section 4: Submission Controls */}
        <div className="p-5 bg-white rounded-lg border border-slate-200 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <Send size={16} className="text-amber-600" />
            <h2 className="text-sm font-semibold text-slate-900">Leaderboard Submission Policies</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span className="text-slate-500 font-medium block">Default Mode</span>
              <span className="inline-block mt-1 font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                --dry-run (Safety Default)
              </span>
            </div>
            <div>
              <span className="text-slate-500 font-medium block">Daily Cap Limit</span>
              <span className="inline-block mt-1 font-mono font-semibold text-slate-800">
                {settings.submissions.daily_cap_default} Submissions / Day
              </span>
            </div>
            <div className="sm:col-span-2">
              <span className="text-slate-500 font-medium block">Approval Requirement</span>
              <p className="text-slate-600 mt-1">
                Live submissions strictly require explicit interactive checkbox confirmation. The agent will never automatically consume leaderboard quota.
              </p>
            </div>
          </div>
        </div>

        {/* Section 5: Storage Paths */}
        <div className="p-5 bg-white rounded-lg border border-slate-200 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <HardDrive size={16} className="text-slate-600" />
            <h2 className="text-sm font-semibold text-slate-900">Storage Directories</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-[11px]">
            <div className="p-2.5 bg-slate-50 rounded border">
              <span className="text-slate-400 block">Workspaces</span>
              <span className="text-slate-800">{settings.storage.workspaces_dir}</span>
            </div>
            <div className="p-2.5 bg-slate-50 rounded border">
              <span className="text-slate-400 block">SQLite Registry</span>
              <span className="text-slate-800">{settings.storage.registry_db}</span>
            </div>
            <div className="p-2.5 bg-slate-50 rounded border">
              <span className="text-slate-400 block">Research Mined Notes</span>
              <span className="text-slate-800">{settings.storage.research_dir}</span>
            </div>
            <div className="p-2.5 bg-slate-50 rounded border">
              <span className="text-slate-400 block">Evidence Logs</span>
              <span className="text-slate-800">{settings.storage.evidence_dir}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
