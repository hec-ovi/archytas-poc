"""What this box refuses to do."""

from __future__ import annotations


class AlertsError(Exception):
    """Base for everything the alerts box raises."""


class MissingText(AlertsError):
    """A rule asked for wording that is not in `messages/`, or passed it incomplete."""
