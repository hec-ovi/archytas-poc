"""La vuelta completa: el modelo pide una herramienta, la corre, y contesta con el rastro."""

from __future__ import annotations

from .conftest import FakeModel


def test_una_pregunta_usa_la_herramienta_y_contesta_con_el_rastro(agent_with):
    agent, _ = agent_with(
        [
            FakeModel.calls("consultar_proveedor", proveedor="Herramientas Cuyo"),
            FakeModel.says("Le debemos $700.000,00 a Herramientas Cuyo SRL."),
        ]
    )

    answer = agent.ask("cuanto le debemos a Herramientas Cuyo?", user="marcela")

    assert answer.text == "Le debemos $700.000,00 a Herramientas Cuyo SRL."
    assert answer.tools_used == ("consultar_proveedor",)
    assert answer.steps[0].result["deuda_centavos"] == 70000000
    assert answer.as_dict()["pasos"][0]["argumentos"] == {"proveedor": "Herramientas Cuyo"}


def test_el_resultado_de_la_herramienta_vuelve_al_modelo(agent_with):
    agent, model = agent_with(
        [FakeModel.calls("consultar_deudas"), FakeModel.says("Listo.")]
    )

    agent.ask("cuanto debemos?", user="marcela")

    ultimo = model.requests[-1]["messages"][-1]
    assert ultimo["role"] == "tool"
    assert "deuda_total_centavos" in ultimo["content"]


def test_nunca_se_manda_un_limite_de_salida(agent_with):
    agent, model = agent_with([FakeModel.says("Hola.")])

    agent.ask("hola", user="marcela")

    assert "max_tokens" not in model.requests[0]


def test_un_modelo_que_no_para_de_pedir_herramientas_corta_solo(agent_with):
    agent, _ = agent_with([FakeModel.calls("consultar_deudas")], max_turns=3)

    answer = agent.ask("cuanto debemos?", user="marcela")

    assert answer.complete is False
    assert answer.turns == 3
    assert len(answer.steps) == 3


def test_una_herramienta_que_no_existe_no_corta_la_conversacion(agent_with):
    agent, _ = agent_with(
        [FakeModel.calls("borrar_todo"), FakeModel.says("No puedo hacer eso.")]
    )

    answer = agent.ask("borra todo", user="marcela")

    assert answer.text == "No puedo hacer eso."
    assert answer.steps[0].failed is True


def test_el_prompt_del_sistema_llega_completo(agent_with):
    agent, model = agent_with([FakeModel.says("Hola.")])

    agent.ask("hola", user="julian", rol="ventas")

    system = model.requests[0]["messages"][0]["content"]
    assert "julian" in system and "ventas" in system
    assert "{" not in system, "quedo un hueco sin completar en el prompt"
