"""Shared handles the routes ask for.

One store for the whole process, one portal session opened on demand. Both hang off the app
so tests can swap them for a temporary database without touching a route.
"""

from __future__ import annotations

from fastapi import Request

from portal_sync.client import PortalClient
from portal_sync.session import PortalSession
from store import Store

from .config import Settings
from .realtime import Hub


def get_store(request: Request) -> Store:
    return request.app.state.store


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_hub(request: Request) -> Hub:
    return request.app.state.hub


def open_portal(settings: Settings) -> tuple[PortalSession, PortalClient]:
    session = PortalSession(settings.portal_base_url, settings.portal_user, settings.portal_password)
    return session, PortalClient(session)
