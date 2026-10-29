"""Integration test exercising end-to-end pipeline in dry-run mode."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from orch.config import AppConfig, BudgetsConfig, PathsConfig
from orch.connector import KaggleConnector
from orch.discovery import DiscoveryService
from orch.loop import AutoResearchLoop
from orch.registry import Registry
from orch.reporting import DashboardReporter
from orch.submitter import SubmissionManager
from orch.workspace import WorkspaceManager


def test_end_to_end_pipeline_dry_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test_reg.db"
        workspaces_dir = tmp_path / "workspaces"
        research_dir = tmp_path / "research"
        evidence_dir = tmp_path / "evidence"
        reports_dir = tmp_path / "reports"

        config = AppConfig(
            budgets=BudgetsConfig(experiment_timeout_seconds=30, max_experiments_per_run=1, patience_experiments=1),
            paths=PathsConfig(
                registry_db=str(db_path),
                workspaces_dir=str(workspaces_dir),
                research_dir=str(research_dir),
                evidence_dir=str(evidence_dir),
                reports_dir=str(reports_dir),
            ),
        )

        registry = Registry(str(db_path))
        connector = KaggleConnector(max_retries=1)

        slug = "mock-competition"

        # Mock competition metadata
        mock_comp = MagicMock()
        mock_comp.id = 1111
        mock_comp.ref = f"https://www.kaggle.com/competitions/{slug}"
        mock_comp.title = "Mock Competition"
        mock_comp.url = f"https://www.kaggle.com/competitions/{slug}"
        mock_comp.deadline = "2026-12-31T23:59:00"
        mock_comp.category = "Playground"
        mock_comp.reward = "Swag"
        mock_comp.evaluation_metric = "Roc Auc Score"
        mock_comp.is_kernels_submissions_only = False
        mock_comp.user_has_entered = True
        mock_comp.user_rank = 50
        mock_comp.max_daily_submissions = 5
        mock_comp.submissions_disabled = False
        mock_comp.license_name = "Apache 2.0"

        f1 = MagicMock()
        f1.name = "train.csv"
        f1.total_bytes = 1000
        f2 = MagicMock()
        f2.name = "test.csv"
        f2.total_bytes = 500
        f3 = MagicMock()
        f3.name = "sample_submission.csv"
        f3.total_bytes = 200

        mock_api = MagicMock()
        mock_api.competitions_list.return_value = MagicMock(competitions=[mock_comp])
        mock_api.competition_submissions.return_value = []
        mock_api.competition_list_files.return_value = MagicMock(files=[f1, f2, f3])


        with patch.object(connector, "get_api", return_value=mock_api):
            # 1. Discovery
            discovery = DiscoveryService(connector, registry, config)
            comps = discovery.discover_all(incremental=False)
            assert len(comps) == 1
            assert comps[0]["kind"] == "csv_tabular"
            assert comps[0]["status"] == "supported"

            # Create synthetic data in workspace for baseline
            ws_comp_dir = workspaces_dir / slug / "data"
            ws_comp_dir.mkdir(parents=True, exist_ok=True)

            train_df = pd.DataFrame({
                "id": list(range(100)),
                "feat1": [float(i % 5) for i in range(100)],
                "feat2": [float(i % 3) for i in range(100)],
                "target": [i % 2 for i in range(100)],
            })
            test_df = pd.DataFrame({
                "id": list(range(100, 150)),
                "feat1": [float(i % 5) for i in range(50)],
                "feat2": [float(i % 3) for i in range(50)],
            })
            sample_df = pd.DataFrame({
                "id": list(range(100, 150)),
                "target": [0.5 for _ in range(50)],
            })

            train_df.to_csv(ws_comp_dir / "train.csv", index=False)
            test_df.to_csv(ws_comp_dir / "test.csv", index=False)
            sample_df.to_csv(ws_comp_dir / "sample_submission.csv", index=False)

            # 2. Workspace & Baseline
            ws = WorkspaceManager(slug, connector, registry, config)
            schema = ws.inspect_schema()
            assert schema.id_column == "id"
            assert schema.target_column == "target"

            cv_mean, cv_std, baseline_sub, val_res = ws.run_baseline(schema)
            assert cv_mean > 0.0
            assert val_res.is_valid

            # 3. Validation & Dry-Run Submission
            sm = SubmissionManager(slug, connector, registry, config)
            final_sub = sm.refit_best_candidate()
            outcome = sm.process_submission(
                candidate_path=final_sub,
                cv_score=cv_mean,
                message="Integration test dry run submission",
                submit=False,
            )

            assert outcome.mode == "dry-run"
            assert outcome.is_valid
            assert f"kaggle competitions submit -c {slug}" in outcome.command

            # 4. Reporting Dashboard
            reporter = DashboardReporter(registry, config)
            dash_path = reporter.generate_html_dashboard(reports_dir / "dashboard.html")
            assert dash_path.exists()
            assert dash_path.stat().st_size > 0
