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

/**
 * Handle API responses with agent-ready error parsing.
 * Formats errors cleanly from both string and structured error objects.
 */
async function handleResponse<T>(res: Response, fallbackError: string): Promise<T> {
  if (res.ok) {
    return res.json();
  }
  let errorMsg = fallbackError;
  try {
    const errorData = await res.json();
    if (errorData?.detail) {
      if (typeof errorData.detail === 'object') {
        errorMsg = errorData.detail.message || errorData.detail.hint || JSON.stringify(errorData.detail);
      } else {
        errorMsg = errorData.detail;
      }
    }
  } catch {
    // keep fallback
  }
  throw new Error(errorMsg);
}

export const api = {
  async getStatus(): Promise<GlobalStatus> {
    const res = await fetch(`${BASE_URL}/status`);
    return handleResponse<GlobalStatus>(res, 'Failed to fetch status');
  },

  async setActiveCompetition(slug: string): Promise<{ status: string; active_competition: string }> {
    const res = await fetch(`${BASE_URL}/active_competition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug }),
    });
    return handleResponse(res, 'Failed to set active competition');
  },

  async getOverview(slug?: string): Promise<any> {
    const url = slug ? `${BASE_URL}/overview?slug=${slug}` : `${BASE_URL}/overview`;
    const res = await fetch(url);
    return handleResponse(res, 'Failed to fetch overview data');
  },

  async getCompetitions(params?: { search?: string; kind?: string; status?: string }): Promise<CompetitionSummary[]> {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.kind) query.append('kind', params.kind);
    if (params?.status) query.append('status', params.status);
    const res = await fetch(`${BASE_URL}/competitions?${query.toString()}`);
    return handleResponse<CompetitionSummary[]>(res, 'Failed to fetch competitions');
  },

  async getCompetitionDetails(slug: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/competitions/${slug}`);
    return handleResponse(res, `Failed to fetch details for ${slug}`);
  },

  async getResearch(slug: string): Promise<{
    competition_slug: string;
    workflow_stages: Array<{ name: string; status: string; description: string }>;
    notebooks: NotebookRecord[];
    synthesis_markdown: string;
  }> {
    const res = await fetch(`${BASE_URL}/research/${slug}`);
    return handleResponse(res, `Failed to fetch research for ${slug}`);
  },

  async getExperiments(slug?: string): Promise<ExperimentRecord[]> {
    const url = slug ? `${BASE_URL}/experiments?slug=${slug}` : `${BASE_URL}/experiments`;
    const res = await fetch(url);
    return handleResponse<ExperimentRecord[]>(res, 'Failed to fetch experiments');
  },

  async getExperimentDetails(id: number): Promise<any> {
    const res = await fetch(`${BASE_URL}/experiments/${id}`);
    return handleResponse(res, `Failed to fetch experiment #${id}`);
  },

  async getArtifacts(slug?: string): Promise<ArtifactRecord[]> {
    const url = slug ? `${BASE_URL}/artifacts?slug=${slug}` : `${BASE_URL}/artifacts`;
    const res = await fetch(url);
    return handleResponse<ArtifactRecord[]>(res, 'Failed to fetch artifacts');
  },

  async getSubmissions(slug?: string): Promise<SubmissionRecord[]> {
    const url = slug ? `${BASE_URL}/submissions?slug=${slug}` : `${BASE_URL}/submissions`;
    const res = await fetch(url);
    return handleResponse<SubmissionRecord[]>(res, 'Failed to fetch submissions');
  },

  async getLeaderboard(slug: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/leaderboard/${slug}`);
    return handleResponse(res, `Failed to fetch leaderboard for ${slug}`);
  },

  async getQueue(): Promise<{
    current_task: QueueTask | null;
    queued_tasks: QueueTask[];
    history: QueueTask[];
    concurrency: { active_workers: number; max_workers: number };
  }> {
    const res = await fetch(`${BASE_URL}/queue`);
    return handleResponse(res, 'Failed to fetch queue');
  },

  async cancelTask(taskId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/queue/cancel/${taskId}`, { method: 'POST' });
    return handleResponse(res, 'Failed to cancel task');
  },

  async getSettings(): Promise<SettingsData> {
    const res = await fetch(`${BASE_URL}/settings`);
    return handleResponse<SettingsData>(res, 'Failed to fetch settings');
  },

  // Actions
  async syncCompetitions(): Promise<{ status: string; task_id: string }> {
    const res = await fetch(`${BASE_URL}/actions/sync_competitions`, { method: 'POST' });
    return handleResponse(res, 'Failed to trigger competition sync');
  },

  async runResearch(slug: string): Promise<{ status: string; task_id: string }> {
    const res = await fetch(`${BASE_URL}/actions/run_research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ competition_slug: slug }),
    });
    return handleResponse(res, 'Failed to start research task');
  },

  async runBaseline(slug: string): Promise<{ status: string; task_id: string }> {
    const res = await fetch(`${BASE_URL}/actions/run_baseline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ competition_slug: slug }),
    });
    return handleResponse(res, 'Failed to start baseline task');
  },

  async runExperiment(slug: string): Promise<{ status: string; task_id: string }> {
    const res = await fetch(`${BASE_URL}/actions/run_experiment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ competition_slug: slug }),
    });
    return handleResponse(res, 'Failed to start experiment loop');
  },

  async validateSubmission(slug: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/actions/validate_submission`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ competition_slug: slug }),
    });
    return handleResponse(res, 'Validation failed');
  },

  async submitCandidate(slug: string, authorize: boolean, message?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/actions/submit_candidate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ competition_slug: slug, authorize, message }),
    });
    return handleResponse(res, 'Live submission failed');
  },
};
