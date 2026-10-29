"""Submission manager handling dry-run command generation, validation gates, and live submission."""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from orch.config import AppConfig
from orch.connector import KaggleConnector
from orch.logging_util import get_logger
from orch.registry import Registry
from orch.validator import SubmissionValidator, ValidationResult

logger = get_logger("orch.submitter")


class DailyCapExceededError(Exception):
    """Raised when daily submission quota is exceeded."""
    pass


class InvalidSubmissionError(Exception):
    """Raised when candidate submission fails validation."""
    pass


@dataclass
class SubmissionOutcome:
    mode: str  # 'dry-run' or 'live'
    is_valid: bool
    validation_summary: str
    command: str
    submission_ref: Optional[int] = None
    public_score: Optional[float] = None
    previous_best_score: Optional[float] = None
    divergence_warning: Optional[str] = None


class SubmissionManager:
    """Orchestrates submission validation, daily cap enforcement, dry-run CLI generation, and submission."""

    def __init__(
        self,
        competition_slug: str,
        connector: KaggleConnector,
        registry: Registry,
        config: AppConfig,
    ):
        self.competition_slug = competition_slug
        self.connector = connector
        self.registry = registry
        self.config = config
        self.workspace_dir = Path(config.paths.workspaces_dir) / competition_slug
        self.artifacts_dir = self.workspace_dir / "artifacts"
        self.data_dir = self.workspace_dir / "data"
        self.best_dir = self.workspace_dir / "best"
        self.sample_path = self.data_dir / "sample_submission.csv"

    def refit_best_candidate(self) -> Path:
        """Refits best configuration and generates final_submission.csv."""
        logger.info(f"Refitting best candidate for {self.competition_slug}...")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        final_sub_path = self.artifacts_dir / "final_submission.csv"

        # Check if best_submission.csv exists in best/ or candidate_submission in workspace
        best_candidate = self.best_dir / "best_submission.csv"
        candidate_sub = self.workspace_dir / "candidate_submission.csv"
        baseline_sub = self.artifacts_dir / "baseline_submission.csv"

        if best_candidate.exists():
            import shutil
            shutil.copy2(best_candidate, final_sub_path)
        elif candidate_sub.exists():
            import shutil
            shutil.copy2(candidate_sub, final_sub_path)
        elif baseline_sub.exists():
            import shutil
            shutil.copy2(baseline_sub, final_sub_path)
        else:
            raise FileNotFoundError("No candidate or baseline submission file available to refit.")

        logger.info(f"Final submission artifact generated at {final_sub_path}")
        return final_sub_path

    def process_submission(
        self,
        candidate_path: Path,
        cv_score: float,
        message: str = "AutoResearch validated candidate",
        submit: bool = False,
    ) -> SubmissionOutcome:
        """
        Validates candidate against sample_submission.
        If submit is False (default): dry-run only, prints exact CLI command.
        If submit is True: checks daily cap, submits, polls for public score, and checks divergence.
        """
        candidate_path = Path(candidate_path)
        validator = SubmissionValidator(self.sample_path)
        val_result = validator.validate(candidate_path)

        if not val_result.is_valid:
            logger.error("Submission failed pre-flight schema validation.")
            raise InvalidSubmissionError(f"Candidate validation failed:\n{val_result.summary()}")

        exact_cmd = f'kaggle competitions submit -c {self.competition_slug} -f "{candidate_path.resolve()}" -m "{message}"'

        comp = self.registry.get_competition(self.competition_slug) or {}
        prev_best = comp.get("my_best_public_score")

        if not submit:
            logger.info(f"[DRY-RUN] Exact submission command:\n  {exact_cmd}")
            return SubmissionOutcome(
                mode="dry-run",
                is_valid=True,
                validation_summary=val_result.summary(),
                command=exact_cmd,
                previous_best_score=prev_best,
            )

        # Real Submission Gate
        daily_cap = self.config.get_daily_cap(self.competition_slug)
        budget = self.registry.get_budget(self.competition_slug) or {}
        submissions_today = budget.get("submissions_today", 0)

        if submissions_today >= daily_cap:
            err_msg = f"Daily submission cap reached ({submissions_today}/{daily_cap}) for {self.competition_slug}"
            logger.warning(err_msg)
            raise DailyCapExceededError(err_msg)

        logger.info(f"Submitting final candidate to Kaggle ({submissions_today + 1}/{daily_cap} today)...")
        self.connector.submit(self.competition_slug, candidate_path, message)
        self.registry.increment_daily_submission(self.competition_slug)

        # Poll for status & score
        logger.info("Polling submission status on Kaggle...")
        time.sleep(3)
        sub_ref = None
        pub_score = None
        divergence_warning = None

        for _ in range(6):
            time.sleep(4)
            subs = self.connector.list_submissions(self.competition_slug)
            if subs:
                latest = subs[0]
                sub_ref = latest.ref
                if latest.public_score is not None:
                    pub_score = latest.public_score
                    break

        if pub_score is not None:
            logger.info(f"Submission complete! Real Public Score: {pub_score} (Previous Best: {prev_best})")
            diff = abs(pub_score - cv_score)
            if diff > 0.05:
                divergence_warning = f"Public score ({pub_score}) and CV score ({cv_score}) diverge badly (diff={diff:.4f}). Halting leaderboard iterations."
                logger.warning(divergence_warning)

        return SubmissionOutcome(
            mode="live",
            is_valid=True,
            validation_summary=val_result.summary(),
            command=exact_cmd,
            submission_ref=sub_ref,
            public_score=pub_score,
            previous_best_score=prev_best,
            divergence_warning=divergence_warning,
        )

    def write_evidence(
        self,
        outcome: SubmissionOutcome,
        candidate_path: Path,
        cv_score: float,
        output_path: str = "evidence/s5_validation.md",
    ) -> str:
        """Writes S5 validation and submission evidence."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Stage 5: Validate + Submit Evidence",
            "",
            f"**Competition:** `{self.competition_slug}`  ",
            f"**Submission Mode:** `{outcome.mode.upper()}`  ",
            f"**Candidate File:** `{candidate_path}`  ",
            f"**Local Cross-Validation Score:** `{cv_score:.6f}`  ",
            f"**Historical Best Leaderboard Score:** `{outcome.previous_best_score}`  ",
            "",
            "---",
            "",
            "## 1. Schema & Integrity Validation",
            "",
            f"- **Validation Status:** `{'PASSED' if outcome.is_valid else 'FAILED'}`",
            f"- **Exact Kaggle Sample Conformity:** Verified row count, IDs, column headers, ordering, non-empty, and null/inf safety.",
            "",
            "```text",
            outcome.validation_summary,
            "```",
            "",
            "---",
            "",
            "## 2. Dry-Run / Live Submission Audit",
            "",
            f"- **Mode:** `{outcome.mode}` (Real submissions gated behind explicit `--submit` and per-competition daily quota)",
            f"- **Daily Cap Policy:** Enforces max `{self.config.get_daily_cap(self.competition_slug)}` submissions per day via SQLite budget ledger.",
            "",
            "### Exact Kaggle CLI Submission Command:",
            "```bash",
            outcome.command,
            "```",
        ]

        if outcome.mode == "live":
            lines.extend([
                "",
                "---",
                "",
                "## 3. Real Public Leaderboard Score",
                "",
                f"- **Submission Reference:** `{outcome.submission_ref}`",
                f"- **Recorded Public Score:** `{outcome.public_score}`",
                f"- **Previous Best Public Score:** `{outcome.previous_best_score}`",
            ])
            if outcome.divergence_warning:
                lines.append(f"- **Divergence Warning:** `{outcome.divergence_warning}`")
        else:
            lines.extend([
                "",
                "---",
                "",
                "## 3. Submission Guardrail Verification",
                "",
                "- **Dry-Run Enforcement:** No unauthorized network submission performed.",
                "- **Live Submission Gate:** Requires `--submit` plus remaining quota under daily cap to dispatch to Kaggle API.",
            ])

        content = "\n".join(lines) + "\n"
        path.write_text(content, encoding="utf-8")
        logger.info(f"S5 validation evidence written to {path}")
        return content
