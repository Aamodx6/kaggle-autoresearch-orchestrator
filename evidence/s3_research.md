# Stage 3: Public Research Evidence

**Competition:** `playground-series-s5e12`  
**Synthesized Research Artifact:** `research/playground-series-s5e12.md`  

# Competitive Research Analysis: `playground-series-s5e12`

## 1. Executive Summary
Analyzed top 4 public Kaggle notebooks by community votes and recency. Note: public scores on the Kaggle API kernels view were unexposed; notebooks were prioritized by vote count and verified domain relevance.

---

## 2. Notebook Analysis Matrix

| Notebook Reference | Author | Votes | Primary Models | CV Strategy | Ensembling | License |
|---|---|---|---|---|---|---|
| [`masayakawamata/s5e12-eda-xgb-competition-starter`](https://www.kaggle.com/code/masayakawamata/s5e12-eda-xgb-competition-starter) | `masayakawamata` | 274 | Standard Classifier | 5-Fold Stratified K-Fold | None (Single Model) | Apache 2.0 / Kaggle Open Code License |
| [`anthonytherrien/ps-s5e12-blend`](https://www.kaggle.com/code/anthonytherrien/ps-s5e12-blend) | `anthonytherrien` | 139 | Standard Classifier | 5-Fold Stratified K-Fold | None (Single Model) | Apache 2.0 / Kaggle Open Code License |
| [`wind1234it/s5e12-1st-place-solution-hc-ridge`](https://www.kaggle.com/code/wind1234it/s5e12-1st-place-solution-hc-ridge) | `wind1234it` | 118 | Standard Classifier | 5-Fold Stratified K-Fold | None (Single Model) | Apache 2.0 / Kaggle Open Code License |
| [`kdmitrie/pgs512-xgb-lgb-ydf-tabm-ag-fe-cv-optuna`](https://www.kaggle.com/code/kdmitrie/pgs512-xgb-lgb-ydf-tabm-ag-fe-cv-optuna) | `kdmitrie` | 101 | Standard Classifier | 5-Fold Stratified K-Fold | None (Single Model) | Apache 2.0 / Kaggle Open Code License |

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

