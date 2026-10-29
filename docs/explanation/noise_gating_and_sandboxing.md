# Explanation: Cross-Validation Noise Gating & Sandboxing

This document explains the statistical foundations and isolation architecture behind the **Kaggle AutoResearch Orchestrator**.

---

## 1. The Core Problem: Overfitting to Validation Noise

In tabular and machine learning competitions, naive auto-ML loops frequently fall into a classic trap: **hill climbing on random noise**.

When testing dozens or hundreds of arbitrary feature transformations or hyperparameters:
- A change that yields a $+0.00005$ improvement on 5-fold CV might simply be fitting the random split variance rather than real signal.
- In competitive Kaggle leaderboards, submitting such models consistently causes severe private leaderboard shake-downs (divergence between public and private scores).

---

## 2. Statistical Noise Gating: $\Delta > \sigma_{\text{CV}}$

To prevent noise chasing, AutoResearch enforces a statistical significance gate:

$$\Delta = \text{Score}_{\text{candidate}} - \text{Score}_{\text{baseline}}$$

A candidate model is promoted **only if**:

$$\Delta > \sigma_{\text{CV}}$$

where $\sigma_{\text{CV}}$ is the standard deviation across the 5 stratified validation folds of the baseline model.

### Real Example: `playground-series-s6e2`

- **Baseline 5-Fold Stratified ROC-AUC**: $0.95438$
- **Baseline Fold Standard Deviation ($\sigma_{\text{CV}}$)**: $\pm 0.00039$
- **Experiment #8 (Hyperparameter tuning)**:
  - Candidate CV: $0.95442$
  - $\Delta = +0.00004$
  - Result: **Discarded**. Even though the mean improved by $+0.00004$, $\Delta \le 0.00039$. It fell within the random split variance noise floor.
- **Experiment #9 (Non-linear risk interaction terms)**:
  - Candidate CV: $0.95443$
  - $\Delta = +0.00005$
  - Result: **Discarded**.

Only changes that provide a clean, statistically significant leap above the fold variance boundary are retained into the verified baseline.

---

## 3. Sandboxing with Git Worktrees

Running autonomous code mutation requires strict rollback guarantees. The orchestrator isolates research using Git branches and worktrees:

1. **Branch Isolation**: Each experiment executes on an ephemeral branch branched from the current verified best commit.
2. **Deterministic Rollback**: If an experiment fails or does not meet the statistical noise floor:
   ```bash
   git reset --hard HEAD~1
   ```
   ensuring the working tree is restored to an unpolluted baseline state.
3. **Zero Risk to Production**: Only kept candidates update `workspaces/<slug>/best/train.py`, guaranteeing that `final_submission.csv` is always generated from fully reproducible, checked-in code.
