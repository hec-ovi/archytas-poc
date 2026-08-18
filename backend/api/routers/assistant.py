"""Asking the system in plain words.

The agent runs as whoever is logged in: it gets the tools that person's role allows and
nothing else. Marcela asking it to look at sales, or Julian asking it to register a payment,
gets the same answer as clicking there would: that is not their part of the system.

Every answer carries the trace of which tools ran with which arguments. A number without a
way to check where it came from is not usable in a business.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from agent import Agent
from agent.errors import AgentError

from ..deps import get_store
from ..security import current_user

router = APIRouter(prefix="/api/agente", tags=["agente"])


class Question(BaseModel):
    pregunta: str = Field(min_length=2)


@router.get("/herramientas")
def tools(request: Request, user: dict = Depends(current_user)) -> dict:
    agent: Agent = request.app.state.agent
    return {"rol": user["rol"], "herramientas": list(agent.tools(user["rol"]))}


@router.post("")
def ask(body: Question, request: Request, user: dict = Depends(current_user)) -> dict:
    agent: Agent = request.app.state.agent
    try:
        answer = agent.ask(body.pregunta, user=user["usuario"], rol=user["rol"])
    except AgentError as error:
        # the model being down is an outage, not a bad question: say so plainly
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"El asistente no esta disponible: {error}")
    return {"respuesta": answer.text, **answer.as_dict()}
