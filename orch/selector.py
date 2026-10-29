"""Selector module for keep / discard decisions with noise-aware statistical gates."""

from dataclasses import dataclass
from typing import Optional

from orch.logging_util import get_logger

logger = get_logger("orch.selector")


@dataclass
class Decision:
    action: str  # 'keep', 'discard', 'crash'
    reason: str
    delta: float
    is_improvement: bool


class ExperimentSelector:
    """Evaluates experiment outcomes against noise thresholds and optimization direction."""

    def __init__(
        self,
        direction: str = "maximize",
        use_cv_std: bool = True,
        min_epsilon: float = 0.0002,
    ):
        self.direction = direction
        self.use_cv_std = use_cv_std
        self.min_epsilon = min_epsilon

    def evaluate(
        self,
        new_score: Optional[float],
        best_score: float,
        best_std: float,
        run_status: str,
    ) -> Decision:
        """Determines whether to keep or discard a run."""
        if run_status != "DONE" or new_score is None:
            return Decision(
                action="discard",
                reason=f"Run did not finish successfully (status={run_status})",
                delta=0.0,
                is_improvement=False,
            )

        threshold = max(best_std if self.use_cv_std else 0.0, self.min_epsilon)

        if self.direction == "maximize":
            delta = new_score - best_score
            is_better = delta > 0
            beats_noise = delta > threshold
        else:
            delta = best_score - new_score
            is_better = delta > 0
            beats_noise = delta > threshold

        if beats_noise:
            return Decision(
                action="keep",
                reason=f"Improvement of {delta:+.6f} beats noise threshold ({threshold:.6f})",
                delta=delta,
                is_improvement=True,
            )
        elif is_better:
            return Decision(
                action="discard",
                reason=f"Improvement of {delta:+.6f} within CV noise margin ({threshold:.6f}); discarded for conservatism",
                delta=delta,
                is_improvement=False,
            )
        else:
            return Decision(
                action="discard",
                reason=f"Score degraded or matched (delta={delta:+.6f})",
                delta=delta,
                is_improvement=False,
            )
