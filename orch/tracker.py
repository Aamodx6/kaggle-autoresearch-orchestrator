"""Tracker module for results.tsv and experiment history."""

import csv
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from orch.logging_util import get_logger
from orch.registry import Registry

logger = get_logger("orch.tracker")


class ExperimentTracker:
    """Manages results.tsv logging and best checkpoint tracking."""

    def __init__(self, workspace_dir: Path, competition_slug: str, registry: Registry):
        self.workspace_dir = Path(workspace_dir)
        self.competition_slug = competition_slug
        self.registry = registry
        self.results_tsv_path = self.workspace_dir / "results.tsv"
        self.best_dir = self.workspace_dir / "best"
        self.best_dir.mkdir(parents=True, exist_ok=True)

    def log_result(
        self,
        commit_hash: str,
        cv_mean: Optional[float],
        cv_std: Optional[float],
        runtime_sec: float,
        memory_mb: float,
        status: str,
        description: str,
    ) -> None:
        """Appends a row to results.tsv and registers in SQLite."""
        cv_mean_str = f"{cv_mean:.6f}" if cv_mean is not None else "N/A"
        cv_std_str = f"{cv_std:.6f}" if cv_std is not None else "N/A"

        row = [
            commit_hash,
            cv_mean_str,
            cv_std_str,
            f"{runtime_sec:.1f}",
            f"{memory_mb:.0f}",
            status,
            description,
        ]

        with open(self.results_tsv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(row)

        self.registry.record_experiment({
            "competition_slug": self.competition_slug,
            "commit_hash": commit_hash,
            "cv_mean": cv_mean,
            "cv_std": cv_std,
            "runtime_sec": runtime_sec,
            "memory_mb": memory_mb,
            "status": status,
            "description": description,
        })
        logger.info(f"Logged result: {status.upper()} - {description} (CV: {cv_mean_str})")

    def save_best(self, train_path: Path, candidate_submission: Optional[Path] = None) -> None:
        """Saves current best train.py and candidate submission into best/."""
        dest_train = self.best_dir / "train.py"
        shutil.copy2(train_path, dest_train)

        if candidate_submission and candidate_submission.exists():
            dest_sub = self.best_dir / "best_submission.csv"
            shutil.copy2(candidate_submission, dest_sub)
        logger.info(f"Updated best checkpoint in {self.best_dir}")

    def revert_to_best(self, train_path: Path) -> None:
        """Reverts working train.py from best/train.py."""
        src_train = self.best_dir / "train.py"
        if src_train.exists():
            shutil.copy2(src_train, train_path)
            logger.info("Reverted train.py to last known best checkpoint.")
        else:
            logger.warning("No best/train.py found to revert to.")

    def compute_file_hash(self, file_path: Path) -> str:
        """Computes short sha1 hash of file."""
        content = Path(file_path).read_bytes()
        return hashlib.sha1(content).hexdigest()[:7]
