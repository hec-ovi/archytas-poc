"""The local tray: writes the message to a file instead of sending it.

Needs no account and no credentials, so the system can be run and demonstrated with
nothing configured. It is also where alerts land when the other channels are not set up.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

from .channel import Channel, Delivery
from .message import Message

DEFAULT_RECIPIENT = "bandeja"


class OutboxChannel(Channel):
    """Appends one JSON line per message and keeps the same entries in memory."""

    name = "outbox"

    def __init__(self, path: str | Path, recipients: Sequence[str] = (DEFAULT_RECIPIENT,)):
        super().__init__(recipients or (DEFAULT_RECIPIENT,))
        self._path = Path(path)
        self._entries: list[dict[str, Any]] = []

    @property
    def path(self) -> Path:
        return self._path

    @property
    def entries(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._entries)

    def send(self, recipient: str, message: Message) -> Delivery:
        entry = self._entry(recipient, message)
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            return Delivery.failure(self.name, recipient, f"no se pudo escribir la bandeja en {self._path}: {exc}")

        self._entries.append(entry)
        return Delivery.sent(self.name, recipient, entry["id"])

    def _entry(self, recipient: str, message: Message) -> dict[str, Any]:
        template = message.template
        return {
            "id": uuid4().hex,
            "at": datetime.now(timezone.utc).isoformat(),
            "channel": self.name,
            "recipient": recipient,
            "text": message.text,
            "template": (
                {"name": template.name, "language": template.language, "params": dict(template.params)}
                if template
                else None
            ),
        }
