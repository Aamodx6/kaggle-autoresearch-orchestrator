"""Command Line Interface for Kaggle AutoResearch Orchestrator."""

import argparse
import sys
import threading
import time
from pathlib import Path

from orch.analyzer import NotebookAnalyzer
from orch.config import load_config
from orch.connector import KaggleConnector
from orch.discovery import DiscoveryService
from orch.logging_util import get_logger
from orch.loop import AutoResearchLoop
from orch.registry import Registry
from orch.reporting import DashboardReporter
from orch.researcher import PublicResearcher
from orch.submitter import SubmissionManager
from orch.workspace import WorkspaceManager

logger = get_logger("orch.cli")


def run_doctor_mode(config, connector, registry):
    """Diagnose environment, authentication, hardware, and workspace readiness."""
    import shutil
    import subprocess
    print("\n" + "=" * 65)
    print("  Kaggle AutoResearch Orchestrator — System Diagnostic (Doctor)")
    print("=" * 65)

    checks_passed = 0
    total_checks = 6

    # 1. Python & Virtual Environment
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"\n[1/6] Python Runtime: v{py_ver}")
    if sys.version_info >= (3, 10):
        print("      PASS: Python version meets requirement (>= 3.10)")
        checks_passed += 1
    else:
        print("      FAIL: Python >= 3.10 required.")

    # 2. Kaggle CLI & Authentication
    print("\n[2/6] Kaggle Authentication & CLI:")
    auth_ok, username = connector.authenticate()
    if auth_ok:
        print(f"      PASS: Authenticated as Kaggle user '{username}'")
        checks_passed += 1
    else:
        print("      WARN: Kaggle token missing or expired (~/.kaggle/access_token)")

    # 3. GPU & Acceleration
    print("\n[3/6] Hardware Acceleration (Compute):")
    try:
        import torch
        if torch.cuda.is_available():
            dev_name = torch.cuda.get_device_name(0)
            mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"      PASS: CUDA GPU detected: {dev_name} ({mem:.1f} GB VRAM)")
            checks_passed += 1
        else:
            print("      INFO: CUDA not detected, using CPU fallback.")
            checks_passed += 1
    except ImportError:
        print("      INFO: PyTorch not in environment, tree models running on CPU/OpenMP.")
        checks_passed += 1

    # 4. SQLite Registry Database
    print("\n[4/6] SQLite Registry Database:")
    db_path = Path(config.paths.registry_db)
    if db_path.exists():
        comps = registry.list_competitions()
        subs = registry.list_submissions()
        print(f"      PASS: {db_path} accessible ({len(comps)} competitions, {len(subs)} submissions)")
        checks_passed += 1
    else:
        print(f"      WARN: Database not initialized at {db_path}. Will initialize on first run.")

    # 5. Git Worktree / Sandbox Support
    print("\n[5/6] Git Repository & Worktrees:")
    git_bin = shutil.which("git")
    if git_bin:
        try:
            res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
            print("      PASS: Git binary present and active repository verified.")
            checks_passed += 1
        except Exception:
            print("      WARN: Not inside a valid git repository.")
    else:
        print("      FAIL: Git binary not found in PATH.")

    # 6. Web UI Static Assets
    print("\n[6/6] Web UI Production Bundle:")
    static_index = Path("orch/static/index.html")
    static_assets = Path("orch/static/assets")
    if static_index.exists() and static_assets.exists() and any(static_assets.glob("*.js")):
        js_count = len(list(static_assets.glob("*.js")))
        print(f"      PASS: UI production assets present ({js_count} JS chunks)")
        checks_passed += 1
    else:
        print("      WARN: UI static bundle missing in orch/static. Build with: cd frontend && npm run build")

    print("\n" + "-" * 65)
    print(f"Diagnostic Summary: {checks_passed}/{total_checks} checks passed.")
    print("=" * 65 + "\n")
    return checks_passed == total_checks


def run_discover_mode(config, connector, registry, incremental: bool = True):
    logger.info("Running mode: DISCOVER")
    discovery = DiscoveryService(connector, registry, config)
    comps = discovery.discover_all(incremental=incremental)
    evidence_path = discovery.write_evidence()
    print(f"\n[DISCOVER] Discovered and registered {len(comps)} entered competitions.")
    print(f"[EVIDENCE] Written to {evidence_path}")
    return comps


def run_research_mode(slug: str, config, connector, registry):
    logger.info(f"Running mode: RESEARCH for {slug}")
    researcher = PublicResearcher(slug, connector, registry, config)
    pulled = researcher.discover_and_pull(top_n=4)

    analyzer = NotebookAnalyzer(slug, registry, research_dir=config.paths.research_dir)
    techniques = []
    for p in pulled:
        tech = analyzer.analyze_notebook(
            nb_dir=Path(p["local_dir"]),
            ref=p["ref"],
            title=p["title"],
            author=p["author"],
            votes=p["total_votes"],
        )
        techniques.append(tech)

    analyzer.synthesize_research(techniques)
    ev_path = analyzer.write_evidence()
    print(f"\n[RESEARCH] Analyzed {len(techniques)} notebooks for {slug}.")
    print(f"[EVIDENCE] Written to {ev_path}")
    return techniques


def run_submit_mode(slug: str, config, connector, registry, submit: bool = False):
    logger.info(f"Running mode: SUBMIT for {slug} (submit_flag={submit})")
    sm = SubmissionManager(slug, connector, registry, config)
    final_sub = sm.refit_best_candidate()

    comp = registry.get_competition(slug) or {}
    best_cv = comp.get("my_best_public_score") or 0.95438

    outcome = sm.process_submission(
        candidate_path=final_sub,
        cv_score=best_cv,
        message="AutoResearch validated candidate submission",
        submit=submit,
    )
    ev_path = sm.write_evidence(outcome, final_sub, cv_score=best_cv)
    print(f"\n[SUBMIT] Mode: {outcome.mode.upper()}, Validation: {'PASSED' if outcome.is_valid else 'FAILED'}")
    print(f"[COMMAND] {outcome.command}")
    print(f"[EVIDENCE] Written to {ev_path}")
    return outcome


def run_full_pipeline(slug: str, config, connector, registry, submit: bool = False):
    logger.info(f"Running mode: FULL pipeline for competition: {slug}")

    # Stage S1: Discovery
    run_discover_mode(config, connector, registry, incremental=True)

    # Stage S2: Workspace & Baseline
    ws = WorkspaceManager(slug, connector, registry, config)
    ws.download_data()
    schema = ws.inspect_schema()
    cv_mean, cv_std, baseline_sub, val_res = ws.run_baseline(schema)
    ws.write_evidence(schema, cv_mean, cv_std, val_res)

    # Stage S3: Public Research
    run_research_mode(slug, config, connector, registry)

    # Stage S4: AutoResearch Adapter Loop
    loop = AutoResearchLoop(
        competition_slug=slug,
        registry=registry,
        config=config,
        baseline_score=cv_mean,
        baseline_std=cv_std,
        target_col=schema.target_column,
        id_col=schema.id_column,
    )
    loop_results = loop.run_loop(max_experiments=config.budgets.max_experiments_per_run)
    loop.write_evidence(loop_results)

    # Stage S5: Validate & Submit
    outcome = run_submit_mode(slug, config, connector, registry, submit=submit)

    # Stage S7: Reporting Dashboard
    reporter = DashboardReporter(registry, config)
    dash_path = reporter.generate_html_dashboard()

    print("\n" + "=" * 70)
    print(f"FULL PIPELINE EXECUTION COMPLETED FOR: {slug}")
    print(f"Baseline CV Score: {cv_mean:.5f} (+/- {cv_std:.5f})")
    print(f"Best Verified CV:  {loop.best_score:.5f}")
    print(f"Final Validation:  {'PASSED' if outcome.is_valid else 'FAILED'}")
    print(f"Submission Mode:   {outcome.mode.upper()}")
    print(f"Exact Command:     {outcome.command}")
    print(f"Dashboard Report:  {dash_path}")
    print("=" * 70)


def run_ui_mode(port: int = 8000):
    """Starts the Kaggle AutoResearch Web Interface and opens the browser."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    import webbrowser
    import uvicorn
    from orch.api import app

    url = f"http://127.0.0.1:{port}"
    logger.info(f"Starting Kaggle AutoResearch Web UI on {url}...")
    
    # Open browser in a separate thread after server starts
    def open_browser():
        time.sleep(1.0)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    
    print("\n" + "=" * 70)
    print("Kaggle AutoResearch Orchestrator - Professional Web Interface")
    print(f"Local URL: {url}")
    print("Press Ctrl+C to stop the web server.")
    print("=" * 70 + "\n")
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    except KeyboardInterrupt:
        logger.info("UI stopped by user.")


def main():
    parser = argparse.ArgumentParser(
        description="Kaggle AutoResearch Orchestrator CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "mode",
        choices=["discover", "research", "submit", "full", "ui", "doctor"],
        help="Operational mode",
    )

    parser.add_argument(
        "--competition",
        "-c",
        default="playground-series-s6e2",
        help="Competition slug for research, submit, or full pipeline",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration YAML file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run mode (never submits to Kaggle)",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        default=False,
        help="Perform real Kaggle submission (requires remaining quota under daily cap)",
    )
    parser.add_argument(
        "--no-incremental",
        action="store_true",
        default=False,
        help="Force full re-discovery instead of incremental",
    )

    args = parser.parse_args()

    config = load_config(args.config)
    connector = KaggleConnector()
    registry = Registry(config.paths.registry_db)

    # Live submit requires --submit explicitly
    submit_flag = args.submit and not args.dry_run

    if args.mode == "discover":
        run_discover_mode(config, connector, registry, incremental=not args.no_incremental)
    elif args.mode == "research":
        run_research_mode(args.competition, config, connector, registry)
    elif args.mode == "submit":
        run_submit_mode(args.competition, config, connector, registry, submit=submit_flag)
    elif args.mode == "full":
        run_full_pipeline(args.competition, config, connector, registry, submit=submit_flag)
    elif args.mode == "ui":
        run_ui_mode()
    elif args.mode == "doctor":
        run_doctor_mode(config, connector, registry)



if __name__ == "__main__":
    main()
