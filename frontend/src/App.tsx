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
import type { GlobalStatus, CompetitionSummary } from './types';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<string>('overview');
  const [navParams, setNavParams] = useState<any>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [status, setStatus] = useState<GlobalStatus | null>(null);
  const [competitions, setCompetitions] = useState<CompetitionSummary[]>([]);
  const [activeCompetition, setActiveCompetition] = useState<string>('playground-series-s6e2');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchGlobalStatus = async () => {
    try {
      const data = await api.getStatus();
      setStatus(data);
      if (data.active_competition && data.active_competition !== 'None') {
        setActiveCompetition(data.active_competition);
      }
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  const fetchCompetitions = async () => {
    try {
      const comps = await api.getCompetitions();
      setCompetitions(comps);
    } catch (err) {
      console.error('Failed to fetch competitions:', err);
    }
  };

  useEffect(() => {
    fetchGlobalStatus();
    fetchCompetitions();
    const interval = setInterval(fetchGlobalStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectCompetition = async (slug: string) => {
    setActiveCompetition(slug);
    try {
      await api.setActiveCompetition(slug);
      fetchGlobalStatus();
    } catch (err) {
      console.error('Failed to update active competition:', err);
    }
  };

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([fetchGlobalStatus(), fetchCompetitions()]);
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleNavigate = (page: string, params?: any) => {
    setActivePage(page);
    setNavParams(params || null);
    setMobileMenuOpen(false);
    if (params?.slug) {
      handleSelectCompetition(params.slug);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#f8fafc] text-slate-900 font-sans">
      {/* Persistent Left Sidebar (Desktop) / Slide-over Drawer (Mobile) */}
      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
        accountInfo={status?.account}
      />

      {/* Main Application Area */}
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        {/* Persistent Global Status Header with Target Dropdown */}
        <Header
          status={status}
          competitions={competitions}
          activeCompetition={activeCompetition}
          onSelectCompetition={handleSelectCompetition}
          onOpenQueue={() => handleNavigate('queue')}
          onRefresh={handleManualRefresh}
          isRefreshing={isRefreshing}
          onToggleMobileMenu={() => setMobileMenuOpen(!mobileMenuOpen)}
        />

        {/* Scrollable Main Content Container */}
        <main className="flex-1 overflow-y-auto px-3 py-4 sm:px-6 sm:py-6 max-w-7xl w-full mx-auto">
          {activePage === 'overview' && (
            <OverviewPage
              activeCompetition={activeCompetition}
              onNavigate={handleNavigate}
              onOpenQueue={() => handleNavigate('queue')}
            />
          )}
          {activePage === 'competitions' && (
            <CompetitionsPage
              activeCompetition={activeCompetition}
              onSelectCompetition={handleSelectCompetition}
              onNavigate={handleNavigate}
              onOpenQueue={() => handleNavigate('queue')}
              initialSlug={navParams?.slug || null}
            />
          )}
          {activePage === 'research' && (
            <ResearchPage
              activeCompetition={activeCompetition}
              onSelectCompetition={handleSelectCompetition}
              onNavigate={handleNavigate}
              onOpenQueue={() => handleNavigate('queue')}
              initialSlug={navParams?.slug || null}
            />
          )}
          {activePage === 'experiments' && (
            <ExperimentsPage
              activeCompetition={activeCompetition}
              onOpenQueue={() => handleNavigate('queue')}
              initialExpId={navParams?.expId}
            />
          )}
          {activePage === 'artifacts' && (
            <ArtifactsPage activeCompetition={activeCompetition} />
          )}
          {activePage === 'submissions' && (
            <SubmissionsPage
              activeCompetition={activeCompetition}
              onOpenQueue={() => handleNavigate('queue')}
            />
          )}
          {activePage === 'leaderboard' && (
            <LeaderboardHistoryPage activeCompetition={activeCompetition} />
          )}
          {activePage === 'queue' && <ExecutionQueuePage />}
          {activePage === 'settings' && <SettingsPage />}
        </main>
      </div>
    </div>
  );
};

export default App;
