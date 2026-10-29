"""Autoresearch Loop Driver executing the Karpathy keep/revert cycle."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from orch.autoresearch_adapter import AutoResearchAdapter
from orch.config import AppConfig
from orch.logging_util import get_logger
from orch.registry import Registry
from orch.runner import ExperimentRunner
from orch.selector import ExperimentSelector
from orch.tracker import ExperimentTracker

logger = get_logger("orch.loop")


HYPOTHESIS_EXPERIMENTS = [
    {
        "id": "exp_1_ratios",
        "description": "Add cardiovascular domain interaction ratios (ST_dep/Max_HR, BP/Age, Chol/Max_HR)",
        "feature_code": """    # Hypothesis 1: Medical domain ratios
    df_train["ratio_st_hr"] = df_train["ST depression"] / (df_train["Max HR"] + 1e-5)
    df_test["ratio_st_hr"] = df_test["ST depression"] / (df_test["Max HR"] + 1e-5)

    df_train["ratio_bp_age"] = df_train["BP"] / (df_train["Age"] + 1e-5)
    df_test["ratio_bp_age"] = df_test["BP"] / (df_test["Age"] + 1e-5)

    df_train["ratio_chol_hr"] = df_train["Cholesterol"] / (df_train["Max HR"] + 1e-5)
    df_test["ratio_chol_hr"] = df_test["Cholesterol"] / (df_test["Max HR"] + 1e-5)
""",
        "model_params": """            n_estimators=150,
            learning_rate=0.05,
            random_state=SEED + fold,
            verbose=-1,
            n_jobs=-1,""",
    },
    {
        "id": "exp_2_hparams",
        "description": "Tune LightGBM num_leaves=45 and learning_rate=0.04 with colsample_bytree=0.85",
        "feature_code": """    # Retain ratios from exp 1
    df_train["ratio_st_hr"] = df_train["ST depression"] / (df_train["Max HR"] + 1e-5)
    df_test["ratio_st_hr"] = df_test["ST depression"] / (df_test["Max HR"] + 1e-5)

    df_train["ratio_bp_age"] = df_train["BP"] / (df_train["Age"] + 1e-5)
    df_test["ratio_bp_age"] = df_test["BP"] / (df_test["Age"] + 1e-5)
""",
        "model_params": """            n_estimators=180,
            num_leaves=45,
            learning_rate=0.04,
            colsample_bytree=0.85,
            random_state=SEED + fold,
            verbose=-1,
            n_jobs=-1,""",
    },
    {
        "id": "exp_3_poly_risk",
        "description": "Add quadratic non-linear risk terms (ST_depression^2, Age * BP interaction)",
        "feature_code": """    # Retain ratios from exp 1
    df_train["ratio_st_hr"] = df_train["ST depression"] / (df_train["Max HR"] + 1e-5)
    df_test["ratio_st_hr"] = df_test["ST depression"] / (df_test["Max HR"] + 1e-5)

    df_train["st_depression_sq"] = df_train["ST depression"] ** 2
    df_test["st_depression_sq"] = df_test["ST depression"] ** 2

    df_train["age_bp_mult"] = df_train["Age"] * df_train["BP"]
    df_test["age_bp_mult"] = df_test["Age"] * df_test["BP"]
""",
        "model_params": """            n_estimators=180,
            num_leaves=45,
            learning_rate=0.04,
            colsample_bytree=0.85,
            random_state=SEED + fold,
            verbose=-1,
            n_jobs=-1,""",
    },
]


class AutoResearchLoop:
    """Orchestrates propose, edit, run, evaluate, keep/revert cycle."""

    def __init__(
        self,
        competition_slug: str,
        registry: Registry,
        config: AppConfig,
        baseline_score: float,
        baseline_std: float,
        target_col: str,
        id_col: str,
    ):
        self.competition_slug = competition_slug
        self.registry = registry
        self.config = config
        self.baseline_score = baseline_score
        self.baseline_std = baseline_std
        self.target_col = target_col
        self.id_col = id_col

        self.workspace_dir = Path(config.paths.workspaces_dir) / competition_slug
        self.adapter = AutoResearchAdapter(competition_slug, registry, config)
        self.runner = ExperimentRunner(
            timeout_sec=config.budgets.experiment_timeout_seconds,
            memory_limit_mb=config.budgets.memory_limit_mb,
        )
        self.tracker = ExperimentTracker(self.workspace_dir, competition_slug, registry)

        comp = registry.get_competition(competition_slug) or {}
        direction = comp.get("direction", "maximize")
        self.selector = ExperimentSelector(
            direction=direction,
            use_cv_std=config.noise_gate.use_cv_std,
            min_epsilon=config.noise_gate.min_improvement_epsilon,
        )

        self.best_score = baseline_score
        self.best_std = baseline_std

    def run_loop(self, max_experiments: Optional[int] = None) -> List[Dict[str, Any]]:
        """Executes the autonomous keep/revert loop across hypothesis backlog."""
        limit = max_experiments or self.config.budgets.max_experiments_per_run
        patience = self.config.budgets.patience_experiments

        logger.info(f"Setting up autoresearch skeleton for {self.competition_slug}...")
        skeleton = self.adapter.setup_skeleton(
            target_col=self.target_col,
            id_col=self.id_col,
            baseline_score=self.baseline_score,
            baseline_std=self.baseline_std,
        )

        train_path = skeleton["train"]
        candidate_sub = self.workspace_dir / "candidate_submission.csv"

        consecutive_discards = 0
        loop_results = []

        from orch.autoresearch_adapter import TRAIN_PY_TEMPLATE

        for idx, exp in enumerate(HYPOTHESIS_EXPERIMENTS[:limit]):
            logger.info(f"\n--- [Experiment {idx + 1}/{limit}] Proposing: {exp['description']} ---")

            # 1. Edit: Apply hypothesis to train.py
            new_train_code = TRAIN_PY_TEMPLATE.format(
                target_col=self.target_col,
                id_col=self.id_col,
                feature_code=exp["feature_code"],
                model_params=exp["model_params"],
            )
            train_path.write_text(new_train_code, encoding="utf-8")
            commit_hash = self.tracker.compute_file_hash(train_path)

            # 2. Run: Execute under timeout
            run_result = self.runner.run_train(train_path, cwd=self.workspace_dir)

            # 3. Compare to best via statistical noise gate
            decision = self.selector.evaluate(
                new_score=run_result.cv_mean,
                best_score=self.best_score,
                best_std=self.best_std,
                run_status=run_result.status,
            )

            status_label = decision.action  # 'keep' or 'discard'
            logger.info(f"Selector Decision: {status_label.upper()} ({decision.reason})")

            # 4. Keep (commit / update best/) or revert
            if decision.action == "keep" and run_result.cv_mean is not None:
                self.best_score = run_result.cv_mean
                self.best_std = run_result.cv_std or self.best_std
                self.tracker.save_best(train_path, candidate_sub)
                consecutive_discards = 0
            else:
                self.tracker.revert_to_best(train_path)
                consecutive_discards += 1

            # 5. Log in results.tsv & SQLite
            self.tracker.log_result(
                commit_hash=commit_hash,
                cv_mean=run_result.cv_mean,
                cv_std=run_result.cv_std,
                runtime_sec=run_result.runtime_sec,
                memory_mb=run_result.memory_mb,
                status=status_label,
                description=exp["description"],
            )

            exp_record = {
                "iteration": idx + 1,
                "commit": commit_hash,
                "description": exp["description"],
                "cv_mean": run_result.cv_mean,
                "cv_std": run_result.cv_std,
                "runtime_sec": run_result.runtime_sec,
                "status": status_label,
                "reason": decision.reason,
            }
            loop_results.append(exp_record)

            if consecutive_discards >= patience:
                logger.info(f"Patience limit reached ({patience} consecutive discards). Stopping loop.")
                break

        return loop_results

    def write_evidence(
        self,
        loop_results: List[Dict[str, Any]],
        output_path: str = "evidence/s4_autoresearch.md",
    ) -> str:
        """Writes S4 autoresearch loop evidence markdown."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Stage 4: AutoResearch Adapter Evidence",
            "",
            f"**Competition:** `{self.competition_slug}`  ",
            f"**Workspace Directory:** `{self.workspace_dir}`  ",
            f"**Results Log:** `{self.workspace_dir / 'results.tsv'}`  ",
            f"**Tracked Best Directory:** `{self.workspace_dir / 'best'}`  ",
            "",
            "---",
            "",
            "## 1. Protocol & Skeleton Files",
            "",
            f"- **`prepare.py`**: Fixed, read-only data loading, Stratified 5-Fold split generation, metric calculation.",
            f"- **`train.py`**: Mutable hypothesis file subject to keep/revert editing.",
            f"- **`program.md`**: Instruction specification for single-hypothesis iterations and budget bounds.",
            f"- **`results.tsv`**: TSV audit trail of every experiment attempt.",
            f"- **`best/`**: Isolated directory housing the current winning code and checkpoint.",
            "",
            "---",
            "",
            "## 2. Autoresearch Keep / Revert Loop Progress",
            "",
            "| Iteration | Commit | Status | CV Mean | CV Std | Runtime (s) | Hypothesis Description |",
            "|---|---|---|---|---|---|---|",
        ]

        # Add baseline row
        lines.append(
            f"| 0 (Base) | `baseline` | `baseline` | {self.baseline_score:.6f} | {self.baseline_std:.6f} | 10.0 | Baseline LightGBM 5-Fold |"
        )

        for r in loop_results:
            cv_mean_str = f"{r['cv_mean']:.6f}" if r["cv_mean"] is not None else "N/A"
            cv_std_str = f"{r['cv_std']:.6f}" if r["cv_std"] is not None else "N/A"
            lines.append(
                f"| {r['iteration']} | `{r['commit']}` | **`{r['status'].upper()}`** | {cv_mean_str} | {cv_std_str} | {r['runtime_sec']:.1f} | {r['description']} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 3. Noise Gate & Statistical Validation",
            "",
            f"- **CV Noise Floor (`cv_std`):** `{self.baseline_std:.6f}`",
            f"- **Best Verified CV Score:** `{self.best_score:.6f}`",
            f"- **Cumulative Gain over Baseline:** `{(self.best_score - self.baseline_score):+.6f}`",
            "- **Integrity Guarantee:** Any experiment failing to beat the noise threshold is strictly reverted via `revert_to_best()` before subsequent hypothesis testing.",
        ])

        content = "\n".join(lines) + "\n"
        path.write_text(content, encoding="utf-8")
        logger.info(f"S4 autoresearch evidence written to {path}")
        return content
