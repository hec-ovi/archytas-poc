"""The HTTP surface, through real requests against a real temporary database.

Two things matter most here and both are things the client asked for by name: that each
person only reaches their own part of the system, and that the three actions he wanted to do
himself actually work and leave a trace.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from store import Store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CORDILLERA_DATA_DIR", str(tmp_path))
    app = create_app()
    with TestClient(app) as test_client:
        store: Store = app.state.store
        supplier = store.suppliers.save({"slug": "aceros", "name": "Aceros Belgrano SA",
                                         "cuit": "30-70918273-4", "email": "a@b.com", "terms_days": 45})
        store.invoices.save({"external_id": "f1", "number": "F-1", "supplier_id": supplier,
                             "issued_on": "2026-01-01", "due_on": "2099-01-01", "amount_cents": 100000})
        store.invoices.save({"external_id": "f2", "number": "F-2", "supplier_id": supplier,
                             "issued_on": "2020-01-01", "due_on": "2020-02-01", "amount_cents": 50000})
        yield test_client


def login(client, username):
    return client.post("/api/auth/login", json={"usuario": username, "clave": "cordillera2026"})


def invoice_id(client, number):
    return next(i["id"] for i in client.get("/api/facturas").json()["facturas"] if i["number"] == number)


class TestAccess:
    def test_a_wrong_password_does_not_get_in(self, client):
        assert client.post("/api/auth/login", json={"usuario": "marcela", "clave": "mala"}).status_code == 401

    def test_without_a_session_nothing_opens(self, client):
        assert client.get("/api/facturas").status_code == 401

    def test_each_person_gets_their_own_sections(self, client):
        assert login(client, "marcela").json()["secciones"] == [
            "proveedores", "facturas", "ordenes", "calendario", "revision", "mensajes"
        ]
        assert login(client, "julian").json()["secciones"] == ["tablero", "ventas", "productos"]

    def test_purchases_cannot_see_the_company_numbers(self, client):
        login(client, "marcela")
        assert client.get("/api/tablero").status_code == 403
        assert client.get("/api/ventas").status_code == 403

    def test_sales_cannot_touch_the_supplier_accounts(self, client):
        login(client, "julian")
        assert client.get("/api/proveedores").status_code == 403
        assert client.get("/api/facturas").status_code == 403

    def test_the_owner_sees_everything(self, client):
        login(client, "duenio")
        for path in ("/api/tablero", "/api/proveedores", "/api/facturas", "/api/ventas", "/api/configuracion"):
            assert client.get(path).status_code == 200, path


class TestPayments:
    def test_a_partial_payment_moves_the_invoice_to_half_paid(self, client):
        login(client, "marcela")
        target = invoice_id(client, "F-1")
        response = client.post(f"/api/facturas/{target}/pagos", json={"monto_centavos": 40000})
        assert response.status_code == 201
        assert response.json()["factura"]["payment_state"] == "parcial"

    def test_paying_the_rest_settles_it(self, client):
        login(client, "marcela")
        target = invoice_id(client, "F-1")
        client.post(f"/api/facturas/{target}/pagos", json={"monto_centavos": 40000})
        response = client.post(f"/api/facturas/{target}/pagos", json={"monto_centavos": 60000})
        assert response.json()["factura"]["payment_state"] == "saldada"

    def test_a_payment_bigger_than_the_balance_is_refused(self, client):
        login(client, "marcela")
        target = invoice_id(client, "F-1")
        response = client.post(f"/api/facturas/{target}/pagos", json={"monto_centavos": 999999})
        assert response.status_code == 400
        assert "supera el saldo" in response.json()["detail"]


class TestReceipts:
    def test_a_receipt_can_be_issued_before_the_due_date(self, client):
        login(client, "marcela")
        response = client.post(f"/api/facturas/{invoice_id(client, 'F-1')}/recibo")
        assert response.status_code == 201
        assert response.json()["recibo"]["number"] == "REC-F-1"

    def test_issuing_it_twice_does_not_make_two(self, client):
        login(client, "marcela")
        target = invoice_id(client, "F-1")
        client.post(f"/api/facturas/{target}/recibo")
        assert client.post(f"/api/facturas/{target}/recibo").json()["nuevo"] is False

    def test_an_invoice_already_past_due_cannot_get_one(self, client):
        login(client, "marcela")
        response = client.post(f"/api/facturas/{invoice_id(client, 'F-2')}/recibo")
        assert response.status_code == 409
        assert "vencio" in response.json()["detail"]


class TestAdjustments:
    def test_adjusting_an_amount_records_who_and_why(self, client):
        login(client, "marcela")
        target = invoice_id(client, "F-1")
        response = client.patch(f"/api/facturas/{target}",
                                json={"monto_centavos": 80000, "motivo": "nota de credito del proveedor"})
        assert response.status_code == 200
        change = response.json()["ajustes"][-1]
        assert change["de"] == 100000 and change["a"] == 80000
        assert change["por"] == "marcela" and "credito" in change["motivo"]


class TestCalendar:
    def test_every_due_date_is_on_the_calendar(self, client):
        login(client, "duenio")
        store = client.app.state.store
        for invoice in store.invoices.all():
            store.calendar.sync_from_invoice(invoice, invoice["supplier_id"])
        events = client.get("/api/calendario?desde=2020-01-01&hasta=2099-12-31").json()["eventos"]
        assert {e["invoice_number"] for e in events} == {"F-1", "F-2"}

    def test_moving_a_date_remembers_where_it_came_from(self, client):
        login(client, "duenio")
        created = client.post("/api/calendario", json={"titulo": "Pago acordado", "fecha": "2026-06-01"}).json()
        moved = client.patch(f"/api/calendario/{created['evento']['id']}", json={"fecha": "2026-06-15"}).json()
        assert moved["evento"]["on_date"] == "2026-06-15"
        assert moved["evento"]["moved_from"] == "2026-06-01"

    def test_a_due_date_of_an_invoice_is_not_deleted_from_the_calendar(self, client):
        login(client, "duenio")
        store = client.app.state.store
        invoice = store.invoices.all()[0]
        event_id = store.calendar.sync_from_invoice(invoice, invoice["supplier_id"])
        assert client.delete(f"/api/calendario/{event_id}").status_code == 409


class TestSettings:
    def test_the_client_can_change_a_threshold_himself(self, client):
        login(client, "duenio")
        response = client.put("/api/configuracion/aviso_dias_antes", json={"valor": 15})
        assert response.status_code == 200
        values = {row["key"]: row["value"] for row in response.json()["configuracion"]}
        assert values["aviso_dias_antes"] == 15

    def test_an_invented_parameter_is_refused(self, client):
        login(client, "duenio")
        assert client.put("/api/configuracion/inventado", json={"valor": 1}).status_code == 404
