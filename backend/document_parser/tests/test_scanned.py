"""PDF escaneado: lo que pasa con tesseract y lo que pasa sin el."""

import pytest

from document_parser.ocr import TesseractEngine

SCAN = "F-9936_Electrical_Supply_Argentina.pdf"


def test_sin_tesseract_el_resultado_lo_dice(parser, fixtures, tmp_path, monkeypatch):
    monkeypatch.setenv("TESSERACT_BIN", str(tmp_path / "tesseract-que-no-existe"))

    result = parser.parse(fixtures / SCAN)

    assert result.reader == "ocr"
    assert result.text == ""
    assert any("tesseract no esta instalado" in item.reason for item in result.notes)
    # ningun campo se inventa: los seis vuelven marcados
    assert result.records[0].fields == {}
    assert len(result.records[0].unreadable) == 6
    assert result.needs_review is True


@pytest.mark.skipif(not TesseractEngine().available, reason="tesseract no esta en esta maquina")
def test_con_tesseract_lee_la_factura_escaneada(parser, fixtures):
    result = parser.parse(fixtures / SCAN)

    assert (result.kind, result.reader) == ("factura", "ocr")
    assert result.text.strip()
    assert result.fields["numero"].value == "F-9936"
    # todo lo que sale de OCR viaja con el descuento
    assert all(field.confidence <= 0.95 for field in result.fields.values())
