"""What the store promises, against a real temporary database.

The interesting promises are all in the views: a balance that comes from the payments rather
than from a stored number, a supplier position that adds those balances up, and sales that
stay out of every total when they cannot be trusted.
"""

import pytest

from store import Store, verify_password


@pytest.fixture
def store(tmp_path):
    handle = Store.open(str(tmp_path / "prueba.db"))
    yield handle
    handle.close()


@pytest.fixture
def loaded(store):
    supplier = store.suppliers.save({"slug": "aceros", "name": "Aceros Belgrano SA", "cuit": "30-70918273-4", "terms_days": 45})
    invoice = store.invoices.save({"number": "F-1", "supplier_id": supplier, "issued_on": "2026-01-01",
                                   "due_on": "2026-02-15", "amount_cents": 100000})
    return {"supplier": supplier, "invoice": invoice}


class TestBootstrap:
    def test_creates_the_three_people_the_client_named(self, store):
        assert {u["username"] for u in store.users.listing()} == {"marcela", "julian", "duenio"}

    def test_each_one_only_gets_their_own_sections(self, store):
        assert "ventas" not in store.users.sections_for("compras")
        assert "proveedores" not in store.users.sections_for("ventas")
        assert "proveedores" in store.users.sections_for("duenio")

    def test_passwords_are_hashed_not_stored(self, store):
        user = store.users.by_username("marcela")
        assert user["password_hash"] != "cordillera2026"
        assert verify_password(user["password_hash"], "cordillera2026")

    def test_opening_an_existing_database_changes_nothing(self, tmp_path):
        path = str(tmp_path / "otra.db")
        Store.open(path).close()
        again = Store.open(path)
        assert len(again.users.listing()) == 3
        again.close()


class TestInvoiceBalance:
    def test_an_invoice_with_no_payments_is_untouched(self, store, loaded):
        balance = store.invoices.balance(loaded["invoice"])
        assert balance["paid_cents"] == 0
        assert balance["balance_cents"] == 100000
        assert balance["payment_state"] == "impaga"

    def test_two_partial_payments_add_up(self, store, loaded):
        for amount in (30000, 25000):
            store.payments.insert({"reference": "x", "invoice_id": loaded["invoice"], "amount_cents": amount})
        balance = store.invoices.balance(loaded["invoice"])
        assert balance["paid_cents"] == 55000
        assert balance["payment_state"] == "parcial"

    def test_paying_it_all_settles_it(self, store, loaded):
        store.payments.insert({"reference": "x", "invoice_id": loaded["invoice"], "amount_cents": 100000})
        assert store.invoices.balance(loaded["invoice"])["payment_state"] == "saldada"

    def test_the_receipt_shows_up_on_the_invoice(self, store, loaded):
        assert store.invoices.balance(loaded["invoice"])["has_receipt"] == 0
        store.receipts.save({"number": "REC-F-1", "invoice_id": loaded["invoice"], "issued_on": "2026-02-01"})
        assert store.invoices.balance(loaded["invoice"])["has_receipt"] == 1


class TestSupplierPosition:
    def test_adds_up_what_we_owe(self, store, loaded):
        store.payments.insert({"reference": "x", "invoice_id": loaded["invoice"], "amount_cents": 40000})
        position = store.suppliers.position(loaded["supplier"])
        assert position["purchased_cents"] == 100000
        assert position["paid_cents"] == 40000
        assert position["owed_cents"] == 60000

    def test_terms_compliance_compares_the_due_date_to_the_agreement(self, store, loaded):
        # the invoice above runs 45 days, which is exactly the agreed term
        row = next(r for r in store.suppliers.with_terms_compliance() if r["supplier_id"] == loaded["supplier"])
        assert row["invoice_count"] == 1 and row["on_terms_count"] == 1

        store.invoices.save({"number": "F-2", "supplier_id": loaded["supplier"], "issued_on": "2026-01-01",
                             "due_on": "2026-03-30", "amount_cents": 5000})
        row = next(r for r in store.suppliers.with_terms_compliance() if r["supplier_id"] == loaded["supplier"])
        assert row["invoice_count"] == 2 and row["on_terms_count"] == 1


class TestSales:
    def seed(self, store, status, code="V-1", total=1000):
        return store.sales.save({"code": code, "sold_on": "2026-01-05", "quantity": 1, "unit_cents": total,
                                 "total_cents": total, "status": status, "row_hash": f"{code}-{status}-{total}"})

    def test_only_trustworthy_sales_reach_a_total(self, store):
        self.seed(store, "valida", "V-1", 1000)
        self.seed(store, "duplicada", "V-2", 5000)
        self.seed(store, "conflicto", "V-3", 7000)
        self.seed(store, "rota", "V-4", 9000)
        months = store.sales.revenue_by_month()
        assert len(months) == 1 and months[0]["revenue_cents"] == 1000

    def test_what_was_left_out_is_listed_with_its_reason(self, store):
        self.seed(store, "valida", "V-1")
        broken = self.seed(store, "rota", "V-4", 9000)
        store.sales.flag(broken, "rota", "el total no cierra con cantidad por precio")
        excluded = store.sales.excluded()
        assert len(excluded) == 1
        assert "no cierra" in excluded[0]["status_note"]


class TestFlexibleColumns:
    def test_extra_properties_need_no_migration(self, store):
        supplier_id = store.suppliers.save({"slug": "x", "name": "X", "extra": {"contacto": "Ana", "prioridad": 3}})
        assert store.suppliers.get(supplier_id)["extra"]["contacto"] == "Ana"

    def test_a_document_type_nobody_planned_for_still_fits(self, store):
        doc_id = store.documents.save({"kind": "remito", "filename": "r.pdf", "content_hash": "abc",
                                       "parsed": {"bultos": 12, "transportista": "Andreani"}})
        assert store.documents.get(doc_id)["parsed"]["bultos"] == 12


class TestSettings:
    def test_a_setting_can_be_changed_without_touching_code(self, store):
        store.settings.set_value("aviso_dias_antes", 15, user="duenio")
        assert store.settings.get_value("aviso_dias_antes") == 15
