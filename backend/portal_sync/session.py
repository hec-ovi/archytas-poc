"""Session handling for the SIGProv portal.

The portal authenticates with a form POST that sets an HttpOnly cookie valid for 30 days.
There is no refresh endpoint: when the cookie stops working we log in again.
"""

from __future__ import annotations

import httpx

from .errors import PortalAuthError, PortalUnavailable

LOGIN_PATH = "/api/login"
COOKIE_NAME = "portal_session"


class PortalSession:
    """Keeps a logged-in httpx client, and logs back in when the cookie dies."""

    def __init__(self, base_url: str, user: str, password: str, timeout: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._user = user
        self._password = password
        self._client = httpx.Client(base_url=self._base_url, timeout=timeout, follow_redirects=False)
        self._logged_in = False

    def login(self) -> None:
        try:
            response = self._client.post(
                LOGIN_PATH,
                data={"usuario": self._user, "clave": self._password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as exc:
            raise PortalUnavailable(f"login request failed: {exc}") from exc

        if COOKIE_NAME not in self._client.cookies:
            raise PortalAuthError(f"portal rejected the credentials (status {response.status_code})")
        self._logged_in = True

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Issue a request, logging in first and retrying once if the session died."""
        if not self._logged_in:
            self.login()

        response = self._send(method, path, **kwargs)
        if self._session_died(response):
            self.login()
            response = self._send(method, path, **kwargs)
            if self._session_died(response):
                raise PortalAuthError(f"session still refused after re-login: {method} {path}")
        return response

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PortalSession":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def _send(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            return self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise PortalUnavailable(f"{method} {path} failed: {exc}") from exc

    @staticmethod
    def _session_died(response: httpx.Response) -> bool:
        """Detect a logged-out request.

        The portal does not answer 401. Sometimes it redirects to /login, and sometimes it
        answers 200 with the login page as the body, content type and all. Trusting the
        status code alone writes an HTML login form into the database, so the body is
        checked too whenever an API path did not come back as JSON.
        """
        # 401 is a cookie the portal refuses. 403 is not the session: it is how an expired
        # download link answers, and re-logging in would not make it valid again.
        if response.status_code == 401:
            return True

        location = response.headers.get("location", "")
        if response.status_code in (302, 303, 307) and "/login" in location:
            return True

        if response.status_code == 200 and "text/html" in response.headers.get("content-type", ""):
            return "/api/login" in response.text or "login-box" in response.text
        return False
