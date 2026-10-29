"""Base types and abstract backend interface for LLM Driver."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class TaskResult:
    """Standardized result returned by LLMDriver.run_task."""
    diff: str
    stdout: str
    tokens: int
    cost: float
    backend_used: str = ""
    role: str = ""
    status: str = "SUCCESS"  # SUCCESS, RATE_LIMITED, TIMEOUT, CRASH, BUDGET_EXCEEDED
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diff": self.diff,
            "stdout": self.stdout,
            "tokens": self.tokens,
            "cost": self.cost,
            "backend_used": self.backend_used,
            "role": self.role,
            "status": self.status,
            "metadata": self.metadata,
        }

    # Dict-like access for backwards compatibility
    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)


class BaseBackend(ABC):
    """Abstract base class for LLM backends."""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    @abstractmethod
    def execute(self, role: str, prompt: str, workdir: Path, timeout: int) -> TaskResult:
        """Executes a task for a given role and returns TaskResult."""
        pass
