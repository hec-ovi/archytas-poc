"""The record of what the agent actually did.

An answer nobody can check is an answer nobody should trust. Every tool that ran is kept
with the arguments it ran with and what it returned, so a person reads the answer and the
steps that produced it side by side.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolStep:
    """One tool call: what ran, with what, and what came back."""

    tool: str
    arguments: dict[str, Any]
    result: Any

    @property
    def failed(self) -> bool:
        return isinstance(self.result, dict) and "error" in self.result

    def as_dict(self) -> dict[str, Any]:
        return {"herramienta": self.tool, "argumentos": self.arguments, "resultado": self.result}


@dataclass(frozen=True)
class Answer:
    """What the agent replies, and the trace behind it."""

    text: str
    steps: tuple[ToolStep, ...] = field(default_factory=tuple)
    turns: int = 0
    complete: bool = True

    @property
    def tools_used(self) -> tuple[str, ...]:
        return tuple(step.tool for step in self.steps)

    def as_dict(self) -> dict[str, Any]:
        return {
            "respuesta": self.text,
            "pasos": [step.as_dict() for step in self.steps],
            "vueltas": self.turns,
            "completo": self.complete,
        }
