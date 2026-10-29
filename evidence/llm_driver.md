# LLM Driver Layer Verification Evidence

**Generated:** 2026-10-29 19:04:00 (Local Time)  
**Target:** Kaggle AutoResearch Orchestrator (`orch`)  
**Specification Document:** [`docs/reuse.md`](file:///c:/Users/aamod/OneDrive/Desktop/Orch/docs/reuse.md)  
**Core Implementation:** [`llm/driver.py`](file:///c:/Users/aamod/OneDrive/Desktop/Orch/llm/driver.py)  

---

## 1. Architectural Summary & Responsibilities

The LLM Driver layer (`class LLMDriver`) acts as the autonomous reasoning and coding brain for the orchestrator, decoupling competitive tasks into specialized roles and resilient backend fallback chains.

- **Unified Method Signature:**
  ```python
  run_task(role: str, prompt: str, workdir: Path, timeout: Optional[int] = None) -> Dict[str, Any]
  ```
  Returns standardized output:
  ```json
  {
    "diff": "<git unified diff>",
    "stdout": "<model thoughts / response text>",
    "tokens": 350,
    "cost": 0.00005,
    "backend_used": "local_headless",
    "role": "editor",
    "status": "SUCCESS"
  }
  ```

- **Specialized Roles:**
  1. `researcher`: Mined notebook parsing and technique summarization.
  2. `proposer`: Hypothesis generation derived from metrics and idea backlogs.
  3. `editor`: Modifies code strictly inside an isolated git worktree sandbox.
  4. `reviewer`: Audits diffs for data leakage, synthetic lookahead, target column corruption, or prohibited modifications to `prepare.py` (`must_differ_from: editor`).

- **Backend Implementations (`llm/backends/`):**
  - `mock`: Deterministic canned diffs and outputs for fast, offline unit and integration testing.
  - `headless_cli`: Spawns CLI coding assistants (`claude -p`, `gemini -p`, `freebuff`, `python -m orch.llm_cli`) in worktree sandboxes, extracting git diffs as code edits.
  - `openai_compat`: Connects to OpenAI-compatible endpoints (`gemini_api`, `groq`, `openrouter_free`) with proxy safety audits, token usage tracking, and rate-limit backoff.

- **Account-Safe Pacing & Resilient Fallback Chains:**
  - Automatic HTTP 429 detection triggers backend cooldown (`cooldown_minutes: 60`).
  - Cooldown timestamps are persisted to [`llm_state.json`](file:///c:/Users/aamod/OneDrive/Desktop/Orch/llm_state.json).
  - Failed or rate-limited backends automatically advance to the next candidate in the role's chain (`on_429: {action: next_in_chain}`).

- **Hard Budget & Rate Controls:**
  - Daily experiment cap enforced (`max_experiments_per_day: 40`).
  - Halts the autonomous loop when exhausted (`stop_on_all_backends_exhausted: true`).

- **Git Worktree Sandbox & Write Security:**
  - The `editor` role executes exclusively in an isolated git worktree (`.worktrees/sandbox_<role>_<timestamp>`).
  - **Strict Invariant:** Agents can modify ONLY `train.py` and `program.md`. `prepare.py` is strictly read-only.
  - Any attempt to touch unauthorized files or edit `prepare.py` is caught by `SandboxManager`, triggering `SandboxViolationError` and immediate worktree rollback.

- **Prompt Hygiene & Compliance:**
  - Whitelist: code diffs, `results.tsv` rows, metric values, schema, summary stats, error logs.
  - Blacklist: raw dataset rows, label vectors, API credentials.
  - TOS-violating unvetted proxies are blocked by default; opt-in proxy endpoints require explicit config and log a startup warning.

---

## 2. Verification Step 1: Mock Backend & Unit Test Suite

The `mock` backend was verified across all roles, fallback behaviors, and security gates.

```text
============================= test session starts =============================
tests/test_llm_driver.py::test_mock_backend_run_task_all_roles PASSED    [ 25%]
tests/test_llm_driver.py::test_rate_limit_429_failover_and_cooldown PASSED [ 50%]
tests/test_llm_driver.py::test_budget_exceeded_enforcement PASSED        [ 75%]
tests/test_llm_driver.py::test_sandbox_security_blocks_prepare_py_modification PASSED [100%]
============================== 4 passed in 1.23s ==============================
```

- **Proposer & Researcher:** Returned structured reasoning, token estimates, and valid responses.
- **Reviewer:** Enforced `must_differ_from: editor` by selecting `mock_backup` rather than the editor's backend.
- **Failover on 429:** When `mock_429` simulated a rate limit, the driver stamped a 30-minute cooldown in `llm_state.json` and cleanly fell over to `mock_backup`.
- **Budget Exceeded:** Halts with `BudgetExceededError` when daily experiment threshold is crossed.
- **Sandbox Security:** Modifying `prepare.py` raised `SandboxViolationError`, proving read-only protection.

---

## 3. Verification Step 2: Real `headless_cli` Experiment

A real headless CLI experiment was executed on the `playground-series-s6e2` competition workspace.

### Execution Log:
```json
{"timestamp": "2026-10-29T13:33:01.987916+00:00", "level": "INFO", "logger": "llm.headless_cli", "message": "[local_headless] Executing role 'editor' in C:\\Users\\aamod\\OneDrive\\Desktop\\Orch\\workspaces\\playground-series-s6e2 (mode=worktree)"}
{"timestamp": "2026-10-29T13:33:02.077184+00:00", "level": "INFO", "logger": "llm.sandbox", "message": "Sandbox worktree created at C:\\Users\\aamod\\OneDrive\\Desktop\\Orch\\.worktrees\\sandbox_editor_1793280781"}
{"timestamp": "2026-10-29T13:33:02.103595+00:00", "level": "INFO", "logger": "llm.headless_cli", "message": "[local_headless] Spawning process: python.exe -m orch.llm_cli in sandbox_editor_1793280781\\workspaces\\playground-series-s6e2"}
{"timestamp": "2026-10-29T13:33:02.225898+00:00", "level": "INFO", "logger": "llm.sandbox", "message": "Applied validated edit to C:\\Users\\aamod\\OneDrive\\Desktop\\Orch\\workspaces\\playground-series-s6e2\\train.py"}
{"timestamp": "2026-10-29T13:33:02.281046+00:00", "level": "INFO", "logger": "llm.sandbox", "message": "Sandbox worktree cleaned up: sandbox_editor_1793280781"}
```

### Captured Git Unified Diff:
```diff
--- a/train.py
+++ b/train.py
@@ -26,6 +26,9 @@
     feature_cols = [c for c in df_train.columns if c not in [TARGET_COL, ID_COL]]
 
     # Hypothesis / Feature additions:
+    # Autonomous LLM Headless CLI Feature: ST depression / Max HR ratio
+    df_train["ratio_st_hr"] = df_train["ST depression"] / (df_train["Max HR"] + 1e-5)
+    df_test["ratio_st_hr"] = df_test["ST depression"] / (df_test["Max HR"] + 1e-5)
     # Baseline: no added features
 
     feature_cols = [c for c in df_train.columns if c not in [TARGET_COL, ID_COL]]
```

### Downstream Model Verification:
The resulting `train.py` was executed across the 5-fold Stratified CV dataset (630,000 train rows) via `ExperimentRunner`:
- **Status:** `DONE`
- **CV Mean (ROC-AUC):** `0.954312`
- **CV Std:** `0.000419`
- **Runtime:** `17.46s`
- **Audit:** The code modification executed smoothly without errors, proving full end-to-end compatibility between the LLM Driver worktree sandbox and the autoresearch training loop.
