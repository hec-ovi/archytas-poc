"""Las consultas contestan lo que el contrato promete, y no tocan nada."""

from __future__ import annotations

from .conftest import days_from_today


def test_la_posicion_de_un_proveedor_trae_la_deuda_calculada(registry):
    result = registry.dispatch("consultar_proveedor", {"proveedor": "Herramientas Cuyo"})

    assert result["proveedor"] == "Herramientas Cuyo SRL"
    assert result["deuda_centavos"] == 70000000
    assert result["deuda"] == "$700.000,00"


def test_un_proveedor_que_no_existe_vuelve_como_error_con_los_del_catalogo(registry):
    result = registry.dispatch("consultar_proveedor", {"proveedor": "Ferreteria Marte"})

    assert "No pude identificar" in result["error"]
    assert "Herramientas Cuyo SRL" in result["error"]


def test_las_deudas_suman_todos_los_proveedores(registry):
    result = registry.dispatch("consultar_deudas", {})

    assert result["deuda_total_centavos"] == 76000000
    assert [row["proveedor"] for row in result["proveedores"]][0] == "Herramientas Cuyo SRL"


def test_las_facturas_se_filtran_por_estado(registry):
    parcial = registry.dispatch("consultar_facturas", {"estado": "parcial"})

    assert [row["numero"] for row in parcial["facturas"]] == ["F-2000"]
    assert parcial["facturas"][0]["saldo_centavos"] == 6000000


def test_las_facturas_se_filtran_por_proveedor(registry):
    result = registry.dispatch("consultar_facturas", {"proveedor": "Aceros Belgrano"})

    assert [row["numero"] for row in result["facturas"]] == ["F-2000"]


def test_una_factura_viene_con_sus_pagos_y_su_recibo(registry):
    result = registry.dispatch("consultar_factura", {"factura": "F-2000"})

    assert result["factura"]["estado_pago"] == "parcial"
    assert result["pagos"][0]["monto_centavos"] == 4000000
    assert result["recibo"] is None


def test_una_factura_que_no_existe_lo_dice(registry):
    assert registry.dispatch("consultar_factura", {"factura": "F-0"})["error"] == "No encontre la factura F-0"


def test_las_ventas_salen_por_mes(registry):
    result = registry.dispatch("consultar_ventas", {})

    assert result["facturado_total_centavos"] == 9000000
    assert result["meses"][0]["ventas"] == 1


def test_los_productos_se_filtran_por_stock(registry):
    result = registry.dispatch("consultar_productos", {"stock_maximo": 2})

    assert result["productos"][0]["codigo"] == "COR-0001"
    assert result["productos"][0]["precio"] == "$45.000,00"


def test_el_calendario_devuelve_los_vencimientos_del_periodo(registry):
    result = registry.dispatch(
        "consultar_calendario", {"desde": days_from_today(0), "hasta": days_from_today(12)}
    )

    assert [row["factura"] for row in result["vencimientos"]] == ["F-7797"]


def test_una_fecha_ilegible_no_se_adivina(registry):
    result = registry.dispatch("consultar_calendario", {"desde": "cuando sea", "hasta": "manana"})

    assert "No puedo leer la fecha desde" in result["error"]


def test_la_cola_de_revision_trae_los_pendientes_con_su_id(registry):
    result = registry.dispatch("consultar_revision", {"tipo": "proveedor"})

    assert result["cantidad"] == 1
    assert result["pendientes"][0]["titulo"] == "Proveedor sin identificar"


def test_la_bandeja_trae_los_mensajes_abiertos(registry):
    result = registry.dispatch("consultar_mensajes", {})

    assert result["abiertos"] == 1
    assert result["mensajes"][0]["asunto"] == "Reclamo de pago"
