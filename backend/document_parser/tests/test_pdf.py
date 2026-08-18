"""PDFs with a text layer, through the entry point."""


def test_factura_en_pdf_de_texto(parser, fixtures):
    result = parser.parse(fixtures / "F-8411_Ferretera_del_Norte_S_R_L_.pdf")

    assert (result.kind, result.reader) == ("factura", "pdf-texto")
    assert result.fields["numero"].value == "F-8411"
    assert result.fields["proveedor"].value == "Ferretera del Norte S.R.L."
    assert result.fields["total"].value == 58123000  # $581.230 en centavos
    # 03/01/2025 se lee dia primero, con la confianza que deja el normalizer
    assert result.fields["fecha"].value == "2025-01-03"
    assert result.fields["fecha"].confidence == 0.93
    assert result.fields["numero"].source == "texto del PDF, linea 3"
    assert result.needs_review is False


def test_el_cuit_del_cliente_no_se_toma_como_del_proveedor(parser, fixtures):
    result = parser.parse(fixtures / "F-8411_Ferretera_del_Norte_S_R_L_.pdf")

    assert "cuit" not in result.fields
    flagged = {item.field: item.reason for item in result.unreadable}
    assert "cliente" in flagged["cuit"]


def test_recibo_con_dos_importes_no_elige_uno(parser, fixtures):
    result = parser.parse(fixtures / "Recibo_REC-1650.pdf")

    assert result.kind == "recibo"
    assert result.fields["numero"].value == "REC-1650"
    # el CUIT que sigue a "Pagado a" es el del proveedor, y su digito verificador no cierra
    assert result.fields["cuit"].value == "30-65432198-7"
    assert result.fields["cuit"].confidence < 0.9
    assert "verificador" in result.fields["cuit"].reason

    flagged = {item.field: item.reason for item in result.unreadable}
    assert "$468.392" in flagged["total"] and "$211.000" in flagged["total"]
    assert result.needs_review is True
