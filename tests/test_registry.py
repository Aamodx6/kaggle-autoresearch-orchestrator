"""Unit tests for SQLite Registry."""

import tempfile
from pathlib import Path
import pytest

from orch.registry import Registry


@pytest.fixture
def temp_registry():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_reg.db"
        yield Registry(str(db_path))


def test_registry_competitions_upsert_and_retrieve(temp_registry):
    temp_registry.upsert_competition({
        "slug": "test-comp",
        "id": 999,
        "title": "Test Comp",
        "url": "http://example.com",
        "deadline": "2026-12-31",
        "category": "Featured",
        "reward": "$10,000",
        "evaluation_metric": "Roc Auc Score",
        "direction": "maximize",
        "kind": "csv_tabular",
        "status": "supported",
        "is_kernels_submissions_only": False,
        "max_daily_submissions": 5,
        "my_best_public_score": 0.952,
    })

    comp = temp_registry.get_competition("test-comp")
    assert comp is not None
    assert comp["slug"] == "test-comp"
    assert comp["kind"] == "csv_tabular"
    assert comp["status"] == "supported"
    assert comp["my_best_public_score"] == 0.952


def test_registry_submissions_and_experiments(temp_registry):
    temp_registry.upsert_submission({
        "ref": 101,
        "competition_slug": "test-comp",
        "file_name": "sub.csv",
        "date": "2026-01-01",
        "description": "Baseline submission",
        "status": "COMPLETE",
        "public_score": 0.95,
        "private_score": 0.94,
        "is_baseline": True,
    })

    subs = temp_registry.list_submissions("test-comp")
    assert len(subs) == 1
    assert subs[0]["public_score"] == 0.95
    assert subs[0]["is_baseline"] == 1

    exp_id = temp_registry.record_experiment({
        "competition_slug": "test-comp",
        "commit_hash": "abc1234",
        "cv_mean": 0.955,
        "cv_std": 0.001,
        "runtime_sec": 12.5,
        "memory_mb": 512,
        "status": "keep",
        "description": "Added ratio features",
    })
    assert exp_id > 0

    exps = temp_registry.list_experiments("test-comp")
    assert len(exps) == 1
    assert exps[0]["commit_hash"] == "abc1234"
    assert exps[0]["status"] == "keep"


def test_registry_budgets_and_daily_cap(temp_registry):
    temp_registry.set_budget("test-comp", cap=3, timeout_sec=120, mem_mb=2048)
    b = temp_registry.get_budget("test-comp")
    assert b["daily_submission_cap"] == 3
    assert b["submissions_today"] == 0

    c1 = temp_registry.increment_daily_submission("test-comp")
    assert c1 == 1
    c2 = temp_registry.increment_daily_submission("test-comp")
    assert c2 == 2
