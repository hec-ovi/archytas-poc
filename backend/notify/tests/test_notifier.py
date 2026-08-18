"""Configuration: credentials missing means the tray takes over, a bad name stops."""

from __future__ import annotations

import pytest

from notify import Message, Notifier, UnknownChannel


def test_whatsapp_without_credentials_degrades_to_the_outbox(tmp_path):
    notifier = Notifier.from_env(
        {
            "NOTIFY_CHANNELS": "whatsapp",
            "WHATSAPP_TOKEN": "",
            "WHATSAPP_PHONE_ID": "",
            "NOTIFY_OUTBOX_PATH": str(tmp_path / "outbox.jsonl"),
        }
    )

    results = notifier.send(Message(text="Factura vencida"))

    assert notifier.channels == ("outbox",)
    assert results[0].delivered is True


def test_an_unknown_channel_name_is_refused():
    with pytest.raises(UnknownChannel):
        Notifier.from_env({"NOTIFY_CHANNELS": "sms"})
