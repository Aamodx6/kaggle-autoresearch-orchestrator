# Stage 4: AutoResearch Adapter Evidence

**Competition:** `playground-series-s6e2`  
**Workspace Directory:** `workspaces\playground-series-s6e2`  
**Results Log:** `workspaces\playground-series-s6e2\results.tsv`  
**Tracked Best Directory:** `workspaces\playground-series-s6e2\best`  

---

## 1. Protocol & Skeleton Files

- **`prepare.py`**: Fixed, read-only data loading, Stratified 5-Fold split generation, metric calculation.
- **`train.py`**: Mutable hypothesis file subject to keep/revert editing.
- **`program.md`**: Instruction specification for single-hypothesis iterations and budget bounds.
- **`results.tsv`**: TSV audit trail of every experiment attempt.
- **`best/`**: Isolated directory housing the current winning code and checkpoint.

---

## 2. Autoresearch Keep / Revert Loop Progress

| Iteration | Commit | Status | CV Mean | CV Std | Runtime (s) | Hypothesis Description |
|---|---|---|---|---|---|---|
| 0 (Base) | `baseline` | `baseline` | 0.954383 | 0.000389 | 10.0 | Baseline LightGBM 5-Fold |
| 1 | `ac8a8ad` | **`DISCARD`** | 0.954271 | 0.000420 | 44.0 | Add cardiovascular domain interaction ratios (ST_dep/Max_HR, BP/Age, Chol/Max_HR) |
| 2 | `17b1b61` | **`DISCARD`** | 0.954425 | 0.000399 | 76.8 | Tune LightGBM num_leaves=45 and learning_rate=0.04 with colsample_bytree=0.85 |
| 3 | `e013c07` | **`DISCARD`** | 0.954429 | 0.000429 | 76.1 | Add quadratic non-linear risk terms (ST_depression^2, Age * BP interaction) |

---

## 3. Noise Gate & Statistical Validation

- **CV Noise Floor (`cv_std`):** `0.000389`
- **Best Verified CV Score:** `0.954383`
- **Cumulative Gain over Baseline:** `+0.000000`
- **Integrity Guarantee:** Any experiment failing to beat the noise threshold is strictly reverted via `revert_to_best()` before subsequent hypothesis testing.
