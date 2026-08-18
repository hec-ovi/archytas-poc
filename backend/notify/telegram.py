"""Telegram through the Bot API.

No templates, no approval, no 24h window: whoever pressed /start on the bot can be
messaged at any time. That is why it is the channel that works while the WhatsApp
credentials are still being arranged.
"""

from __future__ import annotations

from typing import Sequence

import httpx

from .channel import Channel, Delivery
from .message import Message

API_HOST = "https://api.telegram.org"


class TelegramChannel(Channel):
    """Sends alerts through a Telegram bot. Recipients are chat ids."""

    name = "telegram"

    def __init__(
        self,
        token: str,
        recipients: Sequence[str] = (),
        client: httpx.Client | None = None,
        timeout: float = 15.0,
    ):
        super().__init__(recipients)
        self._url = f"{API_HOST}/bot{token}/sendMessage"
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def send(self, recipient: str, message: Message) -> Delivery:
        try:
            response = self._client.post(self._url, json={"chat_id": recipient, "text": message.text})
        except httpx.HTTPError as exc:
            return Delivery.failure(self.name, recipient, f"no se pudo contactar la API de Telegram: {exc}")

        if response.status_code != 200:
            # Telegram's error body is not part of the researched surface, so it travels
            # as it came instead of being interpreted.
            return Delivery.failure(self.name, recipient, f"Telegram respondio {response.status_code}: {response.text}")

        try:
            message_id = str(response.json()["result"]["message_id"])
        except (ValueError, KeyError, TypeError):
            return Delivery.failure(self.name, recipient, f"Telegram respondio 200 sin id de mensaje: {response.text}")
        return Delivery.sent(self.name, recipient, message_id)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
