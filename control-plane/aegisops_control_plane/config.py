from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Mapping


def _load_bound_string(
    source: Mapping[str, str],
    env_name: str,
    default: str,
) -> str:
    raw_value = source.get(env_name, "")
    raw_file_path = source.get(f"{env_name}_FILE", "")
    value = raw_value.strip()
    file_path = raw_file_path.strip()

    if value and file_path:
        raise ValueError(
            f"{env_name} and {env_name}_FILE are mutually exclusive; provide exactly one binding"
        )

    if file_path:
        try:
            with open(file_path, encoding="utf-8") as handle:
                file_value = handle.read().strip()
        except OSError as exc:
            raise ValueError(
                f"{env_name}_FILE must point to a readable file, got: {file_path!r}"
            ) from exc
        if file_value == "":
            raise ValueError(f"{env_name}_FILE must not resolve to an empty value")
        return file_value

    if value:
        return value
    return default


@dataclass(frozen=True)
class RuntimeConfig:
    host: str = "127.0.0.1"
    port: int = 8080
    postgres_dsn: str = "<set-me>"
    opensearch_url: str = "<set-me>"
    n8n_base_url: str = "<set-me>"
    shuffle_base_url: str = "<set-me>"
    isolated_executor_base_url: str = "<set-me>"
    wazuh_ingest_shared_secret: str = field(default="", repr=False)
    wazuh_ingest_reverse_proxy_secret: str = field(default="", repr=False)
    wazuh_ingest_trusted_proxy_cidrs: tuple[str, ...] = ()
    protected_surface_reverse_proxy_secret: str = field(default="", repr=False)
    protected_surface_trusted_proxy_cidrs: tuple[str, ...] = ()
    protected_surface_proxy_service_account: str = ""
    admin_bootstrap_token: str = field(default="", repr=False)
    break_glass_token: str = field(default="", repr=False)

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

        trusted_proxy_cidrs = tuple(
            item.strip()
            for item in source.get(
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS",
                "",
            ).split(",")
            if item.strip()
        )
        protected_surface_trusted_proxy_cidrs = tuple(
            item.strip()
            for item in source.get(
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS",
                "",
            ).split(",")
            if item.strip()
        )

        return cls(
            host=source.get("AEGISOPS_CONTROL_PLANE_HOST", cls.host),
            port=port,
            postgres_dsn=_load_bound_string(
                source,
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN",
                cls.postgres_dsn,
            ),
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
            wazuh_ingest_shared_secret=_load_bound_string(
                source,
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET",
                cls.wazuh_ingest_shared_secret,
            ),
            wazuh_ingest_reverse_proxy_secret=_load_bound_string(
                source,
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET",
                cls.wazuh_ingest_reverse_proxy_secret,
            ),
            wazuh_ingest_trusted_proxy_cidrs=trusted_proxy_cidrs,
            protected_surface_reverse_proxy_secret=_load_bound_string(
                source,
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET",
                cls.protected_surface_reverse_proxy_secret,
            ),
            protected_surface_trusted_proxy_cidrs=protected_surface_trusted_proxy_cidrs,
            protected_surface_proxy_service_account=source.get(
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT",
                cls.protected_surface_proxy_service_account,
            ).strip(),
            admin_bootstrap_token=_load_bound_string(
                source,
                "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN",
                cls.admin_bootstrap_token,
            ),
            break_glass_token=_load_bound_string(
                source,
                "AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN",
                cls.break_glass_token,
            ),
        )
