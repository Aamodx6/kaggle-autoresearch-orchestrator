# Stage 5: Validate + Submit Evidence

**Competition:** `playground-series-s6e2`  
**Submission Mode:** `DRY-RUN`  
**Candidate File:** `workspaces\playground-series-s6e2\artifacts\final_submission.csv`  
**Local Cross-Validation Score:** `0.954080`  
**Historical Best Leaderboard Score:** `0.95408`  

---

## 1. Schema & Integrity Validation

- **Validation Status:** `PASSED`
- **Exact Kaggle Sample Conformity:** Verified row count, IDs, column headers, ordering, non-empty, and null/inf safety.

```text
Validation Status: PASSED
Rows: 270000, Columns: 2 (id, Heart Disease)
```

---

## 2. Dry-Run / Live Submission Audit

- **Mode:** `dry-run` (Real submissions gated behind explicit `--submit` and per-competition daily quota)
- **Daily Cap Policy:** Enforces max `5` submissions per day via SQLite budget ledger.

### Exact Kaggle CLI Submission Command:
```bash
kaggle competitions submit -c playground-series-s6e2 -f "C:\Users\aamod\OneDrive\Desktop\Orch\workspaces\playground-series-s6e2\artifacts\final_submission.csv" -m "AutoResearch validated candidate submission"
```

---

## 3. Submission Guardrail Verification

- **Dry-Run Enforcement:** No unauthorized network submission performed.
- **Live Submission Gate:** Requires `--submit` plus remaining quota under daily cap to dispatch to Kaggle API.
