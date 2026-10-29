"""Discovery module for detecting, classifying, and registering Kaggle competitions."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from orch.config import AppConfig
from orch.connector import KaggleConnector, CompetitionMetadata
from orch.logging_util import get_logger
from orch.registry import Registry

logger = get_logger("orch.discovery")

MAXIMIZE_METRICS = {
    "auc", "roc", "accuracy", "f1", "map", "precision", "recall",
    "spearman", "pearson", "qwk", "cohen", "r2", "sharpe", "balanced accuracy", "score"
}

MINIMIZE_METRICS = {
    "loss", "logloss", "rmse", "mse", "mae", "error", "rmsle", "brier", "distance"
}


def infer_direction(metric_name: str) -> str:
    """Infers whether higher or lower is better for the given metric."""
    m_lower = metric_name.lower().strip()
    for term in MINIMIZE_METRICS:
        if term in m_lower:
            return "minimize"
    for term in MAXIMIZE_METRICS:
        if term in m_lower:
            return "maximize"
    return "maximize"


def classify_competition(
    comp: CompetitionMetadata,
    files: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[str, str]:
    """
    Classifies competition kind and status.
    Returns: (kind, status)
    Kinds: csv_tabular, csv_cv, csv_nlp, code_competition, agent_or_optimization, other
    Statuses: supported, report_only, blocked: <reason>
    """
    if comp.submissions_disabled:
        return "other", "blocked: submissions disabled"

    if comp.is_kernels_submissions_only:
        return "code_competition", "report_only"

    slug_lower = comp.slug.lower()
    title_lower = comp.title.lower()

    if any(k in slug_lower or k in title_lower for k in [
        "quantum", "connectx", "pokemon", "agent", "squares-in-squares", "simulation", "game"
    ]):
        return "agent_or_optimization", "report_only"

    if files is not None:
        file_names = [f["name"].lower() for f in files]
        has_train_csv = any("train.csv" in fn for fn in file_names)
        has_test_csv = any("test.csv" in fn for fn in file_names)

        # Check for image files/zip/dicom
        has_images = any(fn.endswith((".jpg", ".png", ".jpeg", ".dcm", ".tif")) for fn in file_names)
        # Check text/nlp cues
        has_nlp = any(k in slug_lower or k in title_lower for k in ["nlp", "text", "sentiment", "essay", "llm"])

        if has_images:
            return "csv_cv", "supported"
        if has_nlp:
            return "csv_nlp", "supported"
        if has_train_csv or has_test_csv:
            return "csv_tabular", "supported"

    # Default heuristic based on category/title
    if "playground" in slug_lower:
        return "csv_tabular", "supported"

    return "other", "report_only"


class DiscoveryService:
    """Discovers entered Kaggle competitions and populates SQLite registry."""

    def __init__(self, connector: KaggleConnector, registry: Registry, config: AppConfig):
        self.connector = connector
        self.registry = registry
        self.config = config

    def discover_all(self, incremental: bool = True) -> List[Dict[str, Any]]:
        """
        Discovers all entered competitions, retrieves user's submissions,
        classifies each kind, and persists to SQLite registry.
        """
        logger.info("Starting competition discovery...")
        entered_comps = self.connector.list_entered_competitions()
        discovered = []

        for comp in entered_comps:
            slug = comp.slug
            existing = self.registry.get_competition(slug) if incremental else None

            if existing and incremental:
                logger.info(f"Skipping already-discovered competition: {slug}")
                discovered.append(existing)
                continue

            logger.info(f"Processing entered competition: {slug}...")

            # List competition files if not code-only to classify kind
            files = None
            if not comp.is_kernels_submissions_only:
                try:
                    files = self.connector.list_competition_files(slug)
                except Exception as fe:
                    logger.warning(f"Could not list files for {slug}: {fe}")

            kind, status = classify_competition(comp, files)
            direction = infer_direction(comp.evaluation_metric)

            # Discover user's submissions for this competition
            my_best_score = None
            my_best_ref = None
            try:
                submissions = self.connector.list_submissions(slug)
                valid_subs = [s for s in submissions if s.public_score is not None]
                if valid_subs:
                    if direction == "maximize":
                        best_sub = max(valid_subs, key=lambda s: s.public_score or -float("inf"))
                    else:
                        best_sub = min(valid_subs, key=lambda s: s.public_score or float("inf"))
                    my_best_score = best_sub.public_score
                    my_best_ref = best_sub.ref

                # Persist submissions
                for s in submissions:
                    self.registry.upsert_submission({
                        "ref": s.ref,
                        "competition_slug": slug,
                        "file_name": s.file_name,
                        "date": s.date,
                        "description": s.description,
                        "status": s.status,
                        "public_score": s.public_score,
                        "private_score": s.private_score,
                        "is_baseline": (s.ref == my_best_ref),
                    })
            except Exception as se:
                logger.warning(f"Could not retrieve submissions for {slug}: {se}")

            comp_record = {
                "slug": slug,
                "id": comp.id,
                "title": comp.title,
                "url": comp.url,
                "deadline": comp.deadline,
                "category": comp.category,
                "reward": comp.reward,
                "evaluation_metric": comp.evaluation_metric,
                "direction": direction,
                "kind": kind,
                "status": status,
                "is_kernels_submissions_only": comp.is_kernels_submissions_only,
                "max_daily_submissions": comp.max_daily_submissions,
                "my_best_public_score": my_best_score,
                "my_best_submission_ref": my_best_ref,
            }

            self.registry.upsert_competition(comp_record)

            # Initialize budget
            daily_cap = self.config.get_daily_cap(slug)
            self.registry.set_budget(
                competition_slug=slug,
                cap=daily_cap,
                timeout_sec=self.config.budgets.experiment_timeout_seconds,
                mem_mb=self.config.budgets.memory_limit_mb,
            )

            discovered.append(comp_record)

        logger.info(f"Discovery complete. Total entered competitions processed: {len(discovered)}")
        return discovered

    def write_evidence(self, output_path: str = "evidence/s1_discovery.md") -> str:
        """Writes comprehensive discovery evidence markdown."""
        comps = self.registry.list_competitions()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Stage 1: Registry + Discovery Evidence",
            "",
            f"**Total Entered Competitions Discovered:** {len(comps)}  ",
            "**Registry Database:** `registry.db` (SQLite)  ",
            "",
            "---",
            "",
            "## 1. Discovered Competitions Matrix",
            "",
            "| Slug | Kind | Status | Metric | Direction | Best Score | Deadline |",
            "|---|---|---|---|---|---|---|",
        ]

        for c in comps:
            score_str = f"{c['my_best_public_score']:.5f}" if c.get("my_best_public_score") is not None else "None"
            deadline_str = c.get("deadline", "N/A")[:10] if c.get("deadline") else "N/A"
            lines.append(
                f"| `{c['slug']}` | `{c['kind']}` | `{c['status']}` | {c['evaluation_metric']} | {c['direction']} | {score_str} | {deadline_str} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 2. Classification Breakdown",
            "",
            "- **Supported (`csv_*`):** Automated keep/revert loop, metric validation, and submission pipeline enabled.",
            "- **Report Only (`code_competition`, `agent_or_optimization`, `other`):** Discovered, metadata tracked, reports generated, but autonomous file loop disabled as required.",
            "",
            "### Supported Competitions Summary:",
        ])

        supported = [c for c in comps if c.get("status") == "supported"]
        for s in supported:
            lines.append(
                f"- **`{s['slug']}`** ({s['kind']}): Metric `{s['evaluation_metric']}` ({s['direction']}), Best Baseline: `{s.get('my_best_public_score')}`"
            )

        content = "\n".join(lines) + "\n"
        path.write_text(content, encoding="utf-8")
        logger.info(f"Discovery evidence written to {path}")
        return content
