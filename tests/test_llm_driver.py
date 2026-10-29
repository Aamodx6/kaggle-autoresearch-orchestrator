"""Unit tests for LLMDriver, roles, fallback chains, rate-limit cooldowns, and worktree sandboxes."""

import tempfile
from pathlib import Path
import pytest

from llm.driver import LLMDriver, BudgetExceededError, AllBackendsExhaustedError
from llm.sandbox import SandboxManager, SandboxViolationError
from orch.config import AppConfig, LLMConfig, LLMBudgetConfig, LLMOn429Config


@pytest.fixture
def test_driver_and_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir) / "repo"
        repo_dir.mkdir()
        state_file = repo_dir / "test_llm_state.json"

        # Initialize mock git repository
        import subprocess
        subprocess.run(["git", "init"], cwd=str(repo_dir), capture_output=True)
        subprocess.run(["git", "config", "user.name", "TestAgent"], cwd=str(repo_dir), capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@agent.ai"], cwd=str(repo_dir), capture_output=True)

        # Create prepare.py and train.py
        (repo_dir / "prepare.py").write_text("# Read-only prepare.py\ndef load(): pass\n", encoding="utf-8")
        (repo_dir / "train.py").write_text("# Mutable train.py\ndef train(): pass\n", encoding="utf-8")
        (repo_dir / "program.md").write_text("# Protocol\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=str(repo_dir), capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=str(repo_dir), capture_output=True)

        config = AppConfig(
            llm=LLMConfig(
                budget=LLMBudgetConfig(max_experiments_per_day=5),
                backends={
                    "mock_primary": {"type": "mock", "workdir_mode": "direct"},
                    "mock_backup": {"type": "mock", "workdir_mode": "direct"},
                    "mock_429": {"type": "mock", "simulate_429": True},
                },
                roles={
                    "editor": {"chain": ["mock_primary"]},
                    "proposer": {"chain": ["mock_primary"]},
                    "researcher": {"chain": ["mock_primary"]},
                    "reviewer": {"chain": ["mock_backup"], "must_differ_from": "editor"},
                    "failover_role": {"chain": ["mock_429", "mock_backup"]},
                },
                on_429=LLMOn429Config(action="next_in_chain", cooldown_minutes=30),
            )
        )

        driver = LLMDriver(config=config, state_file=str(state_file))
        yield driver, repo_dir


def test_mock_backend_run_task_all_roles(test_driver_and_repo):
    driver, repo_dir = test_driver_and_repo

    # 1. Proposer Role
    res_prop = driver.run_task(
        role="proposer",
        prompt="Propose interaction features for heart disease classification",
        workdir=repo_dir,
    )
    assert res_prop["status"] == "SUCCESS"
    assert "Mock LLM Output for proposer" in res_prop["stdout"]
    assert res_prop["tokens"] > 0
    assert res_prop["cost"] > 0.0

    # 2. Editor Role
    res_edit = driver.run_task(
        role="editor",
        prompt="Add ratio_st_hr to train.py",
        workdir=repo_dir,
    )
    assert res_edit["status"] == "SUCCESS"
    assert len(res_edit["diff"]) > 0
    assert "ratio_st_hr" in res_edit["diff"]

    # 3. Reviewer Role
    res_rev = driver.run_task(
        role="reviewer",
        prompt="Check code diff for test target leakage",
        workdir=repo_dir,
    )
    assert res_rev["status"] == "SUCCESS"
    assert res_rev["backend_used"] == "mock_backup"  # Verified must_differ_from editor!

    # 4. Researcher Role
    res_res = driver.run_task(
        role="researcher",
        prompt="Summarize public notebook findings",
        workdir=repo_dir,
    )
    assert res_res["status"] == "SUCCESS"


def test_rate_limit_429_failover_and_cooldown(test_driver_and_repo):
    driver, repo_dir = test_driver_and_repo

    # Role configured with chain: [mock_429, mock_backup]
    # mock_429 returns RATE_LIMITED -> driver marks cooldown and fails over to mock_backup
    res = driver.run_task(
        role="failover_role",
        prompt="Run failover experiment",
        workdir=repo_dir,
    )

    assert res["status"] == "SUCCESS"
    assert res["backend_used"] == "mock_backup"
    assert driver.is_backend_on_cooldown("mock_429")


def test_budget_exceeded_enforcement(test_driver_and_repo):
    driver, repo_dir = test_driver_and_repo
    # Max experiments per day is 5 in test config
    driver.state["experiments_today"] = 5
    driver._save_state()

    with pytest.raises(BudgetExceededError):
        driver.run_task(role="proposer", prompt="Should fail due to daily budget", workdir=repo_dir)


def test_sandbox_security_blocks_prepare_py_modification():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir)
        import subprocess
        subprocess.run(["git", "init"], cwd=str(repo_dir), capture_output=True)
        subprocess.run(["git", "config", "user.name", "TestAgent"], cwd=str(repo_dir), capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@agent.ai"], cwd=str(repo_dir), capture_output=True)

        (repo_dir / "prepare.py").write_text("# Read-only\n", encoding="utf-8")
        (repo_dir / "train.py").write_text("# Mutable\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=str(repo_dir), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo_dir), capture_output=True)

        mgr = SandboxManager(repo_dir)

        # Illegal modification to prepare.py
        (repo_dir / "prepare.py").write_text("# Illegal override attempt\n", encoding="utf-8")

        with pytest.raises(SandboxViolationError):
            mgr.audit_and_extract_diff(repo_dir)
