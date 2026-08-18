"""Everything the server reads from the environment.

Defaults are the ones that make a fresh checkout run: the portal credentials the client was
given, the llama.cpp server on this machine, and a data directory that is created on start.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


# where the UI runs in development. In the container both sides are the same origin, so this
# only matters when the two are served from different ports.
DEFAULT_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


def _origins(raw: str) -> tuple[str, ...]:
    """Origins allowed to call the api, from a comma separated list."""
    listed = tuple(origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip())
    return listed or DEFAULT_ORIGINS


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_path: Path
    portal_base_url: str
    portal_user: str
    portal_password: str
    secret_key: str
    llm_base_url: str
    llm_model: str
    llm_api_key: str
    cors_origins: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = Path(os.getenv("CORDILLERA_DATA_DIR", "./data")).resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            data_dir=data_dir,
            database_path=data_dir / "cordillera.db",
            portal_base_url=os.getenv("PORTAL_BASE_URL", "https://prueba-tecnica-portal.vercel.app"),
            portal_user=os.getenv("PORTAL_USER", ""),
            portal_password=os.getenv("PORTAL_PASSWORD", ""),
            secret_key=os.getenv("SECRET_KEY", "cordillera-cambiar-esta-clave-en-produccion"),
            llm_base_url=os.getenv("LLM_BASE_URL", "http://host.docker.internal:8080/v1"),
            llm_model=os.getenv("LLM_MODEL", "gemma-4-26b-a4b-qat-q4"),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            cors_origins=_origins(os.getenv("CORS_ORIGINS", "")),
        )
