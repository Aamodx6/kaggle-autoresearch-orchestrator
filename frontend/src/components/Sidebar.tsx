import React from 'react';
import {
  LayoutDashboard,
  Trophy,
  BookOpen,
  FlaskConical,
  Layers,
  Send,
  TrendingUp,
  Cpu,
  Settings,
  ChevronLeft,
  ChevronRight,
  Terminal,
} from 'lucide-react';

interface SidebarProps {
  activePage: string;
  onNavigate: (page: string) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  accountInfo?: {
    username: string;
    cli_version: string;
    status: string;
    token_present: boolean;
  };
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onNavigate,
  collapsed,
  onToggleCollapse,
  accountInfo,
}) => {
  const navGroups = [
    {
      label: 'WORKSPACE',
      items: [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard },
        { id: 'competitions', label: 'Competitions', icon: Trophy },
        { id: 'research', label: 'Research', icon: BookOpen },
      ],
    },
    {
      label: 'EXPERIMENTATION',
      items: [
        { id: 'experiments', label: 'Experiments', icon: FlaskConical },
        { id: 'artifacts', label: 'Models & Artifacts', icon: Layers },
      ],
    },
    {
      label: 'RESULTS',
      items: [
        { id: 'submissions', label: 'Submissions', icon: Send },
        { id: 'leaderboard', label: 'Leaderboard History', icon: TrendingUp },
      ],
    },
    {
      label: 'SYSTEM',
      items: [
        { id: 'queue', label: 'Execution Queue', icon: Cpu },
        { id: 'settings', label: 'Settings', icon: Settings },
      ],
    },
  ];

  return (
    <aside
      className={`relative flex flex-col border-r border-slate-200 bg-white transition-all duration-200 ease-in-out select-none ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="flex h-14 items-center justify-between px-4 border-b border-slate-200">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-white font-bold text-sm shrink-0">
            KR
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="font-semibold text-sm text-slate-900 tracking-tight">Kaggle Research</span>
              <span className="text-[11px] text-slate-400 font-mono">v0.1.0</span>
            </div>
          )}
        </div>
        <button
          onClick={onToggleCollapse}
          className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto py-3 px-2 space-y-5">
        {navGroups.map((group) => (
          <div key={group.label} className="space-y-1">
            {!collapsed && (
              <div className="px-2 text-[10px] font-semibold text-slate-400 tracking-wider">
                {group.label}
              </div>
            )}
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  title={collapsed ? item.label : undefined}
                  className={`group relative flex w-full items-center gap-2.5 px-2.5 py-1.5 rounded-md text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Icon
                    size={17}
                    className={`shrink-0 transition-colors ${
                      isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-700'
                    }`}
                  />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Footer: Connected Account */}
      <div className="border-t border-slate-200 p-3 bg-slate-50/50">
        <div className="flex items-center gap-2.5">
          <div className="relative shrink-0">
            <div className="h-8 w-8 rounded-full bg-slate-200 border border-slate-300 flex items-center justify-center font-semibold text-xs text-slate-700">
              {accountInfo?.username ? accountInfo.username.substring(0, 2).toUpperCase() : 'AG'}
            </div>
            <span className="absolute bottom-0 right-0 h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="text-xs font-medium text-slate-800 truncate">
                {accountInfo?.username || 'aamod'}
              </span>
              <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                <Terminal size={10} /> CLI {accountInfo?.cli_version || '2.2.5'}
              </span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
