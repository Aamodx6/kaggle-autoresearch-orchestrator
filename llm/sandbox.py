"""Git worktree sandbox manager and strict file write permission enforcer."""

import difflib
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple

from orch.logging_util import get_logger

logger = get_logger("llm.sandbox")

ALLOWED_MUTABLE_FILES = {"train.py", "program.md"}
PROTECTED_READONLY_FILES = {"prepare.py"}


class SandboxViolationError(Exception):
    """Raised when an agent attempts to modify a protected or unauthorized file."""
    pass


class SandboxManager:
    """Manages isolated git worktree sandboxes with strict file permission enforcement."""

    def __init__(self, base_repo_dir: Path):
        self.base_repo_dir = Path(base_repo_dir).resolve()

    def create_worktree(self, worktree_name: str) -> Path:
        """Creates a temporary git worktree off HEAD."""
        worktree_path = self.base_repo_dir / ".worktrees" / worktree_name
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        if worktree_path.exists():
            self.remove_worktree(worktree_path)

        cmd = ["git", "worktree", "add", "--detach", str(worktree_path), "HEAD"]
        res = subprocess.run(cmd, cwd=str(self.base_repo_dir), capture_output=True, text=True)
        if res.returncode != 0:
            logger.warning(f"Could not create git worktree via detached HEAD: {res.stderr}. Fallback to directory copy.")
            shutil.copytree(self.base_repo_dir, worktree_path, ignore=shutil.ignore_patterns(".git", ".venv", "data"))

        logger.info(f"Sandbox worktree created at {worktree_path}")
        return worktree_path

    def remove_worktree(self, worktree_path: Path) -> None:
        """Safely cleans up and detaches git worktree."""
        worktree_path = Path(worktree_path)
        if not worktree_path.exists():
            return

        cmd = ["git", "worktree", "remove", "--force", str(worktree_path)]
        subprocess.run(cmd, cwd=str(self.base_repo_dir), capture_output=True, text=True)

        if worktree_path.exists():
            try:
                shutil.rmtree(worktree_path, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Error removing worktree directory: {e}")

        logger.info(f"Sandbox worktree cleaned up: {worktree_path.name}")

    def audit_and_extract_diff(self, sandbox_dir: Path, target_dir: Optional[Path] = None) -> Tuple[str, List[str]]:
        """
        Audits modified files in sandbox.
        Enforces rule: ONLY train.py and program.md can be modified.
        If prepare.py or any unauthorized file was modified, raises SandboxViolationError.
        Returns: (git_diff, modified_files_list)
        """
        sandbox_dir = Path(sandbox_dir).resolve()
        target_dir = Path(target_dir).resolve() if target_dir else None

        modified_files = []
        diff_lines = []

        # 1. Direct file audit against target_dir
        if target_dir:
            for item in sandbox_dir.iterdir():
                if item.is_file():
                    fn = item.name
                    target_file = target_dir / fn
                    if target_file.exists():
                        orig_text = target_file.read_text(encoding="utf-8", errors="ignore")
                        sand_text = item.read_text(encoding="utf-8", errors="ignore")
                        if orig_text != sand_text:
                            modified_files.append(fn)
                            if fn in PROTECTED_READONLY_FILES:
                                raise SandboxViolationError(f"PROTECTED READ-ONLY FILE MODIFIED: {fn}")
                            if fn not in ALLOWED_MUTABLE_FILES:
                                raise SandboxViolationError(f"UNAUTHORIZED FILE MODIFIED: {fn}")

                            # Generate unified diff
                            udiff = list(difflib.unified_diff(
                                orig_text.splitlines(keepends=True),
                                sand_text.splitlines(keepends=True),
                                fromfile=f"a/{fn}",
                                tofile=f"b/{fn}",
                            ))
                            diff_lines.extend(udiff)

            # Apply validated files back to target_dir
            for fn in modified_files:
                if fn in ALLOWED_MUTABLE_FILES:
                    shutil.copy2(sandbox_dir / fn, target_dir / fn)
                    logger.info(f"Applied validated edit to {target_dir / fn}")

            return "".join(diff_lines), modified_files

        # 2. Git status fallback when no target_dir
        cmd = ["git", "status", "--porcelain"]
        res = subprocess.run(cmd, cwd=str(sandbox_dir), capture_output=True, text=True)
        output = res.stdout.strip()

        if output:
            for line in output.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    file_name = Path(parts[-1]).name
                    modified_files.append(file_name)

        violations = []
        for fn in modified_files:
            if fn in PROTECTED_READONLY_FILES:
                violations.append(f"PROTECTED READ-ONLY FILE MODIFIED: {fn}")
            elif fn not in ALLOWED_MUTABLE_FILES and not fn.endswith(".pyc"):
                violations.append(f"UNAUTHORIZED FILE MODIFIED: {fn}")

        if violations:
            violation_msg = "; ".join(violations)
            logger.error(f"Sandbox security check failed: {violation_msg}")
            raise SandboxViolationError(f"Sandbox boundary violated: {violation_msg}")

        diff_cmd = ["git", "diff", "HEAD", "--", "train.py", "program.md"]
        diff_res = subprocess.run(diff_cmd, cwd=str(sandbox_dir), capture_output=True, text=True)
        return diff_res.stdout, modified_files
