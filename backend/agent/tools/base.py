"""What every tool is.

A tool is a class with a name, the arguments it takes, and a `run`. Its description and the
description of each argument are not here: they live in `prompts/herramientas/<nombre>.md`,
because that text is a prompt and prompts belong in files a person can edit.

The shape of the arguments is code, since it is structure and not wording: names, JSON types
and which ones are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from store import Store

from ..library import PromptLibrary


@dataclass(frozen=True)
class Parameter:
    """One argument of a tool, in JSON-schema terms."""

    name: str
    type: str = "string"
    required: bool = False
    enum: tuple[str, ...] = field(default_factory=tuple)


class Tool:
    """The contract every tool answers to."""

    name: str = ""
    parameters: tuple[Parameter, ...] = ()
    # a tool that writes gets the name of whoever asked, injected by the registry and never
    # exposed to the model, so nobody can be impersonated from a chat message
    needs_user: bool = False

    def __init__(self, store: Store, prompts: PromptLibrary):
        self._store = store
        self._text = prompts.tool(self.name)

    @property
    def schema(self) -> dict[str, Any]:
        """The tool as the chat API describes it."""
        properties = {}
        for parameter in self.parameters:
            entry: dict[str, Any] = {"type": parameter.type, "description": self._text.param(parameter.name)}
            if parameter.enum:
                entry["enum"] = list(parameter.enum)
            properties[parameter.name] = entry

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self._text.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": [p.name for p in self.parameters if p.required],
                },
            },
        }

    @property
    def argument_names(self) -> tuple[str, ...]:
        return tuple(p.name for p in self.parameters)

    def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError
