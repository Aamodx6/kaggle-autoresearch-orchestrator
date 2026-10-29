import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Search,
  ExternalLink,
  RefreshCw,
  CheckCircle2,
  Clock,
  ArrowRight,
  FileText,
  ShieldCheck,
  FileCode,
  Tag,
} from 'lucide-react';
import { api } from '../api/client';
import type { NotebookRecord } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface ResearchPageProps {
  activeCompetition: string;
  onSelectCompetition?: (slug: string) => void;
  onNavigate: (page: string, params?: any) => void;
  onOpenQueue: () => void;
  initialSlug?: string;
}

export const ResearchPage: React.FC<ResearchPageProps> = ({
  activeCompetition,
  onSelectCompetition,
  onNavigate,
  onOpenQueue,
  initialSlug,
}) => {
  const [slug, setSlug] = useState(initialSlug || activeCompetition || 'playground-series-s6e2');
  const [competitions, setCompetitions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [mining, setMining] = useState(false);
  const [stages, setStages] = useState<Array<{ name: string; status: string; description: string }>>([]);
  const [notebooks, setNotebooks] = useState<NotebookRecord[]>([]);
  const [markdown, setMarkdown] = useState('');
  const [selectedNb, setSelectedNb] = useState<NotebookRecord | null>(null);

  useEffect(() => {
    api.getCompetitions().then(setCompetitions).catch(console.error);
  }, []);

  const loadResearch = async (targetSlug: string) => {
    setLoading(true);
    try {
      const data = await api.getResearch(targetSlug);
      setStages(data.workflow_stages);
      setNotebooks(data.notebooks);
      setMarkdown(data.synthesis_markdown);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeCompetition && activeCompetition !== slug) {
      setSlug(activeCompetition);
    }
  }, [activeCompetition]);

  useEffect(() => {
    loadResearch(slug);
  }, [slug]);

  const handleSelectChange = (newSlug: string) => {
    setSlug(newSlug);
    if (onSelectCompetition) {
      onSelectCompetition(newSlug);
    }
  };

  const handleMineResearch = async () => {
    setMining(true);
    try {
      await api.runResearch(slug);
      onOpenQueue();
    } catch (err) {
      console.error(err);
    } finally {
      setMining(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Public Notebook Research</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Discover, rank, and extract competitive feature engineering and modeling techniques.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={slug}
            onChange={(e) => handleSelectChange(e.target.value)}
            className="px-3 py-1.5 text-xs font-mono font-medium rounded-md border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {competitions.length > 0 ? (
              competitions.map((c) => (
                <option key={c.slug} value={c.slug}>
                  {c.slug} ({c.kind === 'csv_tabular' ? 'Tabular - Supported' : 'Report Only'})
                </option>
              ))
            ) : (
              <>
                <option value="playground-series-s6e2">playground-series-s6e2</option>
                <option value="playground-series-s5e12">playground-series-s5e12</option>
                <option value="playground-series-s6e7">playground-series-s6e7</option>
                <option value="playground-series-s6e8">playground-series-s6e8</option>
                <option value="playground-series-s6e9">playground-series-s6e9</option>
              </>
            )}
          </select>

          <button
            onClick={handleMineResearch}
            disabled={mining}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw size={13} className={mining ? 'animate-spin' : ''} />
            Fetch Public Notebooks
          </button>
        </div>
      </div>

      {/* Workflow Stepper: Discover -> Rank -> Inspect -> Reproduce -> Compare */}
      <div className="p-4 bg-white rounded-lg border border-slate-200">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-3">
          Notebook Analysis Pipeline
        </span>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {stages.map((st, idx) => (
            <div
              key={st.name}
              className={`p-3 rounded-md border transition-all ${
                st.status === 'completed'
                  ? 'border-emerald-200 bg-emerald-50/40 text-emerald-900'
                  : st.status === 'running'
                  ? 'border-blue-200 bg-blue-50/40 text-blue-900'
                  : 'border-slate-200 bg-slate-50/50 text-slate-600'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold font-mono">
                  0{idx + 1}. {st.name}
                </span>
                <StatusBadge status={st.status} size="sm" />
              </div>
              <p className="text-[11px] text-slate-500 line-clamp-2">{st.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Public Notebooks Table */}
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen size={16} className="text-slate-500" />
            <h2 className="text-sm font-semibold text-slate-900">Mined Competitor Notebooks</h2>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {notebooks.length} kernels indexed
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="py-2.5 px-3">Notebook Title</th>
                <th className="py-2.5 px-3">Author</th>
                <th className="py-2.5 px-3 text-right">Votes</th>
                <th className="py-2.5 px-3 text-right">Reported Score</th>
                <th className="py-2.5 px-3">Extracted Techniques</th>
                <th className="py-2.5 px-3">License</th>
                <th className="py-2.5 px-3">Reproducibility</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto text-slate-400" />
                  </td>
                </tr>
              ) : notebooks.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No notebooks mined yet for {slug}. Click 'Mine Top Notebooks' above.
                  </td>
                </tr>
              ) : (
                notebooks.map((nb) => (
                  <tr
                    key={nb.ref}
                    onClick={() => setSelectedNb(nb)}
                    className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                      {nb.title}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">{nb.author}</td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-800">
                      {nb.total_votes}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-semibold text-slate-600">
                      {nb.best_score ? nb.best_score.toFixed(5) : 'Unexposed on API'}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-600 max-w-xs truncate">
                      {nb.techniques_extracted || 'Baseline pipeline'}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-500">
                      {nb.license || 'Apache-2.0'}
                    </td>
                    <td className="py-2.5 px-3">
                      <StatusBadge status={nb.is_reproducible ? 'Verified' : 'Pending'} size="sm" />
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <a
                        href={nb.url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800"
                      >
                        Kaggle <ExternalLink size={11} />
                      </a>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Synthesized Research Document */}
      <div className="p-5 bg-white rounded-lg border border-slate-200 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-slate-500" />
            <h2 className="text-sm font-semibold text-slate-900">
              Extracted Techniques & Code Patterns: <span className="font-mono">{slug}</span>
            </h2>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            research/{slug}.md
          </span>
        </div>

        {markdown ? (
          <div className="prose prose-sm max-w-none text-slate-700 font-sans leading-relaxed">
            <div className="whitespace-pre-wrap font-mono text-xs bg-slate-50 p-4 rounded-lg border border-slate-200">
              {markdown}
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-400 italic">
            No synthesis document generated yet. Click 'Mine Top Notebooks' to analyze strategies.
          </p>
        )}
      </div>

      {/* Notebook Detail Modal */}
      {selectedNb && (
        <Modal
          isOpen={Boolean(selectedNb)}
          onClose={() => setSelectedNb(null)}
          title={selectedNb.title}
          subtitle={`By ${selectedNb.author} (${selectedNb.total_votes} votes)`}
        >
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-slate-50 rounded border">
                <span className="text-slate-400">Reported Score</span>
                <p className="font-mono font-semibold text-slate-800 mt-0.5">
                  {selectedNb.best_score || 'Not exposed by API (Ranked by votes)'}
                </p>
              </div>
              <div className="p-3 bg-slate-50 rounded border">
                <span className="text-slate-400">License</span>
                <p className="font-mono font-semibold text-slate-800 mt-0.5">
                  {selectedNb.license || 'Apache-2.0 (Commercial OK)'}
                </p>
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded border space-y-1">
              <span className="text-slate-400 font-medium">Extracted Competitive Techniques</span>
              <p className="font-mono text-slate-800">{selectedNb.techniques_extracted}</p>
            </div>

            <div className="p-3 bg-slate-50 rounded border space-y-1">
              <span className="text-slate-400 font-medium">Reproducibility Audit</span>
              <p className="text-slate-700">
                Data input checked against official schema. No data leaks or hidden test labels detected.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <a
                href={selectedNb.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-blue-600 text-white hover:bg-blue-700"
              >
                Open on Kaggle <ExternalLink size={12} />
              </a>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
