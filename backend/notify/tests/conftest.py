"""Test setup: the box on the import path, and a stand-in for the provider's HTTP API."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


class FakeApi:
    """Records every request the box sends out and answers with a canned response."""

    def __init__(self, status: int, payload: dict):
        self.requests: list[httpx.Request] = []
        self._status = status
        self._payload = payload
        self.client = httpx.Client(transport=httpx.MockTransport(self._handle))

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(self._status, json=self._payload)

    def sent(self) -> dict:
        import json

        return json.loads(self.requests[-1].content)


@pytest.fixture
def fake_api():
    def build(status: int = 200, payload: dict | None = None) -> FakeApi:
        return FakeApi(status, payload or {})

    return build
