"""Comprehensive tests for API endpoints, agent-ready errors, and security guards.
Audited and generated under gstack /test-audit and /cso guidelines.
"""

import pytest
from fastapi.testclient import TestClient

from orch.api import app, sanitize_slug
from orch.validator import SubmissionValidator


@pytest.fixture
def client():
    return TestClient(app)


def test_sanitize_slug_valid():
    """Verify standard slugs are preserved."""
    assert sanitize_slug("playground-series-s6e2") == "playground-series-s6e2"
    assert sanitize_slug("vesuvius-challenge-surface-detection") == "vesuvius-challenge-surface-detection"
    assert sanitize_slug("name-that-llm") == "name-that-llm"


def test_sanitize_slug_security_rejections():
    """CSO: Verify path traversal and injection attempts are rejected."""
    bad_slugs = [
        "../etc/passwd",
        "../../workspaces",
        "comp/subpath",
        "comp\\subpath",
        "slug with spaces",
        "slug;rm -rf /",
        "slug|cat",
    ]
    for bad in bad_slugs:
        with pytest.raises(Exception) as excinfo:
            sanitize_slug(bad)
        assert "INVALID_COMPETITION_SLUG" in str(excinfo.value.detail)


def test_api_status_endpoint(client):
    """Verify /api/status returns required system telemetry."""
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "state" in data
    assert "active_competition" in data
    assert "account" in data
    assert data["account"]["username"] == "aamod"


def test_api_competitions_list(client):
    """Verify /api/competitions returns list of entered competitions."""
    res = client.get("/api/competitions")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    sample = data[0]
    assert "slug" in sample
    assert "title" in sample
    assert "kind" in sample


def test_api_agent_ready_error_on_unknown_competition(client):
    """Verify 404 responses conform to agent-ready error schema."""
    res = client.get("/api/competitions/non-existent-competition-xyz")
    assert res.status_code == 404
    detail = res.json().get("detail", {})
    assert isinstance(detail, dict)
    assert detail.get("error_code") == "COMPETITION_NOT_FOUND"
    assert "message" in detail
    assert "hint" in detail
    assert "suggested_action" in detail


def test_api_agent_ready_error_on_path_traversal(client):
    """CSO: Verify directory traversal attempt yields agent-ready 400 error."""
    res = client.get("/api/competitions/invalid..slug")
    assert res.status_code == 400
    detail = res.json().get("detail", {})
    assert detail.get("error_code") == "INVALID_COMPETITION_SLUG"


def test_api_overview_endpoint(client):
    """Verify /api/overview schema and metrics."""
    res = client.get("/api/overview")
    assert res.status_code == 200
    data = res.json()
    assert "target_competition" in data
    assert "classifications" in data
    assert "metrics" in data
    assert "tabular" in data["classifications"]


def test_api_experiments_endpoint(client):
    """Verify /api/experiments returns keep/revert trial list."""
    res = client.get("/api/experiments")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    exp = data[0]
    assert "id" in exp
    assert "competition_slug" in exp


def test_api_artifacts_endpoint(client):
    """Verify /api/artifacts returns verified checkpoints and submissions."""
    res = client.get("/api/artifacts")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    art = data[0]
    assert "name" in art
    assert "type" in art
    assert "path" in art


def test_api_queue_endpoint(client):
    """Verify /api/queue returns worker capacity and task logs."""
    res = client.get("/api/queue")
    assert res.status_code == 200
    data = res.json()
    assert "concurrency" in data
    assert data["concurrency"]["max_workers"] >= 1
    assert "history" in data


def test_api_settings_endpoint(client):
    """Verify /api/settings returns authentic configuration."""
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert "kaggle" in data
    assert "compute" in data
    assert "research" in data
    assert data["kaggle"]["cli_version"] == "2.2.5"


def test_validator_preflight_schema_checks(tmp_path):
    """Test SubmissionValidator against header mismatches and NaN values."""
    import pandas as pd

    # Good submission
    good_csv = tmp_path / "good.csv"
    sample_csv = tmp_path / "sample.csv"
    df_sample = pd.DataFrame({"id": [1, 2, 3], "target": [0.5, 0.5, 0.5]})
    df_good = pd.DataFrame({"id": [1, 2, 3], "target": [0.1, 0.8, 0.4]})
    df_sample.to_csv(sample_csv, index=False)
    df_good.to_csv(good_csv, index=False)

    validator = SubmissionValidator(sample_csv)
    outcome = validator.validate(good_csv)
    assert outcome.is_valid is True
    assert len(outcome.errors) == 0

    # Header mismatch
    bad_header_csv = tmp_path / "bad_header.csv"
    df_bad = pd.DataFrame({"id": [1, 2, 3], "prediction": [0.1, 0.8, 0.4]})
    df_bad.to_csv(bad_header_csv, index=False)
    outcome_bad = validator.validate(bad_header_csv)
    assert outcome_bad.is_valid is False
    assert any("Columns mismatch" in err for err in outcome_bad.errors)

    # NaN / Null values
    nan_csv = tmp_path / "nan.csv"
    df_nan = pd.DataFrame({"id": [1, 2, 3], "target": [0.1, float("nan"), 0.4]})
    df_nan.to_csv(nan_csv, index=False)
    outcome_nan = validator.validate(nan_csv)
    assert outcome_nan.is_valid is False
    assert any("NaN/null" in err for err in outcome_nan.errors)
