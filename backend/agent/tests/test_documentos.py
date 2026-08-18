"""Cargar un documento: sale una factura, o sale un pendiente. Nunca sale un proveedor nuevo."""

from __future__ import annotations

import openpyxl
import pytest

from conftest import days_from_today


@pytest.fixture
def factura_xlsx(tmp_path):
    """Una planilla de etiqueta y valor, como las que manda un proveedor."""

    def build(numero: str, proveedor: str) -> str:
        path = tmp_path / f"{numero}.xlsx"
        book = openpyxl.Workbook()
        sheet = book.active
        for row in [
            ("Numero", numero),
            ("Fecha", days_from_today(-2)),
            ("Vencimiento", days_from_today(28)),
            ("Proveedor", proveedor),
            ("Total", "$1.234.500,00"),
        ]:
            sheet.append(row)
        book.save(path)
        return str(path)

    return build


def _document(store, path: str, filename: str) -> int:
    return store.documents.save(
        {"kind": "factura", "filename": filename, "stored_path": path,
         "content_hash": filename, "uploaded_by": "marcela"}
    )


def test_un_documento_de_un_proveedor_conocido_se_convierte_en_factura(registry, store, factura_xlsx):
    document_id = _document(store, factura_xlsx("F-9001", "Herramientas Cuyo S.R.L."), "F-9001.xlsx")

    result = registry.dispatch("cargar_documento", {"documento_id": document_id}, user="marcela")

    assert result["cargadas"] == 1
    factura = result["resultados"][0]["factura"]
    assert factura["numero"] == "F-9001"
    assert factura["proveedor"] == "Herramientas Cuyo SRL"
    assert factura["total_centavos"] == 123450000
    assert store.documents.get(document_id)["status"] == "aplicado"
    assert store.calendar.for_invoice(factura["id"])["on_date"] == days_from_today(28)


def test_un_proveedor_que_no_esta_en_el_catalogo_deja_el_documento_en_revision(registry, store, factura_xlsx):
    document_id = _document(store, factura_xlsx("F-9002", "Ferreteria Marte SA"), "F-9002.xlsx")

    result = registry.dispatch("cargar_documento", {"documento_id": document_id}, user="marcela")

    assert result["a_revision"] == 1
    assert store.suppliers.count() == 2
    assert store.invoices.get_by("number", "F-9002") is None
    assert store.documents.get(document_id)["status"] == "en-revision"
    assert [item["kind"] for item in store.reviews.pending()].count("proveedor") == 2


def test_un_documento_ya_aplicado_no_carga_la_factura_de_nuevo(registry, store, factura_xlsx):
    document_id = _document(store, factura_xlsx("F-9003", "Herramientas Cuyo SRL"), "F-9003.xlsx")
    registry.dispatch("cargar_documento", {"documento_id": document_id}, user="marcela")

    result = registry.dispatch("cargar_documento", {"documento_id": document_id}, user="marcela")

    assert result["cargado"] is False
    assert store.invoices.count("number = 'F-9003'") == 1


def test_un_documento_sin_archivo_lo_dice(registry, store):
    document_id = store.documents.save(
        {"kind": "factura", "filename": "perdida.pdf", "content_hash": "x", "uploaded_by": "marcela"}
    )

    result = registry.dispatch("cargar_documento", {"documento_id": document_id}, user="marcela")

    assert result["error"] == f"El documento {document_id} no tiene archivo guardado"
