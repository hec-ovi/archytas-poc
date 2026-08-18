"""agent: el LLM con herramientas, para lo que no se puede resolver con una regla.

    from agent import Agent
    respuesta = Agent(store).ask("cuanto le debemos a Herramientas Cuyo?", user="marcela")
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
    "DEFAULT_ROLE",
    "AgentError",
    "AgentSettings",
    "Answer",
    "ChatClient",
    "LlmError",
    "PromptLibrary",
    "ToolError",
    "ToolRegistry",
    "ToolStep",
]
