"""Alerts: what is worth interrupting a person for, and when it gets decided."""

from .dates import Clock
from .engine import AlertEngine
from .errors import AlertsError, MissingText
from .event import AVISO, URGENTE, AlertEvent
from .report import AlertRun
from .rule import Rule
from .rules import (
    LargeInvoiceDueRule,
    MissingReceiptRule,
    OpenClaimRule,
    OverdueInvoiceRule,
    ReviewQueueRule,
    StaleOrderRule,
    default_rules,
)
from .scheduler import AlertScheduler
from .settings import AlertSettings
from .texts import AlertText, TextLibrary

__all__ = [
    "AVISO",
    "URGENTE",
    "AlertEngine",
    "AlertEvent",
    "AlertRun",
    "AlertScheduler",
    "AlertSettings",
    "AlertText",
    "AlertsError",
    "Clock",
    "LargeInvoiceDueRule",
    "MissingReceiptRule",
    "MissingText",
    "OpenClaimRule",
    "OverdueInvoiceRule",
    "ReviewQueueRule",
    "Rule",
    "StaleOrderRule",
    "TextLibrary",
    "default_rules",
]
