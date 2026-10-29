"""Configuration loader and validator for Kaggle AutoResearch Orchestrator."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class BudgetsConfig:
    experiment_timeout_seconds: int = 300
    max_experiments_per_run: int = 5
    patience_experiments: int = 3
    memory_limit_mb: int = 4096


@dataclass
class PathsConfig:
    registry_db: str = "registry.db"
    workspaces_dir: str = "workspaces"
    research_dir: str = "research"
    evidence_dir: str = "evidence"
    reports_dir: str = "reports"


@dataclass
class CVConfig:
    n_splits: int = 5
    seed: int = 42


@dataclass
class NoiseGateConfig:
    use_cv_std: bool = True
    min_improvement_epsilon: float = 0.0002


@dataclass
class LLMBudgetConfig:
    max_experiments_per_day: int = 40
    stop_on_all_backends_exhausted: bool = True


@dataclass
class LLMOn429Config:
    action: str = "next_in_chain"
    cooldown_minutes: int = 60
    persist_state: bool = True


@dataclass
class LLMPromptHygieneConfig:
    send: List[str] = field(default_factory=lambda: [
        "train.py diff", "results.tsv rows", "metric values", "schema", "summary stats", "error logs"
    ])
    never_send: List[str] = field(default_factory=lambda: [
        "raw data rows", "labels", "credentials"
    ])


@dataclass
class LLMConfig:
    budget: LLMBudgetConfig = field(default_factory=LLMBudgetConfig)
    backends: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    roles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    on_429: LLMOn429Config = field(default_factory=LLMOn429Config)
    prompt_hygiene: LLMPromptHygieneConfig = field(default_factory=LLMPromptHygieneConfig)


@dataclass
class AppConfig:
    budgets: BudgetsConfig = field(default_factory=BudgetsConfig)
    daily_caps: Dict[str, int] = field(default_factory=lambda: {"default": 5})
    paths: PathsConfig = field(default_factory=PathsConfig)
    cv: CVConfig = field(default_factory=CVConfig)
    noise_gate: NoiseGateConfig = field(default_factory=NoiseGateConfig)
    modes: Dict[str, str] = field(default_factory=lambda: {"default": "dry-run"})
    llm: LLMConfig = field(default_factory=LLMConfig)

    def get_daily_cap(self, competition_slug: str) -> int:
        return self.daily_caps.get(competition_slug, self.daily_caps.get("default", 5))


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """Loads application configuration from YAML file or returns defaults."""
    path = Path(config_path)
    if not path.is_file():
        return AppConfig()

    with open(path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f) or {}

    budgets_data = raw_data.get("budgets", {})
    paths_data = raw_data.get("paths", {})
    cv_data = raw_data.get("cv", {})
    noise_data = raw_data.get("noise_gate", {})
    llm_data = raw_data.get("llm", {})

    llm_budget = LLMBudgetConfig(**llm_data.get("budget", {})) if "budget" in llm_data else LLMBudgetConfig()
    llm_on429 = LLMOn429Config(**llm_data.get("on_429", {})) if "on_429" in llm_data else LLMOn429Config()
    llm_hygiene = LLMPromptHygieneConfig(**llm_data.get("prompt_hygiene", {})) if "prompt_hygiene" in llm_data else LLMPromptHygieneConfig()

    llm_config = LLMConfig(
        budget=llm_budget,
        backends=llm_data.get("backends", {}),
        roles=llm_data.get("roles", {}),
        on_429=llm_on429,
        prompt_hygiene=llm_hygiene,
    )

    return AppConfig(
        budgets=BudgetsConfig(**budgets_data) if budgets_data else BudgetsConfig(),
        daily_caps=raw_data.get("daily_caps", {"default": 5}),
        paths=PathsConfig(**paths_data) if paths_data else PathsConfig(),
        cv=CVConfig(**cv_data) if cv_data else CVConfig(),
        noise_gate=NoiseGateConfig(**noise_data) if noise_data else NoiseGateConfig(),
        modes=raw_data.get("modes", {"default": "dry-run"}),
        llm=llm_config,
    )
