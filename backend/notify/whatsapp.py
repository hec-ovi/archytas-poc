"""WhatsApp through Meta's Cloud API.

Two shapes of message: a template, which lands whether or not the recipient wrote first,
and free-form text, which Meta only accepts inside the 24h window opened by the
recipient's last message. A 200 means Meta accepted the message, not that it arrived:
delivery lands later on the webhook, which this box does not implement.
"""

from __future__ import annotations

from typing import Any, Sequence

import httpx

from .channel import Channel, Delivery
from .message import Message, Template
from .meta_errors import MetaError
from .phone import to_wa_recipient

GRAPH_HOST = "https://graph.facebook.com"
DEFAULT_API_VERSION = "v25.0"


class WhatsAppChannel(Channel):
    """Sends alerts through Meta's Cloud API."""

    name = "whatsapp"

    def __init__(
        self,
        token: str,
        phone_id: str,
        recipients: Sequence[str] = (),
        api_version: str = DEFAULT_API_VERSION,
        development_mode: bool = True,
        client: httpx.Client | None = None,
        timeout: float = 15.0,
    ):
        super().__init__(recipients)
        self._url = f"{GRAPH_HOST}/{api_version}/{phone_id}/messages"
        self._headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        self._development_mode = development_mode
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def send(self, recipient: str, message: Message) -> Delivery:
        to = to_wa_recipient(recipient, self._development_mode)
        payload = (
            self._template_payload(to, message.template)
            if message.template
            else self._text_payload(to, message.text)
        )
        try:
            response = self._client.post(self._url, headers=self._headers, json=payload)
        except httpx.HTTPError as exc:
            return Delivery.failure(self.name, recipient, f"no se pudo contactar la API de WhatsApp: {exc}")

        if response.status_code != 200:
            return Delivery.failure(self.name, recipient, MetaError(response).reason())

        message_id = self._message_id(response)
        if message_id is None:
            return Delivery.failure(self.name, recipient, f"WhatsApp respondio 200 sin id de mensaje: {response.text}")
        return Delivery.sent(self.name, recipient, message_id)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _text_payload(self, to: str, body: str) -> dict[str, Any]:
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }

    def _template_payload(self, to: str, template: Template) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {"name": template.name, "language": {"code": template.language}},
        }
        if template.params:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "parameter_name": key, "text": value}
                        for key, value in template.params.items()
                    ],
                }
            ]
        return payload

    @staticmethod
    def _message_id(response: httpx.Response) -> str | None:
        try:
            return response.json()["messages"][0]["id"]
        except (ValueError, KeyError, IndexError, TypeError):
            return None
