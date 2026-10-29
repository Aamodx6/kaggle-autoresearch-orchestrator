"""AutoResearch Adapter for creating and managing Karpathy-style autoresearch skeletons."""

import shutil
from pathlib import Path
from typing import Dict, Any

from orch.config import AppConfig
from orch.logging_util import get_logger
from orch.registry import Registry

logger = get_logger("orch.autoresearch_adapter")


PREPARE_PY_TEMPLATE = '''"""prepare.py - FIXED & READ-ONLY TO AGENTS.
Handles data loading, CV splitting, metric evaluation, and directional configuration.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

DATA_DIR = Path(__file__).resolve().parent / "data"
TRAIN_PATH = DATA_DIR / "train.csv"
TEST_PATH = DATA_DIR / "test.csv"
SAMPLE_PATH = DATA_DIR / "sample_submission.csv"

METRIC_NAME = "{metric_name}"
DIRECTION = "{direction}"
N_SPLITS = {n_splits}
SEED = {seed}


def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads raw train, test, and sample_submission DataFrames."""
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(f"Missing train data at {{TRAIN_PATH}}")
    train_df = pd.read_csv(TRAIN_PATH)
    test_df = pd.read_csv(TEST_PATH)
    sample_df = pd.read_csv(SAMPLE_PATH)
    return train_df, test_df, sample_df


def get_cv_folds(train_df: pd.DataFrame, target_col: str = "{target_col}") -> List[Tuple[np.ndarray, np.ndarray]]:
    """Generates stratified fold splits matching official competition metric."""
    y = train_df[target_col].values
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    return list(skf.split(train_df, y))


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Computes competition evaluation metric."""
    return float(roc_auc_score(y_true, y_pred))


def is_better(new_score: float, current_best: float, noise_std: float = 0.0) -> bool:
    """Evaluates whether new_score statistically beats current_best beyond noise floor."""
    if DIRECTION == "maximize":
        return (new_score - current_best) > max(noise_std, 0.0001)
    else:
        return (current_best - new_score) > max(noise_std, 0.0001)
'''


TRAIN_PY_TEMPLATE = '''"""train.py - EDITABLE BY AUTORESEARCH AGENT.
Executes feature engineering, model training across CV folds, and prints standardized results.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier

# Import fixed data loader and evaluation from prepare.py
from prepare import load_raw_data, get_cv_folds, evaluate_predictions, SEED, METRIC_NAME, DIRECTION

TARGET_COL = "{target_col}"
ID_COL = "{id_col}"


def feature_engineering(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """Applies domain feature transformations."""
    df_train = train_df.copy()
    df_test = test_df.copy()

    # Drop target and ID
    feature_cols = [c for c in df_train.columns if c not in [TARGET_COL, ID_COL]]

    # Hypothesis / Feature additions:
{feature_code}

    feature_cols = [c for c in df_train.columns if c not in [TARGET_COL, ID_COL]]
    return df_train, df_test, feature_cols


def run_experiment() -> float:
    start_time = time.time()
    train_df, test_df, _ = load_raw_data()
    df_train, df_test, features = feature_engineering(train_df, test_df)

    y = df_train[TARGET_COL].values
    folds = get_cv_folds(df_train, TARGET_COL)

    fold_scores = []
    test_preds = np.zeros(len(df_test))
    oof_preds = np.zeros(len(df_train))

    for fold, (train_idx, val_idx) in enumerate(folds):
        X_tr = df_train.iloc[train_idx][features]
        y_tr = y[train_idx]
        X_val = df_train.iloc[val_idx][features]
        y_val = y[val_idx]

        model = LGBMClassifier(
{model_params}
        )
        model.fit(X_tr, y_tr)

        val_probs = model.predict_proba(X_val)[:, 1]
        oof_preds[val_idx] = val_probs
        score = evaluate_predictions(y_val, val_probs)
        fold_scores.append(score)

        test_preds += model.predict_proba(df_test[features])[:, 1] / len(folds)

    runtime = time.time() - start_time
    cv_mean = float(np.mean(fold_scores))
    cv_std = float(np.std(fold_scores))

    # Save candidate submission
    sub = pd.DataFrame({{ID_COL: df_test[ID_COL], TARGET_COL: test_preds}})
    sub_path = Path(__file__).parent / "candidate_submission.csv"
    sub.to_csv(sub_path, index=False)

    print(f"CV_MEAN={{cv_mean:.6f}}")
    print(f"CV_STD={{cv_std:.6f}}")
    print(f"RUNTIME={{runtime:.2f}}")
    print(f"STATUS=DONE")
    return cv_mean


if __name__ == "__main__":
    run_experiment()
'''


PROGRAM_MD_TEMPLATE = '''# Autoresearch Protocol: `{competition_slug}`

## Goal
Maximize local 5-fold CV score ({evaluation_metric}, {direction}).
Current Baseline Score: {baseline_score:.5f} (+/- {baseline_std:.5f}).

## Ground Rules
1. Edit ONLY `train.py`.
2. NEVER touch `prepare.py` or edit raw data files in `data/`.
3. Exactly ONE hypothesis per experiment iteration.
4. Keep a change ONLY if `cv_mean` improves over current best by more than the CV noise floor (`cv_std`={baseline_std:.5f}).
5. Discard non-improving changes immediately (reset to `best/train.py`).
6. Enforce time budget: <= {timeout_seconds}s per run, memory <= {memory_mb}MB.

## Hypothesis Backlog (Derived from Stage S3 Public Research)
- [Hypothesis 1]: Medical interaction ratios (`ST depression / Max HR`, `BP / Age`).
- [Hypothesis 2]: LightGBM hyperparameter depth tuning (`num_leaves=63`, `learning_rate=0.03`).
- [Hypothesis 3]: Polynomial feature interaction (`ST depression` squared + `Max HR`).
- [Hypothesis 4]: Out-of-fold probability blending with regularized Logistic Regression.
'''


class AutoResearchAdapter:
    """Sets up and manages the Karpathy autoresearch skeleton for a competition workspace."""

    def __init__(
        self,
        competition_slug: str,
        registry: Registry,
        config: AppConfig,
    ):
        self.competition_slug = competition_slug
        self.registry = registry
        self.config = config
        self.workspace_dir = Path(config.paths.workspaces_dir) / competition_slug
        self.best_dir = self.workspace_dir / "best"
        self.results_tsv_path = self.workspace_dir / "results.tsv"

    def setup_skeleton(
        self,
        target_col: str,
        id_col: str,
        baseline_score: float,
        baseline_std: float,
    ) -> Dict[str, Path]:
        """Generates prepare.py, train.py, program.md, results.tsv, and best/ tracking."""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.best_dir.mkdir(parents=True, exist_ok=True)

        comp = self.registry.get_competition(self.competition_slug) or {}
        metric_name = comp.get("evaluation_metric", "Roc Auc Score")
        direction = comp.get("direction", "maximize")

        # 1. prepare.py (read-only)
        prepare_code = PREPARE_PY_TEMPLATE.format(
            metric_name=metric_name,
            direction=direction,
            n_splits=self.config.cv.n_splits,
            seed=self.config.cv.seed,
            target_col=target_col,
        )
        prepare_path = self.workspace_dir / "prepare.py"
        prepare_path.write_text(prepare_code, encoding="utf-8")

        # 2. train.py (initial working copy)
        model_params = "            n_estimators=150,\n            learning_rate=0.05,\n            random_state=SEED + fold,\n            verbose=-1,\n            n_jobs=-1,"
        train_code = TRAIN_PY_TEMPLATE.format(
            target_col=target_col,
            id_col=id_col,
            feature_code="    # Baseline: no added features",
            model_params=model_params,
        )
        train_path = self.workspace_dir / "train.py"
        train_path.write_text(train_code, encoding="utf-8")

        # 3. Snapshot initial baseline into best/
        best_train_path = self.best_dir / "train.py"
        best_train_path.write_text(train_code, encoding="utf-8")

        # 4. program.md
        program_code = PROGRAM_MD_TEMPLATE.format(
            competition_slug=self.competition_slug,
            evaluation_metric=metric_name,
            direction=direction,
            baseline_score=baseline_score,
            baseline_std=baseline_std,
            timeout_seconds=self.config.budgets.experiment_timeout_seconds,
            memory_mb=self.config.budgets.memory_limit_mb,
        )
        program_path = self.workspace_dir / "program.md"
        program_path.write_text(program_code, encoding="utf-8")

        # 5. results.tsv
        if not self.results_tsv_path.exists():
            headers = "commit\tcv_mean\tcv_std\truntime\tmem\tstatus\tdescription\n"
            baseline_row = f"baseline\t{baseline_score:.6f}\t{baseline_std:.6f}\t10.0\t512\tbaseline\tInitial LightGBM 5-Fold Stratified\n"
            self.results_tsv_path.write_text(headers + baseline_row, encoding="utf-8")

        logger.info(f"AutoResearch skeleton successfully created in {self.workspace_dir}")
        return {
            "prepare": prepare_path,
            "train": train_path,
            "program": program_path,
            "results_tsv": self.results_tsv_path,
            "best_train": best_train_path,
        }

