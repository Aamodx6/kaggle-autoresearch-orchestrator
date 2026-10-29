"""Mock Backend for deterministic tests and offline verification."""

from pathlib import Path
from typing import Any, Dict

from llm.backends.base import BaseBackend, TaskResult
from orch.logging_util import get_logger

logger = get_logger("llm.mock")

DEFAULT_CANNED_DIFF = """--- a/train.py
+++ b/train.py
@@ -25,2 +25,4 @@
+    # Mock hypothesis: domain ratios
+    df_train['ratio_st_hr'] = df_train['ST depression'] / (df_train['Max HR'] + 1e-5)
+    df_test['ratio_st_hr'] = df_test['ST depression'] / (df_test['Max HR'] + 1e-5)
"""


class MockBackend(BaseBackend):
    """Deterministic mock backend simulating LLM outputs for testing."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.simulate_429 = config.get("simulate_429", False)
        self.simulate_timeout = config.get("simulate_timeout", False)
        self.simulate_crash = config.get("simulate_crash", False)
        self.canned_diff = config.get("canned_diff", DEFAULT_CANNED_DIFF)

    def execute(self, role: str, prompt: str, workdir: Path, timeout: int) -> TaskResult:
        logger.info(f"[MockBackend:{self.name}] Executing role '{role}' in {workdir}")

        if self.simulate_429:
            logger.warning(f"[MockBackend:{self.name}] Simulating HTTP 429 Too Many Requests")
            return TaskResult(
                diff="",
                stdout="429 Rate Limit Exceeded",
                tokens=0,
                cost=0.0,
                backend_used=self.name,
                role=role,
                status="RATE_LIMITED",
            )

        if self.simulate_timeout:
            logger.warning(f"[MockBackend:{self.name}] Simulating execution timeout")
            return TaskResult(
                diff="",
                stdout="Execution timed out",
                tokens=0,
                cost=0.0,
                backend_used=self.name,
                role=role,
                status="TIMEOUT",
            )

        if self.simulate_crash:
            logger.warning(f"[MockBackend:{self.name}] Simulating process crash")
            return TaskResult(
                diff="",
                stdout="Process exited with error code 1",
                tokens=0,
                cost=0.0,
                backend_used=self.name,
                role=role,
                status="CRASH",
            )

        stdout_msg = f"[Mock LLM Output for {role}]: Successfully proposed and evaluated."
        diff_out = ""

        # If editor role, apply canned diff to train.py if present
        if role == "editor":
            train_path = workdir / "train.py"
            if train_path.exists():
                old_code = train_path.read_text(encoding="utf-8")
                # Append mock feature edit
                if "ratio_st_hr" not in old_code:
                    new_code = old_code.replace(
                        "feature_cols = [c for c in df_train.columns if c not in [TARGET_COL, ID_COL]]",
                        "df_train['ratio_st_hr'] = df_train['ST depression'] / (df_train['Max HR'] + 1e-5)\n    "
                        "df_test['ratio_st_hr'] = df_test['ST depression'] / (df_test['Max HR'] + 1e-5)\n    "
                        "feature_cols = [c for c in df_train.columns if c not in [TARGET_COL, ID_COL]]",
                        1,
                    )
                    train_path.write_text(new_code, encoding="utf-8")
            diff_out = self.canned_diff

        return TaskResult(
            diff=diff_out,
            stdout=stdout_msg,
            tokens=350,
            cost=0.00005,
            backend_used=self.name,
            role=role,
            status="SUCCESS",
        )
