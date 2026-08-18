"""WhatsApp: the two message shapes, the Argentine number trap, and a mapped rejection."""

from __future__ import annotations

import pytest

from notify import Message, Notifier, Template, WhatsAppChannel

ACCEPTED = {
    "messaging_product": "whatsapp",
    "contacts": [{"input": "541122334455", "wa_id": "5491122334455"}],
    "messages": [{"id": "wamid.HBgLTEST", "message_status": "accepted"}],
}


def channel(fake_api, status=200, payload=None, recipients=("5491122334455",), development_mode=True):
    api = fake_api(status, payload or ACCEPTED)
    return api, WhatsAppChannel(
        token="EAAtoken",
        phone_id="106540352242922",
        recipients=recipients,
        development_mode=development_mode,
        client=api.client,
    )


def test_free_form_text_is_sent_to_the_messages_endpoint(fake_api):
    api, whatsapp = channel(fake_api)

    results = Notifier([whatsapp]).send(Message(text="Factura A-0001 vence el 21/08/2026"))

    assert results[0].delivered is True
    assert results[0].message_id == "wamid.HBgLTEST"
    request = api.requests[-1]
    assert str(request.url) == "https://graph.facebook.com/v25.0/106540352242922/messages"
    assert request.headers["authorization"] == "Bearer EAAtoken"
    assert api.sent() == {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "541122334455",
        "type": "text",
        "text": {"preview_url": False, "body": "Factura A-0001 vence el 21/08/2026"},
    }


def test_template_carries_its_named_parameters(fake_api):
    api, whatsapp = channel(fake_api)
    message = Message(
        text="Factura A-0001 de Ferreteria Sur vence el 21/08/2026",
        template=Template(
            name="invoice_due_alert",
            language="es_AR",
            params={"invoice_number": "A-0001", "due_date": "21/08/2026"},
        ),
    )

    results = Notifier([whatsapp]).send(message)

    assert results[0].delivered is True
    assert api.sent()["type"] == "template"
    assert api.sent()["template"] == {
        "name": "invoice_due_alert",
        "language": {"code": "es_AR"},
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "parameter_name": "invoice_number", "text": "A-0001"},
                    {"type": "text", "parameter_name": "due_date", "text": "21/08/2026"},
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    "development_mode, expected",
    [(True, "541122334455"), (False, "5491122334455")],
)
def test_argentine_mobiles_drop_the_nine_only_in_development(fake_api, development_mode, expected):
    api, whatsapp = channel(fake_api, development_mode=development_mode)

    Notifier([whatsapp]).send(Message(text="hola"))

    assert api.sent()["to"] == expected


def test_a_rejection_comes_back_as_a_readable_reason(fake_api):
    rejection = {
        "error": {
            "message": "(#131047) Re-engagement message",
            "type": "OAuthException",
            "code": 131047,
            "error_data": {"messaging_product": "whatsapp", "details": "More than 24 hours have passed"},
            "fbtrace_id": "Axxx",
        }
    }
    _, whatsapp = channel(fake_api, status=400, payload=rejection)

    results = Notifier([whatsapp]).send(Message(text="hola"))

    assert results[0].delivered is False
    assert results[0].message_id is None
    assert "24 horas" in results[0].reason
    assert "131047" in results[0].reason


def test_one_result_per_recipient(fake_api):
    _, whatsapp = channel(fake_api, recipients=("5491122334455", "5491133445566"))

    results = Notifier([whatsapp]).send(Message(text="hola"))

    assert [r.recipient for r in results] == ["5491122334455", "5491133445566"]
    assert all(r.delivered for r in results)
