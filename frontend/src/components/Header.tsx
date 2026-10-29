import React from 'react';
import { Cpu, RefreshCw, Layers, CheckCircle2, Clock, Activity } from 'lucide-react';
import type { GlobalStatus } from '../types';
import { StatusBadge } from './StatusBadge';

interface HeaderProps {
  status: GlobalStatus | null;
  onOpenQueue: () => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  onOpenQueue,
  onRefresh,
  isRefreshing,
}) => {
  const formatTime = (isoString?: string) => {
    if (!isoString) return 'Never';
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString;
    }
  };

  return (
    <header className="flex h-14 w-full items-center justify-between border-b border-slate-200 bg-white px-6">
      {/* Left: Global Execution Status Indicator */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenQueue}
          className="flex items-center gap-2.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-slate-100/80 px-3 py-1.5 transition-all text-xs"
          title="Click to view full execution queue and live task logs"
        >
          <span className="font-semibold text-slate-500 uppercase tracking-wider text-[10px]">
            System:
          </span>
          <StatusBadge status={status?.state || 'Idle'} size="sm" />

          <div className="h-3 w-px bg-slate-200 mx-1" />

          <div className="flex items-center gap-1.5 text-slate-700">
            <span className="text-slate-400">Target:</span>
            <span className="font-mono font-medium text-slate-800">
              {status?.active_competition || 'None'}
            </span>
          </div>

          {status?.queued_tasks_count ? (
            <span className="ml-1 px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-800 font-mono text-[11px] font-semibold">
              +{status.queued_tasks_count} queued
            </span>
          ) : null}
        </button>

        {status?.current_stage && status.current_stage !== 'Idle' && (
          <span className="text-xs text-slate-500 flex items-center gap-1">
            <Activity size={12} className="text-blue-500 animate-spin" />
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
