"""The promises of portal_sync, against a stubbed portal.

The portal itself is somebody else's system and cannot be part of a test run, so its
behaviours are reproduced here: the ones that matter are the three different ways it tells
you the session is gone, and the fact that a download link expires.
"""

import httpx
import pytest

from portal_sync.client import PortalClient
from portal_sync.downloads import PortalDownloader
from portal_sync.errors import DownloadExpired, PortalAuthError, PortalBadResponse
from portal_sync.session import PortalSession

LOGIN_HTML = '<html><body><form action="/api/login" method="POST"></form></body></html>'


def portal(handler) -> PortalSession:
    session = PortalSession("https://portal.test", "proveedor", "clave")
    session._client = httpx.Client(base_url="https://portal.test", transport=httpx.MockTransport(handler))
    return session


def logged_in(handler):
    """Wrap a handler so /api/login always succeeds and sets the cookie."""

    def wrapped(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/login":
            return httpx.Response(303, headers={"set-cookie": "portal_session=ok; Path=/"})
        return handler(request)

    return wrapped


class TestSession:
    def test_wrong_credentials_are_reported_as_such(self):
        session = portal(lambda request: httpx.Response(401))
        with pytest.raises(PortalAuthError):
            session.login()

    def test_a_redirect_to_login_means_the_session_died(self):
        calls = {"n": 0}

        def handler(request):
            if request.url.path == "/api/login":
                return httpx.Response(303, headers={"set-cookie": "portal_session=ok; Path=/"})
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(307, headers={"location": "https://portal.test/login"})
            return httpx.Response(200, json={"productos": []})

        # it logs back in by itself and the caller never sees the interruption
        assert PortalClient(portal(handler)).dataset("precios") == []

    def test_a_login_page_served_as_200_is_not_data(self):
        """The portal answers 200 with the login form when the cookie is gone. Trusting the
        status code writes an HTML form into the database."""
        calls = {"n": 0}

        def handler(request):
            if request.url.path == "/api/login":
                return httpx.Response(303, headers={"set-cookie": "portal_session=ok; Path=/"})
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(200, text=LOGIN_HTML, headers={"content-type": "text/html"})
            return httpx.Response(200, json={"productos": [{"id": "p1"}]})

        assert PortalClient(portal(handler)).dataset("precios") == [{"id": "p1"}]


class TestClient:
    def test_returns_the_rows_untouched(self):
        rows = [{"id": "f1", "monto": "$223.376", "proveedor": "Aceros Belgrano SA"}]
        client = PortalClient(portal(logged_in(lambda r: httpx.Response(200, json={"facturas": rows}))))
        assert client.dataset("facturas") == rows

    def test_an_unknown_dataset_is_refused_before_any_request(self):
        client = PortalClient(portal(logged_in(lambda r: httpx.Response(200, json={}))))
        with pytest.raises(KeyError):
            client.dataset("inventado")

    def test_a_response_without_the_expected_list_is_an_error(self):
        client = PortalClient(portal(logged_in(lambda r: httpx.Response(200, json={"otra_cosa": []}))))
        with pytest.raises(PortalBadResponse):
            client.dataset("facturas")

    def test_price_history_comes_from_the_article_detail(self):
        history = [{"fecha": "2023-01-01", "precio": 25308}]
        client = PortalClient(portal(logged_in(lambda r: httpx.Response(200, json={"historial": history}))))
        assert client.price_history("p1") == history


class TestDownloads:
    def handler(self, request):
        if request.url.path == "/api/login":
            return httpx.Response(303, headers={"set-cookie": "portal_session=ok; Path=/"})
        if request.url.path == "/api/token":
            return httpx.Response(200, json={"url": "/api/descargar/abc"})
        return httpx.Response(
            200, content=b"%PDF-1.4",
            headers={"content-type": "application/pdf",
                     "content-disposition": 'attachment; filename="F-8411.pdf"'},
        )

    def test_a_download_keeps_the_name_the_portal_gave_it(self):
        downloaded = PortalDownloader(portal(self.handler)).fetch("factura", "f89")
        assert downloaded.filename == "F-8411.pdf"
        assert downloaded.content.startswith(b"%PDF")

    def test_an_unknown_kind_never_reaches_the_portal(self):
        with pytest.raises(PortalBadResponse):
            PortalDownloader(portal(self.handler)).signed_url("inventado", "x")

    def test_an_expired_link_is_reported_as_expired(self):
        def expired(request):
            if request.url.path == "/api/login":
                return httpx.Response(303, headers={"set-cookie": "portal_session=ok; Path=/"})
            if request.url.path == "/api/token":
                return httpx.Response(200, json={"url": "/api/descargar/vencido"})
            return httpx.Response(403, json={"error": "token invalido o vencido"})

        with pytest.raises(DownloadExpired):
            PortalDownloader(portal(expired)).fetch("factura", "f89")
