"""The entry point: hand it a message, it comes back with one result per recipient."""

from __future__ import annotations

from typing import Mapping, Sequence

import httpx

from .channel import Channel, Delivery
from .config import NotifyConfig
from .factory import ChannelFactory
from .message import Message


class Notifier:
    """Sends one message through every configured channel.

    A delivery that fails is a result, not an exception: the caller records it and
    retries later instead of losing the alert to a traceback.
    """

    def __init__(self, channels: Sequence[Channel]):
        self._channels = tuple(channels)

    @classmethod
    def from_config(cls, config: NotifyConfig, client: httpx.Client | None = None) -> "Notifier":
        return cls(ChannelFactory(config, client).build())

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Notifier":
        return cls.from_config(NotifyConfig.from_env(env))

    @property
    def channels(self) -> tuple[str, ...]:
        return tuple(channel.name for channel in self._channels)

    def send(self, message: Message, recipients: Sequence[str] | None = None) -> list[Delivery]:
        """One Delivery per channel and recipient. Recipients default to each channel's own."""
        results: list[Delivery] = []
        for channel in self._channels:
            targets = channel.recipients if recipients is None else tuple(recipients)
            results.extend(self._deliver(channel, target, message) for target in targets)
        return results

    def close(self) -> None:
        for channel in self._channels:
            channel.close()

    def _deliver(self, channel: Channel, recipient: str, message: Message) -> Delivery:
        try:
            return channel.send(recipient, message)
        except Exception as exc:  # an adapter bug must not take the alert down with it
            return Delivery.failure(channel.name, recipient, f"el canal {channel.name} fallo inesperadamente: {exc}")
