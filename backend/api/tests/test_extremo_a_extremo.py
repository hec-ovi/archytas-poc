"""The whole loop, through the real entry points, with nothing stubbed but the portal itself.

New data comes in, gets normalized, lands in the database, shows up on the calendar, a person
acts on it, an alert fires, and the message goes out. If this passes, the system works.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from ingest import IngestRunner
from ingest.tests.test_ingest import FakePortal

FIXTURES = Path(__file__).resolve().parents[2] / "document_parser" / "tests" / "fixtures"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CORDILLERA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NOTIFY_CHANNELS", "outbox")
    monkeypatch.setenv("NOTIFY_OUTBOX_PATH", str(tmp_path / "avisos.jsonl"))
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def login(client, username="duenio"):
    response = client.post("/api/auth/login", json={"usuario": username, "clave": "cordillera2026"})
    assert response.status_code == 200
    return response.json()


def sync(client):
    """A full portal pass, against a portal that serves the real messes."""
    store = client.app.state.store
    return IngestRunner(store, FakePortal()).run("prueba", with_price_history=False)


class TestElCicloCompleto:
    def test_a_pass_leaves_the_system_usable(self, client):
        login(client)
        report = sync(client)
        assert not report.errors

        board = client.get("/api/tablero").json()
        assert board["deuda_por_proveedor"], "el tablero tiene que poder decir a quien le debemos"
        assert board["ventas_por_mes"], "y cuanto vendimos"
        assert board["pendientes_revision"] > 0, "y que quedo esperando una decision"

    def test_the_calendar_fills_itself_from_the_invoices(self, client):
        login(client)
        sync(client)
        events = client.get("/api/calendario?desde=2020-01-01&hasta=2099-12-31").json()["eventos"]
        assert {e["invoice_number"] for e in events} == {"F-1", "F-2"}
        assert all(e["kind"] == "vencimiento" for e in events)

    def test_a_second_pass_changes_nothing(self, client):
        login(client)
        sync(client)
        before = client.get("/api/facturas").json()["resumen"]
        sync(client)
        assert client.get("/api/facturas").json()["resumen"] == before


class TestUnDocumentoQueEntraAMano:
    def test_a_spreadsheet_invoice_becomes_a_real_invoice(self, client):
        login(client)
        sync(client)
        store = client.app.state.store
        # the file names Aceros Belgrano, who is already known from the account statements
        path = FIXTURES / "F-7797_Aceros_Belgrano_SA.xlsx"
        if not path.exists():
            pytest.skip("falta el archivo de ejemplo")

        with path.open("rb") as handle:
            upload = client.post("/api/documentos", files={"archivo": (path.name, handle, "application/vnd.ms-excel")})
        assert upload.status_code == 201
        document = upload.json()["documento"]
        proposal = document["parsed"]["propuesta"]

        assert proposal["numero"] == "F-7797"
        assert proposal["proveedor_id"], "el proveedor tiene que resolverse contra los que ya existen"
        assert proposal["falta"] == [], f"no deberia faltar nada: {proposal['falta']}"

        applied = client.post(f"/api/documentos/{document['id']}/aplicar")
        assert applied.status_code == 201 and applied.json()["nuevo"] is True

        invoice = store.invoices.get(applied.json()["factura_id"])
        assert invoice["number"] == "F-7797"
        # the document carried no due date, so it comes from the term agreed with that supplier
        assert invoice["due_on"] == "2026-06-17"

    def test_the_same_file_twice_does_not_make_two_invoices(self, client):
        login(client)
        sync(client)
        path = FIXTURES / "F-7797_Aceros_Belgrano_SA.xlsx"
        if not path.exists():
            pytest.skip("falta el archivo de ejemplo")

        for _ in range(2):
            with path.open("rb") as handle:
                response = client.post("/api/documentos", files={"archivo": (path.name, handle, "application/vnd.ms-excel")})
        assert response.json()["nuevo"] is False
        assert "ya se habia subido" in response.json()["aviso"]

    def test_an_unreadable_document_is_reported_not_loaded(self, client):
        login(client)
        sync(client)
        response = client.post("/api/documentos", files={"archivo": ("nota.txt", b"cualquier cosa", "text/plain")})
        assert response.status_code == 201, "un archivo ilegible es una respuesta, no un error del servidor"
        document = response.json()["documento"]
        assert document["status"] == "fallido"
        assert "planilla" in response.json()["aviso"]
        assert client.post(f"/api/documentos/{document['id']}/aplicar").status_code == 409


class TestLoQueHaceUnaPersona:
    def invoice(self, client, number="F-1"):
        return next(i["id"] for i in client.get("/api/facturas").json()["facturas"] if i["number"] == number)

    def test_paying_half_and_then_the_rest(self, client):
        login(client)
        sync(client)
        target = self.invoice(client)
        # the pass already loaded a payment of 30.000 against this one
        assert client.get(f"/api/facturas/{target}").json()["factura"]["payment_state"] == "parcial"

        remaining = client.get(f"/api/facturas/{target}").json()["factura"]["balance_cents"]
        response = client.post(f"/api/facturas/{target}/pagos", json={"monto_centavos": remaining})
        assert response.json()["factura"]["payment_state"] == "saldada"

    def test_issuing_a_receipt_shows_up_on_the_calendar(self, client):
        login(client)
        sync(client)
        target = self.invoice(client, "F-2")
        before = client.get("/api/calendario?desde=2020-01-01&hasta=2099-12-31").json()["eventos"]
        assert next(e for e in before if e["invoice_number"] == "F-2")["has_receipt"] == 0

        assert client.post(f"/api/facturas/{target}/recibo").status_code == 201
        after = client.get("/api/calendario?desde=2020-01-01&hasta=2099-12-31").json()["eventos"]
        assert next(e for e in after if e["invoice_number"] == "F-2")["has_receipt"] == 1

    def test_deciding_a_duplicate_sale_puts_one_back_in_the_totals(self, client):
        login(client)
        sync(client)
        store = client.app.state.store

        pending = client.get("/api/revision?tipo=venta-duplicada").json()["pendientes"]
        assert pending, "las ventas con el mismo codigo y distinta cantidad tienen que estar esperando"
        item = pending[0]

        before = sum(m["revenue_cents"] for m in store.sales.revenue_by_month())
        keep = store.sales.by_code("V-2")[0]
        response = client.post(f"/api/revision/{item['id']}/resolver",
                               json={"decision": {"codigo_valido": "V-2", "row_hash": keep["row_hash"]}})
        assert response.status_code == 200

        after = sum(m["revenue_cents"] for m in store.sales.revenue_by_month())
        assert after == before + keep["total_cents"]
        assert item["id"] not in {p["id"] for p in client.get("/api/revision").json()["pendientes"]}

    def test_a_confirmed_spelling_is_remembered(self, client):
        login(client)
        sync(client)
        store = client.app.state.store
        supplier = store.suppliers.by_slug("herramientas-cuyo-srl")
        store.reviews.raise_item({
            "kind": "proveedor", "dedupe_key": "proveedor:Hrram Cuyo",
            "title": "Proveedor sin identificar", "raw": {"proveedor": "Hrram Cuyo"}, "candidates": [],
        })
        item = client.get("/api/revision?tipo=proveedor").json()["pendientes"][0]
        client.post(f"/api/revision/{item['id']}/resolver",
                    json={"decision": {"proveedor_slug": "herramientas-cuyo-srl"}})

        remembered = store.supplier_aliases.resolve("Hrram Cuyo")
        assert remembered and remembered["supplier_id"] == supplier["id"]


class TestElAvisoLlega:
    def test_an_alert_fires_and_the_message_goes_out(self, client, tmp_path):
        login(client)
        sync(client)

        response = client.post("/api/alertas/revisar")
        assert response.status_code == 200
        summary = response.json()["resumen"]
        assert summary["eventos_nuevos"] > 0
        assert summary["entregas"] > 0 and summary["entregas_fallidas"] == 0

        outbox = tmp_path / "avisos.jsonl"
        assert outbox.exists(), "el aviso tiene que quedar registrado aunque no haya WhatsApp"
        sent = [json.loads(line) for line in outbox.read_text().splitlines() if line.strip()]
        assert sent, "tiene que haber al menos un mensaje escrito"

    def test_the_same_alert_does_not_go_out_twice(self, client):
        login(client)
        sync(client)
        client.post("/api/alertas/revisar")
        again = client.post("/api/alertas/revisar").json()["resumen"]
        assert again["eventos_nuevos"] == 0
        assert again["entregas"] == 0


class TestTiempoReal:
    def test_moving_a_due_date_reaches_the_other_open_page(self, client):
        login(client)
        sync(client)
        created = client.post("/api/calendario", json={"titulo": "Pago acordado", "fecha": "2026-06-01"}).json()

        with client.websocket_connect("/ws") as other_page:
            client.patch(f"/api/calendario/{created['evento']['id']}", json={"fecha": "2026-06-20"})
            message = other_page.receive_json()

        assert message["evento"] == "calendario-cambio"
        assert message["datos"]["accion"] == "movido"
        assert message["datos"]["evento"]["on_date"] == "2026-06-20"
        assert message["datos"]["evento"]["moved_from"] == "2026-06-01"

    def test_registering_a_payment_reaches_the_other_open_page(self, client):
        login(client)
        sync(client)
        target = next(i["id"] for i in client.get("/api/facturas").json()["facturas"] if i["number"] == "F-2")

        with client.websocket_connect("/ws") as other_page:
            client.post(f"/api/facturas/{target}/pagos", json={"monto_centavos": 1000})
            message = other_page.receive_json()

        assert message["evento"] == "factura-actualizada"
        assert message["datos"]["estado"] == "parcial"
