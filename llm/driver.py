"""LLM Driver Layer orchestrating role-based execution, backends, fallback chains, and sandboxes."""

import datetime
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from llm.backends.base import BaseBackend, TaskResult
from llm.backends.headless_cli import HeadlessCLIBackend
from llm.backends.mock import MockBackend
from llm.backends.openai_compat import OpenAICompatBackend
from llm.hygiene import PromptHygieneAuditor
from orch.config import AppConfig, load_config
from orch.logging_util import get_logger

logger = get_logger("llm.driver")


class LLMDriverError(Exception):
    """Base exception for LLM Driver errors."""
    pass


class BudgetExceededError(LLMDriverError):
    """Raised when daily experiment or monetary budget is exceeded."""
    pass


class AllBackendsExhaustedError(LLMDriverError):
    """Raised when all backends in a role's fallback chain fail or are on cooldown."""
    pass


class LLMDriver:
    """
    Main LLM Driver layer.
    Executes tasks for specific roles using configured backends, fallback chains,
    429 rate-limit cooldowns, budget accounting, and git worktree sandboxes.
    """

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        state_file: str = "llm_state.json",
    ):
        self.config = config or load_config()
        self.state_file = Path(state_file)
        self.llm_cfg = self.config.llm

        self.auditor = PromptHygieneAuditor(
            send_whitelist=self.llm_cfg.prompt_hygiene.send,
            never_send_blacklist=self.llm_cfg.prompt_hygiene.never_send,
        )

        self._backends: Dict[str, BaseBackend] = {}
        self._init_backends()
        self._load_state()

    def _init_backends(self) -> None:
        """Initializes backend instances from configuration."""
        backend_cfgs = self.llm_cfg.backends
        for b_name, b_info in backend_cfgs.items():
            b_type = b_info.get("type", "")
            if b_type == "headless_cli":
                self._backends[b_name] = HeadlessCLIBackend(b_name, b_info)
            elif b_type == "openai_compat":
                self._backends[b_name] = OpenAICompatBackend(b_name, b_info)
            elif b_type == "mock":
                self._backends[b_name] = MockBackend(b_name, b_info)
            else:
                logger.warning(f"Unknown backend type '{b_type}' for backend '{b_name}'")

    def _load_state(self) -> Dict[str, Any]:
        """Loads persistent 429 cooldown and daily budget state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
                    return self.state
            except Exception as e:
                logger.warning(f"Could not read state file {self.state_file}: {e}")
        self.state = {
            "daily_date": datetime.date.today().isoformat(),
            "experiments_today": 0,
            "cooldowns": {},  # backend_name -> iso_timestamp
            "total_tokens": 0,
            "total_cost": 0.0,
            "last_editor_backend": None,
        }
        self._save_state()
        return self.state

    def _save_state(self) -> None:
        """Saves current state to JSON file."""
        if not self.llm_cfg.on_429.persist_state:
            return
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist LLM state: {e}")

    def _check_and_reset_daily_budget(self) -> None:
        """Checks and resets the daily experiment counter at midnight."""
        today = datetime.date.today().isoformat()
        if self.state.get("daily_date") != today:
            self.state["daily_date"] = today
            self.state["experiments_today"] = 0
            self._save_state()

        max_daily = self.llm_cfg.budget.max_experiments_per_day
        if self.state.get("experiments_today", 0) >= max_daily:
            err_msg = f"Hard budget cap reached: {self.state['experiments_today']}/{max_daily} experiments today."
            logger.error(err_msg)
            raise BudgetExceededError(err_msg)

    def is_backend_on_cooldown(self, backend_name: str) -> bool:
        """Checks if a backend is currently on rate-limit cooldown."""
        cooldowns = self.state.get("cooldowns", {})
        until_iso = cooldowns.get(backend_name)
        if not until_iso:
            return False
        try:
            until_dt = datetime.datetime.fromisoformat(until_iso)
            now_dt = datetime.datetime.now(datetime.timezone.utc)
            if now_dt < until_dt:
                return True
            else:
                # Cooldown expired
                del self.state["cooldowns"][backend_name]
                self._save_state()
                return False
        except Exception:
            return False

    def mark_cooldown(self, backend_name: str, minutes: Optional[int] = None) -> None:
        """Puts a backend on cooldown following a 429 rate limit."""
        cooldown_mins = minutes or self.llm_cfg.on_429.cooldown_minutes
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        until_dt = now_dt + datetime.timedelta(minutes=cooldown_mins)
        if "cooldowns" not in self.state:
            self.state["cooldowns"] = {}
        self.state["cooldowns"][backend_name] = until_dt.isoformat()
        self._save_state()
        logger.warning(
            f"Backend '{backend_name}' placed on cooldown for {cooldown_mins}m until {until_dt.isoformat()}"
        )

    def get_role_chain(self, role: str) -> List[str]:
        """Resolves the ordered backend fallback chain for a role."""
        role_info = self.llm_cfg.roles.get(role, {})
        chain = list(role_info.get("chain", []))

        # Enforce reviewer constraint: must_differ_from editor
        must_differ = role_info.get("must_differ_from")
        if must_differ == "editor" and self.state.get("last_editor_backend"):
            editor_b = self.state["last_editor_backend"]
            chain = [b for b in chain if b != editor_b]
            logger.info(f"Filtered reviewer chain to exclude editor backend '{editor_b}': {chain}")

        return chain

    def run_task(
        self,
        role: str,
        prompt: str,
        workdir: Path,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes a task for the given role against the configured fallback chain.
        Returns: {diff, stdout, tokens, cost}
        """
        workdir = Path(workdir).resolve()
        task_timeout = timeout or self.config.budgets.experiment_timeout_seconds

        # Enforce daily budget cap
        self._check_and_reset_daily_budget()

        # Sanitize prompt against hygiene policies
        clean_prompt = self.auditor.sanitize_prompt(prompt)

        chain = self.get_role_chain(role)
        if not chain:
            # Fallback to mock backend if available
            if "mock_backend" in self._backends:
                chain = ["mock_backend"]
            else:
                raise AllBackendsExhaustedError(f"No configured backends available for role '{role}'")

        last_error = None

        for b_name in chain:
            # Check active cooldowns
            if self.is_backend_on_cooldown(b_name):
                logger.info(f"Skipping '{b_name}' for role '{role}' (active 429 cooldown)")
                continue

            backend = self._backends.get(b_name)
            if not backend:
                logger.warning(f"Backend '{b_name}' referenced in role '{role}' not found in backends.")
                continue

            logger.info(f"Attempting task for role '{role}' with backend '{b_name}'...")
            try:
                result = backend.execute(
                    role=role,
                    prompt=clean_prompt,
                    workdir=workdir,
                    timeout=task_timeout,
                )

                if result.status == "RATE_LIMITED":
                    self.mark_cooldown(b_name)
                    logger.warning(f"Backend '{b_name}' hit rate limit (429). Advancing to next in chain.")
                    continue

                if result.status == "SUCCESS":
                    # Record usage and progress
                    self.state["experiments_today"] = self.state.get("experiments_today", 0) + 1
                    self.state["total_tokens"] = self.state.get("total_tokens", 0) + result.tokens
                    self.state["total_cost"] = round(self.state.get("total_cost", 0.0) + result.cost, 6)

                    if role == "editor":
                        self.state["last_editor_backend"] = b_name

                    self._save_state()

                    logger.info(
                        f"Task for role '{role}' completed via '{b_name}' "
                        f"(tokens={result.tokens}, cost=${result.cost:.5f})"
                    )
                    return result.to_dict()

                # If status is CRASH / AUTH_ERROR, try next in chain
                logger.warning(f"Backend '{b_name}' returned status '{result.status}'. Trying next in chain.")
                last_error = result.stdout

            except Exception as e:
                logger.error(f"Error executing backend '{b_name}': {e}")
                last_error = str(e)

        # All backends in chain failed or are on cooldown
        logger.error(f"All backends in fallback chain exhausted for role '{role}'.")
        if self.llm_cfg.budget.stop_on_all_backends_exhausted:
            raise AllBackendsExhaustedError(
                f"Exhausted all backends in chain for role '{role}'. Last error: {last_error}"
            )

        # Return empty failure result
        return TaskResult(
            diff="",
            stdout=f"All backends exhausted for role '{role}'. Last error: {last_error}",
            tokens=0,
            cost=0.0,
            backend_used="none",
            role=role,
            status="ALL_EXHAUSTED",
        ).to_dict()
