"""Settings read from the environment.

Nothing here fails because a credential is missing: a channel without credentials is
dropped, and if that leaves nothing standing the outbox takes over.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .errors import UnknownChannel
from .whatsapp import DEFAULT_API_VERSION

KNOWN_CHANNELS = ("whatsapp", "telegram", "outbox")
DEFAULT_DATA_DIR = "data"


def _split(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class NotifyConfig:
    """Everything the box needs to build its channels."""

    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    whatsapp_recipients: tuple[str, ...] = ()
    whatsapp_api_version: str = DEFAULT_API_VERSION
    whatsapp_development_mode: bool = True
    telegram_token: str = ""
    telegram_chat_ids: tuple[str, ...] = ()
    outbox_path: Path = Path(DEFAULT_DATA_DIR) / "inbox" / "outbox.jsonl"
    requested_channels: tuple[str, ...] = ()

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "NotifyConfig":
        env = os.environ if env is None else env
        data_dir = env.get("CORDILLERA_DATA_DIR", DEFAULT_DATA_DIR)
        default_outbox = Path(data_dir) / "inbox" / "outbox.jsonl"
        return cls(
            whatsapp_token=env.get("WHATSAPP_TOKEN", "").strip(),
            whatsapp_phone_id=env.get("WHATSAPP_PHONE_ID", "").strip(),
            whatsapp_recipients=_split(env.get("WHATSAPP_RECIPIENTS", "")),
            whatsapp_api_version=env.get("WHATSAPP_API_VERSION", DEFAULT_API_VERSION).strip() or DEFAULT_API_VERSION,
            whatsapp_development_mode=env.get("WHATSAPP_MODE", "development").strip().lower() != "production",
            telegram_token=env.get("TELEGRAM_TOKEN", "").strip(),
            telegram_chat_ids=_split(env.get("TELEGRAM_CHAT_IDS", "")),
            outbox_path=Path(env.get("NOTIFY_OUTBOX_PATH", "").strip() or default_outbox),
            requested_channels=_split(env.get("NOTIFY_CHANNELS", "").lower()),
        )

    @property
    def whatsapp_ready(self) -> bool:
        return bool(self.whatsapp_token and self.whatsapp_phone_id and self.whatsapp_recipients)

    @property
    def telegram_ready(self) -> bool:
        return bool(self.telegram_token and self.telegram_chat_ids)

    def channel_names(self) -> tuple[str, ...]:
        """The channels that will actually be built.

        An unknown name in NOTIFY_CHANNELS is a typo worth stopping for. A configured
        name with no credentials is not: it drops, and the outbox catches the alert.
        """
        for name in self.requested_channels:
            if name not in KNOWN_CHANNELS:
                raise UnknownChannel(f"canal desconocido {name!r}; conocidos: {', '.join(KNOWN_CHANNELS)}")

        wanted = self.requested_channels or tuple(
            name for name, ready in (("whatsapp", self.whatsapp_ready), ("telegram", self.telegram_ready)) if ready
        )
        ready = {"whatsapp": self.whatsapp_ready, "telegram": self.telegram_ready, "outbox": True}
        usable = tuple(name for name in wanted if ready[name])
        return usable or ("outbox",)
