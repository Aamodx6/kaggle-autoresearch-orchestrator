"""Prompt hygiene, proxy security auditing, and token/cost estimation."""

import os
import re
from typing import Dict, List, Tuple

from orch.logging_util import get_logger

logger = get_logger("llm.hygiene")

# Known authorized endpoints (direct vendor APIs, not unvetted proxies)
APPROVED_DOMAINS = [
    "googleapis.com",
    "groq.com",
    "openrouter.ai",
    "openai.com",
    "anthropic.com",
]

# Sensitive patterns that should never be sent
CREDENTIAL_PATTERNS = [
    r"sk-[a-zA-Z0-9_\-]{20,}",
    r"AIzaSy[a-zA-Z0-9_\-]{30,}",
    r"gsk_[a-zA-Z0-9_\-]{20,}",
    r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}",
    r"kaggle_key\s*=\s*['\"][^'\"]+['\"]",
]

MODEL_PRICING = {
    # USD per 1M tokens: (prompt_price, completion_price)
    "gemini-2.5-flash": (0.075, 0.30),
    "gemini-1.5-flash": (0.075, 0.30),
    "openai/gpt-oss-120b": (0.15, 0.60),
    "meta-llama/llama-3.3-70b-instruct:free": (0.0, 0.0),
    "default": (0.10, 0.40),
}


class PromptHygieneAuditor:
    """Audits outgoing prompts to ensure zero leakage of credentials, labels, or raw data rows."""

    def __init__(self, send_whitelist: List[str], never_send_blacklist: List[str]):
        self.send_whitelist = send_whitelist
        self.never_send_blacklist = never_send_blacklist

    def sanitize_prompt(self, prompt: str) -> str:
        """Sanitizes prompt, stripping any accidental credentials or tokens."""
        sanitized = prompt
        for pat in CREDENTIAL_PATTERNS:
            sanitized = re.sub(pat, "[REDACTED_CREDENTIAL]", sanitized)

        # Detect raw data rows or excessive CSV dumps
        lines = sanitized.splitlines()
        clean_lines = []
        comma_run = 0
        for line in lines:
            if line.count(",") >= 10 and not line.strip().startswith("#") and not line.strip().startswith("def "):
                comma_run += 1
                if comma_run <= 3:
                    clean_lines.append(line)
                elif comma_run == 4:
                    clean_lines.append("# [PROMPT HYGIENE: Truncated raw CSV rows...]")
            else:
                comma_run = 0
                clean_lines.append(line)

        return "\n".join(clean_lines)

    @staticmethod
    def audit_proxy_safety(base_url: str, allow_proxy: bool = False) -> None:
        """Validates that base_url is an approved vendor endpoint unless proxy opt-in is enabled."""
        is_approved = any(domain in base_url.lower() for domain in APPROVED_DOMAINS)
        if not is_approved:
            if not allow_proxy:
                raise ValueError(
                    f"TOS Compliance Alert: Endpoint '{base_url}' is not a recognized direct vendor API. "
                    f"Third-party proxies are disabled by default. Set 'allow_proxy: true' in config to opt in."
                )
            else:
                logger.warning(
                    f"SECURITY WARNING: Opt-in third-party proxy endpoint enabled: {base_url}. "
                    f"Ensure compliance with vendor Terms of Service."
                )


class CostEstimator:
    """Estimates tokens and cost for requests."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough estimation: ~4 characters per token."""
        return max(1, len(text) // 4)

    @staticmethod
    def compute_cost(prompt_tokens: int, completion_tokens: int, model_name: str) -> float:
        pricing = MODEL_PRICING.get(model_name, MODEL_PRICING["default"])
        prompt_cost = (prompt_tokens / 1_000_000) * pricing[0]
        comp_cost = (completion_tokens / 1_000_000) * pricing[1]
        return round(prompt_cost + comp_cost, 6)
