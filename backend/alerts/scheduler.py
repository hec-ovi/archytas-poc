"""When the engine runs.

Two triggers, because they answer different worries. An interval, so nothing waits a whole
day, on the same `sync_horas` the client already tunes for the portal refresh. And a fixed
morning run, so whoever opens the shop already has the list. Plus a button: `run_now`.

A pass that blows up is written to the log and the schedule keeps standing. Alerts that stop
firing because one bad row killed the process is the failure this box exists to avoid.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from store import Store

from .engine import AlertEngine
from .report import AlertRun

LOG = logging.getLogger("alerts")

INTERVAL_JOB = "alertas-intervalo"
MORNING_JOB = "alertas-manana"
DEFAULT_HOURS = 12.0
MIN_HOURS = 0.25


class AlertScheduler:
    """Keeps the engine running on its own, and lets a person trigger it by hand."""

    def __init__(
        self,
        engine: AlertEngine,
        store: Store,
        morning_hour: int = 8,
        timezone: str | None = None,
        scheduler: BaseScheduler | None = None,
    ):
        self._engine = engine
        self._store = store
        self._morning_hour = morning_hour
        self._timezone = timezone
        self._scheduler = scheduler or BackgroundScheduler(**({"timezone": timezone} if timezone else {}))
        self._last_run: AlertRun | None = None
        self._last_error: str | None = None

    @property
    def hours(self) -> float:
        """How often the interval fires, from `sync_horas`, never faster than 15 minutes."""
        try:
            hours = float(self._store.settings.get_value("sync_horas", DEFAULT_HOURS))
        except (TypeError, ValueError):
            hours = DEFAULT_HOURS
        return max(hours, MIN_HOURS)

    @property
    def jobs(self) -> tuple[str, ...]:
        return tuple(job.id for job in self._scheduler.get_jobs())

    @property
    def running(self) -> bool:
        return bool(self._scheduler.running)

    @property
    def last_run(self) -> AlertRun | None:
        return self._last_run

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def start(self) -> None:
        """Register both triggers and start. Safe to call on an already running scheduler."""
        self._scheduler.add_job(
            self._run,
            IntervalTrigger(hours=self.hours),
            id=INTERVAL_JOB,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.add_job(
            self._run,
            CronTrigger(hour=self._morning_hour, minute=0, timezone=self._timezone),
            id=MORNING_JOB,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        if not self._scheduler.running:
            self._scheduler.start()

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def run_now(self) -> AlertRun:
        """The manual trigger. Returns the same report the scheduled pass produces."""
        return self._run()

    def _run(self) -> AlertRun:
        try:
            report = self._engine.run()
            self._last_error = None
        except Exception as error:  # the schedule outlives any single bad pass
            LOG.exception("la pasada de alertas fallo")
            self._last_error = str(error)
            report = AlertRun(errors=[f"la pasada fallo: {error}"])
        self._last_run = report
        return report
