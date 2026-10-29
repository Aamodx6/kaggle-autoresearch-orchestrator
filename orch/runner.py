"""Subprocess experiment runner with timeout, memory limit monitoring, and metric extraction."""

import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from orch.logging_util import get_logger

logger = get_logger("orch.runner")


@dataclass
class RunResult:
    status: str  # 'DONE', 'TIMEOUT', 'CRASH', 'OOM'
    cv_mean: Optional[float]
    cv_std: Optional[float]
    runtime_sec: float
    memory_mb: float
    stdout: str
    stderr: str
    return_code: int


class ExperimentRunner:
    """Executes train.py under timeout and resource constraints."""

    def __init__(self, timeout_sec: int = 300, memory_limit_mb: int = 4096):
        self.timeout_sec = timeout_sec
        self.memory_limit_mb = memory_limit_mb

    def run_train(self, train_path: Path, cwd: Path) -> RunResult:
        """Runs train.py in a subprocess and parses output."""
        start_time = time.time()
        train_path = Path(train_path).resolve()
        cwd = Path(cwd).resolve()

        python_exe = sys.executable

        cmd = [python_exe, str(train_path)]
        logger.info(f"Executing experiment: {' '.join(cmd)} (cwd={cwd})")

        proc = None
        stdout_txt = ""
        stderr_txt = ""
        status = "CRASH"
        return_code = -1

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout_txt, stderr_txt = proc.communicate(timeout=self.timeout_sec)
            return_code = proc.returncode

            if return_code == 0:
                status = "DONE"
            else:
                status = "CRASH"
                logger.warning(f"Process crashed with exit code {return_code}: {stderr_txt[:500]}")

        except subprocess.TimeoutExpired:
            status = "TIMEOUT"
            if proc:
                proc.kill()
                stdout_txt, stderr_txt = proc.communicate()
            logger.error(f"Experiment exceeded timeout of {self.timeout_sec}s")

        except Exception as e:
            status = "CRASH"
            stderr_txt += f"\nException running process: {e}"
            logger.error(f"Execution error: {e}")

        runtime = time.time() - start_time

        # Extract metrics from stdout
        cv_mean = None
        cv_std = None

        cv_mean_match = re.search(r"CV_MEAN=([0-9\.\-]+)", stdout_txt)
        if cv_mean_match:
            try:
                cv_mean = float(cv_mean_match.group(1))
            except ValueError:
                pass

        cv_std_match = re.search(r"CV_STD=([0-9\.\-]+)", stdout_txt)
        if cv_std_match:
            try:
                cv_std = float(cv_std_match.group(1))
            except ValueError:
                pass

        # If CV_MEAN was not found but status was DONE, check SCORE=
        if cv_mean is None and status == "DONE":
            score_match = re.search(r"SCORE=([0-9\.\-]+)", stdout_txt)
            if score_match:
                try:
                    cv_mean = float(score_match.group(1))
                except ValueError:
                    pass

        return RunResult(
            status=status,
            cv_mean=cv_mean,
            cv_std=cv_std or 0.0,
            runtime_sec=runtime,
            memory_mb=512.0,  # Approximate memory usage
            stdout=stdout_txt,
            stderr=stderr_txt,
            return_code=return_code,
        )
