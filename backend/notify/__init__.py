"""Message delivery by channel: WhatsApp, Telegram and a local tray."""

from .channel import Channel, Delivery
from .config import NotifyConfig
from .errors import NotifyError, UnknownChannel
from .message import Message, Template
from .notifier import Notifier
from .outbox import OutboxChannel
from .telegram import TelegramChannel
from .whatsapp import WhatsAppChannel

__all__ = [
    "Channel",
    "Delivery",
    "Message",
    "Notifier",
    "NotifyConfig",
    "NotifyError",
    "OutboxChannel",
    "Template",
    "TelegramChannel",
    "UnknownChannel",
    "WhatsAppChannel",
]
