"""The tray delivers with nothing configured, and leaves the message on disk."""

from __future__ import annotations

import json

from notify import Message, Notifier


def test_outbox_delivers_and_writes_the_message(tmp_path):
    path = tmp_path / "inbox" / "outbox.jsonl"
    notifier = Notifier.from_env({"NOTIFY_OUTBOX_PATH": str(path)})

    results = notifier.send(Message(text="Factura A-0001-00012345 vence el 21/08/2026"))

    assert notifier.channels == ("outbox",)
    assert [(r.channel, r.delivered) for r in results] == [("outbox", True)]
    assert results[0].message_id
    written = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert written["text"] == "Factura A-0001-00012345 vence el 21/08/2026"
