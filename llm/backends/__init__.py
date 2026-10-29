"""LLM Backends Package."""

from llm.backends.base import BaseBackend, TaskResult
from llm.backends.mock import MockBackend
from llm.backends.headless_cli import HeadlessCLIBackend
from llm.backends.openai_compat import OpenAICompatBackend

__all__ = ["BaseBackend", "TaskResult", "MockBackend", "HeadlessCLIBackend", "OpenAICompatBackend"]
