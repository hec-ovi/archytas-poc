"""Today, and the arithmetic every rule does against it.

Today enters from outside. A rule that read the system clock would make its own test pass
only until the fixture dates aged out, and a threshold that cannot be tested is a threshold
nobody trusts.
"""

from __future__ import annotations

from datetime import date, timedelta

NO_DATE = "sin fecha"


class Clock:
    """The reference date for one pass, in ISO, plus how far other dates are from it."""

    def __init__(self, today: str | date | None = None):
        self._today = _as_date(today) or date.today()

    @property
    def today(self) -> str:
        return self._today.isoformat()

    def plus_days(self, days: int) -> str:
        return (self._today + timedelta(days=days)).isoformat()

    def days_until(self, iso: str | None) -> int | None:
        """Days left to reach `iso`. Negative once it is in the past."""
        day = _as_date(iso)
        return None if day is None else (day - self._today).days

    def days_since(self, iso: str | None) -> int | None:
        """Days elapsed since `iso`. Negative while it is still ahead."""
        left = self.days_until(iso)
        return None if left is None else -left

    def phrase(self, iso: str | None) -> str:
        """How far away a date is, in the words the alert uses."""
        left = self.days_until(iso)
        if left is None:
            return NO_DATE
        if left < 0:
            return f"hace {abs(left)} dias"
        return {0: "hoy", 1: "manana"}.get(left, f"en {left} dias")

    @staticmethod
    def pretty(iso: str | None) -> str:
        """ISO to the format the client reads: `2026-08-21` -> `21/08/2026`."""
        day = _as_date(iso)
        return NO_DATE if day is None else day.strftime("%d/%m/%Y")


def _as_date(value: str | date | None) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
