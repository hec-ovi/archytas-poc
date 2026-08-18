"""The way in: a question in castellano, an answer plus the trace of what it did.

    Agent(store).ask("cuanto le debemos a Herramientas Cuyo?", user="marcela")

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
from .registry import ToolRegistry
from .settings import AgentSettings
from .trace import Answer


class Agent:
    """One question at a time, with the whole toolbox available."""

    def __init__(self, store: Store, settings: AgentSettings | None = None,
                 client: ChatClient | None = None, registry: ToolRegistry | None = None,
                 prompts: PromptLibrary | None = None):
        self._settings = settings or AgentSettings.from_env()
        self._prompts = prompts or PromptLibrary()
        self._registry = registry or ToolRegistry(store, self._prompts)
        self._client = client or ChatClient(self._settings)

    def ask(self, question: str, user: str = "") -> Answer:
        messages = [
            {"role": "system", "content": self._prompts.system(hoy=date.today().isoformat(), usuario=user or "alguien")},
            {"role": "user", "content": question},
        ]
        return self._client.converse(
            messages,
            self._registry.schemas,
            lambda name, arguments: self._registry.dispatch(name, arguments, user),
        )

    @property
    def tools(self) -> tuple[str, ...]:
        return self._registry.names

    def close(self) -> None:
        self._client.close()
