/**
 * Centralized formatting and display utilities for Kaggle AutoResearch Orchestrator.
 * Extracted via gstack /deslop-shared-libs to eliminate duplicate formatting logic.
 */

export interface DeadlineInfo {
  text: string;
  isPast: boolean;
}

/**
 * Format raw category string into user-friendly category title.
 */
export function formatCategory(cat?: string): string {
  if (!cat) return 'General';
  const lower = cat.toLowerCase();
  if (lower.includes('playground')) return 'Playground Series';
  if (lower.includes('research')) return 'Research';
  if (lower.includes('featured')) return 'Featured';
  if (lower.includes('getting')) return 'Getting Started';
  return cat;
}

/**
 * Format competition kind/format slug into human-readable label.
 */
export function formatKind(kind?: string): string {
  if (!kind) return 'Standard';
  switch (kind) {
    case 'csv_tabular':
      return 'Tabular';
    case 'code_competition':
      return 'Code Competition';
    case 'csv_cv':
      return 'Computer Vision';
    case 'agent_or_optimization':
      return 'Agent Simulation';
    default:
      return kind.replace(/_/g, ' ');
  }
}

/**
 * Detailed modality badge text with execution support level.
 */
export function formatKindBadge(kind?: string): string {
  switch (kind) {
    case 'csv_tabular':
      return 'Tabular (Supported)';
    case 'code_competition':
      return 'Code Competition (Report Only)';
    case 'csv_cv':
      return 'Computer Vision (Report Only)';
    case 'agent_or_optimization':
      return 'Agent Simulation (Report Only)';
    default:
      return 'Custom Format (Report Only)';
  }
}

/**
 * Format competition reward / prize pool.
 */
export function formatReward(reward?: string): string {
  if (!reward || reward.toLowerCase() === 'none') return 'Knowledge';
  const lower = reward.toLowerCase();
  if (lower === 'swag') return 'Swag / Badges';
  if (!reward.includes('$') && lower.includes('usd')) {
    return `$${reward.toUpperCase()}`;
  }
  return reward;
}

/**
 * Format competition deadline relative to current time.
 */
export function formatDeadline(deadlineStr?: string): DeadlineInfo {
  if (!deadlineStr) return { text: 'Ongoing', isPast: false };
  try {
    const date = new Date(deadlineStr);
    if (isNaN(date.getTime())) return { text: deadlineStr, isPast: false };

    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return {
        text: `Ended ${date.toLocaleDateString([], { month: 'short', year: 'numeric' })}`,
        isPast: true,
      };
    }
    if (diffDays < 30) {
      return { text: `${diffDays} days remaining`, isPast: false };
    }
    const months = Math.ceil(diffDays / 30);
    return { text: `${months} months remaining`, isPast: false };
  } catch {
    return { text: deadlineStr, isPast: false };
  }
}

/**
 * Format floating point scores consistently (e.g. 0.95438).
 */
export function formatScore(score?: number | null, fallback = '—', decimals = 5): string {
  if (score === null || score === undefined || isNaN(score)) return fallback;
  return Number(score).toFixed(decimals);
}

/**
 * Format byte sizes into KB / MB.
 */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
