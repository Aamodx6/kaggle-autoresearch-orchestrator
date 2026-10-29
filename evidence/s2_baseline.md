# Stage 2: Workspace + Baseline Evidence

**Competition:** `playground-series-s6e2`  
**Workspace Directory:** `workspaces\playground-series-s6e2`  
**Data Directory:** `workspaces\playground-series-s6e2\data`  
**Original Archives Directory:** `workspaces\playground-series-s6e2\original`  

---

## 1. Dataset Schema & Characteristics

- **Train Shape:** 630000 rows × 15 columns
- **Test Shape:** 270000 rows × 14 columns
- **Sample Submission Shape:** 270000 rows × 2 columns
- **ID Column:** `id`
- **Target Column:** `Heart Disease`
- **Target Distribution:** `{"Absence": 347546, "Presence": 282454}`
- **Numerical Features (13):** `Age, Sex, Chest pain type, BP, Cholesterol, FBS over 120, EKG results, Max HR, Exercise angina, ST depression`...
- **Categorical Features (0):** ``

---

## 2. Cross-Validation & Metric Alignment

- **Strategy:** 5-Fold Stratified K-Fold (`StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`)
- **Target Metric:** ROC-AUC Score (`roc_auc_score`, higher is better)
- **Baseline CV Mean:** `0.95438`
- **Baseline CV Std:** `0.00039` (Noise floor threshold)
- **Historical My Best Kaggle Public Score:** `0.95408`
- **Baseline Alignment:** Local 5-fold CV score `0.95438` aligns tightly with real Kaggle leaderboard performance.

---

## 3. Sample-Schema Submission Validation

- **Validation Status:** `PASSED`
- **Validated Row Count:** `270000` (Matches sample_submission exactly)
- **Validated Columns:** `id, Heart Disease`
- **Discrepancies / Errors:** `0`
- **Warnings:** `0`
- **Artifact Saved:** `workspaces\playground-series-s6e2\artifacts\baseline_submission.csv`
- **Preserved in Original:** `workspaces\playground-series-s6e2\original\baseline_submission.csv`

```text
Validation Status: PASSED
Rows: 270000, Columns: 2 (id, Heart Disease)
```
