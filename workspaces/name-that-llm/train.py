"""train.py - EDITABLE BY AUTORESEARCH AGENT.
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

TARGET_COL = "Heart Disease"
ID_COL = "id"


def feature_engineering(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """Applies domain feature transformations."""
    df_train = train_df.copy()
    df_test = test_df.copy()

    # Drop target and ID
    feature_cols = [c for c in df_train.columns if c not in [TARGET_COL, ID_COL]]

    # Hypothesis / Feature additions:
    # Baseline: no added features

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
            n_estimators=150,
            learning_rate=0.05,
            random_state=SEED + fold,
            verbose=-1,
            n_jobs=-1,
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
    sub = pd.DataFrame({ID_COL: df_test[ID_COL], TARGET_COL: test_preds})
    sub_path = Path(__file__).parent / "candidate_submission.csv"
    sub.to_csv(sub_path, index=False)

    print(f"CV_MEAN={cv_mean:.6f}")
    print(f"CV_STD={cv_std:.6f}")
    print(f"RUNTIME={runtime:.2f}")
    print(f"STATUS=DONE")
    return cv_mean


if __name__ == "__main__":
    run_experiment()
