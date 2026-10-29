# Kaggle AutoResearch Orchestrator (`orch`)

A production-grade Python orchestrator inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch). It discovers your entered Kaggle competitions, baselines your best submissions, mines competitive public notebooks, runs an autonomous keep/revert hypothesis loop to optimize models, validates submission schemas, and safely generates dry-run commands or performs live submissions within strict daily caps.

---

## 🏛️ System Architecture

```text
Orch/
├── orch/
│   ├── connector.py           # Kaggle API/CLI client with retries and exponential backoff
│   ├── registry.py            # SQLite schema (competitions, submissions, notebooks, experiments, budgets)
│   ├── discovery.py           # Discovers entered comps, classifies kinds, tracks best LB scores
│   ├── workspace.py           # Data download, schema inspection, baseline 5-fold CV runner
│   ├── researcher.py          # Discovers and pulls top public notebooks by votes/recency
│   ├── analyzer.py            # Extracts models, features, CV, ensembling, and licenses into research/<slug>.md
│   ├── autoresearch_adapter.py# Creates prepare.py (fixed), train.py (mutable), program.md, results.tsv
│   ├── runner.py              # Executes experiments under timeout and memory monitoring
│   ├── tracker.py             # Logs results.tsv, SQLite records, and best/ checkpoint snapshots
│   ├── selector.py            # Statistical noise-aware keep/revert decision engine
│   ├── validator.py           # Pre-flight schema validation against sample_submission.csv
│   ├── submitter.py           # Dry-run CLI generation and live submission gate with divergence alerts
│   ├── reporting.py           # Self-contained static HTML dashboard generator
│   └── cli.py                 # Multi-mode CLI entrypoint
├── workspaces/                # Competition data, artifacts, and isolated experiments
│   └── <slug>/
│       ├── data/              # Raw competition data (train, test, sample_submission)
│       ├── original/          # Read-only untouched copies of original solutions and baselines
│       ├── best/              # Checkpoint of winning train.py and verified submission
│       ├── prepare.py         # Fixed, read-only data loader & CV split generator
│       ├── train.py           # Mutable experiment file edited by hypothesis iterations
│       ├── program.md         # Autonomous protocol rules, budget bounds, and idea backlog
│       └── results.tsv        # Complete experiment audit log
├── research/                  # Synthesized domain research and technique extractions
├── evidence/                  # Verifiable audit artifacts generated after every stage
├── reports/                   # Static HTML dashboards (reports/dashboard.html)
├── tests/                     # Unit and integration test suite (pytest)
├── config.yaml                # Orchestrator budgets, daily caps, paths, and CV gates
└── orch.ps1 / orch.cmd        # Cross-platform CLI launchers
```

---

## 🔒 Ground Rules & Safety Gates

1. **Zero Fabrication:** Every claim, metric, and score is derived from real runs and persisted in `evidence/` and SQLite `registry.db`.
2. **Credential Security:** Auth credentials read exclusively from `~/.kaggle/access_token`, `~/.kaggle/kaggle.json`, or environment variables. Never committed or logged.
3. **Immutability of Originals:** Original files and initial baselines are preserved in `workspaces/<slug>/original/` before any mutation.
4. **Dry-Run by Default:** The default mode is `--dry-run`, which validates the submission file and outputs the exact `kaggle competitions submit` command without network side-effects.
5. **Live Submission Gate:** Live submission requires the explicit `--submit` flag and enforces per-competition daily quota limits from `config.yaml`.
6. **Statistical Noise Gate:** An experiment is accepted as a `KEEP` only if its CV improvement exceeds the cross-validation standard deviation (`cv_std`). Sub-noise variations are discarded for conservatism.
7. **Immediate Rollback:** Degraded or crashed experiments are immediately rolled back to `best/train.py` via `revert_to_best()`.

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

```bash
# Clone or navigate to the repository
cd Orch

# Install dependencies using uv
uv sync
```

### Kaggle Authentication
Ensure your Kaggle credentials exist in `~/.kaggle/access_token` (recommended for Kaggle 2.x) or `~/.kaggle/kaggle.json`:

```bash
# Verify authentication
uv run kaggle competitions list --group entered
```

---

## 💻 Usage & Operational Modes

Run commands using `./orch.ps1` (PowerShell), `orch.cmd` (Command Prompt), or `uv run python -m orch.cli`:

### 1. Discover Competitions (`discover`)
Discovers entered competitions, checks file schemas, classifies kind (`csv_tabular`, `csv_cv`, `csv_nlp`, `code_competition`, `agent_or_optimization`, `other`), identifies previous best scores, and populates `registry.db`:
```bash
./orch.ps1 discover
```

### 2. Research Public Notebooks (`research`)
Pulls the top 3-5 notebooks by votes/recency, extracts models, features, CV strategy, ensembling, and licenses, and generates `research/<slug>.md`:
```bash
./orch.ps1 research -c playground-series-s6e2
```

### 3. Submission Validation & Dry-Run (`submit`)
Refits the best candidate, performs schema validation (rows, columns, dtypes, nulls, bounds), and outputs the exact submission command:
```bash
# Dry-run mode (Default, safe)
./orch.ps1 submit -c playground-series-s6e2

# Real submission (Requires quota under daily cap)
./orch.ps1 submit -c playground-series-s6e2 --submit
```

### 4. Full End-to-End Pipeline (`full`)
Executes the full pipeline: Discovery -> Baseline Setup -> Public Research -> AutoResearch Keep/Revert Loop -> Validation -> Dashboard Report:
```bash
./orch.ps1 full -c playground-series-s6e2
```

---

## ⚙️ Configuration (`config.yaml`)

```yaml
budgets:
  experiment_timeout_seconds: 300    # Max execution time per hypothesis
  max_experiments_per_run: 5         # Experiment budget per run
  patience_experiments: 3            # Consecutive discards before stopping
  memory_limit_mb: 4096              # Subprocess memory limit

daily_caps:
  default: 5
  playground-series-s6e2: 5           # Daily submission limit per competition

paths:
  registry_db: "registry.db"
  workspaces_dir: "workspaces"
  research_dir: "research"
  evidence_dir: "evidence"
  reports_dir: "reports"

cv:
  n_splits: 5
  seed: 42

noise_gate:
  use_cv_std: true                   # Enforce cv_std noise floor
  min_improvement_epsilon: 0.0002    # Minimum delta threshold
```

---

## 🧪 Testing

Run unit tests with mocked Kaggle client and integration test:

```bash
uv run pytest tests/ -v
```

All 14 tests pass, covering:
- Kaggle API client retries and exponential backoff
- 403 RulesNotAccepted / 404 error handling
- SQLite registry CRUD and daily cap accounting
- Submission schema validator against sample submissions
- Noise-aware statistical selector
- End-to-end integration test in dry-run mode

---

## 📊 Reports & Dashboard

Open `reports/dashboard.html` in any browser to inspect:
- Competition overview and kind classifications
- Public research and mined techniques
- AutoResearch experiment iteration curve
- Full submission and leaderboard history
