"""Los cambios: se aplican con nombre y apellido, o se rechazan con el motivo."""

from __future__ import annotations

from conftest import days_from_today


def test_un_pago_baja_el_saldo_y_queda_a_nombre_de_quien_lo_pidio(registry, store):
    result = registry.dispatch(
        "registrar_pago", {"factura": "F-7797", "monto_centavos": 20000000}, user="marcela"
    )

    assert result["factura"]["saldo_centavos"] == 30000000
    assert result["factura"]["estado_pago"] == "parcial"
    assert store.payments.for_invoice(result["factura"]["id"])[0]["created_by"] == "marcela"


def test_un_pago_mayor_al_saldo_se_rechaza(registry, store):
    result = registry.dispatch(
        "registrar_pago", {"factura": "F-2000", "monto_centavos": 9000000}, user="marcela"
    )

    assert result["error"] == (
        "El pago de $90.000,00 supera el saldo de $60.000,00 de la factura F-2000"
    )
    assert len(store.payments.for_invoice(store.invoices.get_by("number", "F-2000")["id"])) == 1


def test_un_pago_sin_saber_quien_lo_pide_no_se_registra(registry):
    result = registry.dispatch("registrar_pago", {"factura": "F-7797", "monto_centavos": 100})

    assert result["error"] == "No puedo registrar un cambio sin saber quien lo pide"


def test_un_monto_en_palabras_no_se_interpreta(registry):
    result = registry.dispatch(
        "registrar_pago", {"factura": "F-7797", "monto_centavos": "200 mil"}, user="marcela"
    )

    assert "centavos enteros" in result["error"]


def test_el_recibo_se_emite_hasta_el_vencimiento(registry, store):
    result = registry.dispatch("emitir_recibo", {"factura": "F-7797"}, user="marcela")

    assert result["emitido"] is True
    assert result["recibo"]["numero"] == "REC-F-7797"
    assert result["recibo"]["emitido_por"] == "marcela"


def test_el_recibo_de_una_factura_vencida_se_rechaza(registry, store):
    result = registry.dispatch("emitir_recibo", {"factura": "F-1000"}, user="marcela")

    assert "vencio el" in result["error"]
    assert store.receipts.for_invoice(store.invoices.get_by("number", "F-1000")["id"]) is None


def test_el_recibo_no_se_emite_dos_veces(registry):
    registry.dispatch("emitir_recibo", {"factura": "F-7797"}, user="marcela")
    result = registry.dispatch("emitir_recibo", {"factura": "F-7797"}, user="duenio")

    assert result["emitido"] is False
    assert result["recibo"]["emitido_por"] == "marcela"


def test_ajustar_un_monto_guarda_el_motivo_y_quien_lo_hizo(registry, store):
    result = registry.dispatch(
        "ajustar_monto",
        {"factura": "F-7797", "monto_centavos": 45000000, "motivo": "el remito dice otra cosa"},
        user="duenio",
    )

    assert result["factura"]["total_centavos"] == 45000000
    ajuste = store.invoices.get(result["factura"]["id"])["extra"]["ajustes"][0]
    assert ajuste == {
        "de": 50000000, "a": 45000000, "motivo": "el remito dice otra cosa",
        "por": "duenio", "cuando": days_from_today(0), "origen": "agente",
    }


def test_ajustar_sin_motivo_se_rechaza(registry):
    result = registry.dispatch(
        "ajustar_monto", {"factura": "F-7797", "monto_centavos": 1, "motivo": ""}, user="duenio"
    )

    assert result["error"] == "Hace falta un motivo para cambiar el monto de una factura"


def test_resolver_un_pendiente_de_proveedor_aprende_la_escritura(registry, store):
    pendiente = store.reviews.pending("proveedor")[0]

    result = registry.dispatch(
        "resolver_revision",
        {"pendiente_id": pendiente["id"], "proveedor_slug": "herramientas-cuyo-srl"},
        user="marcela",
    )

    assert result["pendientes"] == 0
    assert store.supplier_aliases.resolve("Herram. Cuyo")["method"] == "persona"


def test_un_proveedor_que_no_esta_en_el_catalogo_no_se_crea(registry, store):
    pendiente = store.reviews.pending("proveedor")[0]

    result = registry.dispatch(
        "resolver_revision",
        {"pendiente_id": pendiente["id"], "proveedor_slug": "ferreteria-marte"},
        user="marcela",
    )

    assert "No existe el proveedor" in result["error"]
    assert store.suppliers.by_slug("ferreteria-marte") is None
    assert store.reviews.pending_count() == 1


def test_cerrar_un_mensaje_lo_saca_de_la_bandeja(registry, store):
    mensaje = store.messages.listing(only_open=True)[0]

    result = registry.dispatch(
        "resolver_mensaje", {"mensaje_id": mensaje["id"], "nota": "se pago hoy"}, user="marcela"
    )

    assert result["abiertos"] == 0
    assert store.messages.get(mensaje["id"])["resolved_by"] == "marcela"
