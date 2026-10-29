import React, { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { OverviewPage } from './pages/OverviewPage';
import { CompetitionsPage } from './pages/CompetitionsPage';
import { ResearchPage } from './pages/ResearchPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { ArtifactsPage } from './pages/ArtifactsPage';
import { SubmissionsPage } from './pages/SubmissionsPage';
import { LeaderboardHistoryPage } from './pages/LeaderboardHistoryPage';
import { ExecutionQueuePage } from './pages/ExecutionQueuePage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './api/client';
import type { GlobalStatus } from './types';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<string>('overview');
  const [navParams, setNavParams] = useState<any>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [status, setStatus] = useState<GlobalStatus | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchGlobalStatus = async () => {
    try {
      const data = await api.getStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  useEffect(() => {
    fetchGlobalStatus();
    const interval = setInterval(fetchGlobalStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await fetchGlobalStatus();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleNavigate = (page: string, params?: any) => {
    setActivePage(page);
    setNavParams(params || null);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#f8fafc] text-slate-900 font-sans">
      {/* Persistent Left Sidebar */}
      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
        accountInfo={status?.account}
      />

      {/* Main Application Area */}
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        {/* Persistent Global Status Header */}
        <Header
          status={status}
          onOpenQueue={() => handleNavigate('queue')}
          onRefresh={handleManualRefresh}
          isRefreshing={isRefreshing}
        />

        {/* Scrollable Main Content Container */}
        <main className="flex-1 overflow-y-auto px-6 py-6 max-w-7xl w-full mx-auto">
          {activePage === 'overview' && (
            <OverviewPage
              onNavigate={handleNavigate}
              onOpenQueue={() => handleNavigate('queue')}
            />
          )}
          {activePage === 'competitions' && (
            <CompetitionsPage
              onNavigate={handleNavigate}
              onOpenQueue={() => handleNavigate('queue')}
              initialSlug={navParams?.slug}
            />
          )}
          {activePage === 'research' && (
            <ResearchPage
              onNavigate={handleNavigate}
              onOpenQueue={() => handleNavigate('queue')}
              initialSlug={navParams?.slug}
            />
          )}
          {activePage === 'experiments' && (
            <ExperimentsPage
              onOpenQueue={() => handleNavigate('queue')}
              initialExpId={navParams?.expId}
            />
          )}
          {activePage === 'artifacts' && <ArtifactsPage />}
          {activePage === 'submissions' && (
            <SubmissionsPage onOpenQueue={() => handleNavigate('queue')} />
          )}
          {activePage === 'leaderboard' && <LeaderboardHistoryPage />}
          {activePage === 'queue' && <ExecutionQueuePage />}
          {activePage === 'settings' && <SettingsPage />}
        </main>
      </div>
    </div>
  );
};

export default App;
