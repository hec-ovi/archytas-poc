"""Closed error set for the portal_sync box."""


class PortalError(Exception):
    """Base for everything this box raises."""


class PortalAuthError(PortalError):
    """Credentials rejected, or the session could not be renewed."""


class PortalUnavailable(PortalError):
    """Portal unreachable, timed out, or answered 5xx after retries."""


class PortalBadResponse(PortalError):
    """Portal answered 2xx with something we cannot parse."""


class DownloadExpired(PortalError):
    """The signed download link was refused (expired or tampered)."""
