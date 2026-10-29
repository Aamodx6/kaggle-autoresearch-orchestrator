# Reference: CLI Commands & REST API Endpoints

This document is the definitive specification for the Command Line Interface and FastAPI REST endpoints of the Kaggle AutoResearch Orchestrator.

---

## 1. CLI Command Reference

### Global Invocation

```bash
uv run python -m orch.cli <mode> [options]
```

### Modes

| Mode | Description | Key Flags | Example |
| :--- | :--- | :--- | :--- |
| `doctor` | Diagnose Python runtime, Kaggle authentication, GPU, SQLite DB, Git, and UI bundle. | None | `orch doctor` |
| `discover` | Query Kaggle API for entered competitions and register them. | `--no-incremental` | `orch discover` |
| `research` | Mine top community kernels, extract feature techniques, and synthesize playbook. | `-c <slug>` | `orch research -c playground-series-s6e2` |
| `submit` | Validate submission candidate and optionally perform live submission. | `-c <slug>`, `--dry-run`, `--submit` | `orch submit -c playground-series-s6e2 --dry-run` |
| `full` | Run end-to-end baseline, notebook research, keep/revert loop, and validation. | `-c <slug>`, `--dry-run` | `orch full -c playground-series-s6e2` |
| `ui` | Start the FastAPI web application and serve React frontend on port 8000. | None | `orch ui` |

---

## 2. REST API Reference

Base URL: `http://127.0.0.1:8000/api`

### Core Endpoints

#### `GET /api/status`
Returns global orchestrator state, active target competition, running stage, and Kaggle account credentials status.

#### `POST /api/active_competition`
Sets the globally active target competition.
- **Request Body**: `{"slug": "playground-series-s6e2"}`
- **Response**: `{"status": "success", "active_competition": "..."}`
- **Errors**: Returns `404 COMPETITION_NOT_FOUND` if slug does not exist in registry.

#### `GET /api/overview?slug=<slug>`
Returns classification inventory counts (Tabular, Code, Agent, CV), target key metrics, and recent activity streams.

#### `GET /api/competitions`
Lists all discovered competitions with format, category, metrics, scores, and status.
- **Query Parameters**: `search`, `kind`, `status`.

#### `GET /api/competitions/{slug}`
Returns comprehensive details for a single competition including dataset status, mined public notebooks, experiments, submissions, and local artifacts.

#### `GET /api/research/{slug}`
Returns 5-stage pipeline stepper status, indexed competitor notebooks, and the full markdown synthesis report.

#### `GET /api/experiments?slug=<slug>`
Returns all recorded keep/revert hypothesis trials with Mean CV, standard deviation noise floor ($\sigma_{\text{CV}}$), delta, and commit hashes.

#### `GET /api/experiments/{id}`
Returns granular evaluation metrics, code diff against baseline, resources (runtime, memory, GPU), and decision outcome rationale.

#### `GET /api/artifacts?slug=<slug>`
Returns all physical submission CSV files and verified model weight checkpoints.

#### `GET /api/submissions?slug=<slug>`
Returns historical submission records from `registry.db`.

#### `GET /api/leaderboard/{slug}`
Returns score timeline trajectory comparing local validation vs Kaggle public score.

#### `GET /api/queue`
Returns active worker capacity (`active_workers / max_workers`), running task with live logs stream, pending queue, and execution history.

#### `POST /api/queue/cancel/{task_id}`
Cancels a running or queued background task.

#### `POST /api/actions/validate_submission`
Executes 6-point pre-flight schema verification on `workspaces/<slug>/artifacts/final_submission.csv` and returns dry-run CLI command.

#### `POST /api/actions/submit_candidate`
Executes verified Kaggle CLI submission if `authorize: true`. Strictly requires explicit confirmation.

---

## 3. Agent-Ready Error Specification

When an error occurs, the API returns a structured JSON payload:

```json
{
  "detail": {
    "error_code": "COMPETITION_NOT_FOUND",
    "message": "Competition 'invalid-slug' not found in registry.",
    "hint": "The competition has not been discovered or registered yet.",
    "suggested_action": "Run 'orch discover' or call POST /api/actions/sync_competitions."
  }
}
```
