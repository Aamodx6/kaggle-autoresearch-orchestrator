export type OrchestratorState =
  | 'Idle'
  | 'Discovering'
  | 'Researching'
  | 'Training'
  | 'Validating'
  | 'Submitting'
  | 'Completed'
  | 'Failed';

export interface GlobalStatus {
  state: OrchestratorState;
  active_competition: string;
  current_stage: string;
  queued_tasks_count: number;
  last_sync_time: string;
  account: {
    username: string;
    cli_version: string;
    status: string;
    token_present: boolean;
  };
}

export interface OverviewMetrics {
  joined_competitions: number;
  supported_competitions: number;
  active_research_runs: number;
  experiments_completed: number;
  best_validation_improvement: {
    competition: string;
    metric_name: string;
    direction: string;
    original_value: number;
    current_value: number;
    delta: number;
    has_improved: boolean;
  };
  pending_submissions: number;
  daily_cap: number;
  submissions_today: number;
}

export interface CompetitionSummary {
  slug: string;
  id?: number;
  title?: string;
  url?: string;
  deadline?: string;
  category?: string;
  reward?: string;
  evaluation_metric?: string;
  direction?: string;
  kind?: string;
  status: string;
  my_best_public_score?: number;
  best_validation_score?: number;
  research_status?: string;
  submissions_count?: number;
  last_updated?: string;
}

export interface NotebookRecord {
  ref: string;
  competition_slug: string;
  title: string;
  author: string;
  slug: string;
  total_votes: number;
  best_score?: number;
  url?: string;
  techniques_extracted?: string;
  license?: string;
  is_reproducible: number;
}

export interface ExperimentRecord {
  id: number;
  competition_slug: string;
  commit_hash?: string;
  cv_mean?: number;
  cv_std?: number;
  runtime_sec?: number;
  memory_mb?: number;
  status: string;
  description?: string;
  created_at?: string;
}

export interface SubmissionRecord {
  ref: number;
  competition_slug: string;
  file_name: string;
  date?: string;
  description?: string;
  status?: string;
  public_score?: number;
  private_score?: number;
  is_baseline: number;
  created_at?: string;
}

export interface ArtifactRecord {
  name: string;
  type: string;
  competition: string;
  version: string;
  size_bytes: number;
  size_formatted: string;
  created_at: string;
  path: string;
}

export interface QueueTask {
  id: string;
  name: string;
  competition_slug: string;
  stage: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  start_time?: string;
  end_time?: string;
  elapsed_time?: string;
  resource_allocation: string;
  logs: string[];
  error?: string;
}

export interface SettingsData {
  kaggle: {
    username: string;
    cli_version: string;
    token_path: string;
    connected: boolean;
  };
  research: {
    timeout_seconds: number;
    max_experiments: number;
    patience: number;
    min_delta_folds: number;
    random_seed: number;
    default_competition: string;
  };
  compute: {
    gpu: string;
    cpu_cores: number;
    max_concurrent_runs: number;
    sandbox_worktree_enabled: boolean;
  };
  submissions: {
    dry_run_default: boolean;
    daily_cap_default: number;
    require_approval: boolean;
    per_competition_caps: Record<string, number>;
  };
  storage: {
    workspaces_dir: string;
    research_dir: string;
    registry_db: string;
    reports_dir: string;
    evidence_dir: string;
  };
}
