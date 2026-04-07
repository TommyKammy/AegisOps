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
    shuffle_base_url: str = "<set-me>"
    isolated_executor_base_url: str = "<set-me>"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "RuntimeConfig":
        source = environ if environ is not None else os.environ
        raw_port = source.get("AEGISOPS_CONTROL_PLANE_PORT", "")
        if raw_port == "":
            port = cls.port
        else:
            try:
                port = int(raw_port)
            except ValueError as exc:
                raise ValueError(
                    f"AEGISOPS_CONTROL_PLANE_PORT must be an integer, got: {raw_port!r}"
                ) from exc
            if not (1 <= port <= 65535):
                raise ValueError(
                    f"AEGISOPS_CONTROL_PLANE_PORT must be between 1 and 65535, got: {port}"
                )

        return cls(
            host=source.get("AEGISOPS_CONTROL_PLANE_HOST", cls.host),
            port=port,
            postgres_dsn=source.get("AEGISOPS_CONTROL_PLANE_POSTGRES_DSN", cls.postgres_dsn),
            opensearch_url=source.get("AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL", cls.opensearch_url),
            n8n_base_url=source.get("AEGISOPS_CONTROL_PLANE_N8N_BASE_URL", cls.n8n_base_url),
            shuffle_base_url=source.get(
                "AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL",
                cls.shuffle_base_url,
            ),
            isolated_executor_base_url=source.get(
                "AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL",
                cls.isolated_executor_base_url,
            ),
        )
