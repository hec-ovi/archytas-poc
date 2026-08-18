"""The interface every adapter implements, and the result it returns."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence

from .message import Message


@dataclass(frozen=True)
class Delivery:
    """The outcome of one message to one recipient. Adapters return it, never raise it."""

    channel: str
    recipient: str
    delivered: bool
    message_id: str | None = None
    reason: str | None = None

    @classmethod
    def sent(cls, channel: str, recipient: str, message_id: str) -> "Delivery":
        return cls(channel=channel, recipient=recipient, delivered=True, message_id=message_id)

    @classmethod
    def failure(cls, channel: str, recipient: str, reason: str) -> "Delivery":
        return cls(channel=channel, recipient=recipient, delivered=False, reason=reason)

    def as_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "recipient": self.recipient,
            "delivered": self.delivered,
            "message_id": self.message_id,
            "reason": self.reason,
        }


class Channel(ABC):
    """One outbound channel with its own default audience."""

    name = "channel"

    def __init__(self, recipients: Sequence[str] = ()):
        self._recipients = tuple(recipients)

    @property
    def recipients(self) -> tuple[str, ...]:
        return self._recipients

    @abstractmethod
    def send(self, recipient: str, message: Message) -> Delivery:
        """Deliver one message to one recipient and report what happened."""

    def close(self) -> None:
        """Release whatever the adapter holds open. No-op unless overridden."""
