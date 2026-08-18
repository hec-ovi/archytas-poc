"""What to say. The caller decides the wording; this box only carries it."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class Template:
    """A WhatsApp message template already approved by Meta.

    Named parameters ({{due_date}}) are the maintainable form and Meta supports them
    alongside the older positional ones.
    """

    name: str
    language: str = "es_AR"
    params: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Message:
    """One alert, ready to send.

    `text` is the plain wording every channel can deliver. `template` is only used by
    WhatsApp, which needs one to reach a recipient whose 24h window is closed. Both
    travel together so the same alert lands on any configured channel.
    """

    text: str
    template: Template | None = None
