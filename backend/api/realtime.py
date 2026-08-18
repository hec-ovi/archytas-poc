"""Telling everyone who has the page open that something changed.

The client asked for this by name: "if two people from our team are looking at the calendar
at the same time, both should see the change right away, not have one refresh the page."

A process-local broadcast is enough here because the whole system runs as one container. If
it ever runs as several, this is the one piece that has to move to a shared bus, and it is
one file.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket


class Hub:
    """Every open page, and how to reach them all at once."""

    def __init__(self):
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def join(self, socket: WebSocket) -> None:
        await socket.accept()
        async with self._lock:
            self._clients.add(socket)

    async def leave(self, socket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(socket)

    async def broadcast(self, event: str, payload: dict[str, Any]) -> None:
        message = json.dumps({"evento": event, "datos": payload}, ensure_ascii=False, default=str)
        async with self._lock:
            clients = list(self._clients)
        for socket in clients:
            try:
                await socket.send_text(message)
            except Exception:
                # a page that closed mid-broadcast is not an error worth surfacing
                await self.leave(socket)

    @property
    def connected(self) -> int:
        return len(self._clients)
