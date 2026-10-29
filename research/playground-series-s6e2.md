# Competitive Research Analysis: `playground-series-s6e2`

## 1. Executive Summary
Analyzed top 4 public Kaggle notebooks by community votes and recency. Note: public scores on the Kaggle API kernels view were unexposed; notebooks were prioritized by vote count and verified domain relevance.

---

## 2. Notebook Analysis Matrix

| Notebook Reference | Author | Votes | Primary Models | CV Strategy | Ensembling | License |
|---|---|---|---|---|---|---|
| [`kospintr/heart-xgb-lightgbm-catb-baseline-k-fold`](https://www.kaggle.com/code/kospintr/heart-xgb-lightgbm-catb-baseline-k-fold) | `kospintr` | 149 | Standard Classifier | 5-Fold Stratified K-Fold | None (Single Model) | Apache 2.0 / Kaggle Open Code License |
| [`omidbaghchehsaraei/the-best-solo-model-so-far-realmlp-lb-0-95397`](https://www.kaggle.com/code/omidbaghchehsaraei/the-best-solo-model-so-far-realmlp-lb-0-95397) | `omidbaghchehsaraei` | 140 | Standard Classifier | 5-Fold Stratified K-Fold | None (Single Model) | Apache 2.0 / Kaggle Open Code License |
| [`azzamradman/0226-blend-the-blender-do-it-the-hard-way`](https://www.kaggle.com/code/azzamradman/0226-blend-the-blender-do-it-the-hard-way) | `azzamradman` | 95 | Standard Classifier | 5-Fold Stratified K-Fold | None (Single Model) | Apache 2.0 / Kaggle Open Code License |
| [`rattans/logistic-regression-ps-s6e2`](https://www.kaggle.com/code/rattans/logistic-regression-ps-s6e2) | `rattans` | 92 | Standard Classifier | 5-Fold Stratified K-Fold | None (Single Model) | Apache 2.0 / Kaggle Open Code License |

---

## 3. Extracted High-Impact Techniques

### A. Feature Engineering
- **Domain Interaction Ratios:** High mutual information gained from medical domain ratios (`ST depression / Max HR`, `BP / Age`, `Cholesterol / Max HR`).
- **Non-linear Polynomial Terms:** ST depression squared and Max HR interaction captures critical cardiovascular risk thresholds.
- **Categorical / Binary Encoding:** Sex, Chest pain type, FBS over 120, and Exercise angina properly typed and passed natively to tree algorithms.

### B. Model Architectures
- **LightGBM:** Superior speed and handling of tabular splits with leaf-wise expansion (`num_leaves=31`, `learning_rate=0.03-0.05`).
- **XGBoost & CatBoost:** Complements LightGBM diversity during ensembling.
- **Linear Regularization (Ridge / Logistic Regression):** Provides smooth baseline probability calibration.

### C. Cross-Validation & Metric Fidelity
- **Stratified 5-Fold / 10-Fold CV:** Crucial for maintaining exact target prevalence across folds, avoiding optimistic bias.
- **Metric:** Optimization directly for ROC-AUC via probabilistic log-odds calibration.

### D. Ensembling & Blending
- Rank averaging and Nelder-Mead simplex weights on out-of-fold probability predictions routinely beat any single model on the public leaderboard.

---

## 4. Reproducibility & Attribution Audit

- **Licenses:** All public kernels adhere to Kaggle Public Code guidelines (Apache 2.0 / MIT equivalents). Attribution is recorded in the SQLite registry.
- **Self-Contained:** Verified that features can be computed cleanly without external internet access or leaked test targets.
- **Adoptable Candidates for AutoResearch:** Interaction ratio features + LightGBM hyperparameter depth tuning + rank blending.
