"""El registro: describe las herramientas y nunca deja escapar una excepcion."""

from __future__ import annotations


def test_toda_herramienta_se_describe_con_su_prompt(registry):
    for schema in registry.schemas:
        function = schema["function"]
        assert function["description"].strip()
        for name, parameter in function["parameters"]["properties"].items():
            assert parameter["description"].strip(), f"{function['name']}.{name} sin descripcion"


def test_una_herramienta_que_no_existe_vuelve_como_texto_legible(registry):
    result = registry.dispatch("borrar_todo", {})

    assert result["error"].startswith("No existe la herramienta 'borrar_todo'")
    assert "consultar_deudas" in result["error"]


def test_un_argumento_que_la_herramienta_no_declara_se_ignora(registry):
    result = registry.dispatch("consultar_deudas", {"moneda": "USD"})

    assert "deuda_total_centavos" in result


def test_el_usuario_no_se_puede_falsificar_desde_los_argumentos(registry, store):
    result = registry.dispatch(
        "registrar_pago",
        {"factura": "F-7797", "monto_centavos": 1000, "usuario": "el duenio"},
        user="marcela",
    )

    assert store.payments.for_invoice(result["factura"]["id"])[0]["created_by"] == "marcela"
