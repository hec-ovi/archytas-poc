"""Telegram sends free text to a chat id."""

from __future__ import annotations

from notify import Message, Notifier, TelegramChannel


def test_telegram_delivers_and_returns_the_message_id(fake_api):
    api = fake_api(200, {"ok": True, "result": {"message_id": 4711}})
    notifier = Notifier([TelegramChannel(token="123:ABC", recipients=("55512345",), client=api.client)])

    results = notifier.send(Message(text="Aviso de vencimiento"))

    assert results[0].delivered is True
    assert results[0].message_id == "4711"
    assert api.sent() == {"chat_id": "55512345", "text": "Aviso de vencimiento"}
