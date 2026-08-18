"""Turns a config into live channel instances."""

from __future__ import annotations

import httpx

from .channel import Channel
from .config import NotifyConfig
from .outbox import OutboxChannel
from .telegram import TelegramChannel
from .whatsapp import WhatsAppChannel


class ChannelFactory:
    """Builds the channels the config resolved to, in the order it named them."""

    def __init__(self, config: NotifyConfig, client: httpx.Client | None = None):
        self._config = config
        self._client = client

    def build(self) -> list[Channel]:
        return [self._one(name) for name in self._config.channel_names()]

    def _one(self, name: str) -> Channel:
        config = self._config
        if name == "whatsapp":
            return WhatsAppChannel(
                token=config.whatsapp_token,
                phone_id=config.whatsapp_phone_id,
                recipients=config.whatsapp_recipients,
                api_version=config.whatsapp_api_version,
                development_mode=config.whatsapp_development_mode,
                client=self._client,
            )
        if name == "telegram":
            return TelegramChannel(
                token=config.telegram_token,
                recipients=config.telegram_chat_ids,
                client=self._client,
            )
        return OutboxChannel(path=config.outbox_path)
