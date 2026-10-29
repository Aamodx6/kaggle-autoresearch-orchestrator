"""OpenAI-compatible REST API backend for summarization, ranking, and reviewer roles."""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict

from llm.backends.base import BaseBackend, TaskResult
from llm.hygiene import CostEstimator, PromptHygieneAuditor
from orch.logging_util import get_logger

logger = get_logger("llm.openai_compat")


class OpenAICompatBackend(BaseBackend):
    """Executes calls to OpenAI-compatible endpoints with proxy safety, 429 backoff, and usage tracking."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.base_url = config.get("base_url", "").rstrip("/")
        self.api_key_env = config.get("api_key_env", "")
        self.model = config.get("model", "")
        self.allow_proxy = config.get("allow_proxy", False)

        # Audit proxy safety at initialization
        if self.base_url:
            PromptHygieneAuditor.audit_proxy_safety(self.base_url, self.allow_proxy)

    def execute(self, role: str, prompt: str, workdir: Path, timeout: int) -> TaskResult:
        logger.info(f"[{self.name}] Calling OpenAI-compatible endpoint ({self.model}) for role '{role}'")

        api_key = os.environ.get(self.api_key_env, "").strip() if self.api_key_env else ""
        if not api_key:
            logger.warning(f"[{self.name}] API key environment variable '{self.api_key_env}' not set. Failing over.")
            return TaskResult(
                diff="",
                stdout=f"Missing API key: {self.api_key_env}",
                tokens=0,
                cost=0.0,
                backend_used=self.name,
                role=role,
                status="AUTH_ERROR",
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"You are an expert competitive ML agent acting as {role}."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))

            content = resp_data["choices"][0]["message"]["content"]
            usage = resp_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", len(prompt) // 4)
            completion_tokens = usage.get("completion_tokens", len(content) // 4)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

            cost = CostEstimator.compute_cost(prompt_tokens, completion_tokens, self.model)

            return TaskResult(
                diff="",
                stdout=content,
                tokens=total_tokens,
                cost=cost,
                backend_used=self.name,
                role=role,
                status="SUCCESS",
            )

        except urllib.error.HTTPError as http_err:
            code = http_err.code
            err_body = http_err.read().decode("utf-8", errors="ignore")
            logger.warning(f"[{self.name}] HTTP {code}: {err_body[:300]}")

            if code == 429:
                return TaskResult(
                    diff="",
                    stdout=f"HTTP 429 Too Many Requests: {err_body[:200]}",
                    tokens=0,
                    cost=0.0,
                    backend_used=self.name,
                    role=role,
                    status="RATE_LIMITED",
                )
            return TaskResult(
                diff="",
                stdout=f"HTTP Error {code}: {err_body[:200]}",
                tokens=0,
                cost=0.0,
                backend_used=self.name,
                role=role,
                status="CRASH",
            )

        except Exception as e:
            logger.error(f"[{self.name}] Network / request error: {e}")
            return TaskResult(
                diff="",
                stdout=f"Request error: {e}",
                tokens=0,
                cost=0.0,
                backend_used=self.name,
                role=role,
                status="CRASH",
            )
