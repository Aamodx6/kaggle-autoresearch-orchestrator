import React from 'react';
import { RefreshCw, Clock, Activity, ChevronDown, Check } from 'lucide-react';
import type { GlobalStatus, CompetitionSummary } from '../types';
import { StatusBadge } from './StatusBadge';

interface HeaderProps {
  status: GlobalStatus | null;
  competitions: CompetitionSummary[];
  activeCompetition: string;
  onSelectCompetition: (slug: string) => void;
  onOpenQueue: () => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  competitions,
  activeCompetition,
  onSelectCompetition,
  onOpenQueue,
  onRefresh,
  isRefreshing,
}) => {
  const [dropdownOpen, setDropdownOpen] = React.useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatTime = (isoString?: string) => {
    if (!isoString) return 'Never';
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString;
    }
  };

  const currentComp = competitions.find((c) => c.slug === activeCompetition) || {
    slug: activeCompetition || 'playground-series-s6e2',
    title: activeCompetition || 'playground-series-s6e2',
    kind: 'csv_tabular',
  };

  const formatKindBadge = (kind?: string) => {
    if (kind === 'csv_tabular') return 'Tabular (Supported)';
    if (kind === 'code_competition') return 'Code Competition';
    if (kind === 'csv_cv') return 'Computer Vision';
    if (kind === 'agent_or_optimization') return 'Simulation & Agent';
    return 'Other';
  };

  // Group competitions by modality
  const tabularComps = competitions.filter((c) => c.kind === 'csv_tabular');
  const codeComps = competitions.filter((c) => c.kind === 'code_competition' || c.kind === 'csv_cv');
  const agentComps = competitions.filter((c) => c.kind === 'agent_or_optimization');
  const otherComps = competitions.filter(
    (c) => c.kind !== 'csv_tabular' && c.kind !== 'code_competition' && c.kind !== 'csv_cv' && c.kind !== 'agent_or_optimization'
  );

  return (
    <header className="flex h-14 w-full items-center justify-between border-b border-slate-200 bg-white px-6 z-20">
      {/* Left: Global Execution Status & Target Competition Selector */}
      <div className="flex items-center gap-3">
        {/* Execution State Pill */}
        <button
          onClick={onOpenQueue}
          className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 px-3 py-1.5 transition-all text-xs"
          title="Click to view full execution queue and live task logs"
        >
          <span className="font-semibold text-slate-500 uppercase tracking-wider text-[10px]">
            System:
          </span>
          <StatusBadge status={status?.state || 'Idle'} size="sm" />

          {status?.queued_tasks_count ? (
            <span className="ml-1 px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-800 font-mono text-[11px] font-semibold">
              +{status.queued_tasks_count}
            </span>
          ) : null}
        </button>

        {/* Global Target Competition Switcher Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 px-3 py-1.5 transition-all text-xs"
            title="Switch active target competition"
          >
            <span className="text-slate-400 font-medium">Target:</span>
            <div className="flex items-center gap-1.5">
              <span className="font-mono font-semibold text-slate-900 max-w-[200px] truncate">
                {currentComp.slug}
              </span>
              <span className="px-1.5 py-0.2 rounded bg-slate-100 text-[10px] font-medium text-slate-600">
                {formatKindBadge(currentComp.kind)}
              </span>
            </div>
            <ChevronDown size={13} className="text-slate-400 ml-0.5" />
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="absolute left-0 mt-1.5 w-88 bg-white rounded-lg border border-slate-200 shadow-xl overflow-hidden py-1 z-50 text-xs">
              <div className="px-3 py-2 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
                <span className="font-semibold text-[11px] text-slate-500 uppercase tracking-wider">
                  Target Competition Selector
                </span>
                <span className="font-mono text-[10px] text-slate-400">
                  {competitions.length} Available
                </span>
              </div>
              <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                {/* Group 1: Supported Autonomous Pipeline */}
                {tabularComps.length > 0 && (
                  <div>
                    <div className="px-3 py-1.5 bg-slate-50 text-[10px] font-semibold text-emerald-800 uppercase tracking-wider flex items-center justify-between">
                      <span>Supported Autonomous Pipeline ({tabularComps.length})</span>
                      <span className="text-[9px] font-normal text-emerald-700">AutoResearch Ready</span>
                    </div>
                    {tabularComps.map((comp) => {
                      const isSelected = comp.slug === activeCompetition;
                      return (
                        <button
                          key={comp.slug}
                          onClick={() => {
                            onSelectCompetition(comp.slug);
                            setDropdownOpen(false);
                          }}
                          className={`w-full flex items-center justify-between p-2.5 text-left transition-colors ${
                            isSelected ? 'bg-blue-50/70' : 'hover:bg-slate-50'
                          }`}
                        >
                          <div className="flex flex-col min-w-0 pr-2">
                            <span className={`font-medium truncate ${isSelected ? 'text-blue-900 font-semibold' : 'text-slate-900'}`}>
                              {comp.title || comp.slug}
                            </span>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="font-mono text-[10px] text-slate-400 truncate">
                                {comp.slug}
                              </span>
                              <span className="px-1.5 py-0.2 rounded bg-emerald-50 text-[9px] font-medium text-emerald-700 border border-emerald-200">
                                Tabular · {comp.evaluation_metric || 'ROC AUC'}
                              </span>
                            </div>
                          </div>
                          {isSelected && <Check size={14} className="text-blue-600 shrink-0" />}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Group 2: Code Competitions (Report Only) */}
                {codeComps.length > 0 && (
                  <div>
                    <div className="px-3 py-1.5 bg-slate-50 text-[10px] font-semibold text-slate-600 uppercase tracking-wider flex items-center justify-between">
                      <span>Code Competitions ({codeComps.length})</span>
                      <span className="text-[9px] font-normal text-slate-500">Kernel & Report Only</span>
                    </div>
                    {codeComps.map((comp) => {
                      const isSelected = comp.slug === activeCompetition;
                      return (
                        <button
                          key={comp.slug}
                          onClick={() => {
                            onSelectCompetition(comp.slug);
                            setDropdownOpen(false);
                          }}
                          className={`w-full flex items-center justify-between p-2.5 text-left transition-colors ${
                            isSelected ? 'bg-blue-50/70' : 'hover:bg-slate-50'
                          }`}
                        >
                          <div className="flex flex-col min-w-0 pr-2">
                            <span className={`font-medium truncate ${isSelected ? 'text-blue-900 font-semibold' : 'text-slate-800'}`}>
                              {comp.title || comp.slug}
                            </span>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="font-mono text-[10px] text-slate-400 truncate">
                                {comp.slug}
                              </span>
                              <span className="px-1.5 py-0.2 rounded bg-amber-50 text-[9px] font-medium text-amber-700 border border-amber-200">
                                Code · Report Only
                              </span>
                            </div>
                          </div>
                          {isSelected && <Check size={14} className="text-blue-600 shrink-0" />}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Group 3: Simulation & Agents */}
                {agentComps.length > 0 && (
                  <div>
                    <div className="px-3 py-1.5 bg-slate-50 text-[10px] font-semibold text-purple-800 uppercase tracking-wider flex items-center justify-between">
                      <span>Simulation & Agents ({agentComps.length})</span>
                      <span className="text-[9px] font-normal text-purple-600">Sim Environment</span>
                    </div>
                    {agentComps.map((comp) => {
                      const isSelected = comp.slug === activeCompetition;
                      return (
                        <button
                          key={comp.slug}
                          onClick={() => {
                            onSelectCompetition(comp.slug);
                            setDropdownOpen(false);
                          }}
                          className={`w-full flex items-center justify-between p-2.5 text-left transition-colors ${
                            isSelected ? 'bg-blue-50/70' : 'hover:bg-slate-50'
                          }`}
                        >
                          <div className="flex flex-col min-w-0 pr-2">
                            <span className={`font-medium truncate ${isSelected ? 'text-blue-900 font-semibold' : 'text-slate-800'}`}>
                              {comp.title || comp.slug}
                            </span>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="font-mono text-[10px] text-slate-400 truncate">
                                {comp.slug}
                              </span>
                              <span className="px-1.5 py-0.2 rounded bg-purple-50 text-[9px] font-medium text-purple-700 border border-purple-200">
                                Agent / Sim
                              </span>
                            </div>
                          </div>
                          {isSelected && <Check size={14} className="text-blue-600 shrink-0" />}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Group 4: Other / Submissions Closed */}
                {otherComps.length > 0 && (
                  <div>
                    <div className="px-3 py-1.5 bg-slate-50 text-[10px] font-semibold text-slate-500 uppercase tracking-wider flex items-center justify-between">
                      <span>Other / Submissions Closed ({otherComps.length})</span>
                      <span className="text-[9px] font-normal text-slate-400">Archived</span>
                    </div>
                    {otherComps.map((comp) => {
                      const isSelected = comp.slug === activeCompetition;
                      return (
                        <button
                          key={comp.slug}
                          onClick={() => {
                            onSelectCompetition(comp.slug);
                            setDropdownOpen(false);
                          }}
                          className={`w-full flex items-center justify-between p-2.5 text-left transition-colors ${
                            isSelected ? 'bg-blue-50/70' : 'hover:bg-slate-50'
                          }`}
                        >
                          <div className="flex flex-col min-w-0 pr-2">
                            <span className={`font-medium truncate ${isSelected ? 'text-blue-900 font-semibold' : 'text-slate-600'}`}>
                              {comp.title || comp.slug}
                            </span>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="font-mono text-[10px] text-slate-400 truncate">
                                {comp.slug}
                              </span>
                              <span className="px-1.5 py-0.2 rounded bg-slate-100 text-[9px] font-mono text-slate-500">
                                Blocked / Closed
                              </span>
                            </div>
                          </div>
                          {isSelected && <Check size={14} className="text-blue-600 shrink-0" />}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {status?.current_stage && status.current_stage !== 'Idle' && (
          <span className="text-xs text-slate-500 flex items-center gap-1">
            <Activity size={12} className="text-blue-500" />
            Stage: <span className="font-medium text-slate-700">{status.current_stage}</span>
          </span>
        )}
      </div>

      {/* Right: Sync time & Manual Refresh */}
      <div className="flex items-center gap-4 text-xs text-slate-500">
        <div className="flex items-center gap-1.5">
          <Clock size={13} className="text-slate-400" />
          <span>Last sync:</span>
          <span className="font-mono text-slate-700">{formatTime(status?.last_sync_time)}</span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-1.5 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors disabled:opacity-50"
          title="Refresh Registry & Status"
        >
          <RefreshCw size={14} className={isRefreshing ? 'animate-spin text-blue-600' : ''} />
        </button>
      </div>
    </header>
  );
};
