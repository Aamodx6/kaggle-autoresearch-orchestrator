"""Unit tests for KaggleConnector with mocked API and retry backoff."""

from unittest.mock import MagicMock, patch
import pytest

from orch.connector import (
    KaggleConnector,
    KaggleConnectorError,
    RulesNotAcceptedError,
    ResourceNotFoundError,
    CompetitionMetadata,
)


def test_connector_list_entered_competitions_success():
    connector = KaggleConnector(max_retries=2, base_backoff_sec=0.01)

    mock_comp = MagicMock()
    mock_comp.id = 12345
    mock_comp.ref = "https://www.kaggle.com/competitions/test-comp"
    mock_comp.title = "Test Competition"
    mock_comp.url = "https://www.kaggle.com/competitions/test-comp"
    mock_comp.deadline = "2026-12-31T23:59:00"
    mock_comp.category = "Featured"
    mock_comp.reward = "50,000"
    mock_comp.evaluation_metric = "Roc Auc Score"
    mock_comp.is_kernels_submissions_only = False
    mock_comp.user_has_entered = True
    mock_comp.user_rank = 10
    mock_comp.max_daily_submissions = 5
    mock_comp.submissions_disabled = False
    mock_comp.license_name = "MIT"

    mock_api = MagicMock()
    mock_api.competitions_list.return_value = MagicMock(competitions=[mock_comp])

    with patch.object(connector, "get_api", return_value=mock_api):
        comps = connector.list_entered_competitions()

        assert len(comps) == 1
        c = comps[0]
        assert c.slug == "test-comp"
        assert c.title == "Test Competition"
        assert c.evaluation_metric == "Roc Auc Score"
        assert not c.is_kernels_submissions_only


def test_connector_retries_with_backoff_on_transient_failure():
    connector = KaggleConnector(max_retries=3, base_backoff_sec=0.01)

    mock_api = MagicMock()
    # Fails twice with transient network error, succeeds on 3rd attempt
    mock_api.competition_submissions.side_effect = [
        Exception("Connection timeout"),
        Exception("503 Service Unavailable"),
        [MagicMock(ref=1, file_name="sub.csv", date="", description="", status="COMPLETE", public_score=0.95, private_score=0.96)],
    ]

    with patch.object(connector, "get_api", return_value=mock_api):
        subs = connector.list_submissions("test-comp")
        assert len(subs) == 1
        assert subs[0].ref == 1
        assert mock_api.competition_submissions.call_count == 3


def test_connector_raises_rules_not_accepted():
    connector = KaggleConnector(max_retries=2, base_backoff_sec=0.01)
    mock_api = MagicMock()
    mock_api.competition_download_files.side_effect = Exception("403 - Forbidden: You must accept the competition rules")

    with patch.object(connector, "get_api", return_value=mock_api):
        with pytest.raises(RulesNotAcceptedError):
            connector.download_competition_data("test-comp", dest_dir="test_dir")


def test_connector_raises_resource_not_found():
    connector = KaggleConnector(max_retries=2, base_backoff_sec=0.01)
    mock_api = MagicMock()
    mock_api.competition_list_files.side_effect = Exception("404 - Not Found")

    with patch.object(connector, "get_api", return_value=mock_api):
        with pytest.raises(ResourceNotFoundError):
            connector.list_competition_files("non-existent-comp")
