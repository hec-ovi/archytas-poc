"""What can go wrong, told in the language the person reading it speaks.

Two kinds of failure. A `ToolError` is the system doing its job: the payment is bigger than
the balance, the supplier is not in the catalog. It carries a sentence a person understands
and the model gets it back as a result, not as a crash.

An `LlmError` is the model server not answering. That one is not the model's business, so it
travels up to whoever called `ask`.
"""

from __future__ import annotations


class AgentError(Exception):
    """Anything this box refuses to do."""


class ToolError(AgentError):
    """A tool that will not run, with the reason written for a person."""


class LlmError(AgentError):
    """The model server did not answer, or answered something that is not a chat completion."""
