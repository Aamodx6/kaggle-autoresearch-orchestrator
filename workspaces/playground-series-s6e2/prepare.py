"""prepare.py - FIXED & READ-ONLY TO AGENTS.
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

METRIC_NAME = "Roc Auc Score"
DIRECTION = "maximize"
N_SPLITS = 5
SEED = 42


def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads raw train, test, and sample_submission DataFrames."""
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(f"Missing train data at {TRAIN_PATH}")
    train_df = pd.read_csv(TRAIN_PATH)
    test_df = pd.read_csv(TEST_PATH)
    sample_df = pd.read_csv(SAMPLE_PATH)
    return train_df, test_df, sample_df


def get_cv_folds(train_df: pd.DataFrame, target_col: str = "Heart Disease") -> List[Tuple[np.ndarray, np.ndarray]]:
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
