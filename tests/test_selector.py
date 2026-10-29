"""Unit tests for ExperimentSelector and noise gates."""

import pytest
from orch.selector import ExperimentSelector


def test_selector_keeps_improvement_beating_noise():
    selector = ExperimentSelector(direction="maximize", use_cv_std=True, min_epsilon=0.0002)

    decision = selector.evaluate(
        new_score=0.95550,
        best_score=0.95400,
        best_std=0.00080,
        run_status="DONE",
    )

    assert decision.action == "keep"
    assert decision.is_improvement
    assert decision.delta == pytest.approx(0.00150)


def test_selector_discards_improvement_within_noise_floor():
    selector = ExperimentSelector(direction="maximize", use_cv_std=True, min_epsilon=0.0002)

    # Delta is +0.00030, but noise std is 0.00080
    decision = selector.evaluate(
        new_score=0.95430,
        best_score=0.95400,
        best_std=0.00080,
        run_status="DONE",
    )

    assert decision.action == "discard"
    assert not decision.is_improvement
    assert "within CV noise margin" in decision.reason


def test_selector_discards_degradation_and_crashes():
    selector = ExperimentSelector(direction="maximize", use_cv_std=True, min_epsilon=0.0002)

    decision_degraded = selector.evaluate(
        new_score=0.95300,
        best_score=0.95400,
        best_std=0.00080,
        run_status="DONE",
    )
    assert decision_degraded.action == "discard"

    decision_crash = selector.evaluate(
        new_score=None,
        best_score=0.95400,
        best_std=0.00080,
        run_status="CRASH",
    )
    assert decision_crash.action == "discard"
