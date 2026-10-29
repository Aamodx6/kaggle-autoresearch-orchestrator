import React, { useEffect, useState } from 'react';
import {
  Layers,
  FileText,
  Download,
  Copy,
  Check,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  HardDrive,
} from 'lucide-react';
import { api } from '../api/client';
import type { ArtifactRecord } from '../types';
import { StatusBadge } from '../components/StatusBadge';

export const ArtifactsPage: React.FC = () => {
  const [artifacts, setArtifacts] = useState<ArtifactRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedPath, setCopiedPath] = useState<string | null>(null);
  const [filterType, setFilterType] = useState('all');

  const fetchArtifacts = async () => {
    try {
      const data = await api.getArtifacts();
      setArtifacts(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArtifacts();
  }, []);

  const handleCopy = (path: string) => {
    navigator.clipboard.writeText(path);
    setCopiedPath(path);
    setTimeout(() => setCopiedPath(null), 2000);
  };

  const filtered = artifacts.filter((a) => {
    if (filterType === 'all') return true;
    if (filterType === 'candidates') return a.type.toLowerCase().includes('submission');
    if (filterType === 'checkpoints') return a.type.toLowerCase().includes('checkpoint') || a.name.includes('best');
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Models & Artifacts</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Structured inventory of model checkpoints, verified candidates, and submission artifacts.
          </p>
        </div>
        <button
          onClick={fetchArtifacts}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-sm transition-colors"
        >
          <RefreshCw size={13} />
          Refresh Artifacts
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setFilterType('all')}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            filterType === 'all'
              ? 'bg-slate-900 text-white font-semibold'
              : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          All Artifacts ({artifacts.length})
        </button>
        <button
          onClick={() => setFilterType('candidates')}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            filterType === 'candidates'
              ? 'bg-slate-900 text-white font-semibold'
              : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          Submission Candidates
        </button>
        <button
          onClick={() => setFilterType('checkpoints')}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            filterType === 'checkpoints'
              ? 'bg-slate-900 text-white font-semibold'
              : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          Verified Best Checkpoints
        </button>
      </div>

      {/* Artifacts Table */}
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="py-2.5 px-3">Artifact Name</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Competition</th>
                <th className="py-2.5 px-3">Version</th>
                <th className="py-2.5 px-3 text-right">Size</th>
                <th className="py-2.5 px-3">Created At</th>
                <th className="py-2.5 px-3 text-right">Local Path</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto text-slate-400" />
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No artifacts found matching filter.
                  </td>
                </tr>
              ) : (
                filtered.map((art) => (
                  <tr key={art.path} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2.5 px-3">
                      <div className="flex items-center gap-2">
                        <FileText size={15} className="text-slate-400 shrink-0" />
                        <span className="font-mono font-semibold text-slate-900">
                          {art.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3">
                      <StatusBadge status={art.type} size="sm" />
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-600">
                      {art.competition}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-500">
                      {art.version}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-slate-800">
                      {art.size_formatted}
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">
                      {art.created_at.split('T')[0]}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleCopy(art.path)}
                        className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-500 hover:text-slate-800 px-2 py-0.5 rounded border border-slate-200 bg-white"
                        title={art.path}
                      >
                        {copiedPath === art.path ? (
                          <>
                            <Check size={11} className="text-emerald-600" /> Copied
                          </>
                        ) : (
                          <>
                            <Copy size={11} /> Copy Path
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
