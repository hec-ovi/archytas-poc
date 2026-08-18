"""The way in: a question in castellano, an answer plus the trace of what it did.

    Agent(store).ask("cuanto le debemos a Herramientas Cuyo?", user="marcela", rol="compras")

The role travels with the question. Each person only gets the tools of the sections their
role opens, so what the agent can do for someone is exactly what the app lets them do.

The agent decides nothing about the numbers. It picks which tool answers the question, the
tool reads the database, and the answer is written from what came back. That is why the trace
travels with the answer: whoever reads it can see the invoice, the balance and the payment
that produced every sentence.
"""

from __future__ import annotations

from datetime import date

from store import Store

from .client import ChatClient
from .library import PromptLibrary
from .registry import DEFAULT_ROLE, ToolRegistry
from .settings import AgentSettings
from .trace import Answer


class Agent:
    """One question at a time, with the whole toolbox available."""

    def __init__(self, store: Store, settings: AgentSettings | None = None,
                 client: ChatClient | None = None, registry: ToolRegistry | None = None,
                 prompts: PromptLibrary | None = None):
        self._store = store
        self._settings = settings or AgentSettings.from_env()
        self._prompts = prompts or PromptLibrary()
        self._registry = registry or ToolRegistry(store, self._prompts)
        self._client = client or ChatClient(self._settings)

    def ask(self, question: str, user: str = "", rol: str = DEFAULT_ROLE) -> Answer:
        system = self._prompts.system(
            hoy=date.today().isoformat(),
            usuario=user or "alguien",
            rol=rol,
            secciones=", ".join(self._store.users.sections_for(rol)) or "nada",
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ]
        return self._client.converse(
            messages,
            self._registry.schemas(rol),
            lambda name, arguments: self._registry.dispatch(name, arguments, user, rol),
        )

    def tools(self, rol: str = DEFAULT_ROLE) -> tuple[str, ...]:
        """The tools that role can use."""
        return self._registry.names_for(rol)

    def close(self) -> None:
        self._client.close()
