from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping


@dataclass(frozen=True)
class RuntimeConfig:
    host: str = "127.0.0.1"
    port: int = 8080
    postgres_dsn: str = "<set-me>"
    opensearch_url: str = "<set-me>"
    n8n_base_url: str = "<set-me>"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "RuntimeConfig":
        source = environ if environ is not None else os.environ
        return cls(
            host=source.get("AEGISOPS_CONTROL_PLANE_HOST", cls.host),
            port=int(source.get("AEGISOPS_CONTROL_PLANE_PORT", cls.port)),
            postgres_dsn=source.get("AEGISOPS_CONTROL_PLANE_POSTGRES_DSN", cls.postgres_dsn),
            opensearch_url=source.get("AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL", cls.opensearch_url),
            n8n_base_url=source.get("AEGISOPS_CONTROL_PLANE_N8N_BASE_URL", cls.n8n_base_url),
        )
