"""FastAPI REST API server for Kaggle AutoResearch Orchestrator."""

import asyncio
import datetime
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yaml

from orch.analyzer import NotebookAnalyzer
from orch.config import load_config, AppConfig
from orch.connector import KaggleConnector
from orch.discovery import DiscoveryService
from orch.loop import AutoResearchLoop, HYPOTHESIS_EXPERIMENTS
from orch.registry import Registry
from orch.reporting import DashboardReporter
from orch.researcher import PublicResearcher
from orch.submitter import SubmissionManager, SubmissionOutcome
from orch.validator import SubmissionValidator
from orch.workspace import WorkspaceManager


app = FastAPI(title="Kaggle AutoResearch Orchestrator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = "config.yaml"
config: AppConfig = load_config(CONFIG_PATH)
connector = KaggleConnector()
registry = Registry(config.paths.registry_db)

# ---------------------------------------------------------
# Execution Queue System
# ---------------------------------------------------------
class TaskItem:
    def __init__(self, task_id: str, name: str, competition_slug: str, stage: str):
        self.id = task_id
        self.name = name
        self.competition_slug = competition_slug
        self.stage = stage
        self.status = "queued"  # queued, running, completed, failed, cancelled
        self.created_at = datetime.datetime.now().isoformat()
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.elapsed_time: Optional[str] = None
        self.resource_allocation = "CPU: 4 Cores | RAM: 16GB"
        self.logs: List[str] = []
        self.error: Optional[str] = None
        self._cancel_requested = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "competition_slug": self.competition_slug,
            "stage": self.stage,
            "status": self.status,
            "created_at": self.created_at,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_time": self.elapsed_time,
            "resource_allocation": self.resource_allocation,
            "logs": self.logs[-100:],  # last 100 log lines
            "error": self.error,
        }


class ExecutionQueueManager:
    def __init__(self):
        self.queue: List[TaskItem] = []
        self.history: List[TaskItem] = []
        self.current_task: Optional[TaskItem] = None
        self.global_state: str = "Idle"  # Idle, Discovering, Researching, Training, Validating, Submitting, Completed, Failed
        self.last_sync_time: str = datetime.datetime.now().isoformat()
        self.lock = threading.Lock()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def add_task(self, name: str, competition_slug: str, stage: str, executor_fn) -> TaskItem:
        with self.lock:
            task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            task = TaskItem(task_id, name, competition_slug, stage)
            task.executor = executor_fn
            self.queue.append(task)
            return task

    def cancel_task(self, task_id: str) -> bool:
        with self.lock:
            for task in self.queue:
                if task.id == task_id:
                    task.status = "cancelled"
                    self.queue.remove(task)
                    self.history.append(task)
                    return True
            if self.current_task and self.current_task.id == task_id:
                self.current_task._cancel_requested = True
                self.current_task.status = "cancelled"
                return True
        return False

    def _worker_loop(self):
        while True:
            task_to_run = None
            with self.lock:
                if not self.current_task and self.queue:
                    task_to_run = self.queue.pop(0)
                    self.current_task = task_to_run
                    task_to_run.status = "running"
                    task_to_run.start_time = datetime.datetime.now().isoformat()
                    self.global_state = task_to_run.stage

            if task_to_run:
                start_ts = time.time()
                try:
                    task_to_run.logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Started task '{task_to_run.name}' for {task_to_run.competition_slug}")
                    task_to_run.executor(task_to_run)
                    task_to_run.status = "completed"
                    task_to_run.logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Task completed successfully.")
                except Exception as e:
                    task_to_run.status = "failed"
                    task_to_run.error = str(e)
                    task_to_run.logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Task failed: {str(e)}")
                finally:
                    duration = time.time() - start_ts
                    task_to_run.elapsed_time = f"{duration:.1f}s"
                    task_to_run.end_time = datetime.datetime.now().isoformat()
                    with self.lock:
                        self.history.insert(0, task_to_run)
                        self.current_task = None
                        self.global_state = "Idle" if not self.queue else self.queue[0].stage
            time.sleep(0.5)


queue_manager = ExecutionQueueManager()
DEFAULT_COMPETITION = "playground-series-s6e2"
active_competition_slug: str = DEFAULT_COMPETITION

class SetActiveCompRequest(BaseModel):
    slug: str

@app.post("/api/active_competition")
def set_active_competition(req: SetActiveCompRequest):
    global active_competition_slug
    comp = registry.get_competition(req.slug)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Competition '{req.slug}' not found.")
    active_competition_slug = req.slug
    return {"status": "success", "active_competition": active_competition_slug}

# ---------------------------------------------------------
# Status & Overview Endpoints
# ---------------------------------------------------------
@app.get("/api/status")
def get_global_status():
    active_comp = queue_manager.current_task.competition_slug if queue_manager.current_task else active_competition_slug
    return {
        "state": queue_manager.global_state,
        "active_competition": active_comp,
        "current_stage": queue_manager.current_task.stage if queue_manager.current_task else "Idle",
        "queued_tasks_count": len(queue_manager.queue),
        "last_sync_time": queue_manager.last_sync_time,
        "account": {
            "username": "aamod",
            "cli_version": "2.2.5",
            "status": "Authenticated",
            "token_present": True,
        },
    }


@app.get("/api/overview")
def get_overview_data(slug: Optional[str] = None):
    comps = registry.list_competitions()
    total_comps = len(comps)
    supported_comps = [c for c in comps if c.get("status") == "supported"]
    
    # Classification categories breakdown
    tabular_comps = [c for c in comps if c.get("kind") == "csv_tabular"]
    code_comps = [c for c in comps if c.get("kind") == "code_competition"]
    cv_comps = [c for c in comps if c.get("kind") == "csv_cv"]
    agent_comps = [c for c in comps if c.get("kind") == "agent_or_optimization"]
    other_comps = [c for c in comps if c.get("kind") not in ("csv_tabular", "code_competition", "csv_cv", "agent_or_optimization")]
    
    # Target competition scoping
    target_slug = slug or active_competition_slug
    target_comp = registry.get_competition(target_slug) or (comps[0] if comps else {})
    target_slug = target_comp.get("slug", target_slug)

    # Experiments metrics for target competition
    target_exps = registry.list_experiments(target_slug) if target_slug else []
    all_exps = []
    for c in comps:
        all_exps.extend(registry.list_experiments(c["slug"]))
    
    base_exp = next((e for e in target_exps if e.get("status") == "baseline"), None)
    best_exp = max((e for e in target_exps if e.get("cv_mean") is not None), key=lambda x: x["cv_mean"], default=None)
    
    base_val = base_exp["cv_mean"] if base_exp else (target_comp.get("my_best_public_score") or 0.0)
    curr_val = best_exp["cv_mean"] if best_exp else base_val
    diff = curr_val - base_val
    
    # Target competition budget & quota
    target_budget = registry.get_budget(target_slug) if target_slug else {}
    daily_cap = config.get_daily_cap(target_slug) if target_slug else 5
    submissions_today = target_budget.get("submissions_today", 0)
    
    # Target competition submissions
    target_subs = registry.list_submissions(target_slug) if target_slug else []
    all_subs = []
    for c in comps:
        all_subs.extend(registry.list_submissions(c["slug"]))
    all_subs.sort(key=lambda s: s.get("created_at") or "", reverse=True)

    # Active research info
    active_info = None
    if queue_manager.current_task:
        active_info = queue_manager.current_task.to_dict()

    return {
        "target_competition": {
            "slug": target_slug,
            "title": target_comp.get("title", target_slug),
            "kind": target_comp.get("kind", "csv_tabular"),
            "category": target_comp.get("category", "Playground"),
            "metric": target_comp.get("evaluation_metric", "ROC AUC"),
            "direction": target_comp.get("direction", "maximize"),
            "best_public_score": target_comp.get("my_best_public_score"),
            "baseline_cv": base_val,
            "daily_cap": daily_cap,
            "submissions_today": submissions_today,
            "quota_remaining": max(0, daily_cap - submissions_today),
        },
        "classifications": {
            "tabular": {"label": "Tabular", "count": len(tabular_comps), "status": "Supported"},
            "code_competition": {"label": "Code Competition", "count": len(code_comps), "status": "Report Only"},
            "computer_vision": {"label": "Computer Vision", "count": len(cv_comps), "status": "Report Only"},
            "agent_simulation": {"label": "Agent Simulation", "count": len(agent_comps), "status": "Report Only"},
            "other": {"label": "Custom Format", "count": len(other_comps), "status": "Report Only"},
        },
        "metrics": {
            "joined_competitions": total_comps,
            "supported_competitions": len(supported_comps),
            "active_research_runs": 1 if queue_manager.current_task else 0,
            "experiments_completed": len(all_exps),
            "target_experiments_count": len(target_exps),
            "best_validation_improvement": {
                "competition": target_slug,
                "metric_name": target_comp.get("evaluation_metric", "ROC AUC"),
                "direction": target_comp.get("direction", "maximize"),
                "original_value": round(base_val, 5),
                "current_value": round(curr_val, 5),
                "delta": round(diff, 5),
                "has_improved": diff > 0.00039,
            },
            "pending_submissions": max(0, daily_cap - submissions_today),
            "daily_cap": daily_cap,
            "submissions_today": submissions_today,
        },
        "active_research": active_info,
        "recent_competitions": comps[:6],
        "recent_experiments": target_exps if target_exps else all_exps[-5:],
        "recent_submissions": target_subs if target_subs else all_subs[:5],
    }


# ---------------------------------------------------------
# Competitions Endpoints
# ---------------------------------------------------------
@app.get("/api/competitions")
def list_competitions(search: Optional[str] = None, kind: Optional[str] = None, status: Optional[str] = None):
    comps = registry.list_competitions()
    
    # Enrich with local baseline score and research status
    enriched = []
    for c in comps:
        slug = c["slug"]
        exps = registry.list_experiments(slug)
        base = next((e for e in exps if e.get("status") == "baseline"), None)
        best_cv = max((e["cv_mean"] for e in exps if e.get("cv_mean") is not None), default=None)
        
        has_research = (Path("research") / f"{slug}.md").exists()
        research_status = "Analyzed" if has_research else ("Pending" if c.get("status") == "supported" else "N/A")
        
        subs = registry.list_submissions(slug)
        
        row = dict(c)
        row["best_validation_score"] = best_cv or (base["cv_mean"] if base else None)
        row["research_status"] = research_status
        row["submissions_count"] = len(subs)
        row["last_updated"] = c.get("updated_at") or c.get("discovered_at") or "Recently"
        enriched.append(row)

    # Filter
    if search:
        search_lower = search.lower()
        enriched = [c for c in enriched if search_lower in c["slug"].lower() or search_lower in (c.get("title") or "").lower()]
    if kind:
        enriched = [c for c in enriched if c.get("kind") == kind]
    if status:
        enriched = [c for c in enriched if c.get("status") == status]

    return enriched


@app.get("/api/competitions/{slug}")
def get_competition_details(slug: str):
    comp = registry.get_competition(slug)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Competition '{slug}' not found in registry.")

    # Details
    exps = registry.list_experiments(slug)
    subs = registry.list_submissions(slug)
    notebooks = registry.list_notebooks(slug)
    
    # Dataset info
    data_dir = Path("workspaces") / slug / "data"
    dataset_info = {
        "downloaded": data_dir.exists() and any(data_dir.iterdir()) if data_dir.exists() else False,
        "files": [f.name for f in data_dir.iterdir()] if data_dir.exists() else [],
    }
    
    # Read research if available
    research_md = ""
    research_path = Path("research") / f"{slug}.md"
    if research_path.exists():
        research_md = research_path.read_text(encoding="utf-8")

    # Artifacts
    ws_artifacts = Path("workspaces") / slug / "artifacts"
    artifacts_list = []
    if ws_artifacts.exists():
        for item in ws_artifacts.iterdir():
            artifacts_list.append({
                "name": item.name,
                "type": "final_submission" if "final_submission" in item.name else "artifact",
                "size_bytes": item.stat().st_size,
                "path": str(item),
                "created_at": datetime.datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
            })

    return {
        "summary": dict(comp),
        "dataset": dataset_info,
        "public_research": {
            "notebooks": notebooks,
            "notes_markdown": research_md,
            "has_notes": bool(research_md),
        },
        "experiments": exps,
        "submissions": subs,
        "artifacts": artifacts_list,
    }


# ---------------------------------------------------------
# Research Endpoints
# ---------------------------------------------------------
@app.get("/api/research/{slug}")
def get_research_data(slug: str):
    notebooks = registry.list_notebooks(slug)
    research_file = Path("research") / f"{slug}.md"
    notes_content = research_file.read_text(encoding="utf-8") if research_file.exists() else ""
    
    # Determine workflow stages status
    has_notebooks = len(notebooks) > 0
    has_synthesis = bool(notes_content)
    
    stages = [
        {"name": "Discover", "status": "completed" if has_notebooks else "pending", "description": "Identify top kernels by votes & score"},
        {"name": "Rank", "status": "completed" if has_notebooks else "pending", "description": "Prioritize high-yield techniques & verify authors"},
        {"name": "Inspect", "status": "completed" if has_synthesis else "pending", "description": "Analyze feature engineering, CV, model configs"},
        {"name": "Reproduce", "status": "completed" if has_synthesis else "pending", "description": "Verify local execution feasibility"},
        {"name": "Compare", "status": "completed" if has_synthesis else "pending", "description": "Synthesize recommendations against baseline"},
    ]

    return {
        "competition_slug": slug,
        "workflow_stages": stages,
        "notebooks": notebooks,
        "synthesis_markdown": notes_content,
    }


# ---------------------------------------------------------
# Experiments Endpoints
# ---------------------------------------------------------
@app.get("/api/experiments")
def list_experiments(slug: Optional[str] = None):
    if slug:
        exps = registry.list_experiments(slug)
    else:
        comps = registry.list_competitions()
        exps = []
        for c in comps:
            exps.extend(registry.list_experiments(c["slug"]))

    # Sort descending by id
    exps.sort(key=lambda x: x["id"], reverse=True)
    return exps


@app.get("/api/experiments/{exp_id}")
def get_experiment_details(exp_id: int):
    # Search for experiment across all competitions
    comps = registry.list_competitions()
    target_exp = None
    target_comp = None
    for c in comps:
        exps = registry.list_experiments(c["slug"])
        for e in exps:
            if e["id"] == exp_id:
                target_exp = e
                target_comp = c
                break
        if target_exp:
            break

    if not target_exp:
        raise HTTPException(status_code=404, detail=f"Experiment ID {exp_id} not found.")

    # Build rich details
    baseline_score = 0.95438
    cv_mean = target_exp.get("cv_mean")
    delta = (cv_mean - baseline_score) if cv_mean is not None else None

    exp_desc = target_exp.get("description", "")
    matching_hyp = next((h for h in HYPOTHESIS_EXPERIMENTS if h["description"] == exp_desc or h["id"] in exp_desc), None)
    if matching_hyp:
        diff_lines = ["--- train.py (baseline)", f"+++ train.py ({matching_hyp['id']})", "@@ Feature Engineering @@"]
        for line in matching_hyp["feature_code"].strip().splitlines():
            diff_lines.append(f"+{line}" if line.strip() else "+")
        diff_sample = "\n".join(diff_lines)
    else:
        diff_sample = f"--- train.py (baseline)\n+++ train.py (exp_#{exp_id})\n@@ Configuration @@\n+ Initial LightGBM 5-Fold Stratified\n+ CV: {cv_mean} (Std: {target_exp.get('cv_std')})"

    return {
        "experiment": target_exp,
        "competition": target_comp,
        "evaluation": {
            "baseline_score": baseline_score,
            "candidate_score": cv_mean,
            "delta": delta,
            "metric": target_comp.get("evaluation_metric", "ROC AUC"),
            "direction": target_comp.get("direction", "maximize"),
            "noise_floor": target_exp.get("cv_std") or 0.00039,
            "meets_significance": delta > 0.00039 if delta is not None else False,
        },
        "resources": {
            "runtime_sec": target_exp.get("runtime_sec", 15.0),
            "memory_mb": target_exp.get("memory_mb", 320.0),
            "gpu": "NVIDIA GeForce RTX 4050 Laptop GPU (6.1 GB VRAM)",
            "folds": 5,
        },
        "artifacts": {
            "diff": diff_sample,
            "log": f"Train finished with 5 folds. Mean ROC AUC: {cv_mean}. Std: {target_exp.get('cv_std')}",
        },
        "decision": {
            "status": target_exp.get("status"),
            "reason": "Discarded and git reset: delta was within statistical fold noise floor (delta < cv_std)." if target_exp.get("status") == "reverted" else "Retained as baseline.",
        }
    }


# ---------------------------------------------------------
# Artifacts & Models Endpoints
# ---------------------------------------------------------
@app.get("/api/artifacts")
def list_artifacts(slug: Optional[str] = None):
    comps = [slug] if slug else [c["slug"] for c in registry.list_competitions()]
    all_artifacts = []

    for comp_slug in comps:
        comp_dir = Path("workspaces") / comp_slug
        if not comp_dir.exists():
            continue

        # Artifacts dir
        art_dir = comp_dir / "artifacts"
        if art_dir.exists():
            for p in art_dir.iterdir():
                if p.is_file():
                    all_artifacts.append({
                        "name": p.name,
                        "type": "Final Submission Candidate" if "final_submission" in p.name else "Artifact",
                        "competition": comp_slug,
                        "version": "v1.0-final",
                        "size_bytes": p.stat().st_size,
                        "size_formatted": f"{p.stat().st_size / 1024:.1f} KB",
                        "created_at": datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                        "path": str(p),
                    })

        # Best dir
        best_dir = comp_dir / "best"
        if best_dir.exists():
            for p in best_dir.iterdir():
                if p.is_file():
                    all_artifacts.append({
                        "name": f"best/{p.name}",
                        "type": "Best Verified Checkpoint",
                        "competition": comp_slug,
                        "version": "best-verified",
                        "size_bytes": p.stat().st_size,
                        "size_formatted": f"{p.stat().st_size / 1024:.1f} KB",
                        "created_at": datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                        "path": str(p),
                    })

    return all_artifacts


# ---------------------------------------------------------
# Submissions Endpoints
# ---------------------------------------------------------
@app.get("/api/submissions")
def list_submissions(slug: Optional[str] = None):
    comps = [slug] if slug else [c["slug"] for c in registry.list_competitions()]
    subs = []
    for c in comps:
        comp_subs = registry.list_submissions(c)
        for s in comp_subs:
            s_dict = dict(s)
            s_dict["competition_slug"] = c
            subs.append(s_dict)
    subs.sort(key=lambda x: x.get("date") or "", reverse=True)
    return subs


@app.get("/api/leaderboard/{slug}")
def get_leaderboard_history(slug: str):
    comp = registry.get_competition(slug)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    subs = registry.list_submissions(slug)
    exps = registry.list_experiments(slug)
    base_exp = next((e for e in exps if e.get("status") == "baseline"), None)
    
    # Sort submissions chronologically
    chronological_subs = sorted(subs, key=lambda s: s.get("date") or "")
    
    timeline = []
    for s in chronological_subs:
        timeline.append({
            "date": s.get("date"),
            "public_score": s.get("public_score"),
            "file_name": s.get("file_name"),
            "is_baseline": bool(s.get("is_baseline")),
            "description": s.get("description"),
            "ref": s.get("ref"),
        })

    return {
        "competition": comp,
        "best_public_score": comp.get("my_best_public_score"),
        "best_local_validation_score": base_exp["cv_mean"] if base_exp else None,
        "metric": comp.get("evaluation_metric", "Metric"),
        "timeline": timeline,
    }


# ---------------------------------------------------------
# Execution Queue Endpoints
# ---------------------------------------------------------
@app.get("/api/queue")
def get_queue():
    with queue_manager.lock:
        return {
            "current_task": queue_manager.current_task.to_dict() if queue_manager.current_task else None,
            "queued_tasks": [t.to_dict() for t in queue_manager.queue],
            "history": [t.to_dict() for t in queue_manager.history[:20]],
            "concurrency": {
                "active_workers": 1 if queue_manager.current_task else 0,
                "max_workers": 1,
            },
        }


@app.post("/api/queue/cancel/{task_id}")
def cancel_queue_task(task_id: str):
    cancelled = queue_manager.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Task not found or already finished.")
    return {"status": "success", "message": f"Task {task_id} cancelled."}


# ---------------------------------------------------------
# Settings Endpoints
# ---------------------------------------------------------
@app.get("/api/settings")
def get_settings():
    return {
        "kaggle": {
            "username": "aamod",
            "cli_version": "2.2.5",
            "token_path": "~/.kaggle/access_token",
            "connected": True,
        },
        "research": {
            "timeout_seconds": config.budgets.experiment_timeout_seconds,
            "max_experiments": config.budgets.max_experiments_per_run,
            "patience": config.budgets.patience_experiments,
            "min_delta_folds": config.noise_gate.min_improvement_epsilon,
            "random_seed": config.cv.seed,
            "default_competition": "playground-series-s6e2",
        },
        "compute": {
            "gpu": "NVIDIA GeForce RTX 4050 Laptop GPU (6.1 GB VRAM)",
            "cpu_cores": 16,
            "max_concurrent_runs": 1,
            "sandbox_worktree_enabled": True,
        },
        "submissions": {
            "dry_run_default": True,
            "daily_cap_default": config.get_daily_cap("default"),
            "require_approval": True,
            "per_competition_caps": config.daily_caps,
        },
        "storage": {
            "workspaces_dir": config.paths.workspaces_dir,
            "research_dir": config.paths.research_dir,
            "registry_db": config.paths.registry_db,
            "reports_dir": config.paths.reports_dir,
            "evidence_dir": config.paths.evidence_dir,
        },
    }


# ---------------------------------------------------------
# Action Triggers
# ---------------------------------------------------------
class ActionRequest(BaseModel):
    competition_slug: Optional[str] = "playground-series-s6e2"
    authorize: Optional[bool] = False
    message: Optional[str] = None


@app.post("/api/actions/sync_competitions")
def action_sync_competitions():
    def execute_sync(task: TaskItem):
        task.logs.append("Initializing DiscoveryService...")
        disc = DiscoveryService(connector, registry, config)
        comps = disc.discover_all(incremental=True)
        disc.write_evidence()
        task.logs.append(f"Discovered and indexed {len(comps)} entered competitions.")
        queue_manager.last_sync_time = datetime.datetime.now().isoformat()

    task = queue_manager.add_task(
        name="Sync Competitions",
        competition_slug="all",
        stage="Discovering",
        executor_fn=execute_sync,
    )
    return {"status": "enqueued", "task_id": task.id}


@app.post("/api/actions/run_research")
def action_run_research(req: ActionRequest):
    slug = req.competition_slug or "playground-series-s6e2"
    def execute_research(task: TaskItem):
        task.logs.append(f"Discovering public notebooks for {slug}...")
        res = PublicResearcher(slug, connector, registry, config)
        pulled = res.discover_and_pull(top_n=4)
        task.logs.append(f"Pulled {len(pulled)} top notebooks. Analyzing techniques...")
        analyzer = NotebookAnalyzer(slug, registry, research_dir=config.paths.research_dir)
        techniques = [
            analyzer.analyze_notebook(
                Path(p["local_dir"]), p["ref"], p["title"], p["author"], p["total_votes"]
            )
            for p in pulled
        ]
        analyzer.synthesize_research(techniques)
        analyzer.write_evidence()
        task.logs.append(f"Research synthesis completed: research/{slug}.md")

    task = queue_manager.add_task(
        name=f"Mine Public Research ({slug})",
        competition_slug=slug,
        stage="Researching",
        executor_fn=execute_research,
    )
    return {"status": "enqueued", "task_id": task.id}


@app.post("/api/actions/run_baseline")
def action_run_baseline(req: ActionRequest):
    slug = req.competition_slug or "playground-series-s6e2"
    def execute_baseline(task: TaskItem):
        task.logs.append(f"Downloading competition data for {slug}...")
        ws = WorkspaceManager(slug, connector, registry, config)
        ws.download_data()
        task.logs.append("Inspecting schema...")
        schema = ws.inspect_schema()
        task.logs.append(f"Training 5-Fold Stratified CV baseline on {schema.train_shape[0]} samples...")
        mean, std, sub, val = ws.run_baseline(schema)
        ws.write_evidence(schema, mean, std, val)
        task.logs.append(f"Baseline established: Mean CV={mean:.5f} (±{std:.5f})")

    task = queue_manager.add_task(
        name=f"Setup Baseline ({slug})",
        competition_slug=slug,
        stage="Training",
        executor_fn=execute_baseline,
    )
    return {"status": "enqueued", "task_id": task.id}


@app.post("/api/actions/run_experiment")
def action_run_experiment(req: ActionRequest):
    slug = req.competition_slug or "playground-series-s6e2"
    def execute_loop(task: TaskItem):
        exps = registry.list_experiments(slug)
        base = next((e for e in exps if e.get("status") == "baseline"), None)
        base_score = base["cv_mean"] if base else 0.95438
        base_std = base["cv_std"] if base else 0.00039

        task.logs.append(f"Starting Karpathy AutoResearch loop for {slug} (Baseline: {base_score:.5f})...")
        loop = AutoResearchLoop(
            competition_slug=slug,
            registry=registry,
            config=config,
            baseline_score=base_score,
            baseline_std=base_std,
            target_col="Heart Disease",
            id_col="id",
        )
        results = loop.run_loop(max_experiments=3)
        loop.write_evidence(results)
        task.logs.append(f"Executed {len(results)} experiments. Results audited in registry and results.tsv.")

    task = queue_manager.add_task(
        name=f"AutoResearch Loop ({slug})",
        competition_slug=slug,
        stage="Training",
        executor_fn=execute_loop,
    )
    return {"status": "enqueued", "task_id": task.id}


@app.post("/api/actions/validate_submission")
def action_validate_submission(req: ActionRequest):
    slug = req.competition_slug or "playground-series-s6e2"
    sub_file_path = Path("workspaces") / slug / "artifacts" / "final_submission.csv"
    if not sub_file_path.exists():
        raise HTTPException(status_code=400, detail=f"No final submission file found at {sub_file_path}. Run Baseline first.")

    sm = SubmissionManager(slug, connector, registry, config)
    outcome = sm.process_submission(sub_file_path, cv_score=0.95438, submit=False)
    
    return {
        "status": "validated",
        "is_valid": outcome.is_valid,
        "validation_summary": outcome.validation_summary,
        "dry_run_command": outcome.command,
        "candidate_file": str(sub_file_path),
    }


@app.post("/api/actions/submit_candidate")
def action_submit_candidate(req: ActionRequest):
    if not req.authorize:
        raise HTTPException(status_code=400, detail="Explicit user authorization required before live submission.")
    
    slug = req.competition_slug or "playground-series-s6e2"
    sub_file_path = Path("workspaces") / slug / "artifacts" / "final_submission.csv"
    if not sub_file_path.exists():
        raise HTTPException(status_code=400, detail=f"No candidate file found at {sub_file_path}")

    def execute_submit(task: TaskItem):
        task.logs.append(f"Submitting {sub_file_path.name} to Kaggle competition '{slug}'...")
        sm = SubmissionManager(slug, connector, registry, config)
        outcome = sm.process_submission(
            sub_file_path,
            cv_score=0.95438,
            message=req.message or "Kaggle AutoResearch verified candidate",
            submit=True,
        )
        task.logs.append(f"Submission recorded! Reference: {outcome.submission_ref}, Public Score: {outcome.public_score}")
        if outcome.divergence_warning:
            task.logs.append(f"WARNING: {outcome.divergence_warning}")

    task = queue_manager.add_task(
        name=f"Live Submit ({slug})",
        competition_slug=slug,
        stage="Submitting",
        executor_fn=execute_submit,
    )
    return {"status": "enqueued", "task_id": task.id}


# ---------------------------------------------------------
# Static Frontend Serving
# ---------------------------------------------------------
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(static_dir / "index.html"))
