"""Planillas: una factura sola, una tabla de muchas filas, y las que no son facturas."""

import openpyxl


def test_planilla_de_una_factura(parser, fixtures):
    result = parser.parse(fixtures / "F-7797_Aceros_Belgrano_SA.xlsx")

    assert (result.kind, result.reader) == ("factura", "xlsx")
    assert len(result.records) == 1
    assert result.fields["numero"].value == "F-7797"
    assert result.fields["proveedor"].value == "Aceros Belgrano SA"
    assert result.fields["total"].value == 22337600
    assert result.fields["fecha"].value == "2026-05-03"
    assert result.fields["numero"].source == "celda B4"


def test_planilla_de_muchas_filas(parser, fixtures):
    result = parser.parse(fixtures / "Comprobantes_de_Pago.xlsx")

    assert result.kind == "tabla"
    assert len(result.records) == 82
    first = result.records[0]
    assert first.index == 2
    assert first.fields["numero"].value == "REC-1650"
    assert first.fields["proveedor"].value == "Ferretera del Norte SRL"
    assert first.fields["fecha"].value == "2026-08-15"

    # dos columnas de importe: ninguna se elige sola
    notes = {item.field: item.reason for item in result.notes}
    assert "Importe factura" in notes["total"] and "Importe pagado" in notes["total"]
    assert "total" not in first.fields


def test_encabezado_corrido_y_filas_vacias(parser, tmp_path):
    book = openpyxl.Workbook()
    sheet = book.active
    sheet["A1"] = "LISTADO DE FACTURAS"
    sheet["A4"], sheet["B4"], sheet["C4"], sheet["D4"] = "Nro.", "Fecha", "Proveedor", "Importe"
    sheet["A5"], sheet["B5"], sheet["C5"], sheet["D5"] = "F-1001", "05/03/2026", "Aceros Belgrano SA", "$1.234,56"
    sheet["A7"], sheet["B7"], sheet["C7"] = "F-1002", "2026-03-06", "Ferretera del Norte SRL"
    path = tmp_path / "facturas.xlsx"
    book.save(path)

    result = parser.parse(path)

    assert result.kind == "tabla"
    assert [record.index for record in result.records] == [5, 7]
    assert result.records[0].fields["fecha"].value == "2026-03-05"
    assert result.records[0].fields["total"].value == 123456
    # la celda vacia se informa, no se completa
    flagged = {item.field: item.reason for item in result.records[1].unreadable}
    assert "total" in flagged


def test_planilla_que_no_es_de_facturas(parser, fixtures):
    result = parser.parse(fixtures / "Cuenta_aceros-belgrano-sa.xlsx")

    assert result.kind == "desconocido"
    assert result.records[0].fields == {}
    assert any("no tiene columnas ni etiquetas" in item.reason for item in result.notes)
