"""A full ingestion pass, against a portal that serves the exact messes the real one does.

The rows here are shrunk versions of real portal rows: the same supplier written three ways,
a rubro written two ways, a product with no rubro, a sale loaded twice identically, a sale
loaded twice with different quantities, a sale whose total does not add up, and one with an
impossible date.
"""

import pytest

from ingest import IngestRunner
from store import Store

CUENTAS = [
    {"proveedor": "Aceros Belgrano SA", "slug": "aceros-belgrano-sa", "cuit": "30-70918273-4",
     "email": "cobranzas@acerosbelgrano.com.ar", "telefono": "011", "domicilio": "CABA",
     "condicionPago": "45 dias", "saldoActual": "$100.000", "movimientos": []},
    {"proveedor": "Herramientas Cuyo SRL", "slug": "herramientas-cuyo-srl", "cuit": "30-11111111-1",
     "email": "cuyo@test.com", "telefono": "0261", "domicilio": "Mendoza",
     "condicionPago": "30 dias", "saldoActual": "$0", "movimientos": []},
]

PRECIOS = [
    {"id": "p1", "codigo": "COR-0001", "descripcion": "Adhesivos", "categoria": "PINTURAS Y ADHESIVOS",
     "subcategoria": "Adhesivos", "precio": "$48.210", "stock": "310"},
    {"id": "p2", "codigo": "COR-0002", "descripcion": "Adhesivos 2", "categoria": "Pinturas/Adhesivos",
     "subcategoria": "Adhesivos", "precio": "$10.000", "stock": "5"},
    {"id": "p3", "codigo": "COR-0003", "descripcion": "Sin rubro", "categoria": "",
     "subcategoria": "Adhesivos", "precio": "$1.000", "stock": "0"},
]

FACTURAS = [
    {"id": "f1", "proveedor": "Aceros Belgrano SA", "numero": "F-1", "fecha": "2026-01-01",
     "monto": "$100.000", "tipo": "PDF", "vencimiento": "2026-02-15", "reciboGenerado": True,
     "productoId": "p1", "productoTexto": "", "pagado": "$0", "saldo": "$100.000",
     "estadoPago": "Impaga", "diasVencida": 99},
    {"id": "f2", "proveedor": "ACEROS BELGRANO", "numero": "F-2", "fecha": "2026-02-01",
     "monto": "$50.000", "tipo": "Excel", "vencimiento": "2026-03-18", "reciboGenerado": False,
     "productoId": "p2", "productoTexto": "", "pagado": "$0", "saldo": "$50.000",
     "estadoPago": "Impaga", "diasVencida": 0},
]

PAGOS = [
    {"id": "pago-f1-1", "referencia": "REC-1", "fecha": "2026-01-20", "proveedor": "Aceros Belgrano",
     "facturaId": "f1", "facturaNumero": "F-1", "montoFactura": "$100.000", "monto": "$30.000"},
]

VENTAS = [
    {"codigo": "V-1", "fecha": "2026-01-05", "productoId": "p1", "cliente": "Cliente A",
     "cantidad": "2", "precioUnit": "1000", "total": "2000"},
    {"codigo": " v-1 ", "fecha": "2026-01-05", "productoId": "p1", "cliente": "Cliente A",
     "cantidad": "2", "precioUnit": "1000", "total": "2000"},
    {"codigo": "V-2", "fecha": "2026-01-06", "productoId": "p1", "cliente": "Cliente B",
     "cantidad": "3", "precioUnit": "1000", "total": "3000"},
    {"codigo": "V-2", "fecha": "2026-01-06", "productoId": "p1", "cliente": "Cliente B",
     "cantidad": "9", "precioUnit": "1000", "total": "9000"},
    {"codigo": "V-3", "fecha": "2026-01-07", "productoId": "p1", "cliente": "Cliente C",
     "cantidad": "2", "precioUnit": "1000", "total": "20000"},
    {"codigo": "V-4", "fecha": "31/02/2025", "productoId": "p1", "cliente": "Cliente D",
     "cantidad": "1", "precioUnit": "1000", "total": "1000"},
    {"codigo": "V-5", "fecha": "2026-01-09", "productoId": "p1", "cliente": "Cliente E",
     "cantidad": "N/A", "precioUnit": "1000", "total": "4000"},
]

ORDENES = [
    {"id": "oc1", "numero": "OC-1", "fecha": "2026-01-02", "proveedor": "Herram. Cuyo",
     "productoId": "p1", "productoTexto": "", "cantidad": 10, "montoEstimado": "$10.000",
     "estado": "Pendiente de envio"},
]

MENSAJES = [
    {"id": "msg-reclamo-1", "fecha": "2026-03-01", "remitente": "Aceros Belgrano S.A.",
     "asunto": "Reclamo de pago - F-1", "cuerpo": "adeuda", "leido": False, "factura_id": "f1"},
    {"id": "msg-stock-1", "fecha": "2026-03-02", "remitente": "Sistema SIGProv",
     "asunto": "Stock bajo - COR-0003", "cuerpo": "reponer", "leido": False, "factura_id": None},
]

DATASETS = {
    "estado_cuenta": CUENTAS, "precios": PRECIOS, "catalogo": [], "facturas": FACTURAS,
    "comprobantes_pago": PAGOS, "ordenes_compra": ORDENES, "ventas": VENTAS, "mensajes": MENSAJES,
}


class FakePortal:
    def dataset(self, name):
        return DATASETS.get(name, [])

    def price_history(self, product_id):
        return []


@pytest.fixture
def result(tmp_path):
    store = Store.open(str(tmp_path / "ingest.db"))
    report = IngestRunner(store, FakePortal()).run("prueba", with_price_history=False)
    yield store, report
    store.close()


class TestSuppliers:
    def test_the_account_statements_are_the_real_list(self, result):
        store, _ = result
        assert store.suppliers.count() == 2

    def test_every_spelling_lands_on_the_same_company(self, result):
        store, _ = result
        invoices = store.invoices.listing()
        assert len({i["supplier_id"] for i in invoices}) == 1

    def test_a_spelling_is_remembered_so_it_never_gets_asked_twice(self, result):
        store, _ = result
        supplier = store.suppliers.by_slug("aceros-belgrano-sa")
        spellings = {a["spelling"] for a in store.supplier_aliases.for_supplier(supplier["id"])}
        assert "ACEROS BELGRANO" in spellings

    def test_the_portal_bot_is_not_taken_for_a_supplier(self, result):
        store, _ = result
        assert not any("SIGProv" in s["name"] for s in store.suppliers.all())


class TestCategories:
    def test_the_real_rubros_are_discovered_from_the_spellings(self, result):
        store, _ = result
        assert store.categories.count() == 1

    def test_a_product_with_no_rubro_is_placed_by_its_subrubro(self, result):
        store, _ = result
        assert store.products.without_category() == []


class TestInvoices:
    def test_the_balance_comes_from_the_payments(self, result):
        store, _ = result
        invoice = store.invoices.by_external("f1")
        balance = store.invoices.balance(invoice["id"])
        assert balance["paid_cents"] == 3000000
        assert balance["payment_state"] == "parcial"

    def test_a_receipt_the_portal_already_had_is_kept(self, result):
        store, _ = result
        assert store.receipts.for_invoice(store.invoices.by_external("f1")["id"]) is not None
        assert store.receipts.for_invoice(store.invoices.by_external("f2")["id"]) is None

    def test_every_due_date_lands_on_the_calendar(self, result):
        store, _ = result
        assert len(store.calendar.between("2026-01-01", "2026-12-31")) == 2


class TestSales:
    def by_code(self, store, code):
        return store.sales.by_code(code)

    def test_the_same_row_twice_becomes_one(self, result):
        store, _ = result
        assert len(self.by_code(store, "V-1")) == 1
        assert self.by_code(store, "V-1")[0]["status"] == "valida"

    def test_the_same_code_with_different_amounts_never_sums(self, result):
        store, _ = result
        assert all(sale["status"] == "conflicto" for sale in self.by_code(store, "V-2"))

    def test_a_total_that_does_not_add_up_is_left_out(self, result):
        store, _ = result
        assert self.by_code(store, "V-3")[0]["status"] == "rota"

    def test_an_impossible_date_is_left_out(self, result):
        store, _ = result
        sale = self.by_code(store, "V-4")[0]
        assert sale["status"] == "rota" and "fecha" in sale["status_note"]

    def test_a_missing_quantity_is_worked_out_not_guessed(self, result):
        store, _ = result
        sale = self.by_code(store, "V-5")[0]
        assert sale["status"] == "valida" and sale["quantity"] == 4
        assert sale["extra"]["reparaciones"]

    def test_only_the_trustworthy_ones_reach_the_monthly_total(self, result):
        store, _ = result
        months = store.sales.revenue_by_month()
        # V-1 collapsed to one row, and V-5 once its quantity was worked out. V-2 is in
        # conflict so neither of its rows counts, V-3 does not add up and V-4 has no date.
        assert sum(m["revenue_cents"] for m in months) == 200000 + 400000


class TestReviewQueue:
    def test_everything_undecided_is_waiting_for_a_person(self, result):
        store, _ = result
        kinds = {row["kind"] for row in store.reviews.summary()}
        assert kinds == {"venta-duplicada", "venta-rota"}

    def test_nothing_resolved_automatically_reaches_the_queue(self, result):
        store, _ = result
        assert not any(row["kind"] in ("proveedor", "rubro") for row in store.reviews.summary())


class TestMessages:
    def test_a_claim_is_linked_to_its_invoice(self, result):
        store, _ = result
        claim = next(m for m in store.messages.listing() if m["kind"] == "reclamo")
        assert claim["invoice_number"] == "F-1"

    def test_a_stock_warning_is_linked_to_its_product(self, result):
        store, _ = result
        warning = next(m for m in store.messages.listing() if m["kind"] == "stock")
        assert warning["product_code"] == "COR-0003"


class TestProvenance:
    def test_every_row_is_kept_exactly_as_it_arrived(self, result):
        store, _ = result
        kept = store.raw.history("facturas", "f1")
        assert kept and kept[0]["payload"]["monto"] == "$100.000"

    def test_the_pass_is_recorded_with_what_it_did(self, result):
        store, report = result
        run = store.runs.last_successful()
        assert run["status"] == "ok"
        assert run["summary"]["a_revision"] == report.for_review

    def test_running_twice_does_not_duplicate_anything(self, tmp_path):
        store = Store.open(str(tmp_path / "dos.db"))
        IngestRunner(store, FakePortal()).run("una", with_price_history=False)
        first = store.invoices.count(), store.sales.count(), store.payments.count()
        IngestRunner(store, FakePortal()).run("dos", with_price_history=False)
        assert (store.invoices.count(), store.sales.count(), store.payments.count()) == first
        store.close()
