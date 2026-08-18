"""Where the model lives and how to talk to it.

Everything comes from the environment so the same code runs against llama.cpp on this
machine, against the container host, or against OpenRouter, without a line changing.

There is no output length setting on purpose: capping the answer is how a report ends up cut
in half. What the model writes is steered by the prompt, never by a limit.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

DEFAULT_BASE_URL = "http://host.docker.internal:8080/v1"
DEFAULT_MODEL = "gemma-4-26b-a4b-qat-q4"


@dataclass(frozen=True)
class AgentSettings:
    """How to reach the model, and how many rounds of tools one question may take."""

    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    api_key: str = ""
    temperature: float = 0.2
    timeout: float = 120.0
    max_turns: int = 8

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "AgentSettings":
        source = env if env is not None else os.environ
        return cls(
            base_url=source.get("LLM_BASE_URL") or DEFAULT_BASE_URL,
            model=source.get("LLM_MODEL") or DEFAULT_MODEL,
            api_key=source.get("LLM_API_KEY", ""),
            temperature=float(source.get("LLM_TEMPERATURE", "0.2")),
            timeout=float(source.get("LLM_TIMEOUT", "120")),
            max_turns=int(source.get("AGENT_MAX_TURNS", "8")),
        )

    @property
    def completions_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/chat/completions"

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
