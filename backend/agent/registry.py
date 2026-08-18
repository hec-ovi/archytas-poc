"""The catalog of tools: what exists, how it is described, and who runs it.

Everything the model can do passes through here, and nothing gets out as an exception. A
tool that refuses (the payment is bigger than the balance) and a tool that breaks both come
back as `{"error": "..."}` in Spanish, which the model reads as a result and can explain to
the person. A crash in a tool is not the model's problem to solve.

Two things never reach a tool from a chat message: an argument it did not declare, and the
name of the user. Who is asking is injected here, so nobody can be impersonated by writing
it into a question.
"""

from __future__ import annotations

from typing import Any

from store import Store

from .errors import ToolError
from .library import PromptLibrary
from .tools import (
    AjustarMonto,
    CargarDocumento,
    ConsultarCalendario,
    ConsultarDeudas,
    ConsultarFactura,
    ConsultarFacturas,
    ConsultarMensajes,
    ConsultarProductos,
    ConsultarProveedor,
    ConsultarRevision,
    ConsultarVentas,
    EmitirRecibo,
    InvoiceLookup,
    RegistrarPago,
    ResolverMensaje,
    ResolverRevision,
    SupplierLookup,
    Tool,
)


class ToolRegistry:
    """Builds every tool once, hands out their schemas, and dispatches a call by name."""

    def __init__(self, store: Store, prompts: PromptLibrary | None = None, tools: list[Tool] | None = None):
        self._store = store
        self._prompts = prompts or PromptLibrary()
        built = tools if tools is not None else self._build()
        self._tools: dict[str, Tool] = {tool.name: tool for tool in built}

    def _build(self) -> list[Tool]:
        prompts = self._prompts
        suppliers = SupplierLookup(self._store)
        invoices = InvoiceLookup(self._store, suppliers)
        return [
            CargarDocumento(self._store, prompts, suppliers),
            ConsultarProveedor(self._store, prompts, suppliers),
            ConsultarDeudas(self._store, prompts),
            ConsultarFacturas(self._store, prompts, suppliers),
            ConsultarFactura(self._store, prompts, invoices),
            ConsultarVentas(self._store, prompts),
            ConsultarProductos(self._store, prompts),
            ConsultarCalendario(self._store, prompts),
            ConsultarRevision(self._store, prompts),
            ConsultarMensajes(self._store, prompts),
            RegistrarPago(self._store, prompts, invoices),
            EmitirRecibo(self._store, prompts, invoices),
            AjustarMonto(self._store, prompts, invoices),
            ResolverRevision(self._store, prompts),
            ResolverMensaje(self._store, prompts),
        ]

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    @property
    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema for tool in self._tools.values()]

    def dispatch(self, name: str, arguments: dict[str, Any], user: str = "") -> Any:
        tool = self._tools.get(name)
        if tool is None:
            return {
                "error": f"No existe la herramienta {name!r}. Las que hay son: {', '.join(self.names)}"
            }

        kwargs = {key: value for key, value in arguments.items() if key in tool.argument_names}
        if tool.needs_user:
            kwargs["usuario"] = user

        try:
            return tool.run(**kwargs)
        except ToolError as error:
            return {"error": str(error)}
        except Exception as error:  # a broken tool is a readable answer, never a dead conversation
            return {"error": f"La herramienta {name} fallo: {error}"}
