import type {
  GlobalStatus,
  OverviewMetrics,
  CompetitionSummary,
  NotebookRecord,
  ExperimentRecord,
  SubmissionRecord,
  ArtifactRecord,
  QueueTask,
  SettingsData,
} from '../types';

const BASE_URL = '/api';

export const api = {
  async getStatus(): Promise<GlobalStatus> {
    const res = await fetch(`${BASE_URL}/status`);
    if (!res.ok) throw new Error('Failed to fetch status');
    return res.json();
  },

  async setActiveCompetition(slug: string): Promise<{ status: string; active_competition: string }> {
    const res = await fetch(`${BASE_URL}/active_competition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug }),
    });
    if (!res.ok) throw new Error('Failed to set active competition');
    return res.json();
  },

  async getOverview(slug?: string): Promise<any> {
    const url = slug ? `${BASE_URL}/overview?slug=${slug}` : `${BASE_URL}/overview`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch overview data');
    return res.json();
  },

  async getCompetitions(params?: { search?: string; kind?: string; status?: string }): Promise<CompetitionSummary[]> {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.kind) query.append('kind', params.kind);
    if (params?.status) query.append('status', params.status);
    const res = await fetch(`${BASE_URL}/competitions?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch competitions');
    return res.json();
  },

  async getCompetitionDetails(slug: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/competitions/${slug}`);
    if (!res.ok) throw new Error(`Failed to fetch details for ${slug}`);
    return res.json();
  },

  async getResearch(slug: string): Promise<{
    competition_slug: string;
    workflow_stages: Array<{ name: string; status: string; description: string }>;
    notebooks: NotebookRecord[];
    synthesis_markdown: string;
  }> {
    const res = await fetch(`${BASE_URL}/research/${slug}`);
    if (!res.ok) throw new Error(`Failed to fetch research for ${slug}`);
    return res.json();
  },

  async getExperiments(slug?: string): Promise<ExperimentRecord[]> {
    const url = slug ? `${BASE_URL}/experiments?slug=${slug}` : `${BASE_URL}/experiments`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch experiments');
    return res.json();
  },

  async getExperimentDetails(id: number): Promise<any> {
    const res = await fetch(`${BASE_URL}/experiments/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch experiment ${id}`);
    return res.json();
  },

  async getArtifacts(slug?: string): Promise<ArtifactRecord[]> {
    const url = slug ? `${BASE_URL}/artifacts?slug=${slug}` : `${BASE_URL}/artifacts`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch artifacts');
    return res.json();
  },

  async getSubmissions(slug?: string): Promise<SubmissionRecord[]> {
    const url = slug ? `${BASE_URL}/submissions?slug=${slug}` : `${BASE_URL}/submissions`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch submissions');
    return res.json();
  },

  async getLeaderboard(slug: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/leaderboard/${slug}`);
    if (!res.ok) throw new Error(`Failed to fetch leaderboard for ${slug}`);
    return res.json();
  },

  async getQueue(): Promise<{
    current_task: QueueTask | null;
    queued_tasks: QueueTask[];
    history: QueueTask[];
    concurrency: { active_workers: number; max_workers: number };
  }> {
    const res = await fetch(`${BASE_URL}/queue`);
    if (!res.ok) throw new Error('Failed to fetch queue');
    return res.json();
  },

  async cancelTask(taskId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/queue/cancel/${taskId}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to cancel task');
    return res.json();
  },

  async getSettings(): Promise<SettingsData> {
    const res = await fetch(`${BASE_URL}/settings`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
  },

  // Actions
  async syncCompetitions(): Promise<{ status: string; task_id: string }> {
    const res = await fetch(`${BASE_URL}/actions/sync_competitions`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to trigger competition sync');
    return res.json();
  },

  async runResearch(slug: string): Promise<{ status: string; task_id: string }> {
    const res = await fetch(`${BASE_URL}/actions/run_research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ competition_slug: slug }),
    });
    if (!res.ok) throw new Error('Failed to start research task');
    return res.json();
  },

  async runBaseline(slug: string): Promise<{ status: string; task_id: string }> {
    const res = await fetch(`${BASE_URL}/actions/run_baseline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ competition_slug: slug }),
    });
    if (!res.ok) throw new Error('Failed to start baseline task');
    return res.json();
  },

  async runExperiment(slug: string): Promise<{ status: string; task_id: string }> {
    const res = await fetch(`${BASE_URL}/actions/run_experiment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ competition_slug: slug }),
    });
    if (!res.ok) throw new Error('Failed to start experiment loop');
    return res.json();
  },

  async validateSubmission(slug: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/actions/validate_submission`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ competition_slug: slug }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Validation failed');
    }
    return res.json();
  },

  async submitCandidate(slug: string, authorize: boolean, message?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/actions/submit_candidate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ competition_slug: slug, authorize, message }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Live submission failed');
    }
    return res.json();
  },
};
