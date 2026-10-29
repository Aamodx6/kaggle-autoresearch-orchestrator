"""Unit tests for SubmissionValidator."""

import tempfile
from pathlib import Path
import pandas as pd
import pytest

from orch.validator import SubmissionValidator


@pytest.fixture
def sample_and_candidate_paths():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        sample_path = tmp_path / "sample_submission.csv"
        cand_path = tmp_path / "candidate_submission.csv"

        df_sample = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "target": [0.5, 0.5, 0.5, 0.5, 0.5],
        })
        df_sample.to_csv(sample_path, index=False)

        yield sample_path, cand_path


def test_validator_success(sample_and_candidate_paths):
    sample_path, cand_path = sample_and_candidate_paths
    cand_df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "target": [0.12, 0.88, 0.45, 0.93, 0.05],
    })
    cand_df.to_csv(cand_path, index=False)

    validator = SubmissionValidator(sample_path)
    res = validator.validate(cand_path)

    assert res.is_valid
    assert res.row_count == 5
    assert res.column_count == 2
    assert len(res.errors) == 0


def test_validator_fails_row_count_and_columns(sample_and_candidate_paths):
    sample_path, cand_path = sample_and_candidate_paths
    cand_df = pd.DataFrame({
        "wrong_id": [1, 2, 3],
        "prediction": [0.1, 0.2, 0.3],
    })
    cand_df.to_csv(cand_path, index=False)

    validator = SubmissionValidator(sample_path)
    res = validator.validate(cand_path)

    assert not res.is_valid
    assert any("Row count mismatch" in e for e in res.errors)
    assert any("Columns mismatch" in e for e in res.errors)


def test_validator_fails_on_nan_values(sample_and_candidate_paths):
    sample_path, cand_path = sample_and_candidate_paths
    cand_df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "target": [0.1, None, 0.3, 0.4, 0.5],
    })
    cand_df.to_csv(cand_path, index=False)

    validator = SubmissionValidator(sample_path)
    res = validator.validate(cand_path)

    assert not res.is_valid
    assert any("NaN/null" in e for e in res.errors)
