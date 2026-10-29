"""Headless CLI backend for invoking command-line agents (claude, gemini, freebuff)."""

import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

from llm.backends.base import BaseBackend, TaskResult
from llm.hygiene import CostEstimator
from llm.sandbox import SandboxManager, SandboxViolationError
from orch.logging_util import get_logger

logger = get_logger("llm.headless_cli")


class HeadlessCLIBackend(BaseBackend):
    """Executes a headless CLI coding assistant in a workdir/worktree sandbox and captures git diff."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.cmd_template = config.get("cmd", "")
        self.workdir_mode = config.get("workdir_mode", "direct")

    def execute(self, role: str, prompt: str, workdir: Path, timeout: int) -> TaskResult:
        workdir = Path(workdir).resolve()
        logger.info(f"[{self.name}] Executing role '{role}' in {workdir} (mode={self.workdir_mode})")

        repo_root = Path(__file__).resolve().parent.parent.parent
        sandbox_mgr = SandboxManager(repo_root)
        exec_dir = workdir
        worktree_active = False
        worktree_name = f"sandbox_{role}_{int(time.time())}"
        worktree_root = None

        # Determine relative path from repo_root to workdir
        try:
            rel_subpath = workdir.relative_to(repo_root)
        except ValueError:
            rel_subpath = Path("")

        # If worktree mode is requested for editor
        if self.workdir_mode == "worktree" and role == "editor":
            try:
                worktree_root = sandbox_mgr.create_worktree(worktree_name)
                exec_dir = worktree_root / rel_subpath
                if not exec_dir.exists():
                    import shutil
                    shutil.copytree(
                        workdir,
                        exec_dir,
                        ignore=shutil.ignore_patterns("data", ".venv", "*.zip", "__pycache__"),
                    )
                worktree_active = True
            except Exception as we:
                logger.warning(f"Could not initialize worktree: {we}. Running directly in {workdir}")
                exec_dir = workdir



        # Build command list
        cmd_tokens = shlex.split(self.cmd_template, posix=False)
        if not cmd_tokens:
            return TaskResult(
                diff="",
                stdout=f"No command specified for backend {self.name}",
                tokens=0,
                cost=0.0,
                backend_used=self.name,
                role=role,
                status="CRASH",
            )

        # Append prompt to arguments if tool uses flags like -p
        full_cmd = list(cmd_tokens)
        if "-p" in full_cmd or "--prompt" in full_cmd:
            full_cmd.append(prompt)
        elif len(full_cmd) == 1:
            full_cmd.extend(["-p", prompt])

        # Resolve command path across OS (e.g. .cmd/.bat on Windows)
        import shutil
        import sys
        if full_cmd[0] in ("python", "python3"):
            full_cmd[0] = sys.executable
        else:
            resolved_bin = shutil.which(full_cmd[0]) or full_cmd[0]
            full_cmd[0] = resolved_bin


        logger.info(f"[{self.name}] Spawning process: {' '.join(full_cmd[:3])}... in {exec_dir}")


        stdout_txt = ""
        stderr_txt = ""
        status = "CRASH"

        try:
            # Prepare process environment
            proc_env = dict(os.environ)
            repo_root = str(Path(__file__).resolve().parent.parent.parent)
            if "PYTHONPATH" in proc_env:
                proc_env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{proc_env['PYTHONPATH']}"
            else:
                proc_env["PYTHONPATH"] = repo_root


            # Run CLI subprocess
            proc = subprocess.Popen(
                full_cmd,
                cwd=str(exec_dir),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=proc_env,
            )


            # Pass prompt on stdin as well if the tool reads stdin
            stdout_txt, stderr_txt = proc.communicate(input=prompt, timeout=timeout)
            ret_code = proc.returncode

            if ret_code == 0:
                status = "SUCCESS"
            else:
                out_lower = (stdout_txt + stderr_txt).lower()
                if "429" in out_lower or "rate limit" in out_lower or "quota" in out_lower:
                    status = "RATE_LIMITED"
                    logger.warning(f"[{self.name}] Detected rate limit / quota exhaustion: {stderr_txt[:200]}")
                else:
                    status = "CRASH"
                    logger.warning(f"[{self.name}] Process exited with code {ret_code}: {stderr_txt[:300]}")

        except subprocess.TimeoutExpired:
            status = "TIMEOUT"
            if proc:
                proc.kill()
                stdout_txt, stderr_txt = proc.communicate()
            logger.error(f"[{self.name}] Headless CLI execution timed out after {timeout}s")

        except FileNotFoundError as fnf:
            status = "CRASH"
            stderr_txt = f"Binary not found: {full_cmd[0]} ({fnf})"
            logger.warning(f"[{self.name}] {stderr_txt}")

        except Exception as e:
            status = "CRASH"
            stderr_txt = f"Subprocess exception: {e}"
            logger.error(f"[{self.name}] {stderr_txt}")

        # Capture and audit git diff
        diff_text = ""
        try:
            if worktree_active and worktree_root:
                diff_text, modified = sandbox_mgr.audit_and_extract_diff(exec_dir, target_dir=workdir)
                sandbox_mgr.remove_worktree(worktree_root)
            else:
                diff_cmd = ["git", "diff", "--", "train.py", "program.md"]
                diff_res = subprocess.run(diff_cmd, cwd=str(workdir), capture_output=True, text=True)
                diff_text = diff_res.stdout
        except SandboxViolationError as sve:
            logger.error(f"Sandbox security breach rejected: {sve}")
            if worktree_active and worktree_root:
                sandbox_mgr.remove_worktree(worktree_root)
            return TaskResult(
                diff="",
                stdout=f"Sandbox Violation: {sve}",
                tokens=0,
                cost=0.0,
                backend_used=self.name,
                role=role,
                status="CRASH",
                metadata={"violation": str(sve)},
            )


        # Estimate tokens and cost
        est_tokens = CostEstimator.estimate_tokens(prompt + stdout_txt)
        est_cost = CostEstimator.compute_cost(est_tokens, len(stdout_txt) // 4, "default")

        return TaskResult(
            diff=diff_text,
            stdout=stdout_txt or stderr_txt,
            tokens=est_tokens,
            cost=est_cost,
            backend_used=self.name,
            role=role,
            status=status,
            metadata={"command": " ".join(full_cmd[:2])},
        )
