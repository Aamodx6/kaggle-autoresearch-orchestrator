# Autoresearch Protocol: `playground-series-s6e2`

## Goal
Maximize local 5-fold CV score (Roc Auc Score, maximize).
Current Baseline Score: 0.95438 (+/- 0.00039).

## Ground Rules
1. Edit ONLY `train.py`.
2. NEVER touch `prepare.py` or edit raw data files in `data/`.
3. Exactly ONE hypothesis per experiment iteration.
4. Keep a change ONLY if `cv_mean` improves over current best by more than the CV noise floor (`cv_std`=0.00039).
5. Discard non-improving changes immediately (reset to `best/train.py`).
6. Enforce time budget: <= 300s per run, memory <= 4096MB.

## Hypothesis Backlog (Derived from Stage S3 Public Research)
- [Hypothesis 1]: Medical interaction ratios (`ST depression / Max HR`, `BP / Age`).
- [Hypothesis 2]: LightGBM hyperparameter depth tuning (`num_leaves=63`, `learning_rate=0.03`).
- [Hypothesis 3]: Polynomial feature interaction (`ST depression` squared + `Max HR`).
- [Hypothesis 4]: Out-of-fold probability blending with regularized Logistic Regression.
