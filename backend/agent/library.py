"""Reading the prompts off disk.

No prompt and no tool description is written in Python. They live in `prompts/` as markdown
so anyone can open one, read it in plain Spanish and fix a wording without touching code.

The shape of a tool file: the text before the first heading describes the tool, and each
`## argumento` heading describes one argument.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import AgentError

PROMPTS_DIR = Path(__file__).with_name("prompts")
TOOLS_DIR = PROMPTS_DIR / "herramientas"


@dataclass(frozen=True)
class ToolText:
    """What a tool tells the model about itself."""

    description: str
    params: dict[str, str]

    def param(self, name: str) -> str:
        if name not in self.params:
            raise AgentError(f"falta la descripcion del argumento {name!r} en el prompt de la herramienta")
        return self.params[name]


class PromptLibrary:
    """Loads the markdown once and hands it out already parsed."""

    def __init__(self, folder: Path | None = None):
        self._folder = folder or PROMPTS_DIR
        self._cache: dict[str, str] = {}

    def system(self, **values: str) -> str:
        """The system prompt, with the placeholders written as `{nombre}` filled in."""
        text = self._read(self._folder / "sistema.md")
        for key, value in values.items():
            text = text.replace("{" + key + "}", str(value))
        return text

    def tool(self, name: str) -> ToolText:
        return _parse(self._read(self._folder / "herramientas" / f"{name}.md"))

    def _read(self, path: Path) -> str:
        key = str(path)
        if key not in self._cache:
            if not path.is_file():
                raise AgentError(f"falta el prompt {path.name}")
            self._cache[key] = path.read_text(encoding="utf-8").strip()
        return self._cache[key]


def _parse(text: str) -> ToolText:
    description: list[str] = []
    params: dict[str, list[str]] = {}
    current: str | None = None

    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            params[current] = []
        elif current is None:
            description.append(line)
        else:
            params[current].append(line)

    return ToolText(
        description=" ".join(" ".join(description).split()),
        params={name: " ".join(" ".join(lines).split()) for name, lines in params.items()},
    )
