"""La entrada de la caja: que enruta, que rechaza, y la invariante de los campos."""

import pytest

from document_parser import INVOICE_FIELDS, UnreadableFile, UnsupportedFormat
from conftest import FIXTURES


def test_el_tipo_se_decide_por_los_bytes_no_por_la_extension(parser, fixtures, tmp_path):
    disfrazado = tmp_path / "factura.xlsx"
    disfrazado.write_bytes((fixtures / "F-8411_Ferretera_del_Norte_S_R_L_.pdf").read_bytes())

    result = parser.parse(disfrazado)

    assert result.reader == "pdf-texto"
    assert result.fields["numero"].value == "F-8411"


def test_formato_no_soportado(parser, tmp_path):
    otro = tmp_path / "notas.txt"
    otro.write_text("esto no es una factura")

    with pytest.raises(UnsupportedFormat):
        parser.parse(otro)


def test_archivo_ilegible(parser, tmp_path):
    with pytest.raises(UnreadableFile):
        parser.parse(tmp_path / "no-esta.pdf")

    vacio = tmp_path / "vacio.pdf"
    vacio.write_bytes(b"")
    with pytest.raises(UnreadableFile):
        parser.parse(vacio)


@pytest.mark.parametrize("name", sorted(path.name for path in FIXTURES.iterdir()))
def test_cada_campo_esta_leido_o_marcado(parser, fixtures, name):
    """La invariante de la caja: ningun campo se pierde en silencio."""
    result = parser.parse(fixtures / name)

    del_documento = {item.field for item in result.notes}
    for record in result.records:
        marcados = {item.field for item in record.unreadable}
        assert set(record.fields) & marcados == set()
        assert set(INVOICE_FIELDS) <= set(record.fields) | marcados | del_documento
