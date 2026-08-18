"""agent: el LLM con herramientas, para lo que no se puede resolver con una regla.

    from agent import Agent
    respuesta = Agent(store).ask("cuanto le debemos a Cuyo?", user="marcela", rol="compras")
    respuesta.text, respuesta.as_dict()["pasos"]
"""

from .client import ChatClient
from .conversation import Agent
from .errors import AgentError, LlmError, ToolError
from .library import PromptLibrary
from .registry import DEFAULT_ROLE, ToolRegistry
from .settings import AgentSettings
from .trace import Answer, ToolStep

__all__ = [
    "Agent",
    "AgentError",
    "AgentSettings",
    "Answer",
    "ChatClient",
    "DEFAULT_ROLE",
    "LlmError",
    "PromptLibrary",
    "ToolError",
    "ToolRegistry",
    "ToolStep",
]
