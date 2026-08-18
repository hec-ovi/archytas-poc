"""Talking to the model, and running the tools it asks for.

An OpenAI-compatible chat endpoint over plain `httpx`: llama.cpp on this machine, or
OpenRouter, or anything else that speaks the same shape. Two environment variables decide
which, and nothing in this file knows the difference.

The loop is the whole point. The model answers either with words or with a list of tool
calls. Words end the conversation; tool calls get run, their results go back in, and the
model gets another turn. A question that never settles stops at the turn limit with the
trace of everything it tried, because a loop with no floor is how a local model eats an
afternoon.

No output length is ever sent. What the model writes is steered by the prompt.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import httpx

from .errors import LlmError
from .settings import AgentSettings
from .trace import Answer, ToolStep

Dispatch = Callable[[str, dict[str, Any]], Any]


class ChatClient:
    """One conversation at a time: send, run what it asks for, send again."""

    def __init__(self, settings: AgentSettings | None = None, http: httpx.Client | None = None):
        self._settings = settings or AgentSettings.from_env()
        self._http = http or httpx.Client(timeout=self._settings.timeout)

    def converse(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], dispatch: Dispatch) -> Answer:
        history = list(messages)
        steps: list[ToolStep] = []

        for turn in range(1, self._settings.max_turns + 1):
            reply = self.complete(history, tools)
            calls = reply.get("tool_calls") or []

            if not calls:
                return Answer(text=reply.get("content") or "", steps=tuple(steps), turns=turn)

            history.append({"role": "assistant", "content": reply.get("content") or "", "tool_calls": calls})
            for call in calls:
                step = self._run(call, dispatch)
                steps.append(step)
                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "name": step.tool,
                        "content": json.dumps(step.result, ensure_ascii=False, default=str),
                    }
                )

        return Answer(
            text=(
                f"Corte despues de {self._settings.max_turns} vueltas de herramientas sin llegar a una "
                f"respuesta. Abajo queda lo que consulte."
            ),
            steps=tuple(steps),
            turns=self._settings.max_turns,
            complete=False,
        )

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """One round trip. Returns the assistant message as the server sent it."""
        payload: dict[str, Any] = {
            "model": self._settings.model,
            "messages": messages,
            "temperature": self._settings.temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            response = self._http.post(
                self._settings.completions_url, json=payload, headers=self._settings.headers
            )
        except httpx.HTTPError as error:
            raise LlmError(f"no se pudo hablar con el modelo en {self._settings.completions_url}: {error}") from error

        if response.status_code >= 400:
            raise LlmError(f"el modelo respondio {response.status_code}: {response.text[:400]}")

        try:
            return response.json()["choices"][0]["message"]
        except (ValueError, KeyError, IndexError) as error:
            raise LlmError(f"el modelo respondio algo que no es un chat completion: {response.text[:400]}") from error

    def close(self) -> None:
        self._http.close()

    @staticmethod
    def _run(call: dict[str, Any], dispatch: Dispatch) -> ToolStep:
        function = call.get("function") or {}
        name = function.get("name", "")
        raw = function.get("arguments") or "{}"

        try:
            arguments = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except (ValueError, TypeError):
            return ToolStep(name, {"crudo": raw}, {"error": f"No entendi los argumentos de {name}: {raw!r}"})
        if not isinstance(arguments, dict):
            return ToolStep(name, {"crudo": raw}, {"error": f"Los argumentos de {name} tienen que ser un objeto"})

        return ToolStep(name, arguments, dispatch(name, arguments))
