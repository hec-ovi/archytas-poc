"""The schedule stands on its own, and a pass that fails does not take it down."""

from __future__ import annotations

from alerts import AlertRun, AlertScheduler
from alerts.scheduler import INTERVAL_JOB, MORNING_JOB


class StubEngine:
    """Stands in for the engine so the schedule is what gets tested."""

    def __init__(self, error: Exception | None = None):
        self.runs = 0
        self._error = error

    def run(self, today: str | None = None) -> AlertRun:
        self.runs += 1
        if self._error:
            raise self._error
        return AlertRun(raised=1)


def test_start_registers_both_triggers_with_the_interval_from_the_settings(store):
    store.settings.set_value("sync_horas", 3)
    scheduler = AlertScheduler(StubEngine(), store)

    try:
        scheduler.start()
        assert sorted(scheduler.jobs) == sorted((INTERVAL_JOB, MORNING_JOB))
        assert scheduler.hours == 3
        assert scheduler.running
    finally:
        scheduler.stop()

    assert not scheduler.running


def test_run_now_reports_what_the_pass_did(store):
    engine = StubEngine()
    scheduler = AlertScheduler(engine, store)

    report = scheduler.run_now()

    assert (engine.runs, report.raised) == (1, 1)
    assert scheduler.last_error is None
    assert scheduler.last_run is report


def test_a_failing_pass_does_not_escape_the_scheduler(store):
    scheduler = AlertScheduler(StubEngine(RuntimeError("la base no responde")), store)

    report = scheduler.run_now()

    assert report.errors == ["la pasada fallo: la base no responde"]
    assert scheduler.last_error == "la base no responde"
