# Tutorial: Quickstart with Kaggle AutoResearch Orchestrator

This tutorial walks you through setting up, inspecting, researching, and running an automated optimization loop on an entered Kaggle competition from zero to a verified submission candidate.

---

## Prerequisites

1. **Python 3.10+** (managed via `uv`).
2. **Kaggle Account & CLI Credentials**:
   - Create an API token from your Kaggle profile (`https://www.kaggle.com/settings`).
   - Store it at `~/.kaggle/access_token` or `~/.kaggle/kaggle.json`.
3. **Node.js & npm** (for web UI development; prebuilt production assets are included).

---

## Step 1: System Diagnostic (`orch doctor`)

Before running pipelines, verify that your environment, authentication, database, and hardware acceleration are ready:

```bash
uv run python -m orch.cli doctor
```

**Expected output:**
```
=================================================================
  Kaggle AutoResearch Orchestrator — System Diagnostic (Doctor)
=================================================================
[1/6] Python Runtime: v3.12.x (PASS)
[2/6] Kaggle Authentication & CLI: Authenticated as 'your_username' (PASS)
[3/6] Hardware Acceleration (Compute): CUDA GPU or CPU/OpenMP (PASS)
[4/6] SQLite Registry Database: registry.db accessible (PASS)
[5/6] Git Repository & Worktrees: Active git repository verified (PASS)
[6/6] Web UI Production Bundle: UI production assets present (PASS)
-----------------------------------------------------------------
Diagnostic Summary: 6/6 checks passed.
=================================================================
```

---

## Step 2: Launch the Web UI

Start the local orchestration server:

```bash
uv run python -m orch.cli ui
```

Open [`http://127.0.0.1:8000`](http://127.0.0.1:8000) in your browser. You will see:
- Global status bar with active target selector.
- 4-quadrant classification inventory matrix.
- Active target workbench.

---

## Step 3: Discover Entered Competitions

From the Overview or Competitions page, click **Sync Competitions** (or via CLI):

```bash
uv run python -m orch.cli discover
```

The orchestrator queries Kaggle's API, inspects your joined competitions, categorizes each one (Tabular, Code Competition, Agent Simulation, Computer Vision), and records them into `registry.db`.

---

## Step 4: Extract Community Notebook Research

Navigate to the **Research** tab, select `playground-series-s6e2`, and click **Fetch Public Notebooks** (or via CLI):

```bash
uv run python -m orch.cli research -c playground-series-s6e2
```

The system:
1. Discovers top community notebooks by votes.
2. Extracts domain feature ratios, model algorithms, and CV setups.
3. Generates a synthesis markdown playbook in `research/playground-series-s6e2.md`.

---

## Step 5: Run the AutoResearch Keep/Revert Loop

Click **Run Experiments** on the active workbench or navigate to **Model Experiments**:

```bash
uv run python -m orch.cli full -c playground-series-s6e2
```

The loop will:
1. Train a 5-fold stratified LightGBM baseline and calculate $\sigma_{\text{CV}}$.
2. Formulate iterative hypotheses (e.g., interaction features, depth tuning).
3. Evaluate candidates:
   - If $\Delta > \sigma_{\text{CV}}$: The candidate is **kept**, and a Git commit is saved.
   - If $\Delta \le \sigma_{\text{CV}}$: The candidate is **discarded**, and the worktree is rolled back.
4. Output the final candidate CSV into `workspaces/playground-series-s6e2/artifacts/final_submission.csv`.

---

## Step 6: Verify and Submit Candidate

Navigate to **Submissions**:
1. Click **Submit Candidate**.
2. The 6-point pre-flight verification gate checks row count, exact column headers, zero NaN values, and ID alignment.
3. Inspect the dry-run CLI command preview.
4. Check the authorization checkbox and submit live to Kaggle when ready.
