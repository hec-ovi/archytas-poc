"""Cada rol ve las herramientas de sus secciones, y solo esas."""

from __future__ import annotations

from .conftest import FakeModel


def test_el_duenio_tiene_todas_las_herramientas(registry):
    assert registry.names_for("duenio") == registry.names


def test_ventas_no_ve_ninguna_herramienta_de_facturas_ni_proveedores(registry):
    tools = registry.names_for("ventas")

    assert tools == ("consultar_ventas", "consultar_productos")
    assert [schema["function"]["name"] for schema in registry.schemas("ventas")] == list(tools)


def test_compras_no_ve_las_ventas_pero_si_las_facturas(registry):
    tools = registry.names_for("compras")

    assert "consultar_ventas" not in tools
    assert "consultar_productos" not in tools
    assert "registrar_pago" in tools


def test_un_rol_desconocido_no_recibe_ninguna_herramienta(registry):
    assert registry.names_for("pasante") == ()


def test_ventas_no_puede_registrar_un_pago_aunque_lo_pida(registry, store):
    result = registry.dispatch(
        "registrar_pago", {"factura": "F-7797", "monto_centavos": 1000}, user="julian", rol="ventas"
    )

    assert result["error"] == (
        "El rol ventas no puede usar registrar_pago: es de la seccion facturas, que no le corresponde"
    )
    assert store.payments.for_invoice(store.invoices.get_by("number", "F-7797")["id"]) == []


def test_el_rechazo_por_rol_queda_en_el_rastro(agent_with):
    agent, model = agent_with(
        [
            FakeModel.calls("registrar_pago", factura="F-7797", monto_centavos=1000),
            FakeModel.says("Esa parte no te corresponde."),
        ]
    )

    answer = agent.ask("pagale 10 pesos a la F-7797", user="julian", rol="ventas")

    assert answer.steps[0].failed is True
    assert "no puede usar registrar_pago" in answer.steps[0].result["error"]
    assert [tool["function"]["name"] for tool in model.requests[0]["tools"]] == [
        "consultar_ventas", "consultar_productos",
    ]
