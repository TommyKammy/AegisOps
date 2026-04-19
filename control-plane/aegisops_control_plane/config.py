from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from typing import Mapping, Protocol
from urllib import error, parse, request


class OpenBaoSecretTransport(Protocol):
    def read_secret(
        self,
        *,
        address: str,
        token: str,
        mount: str,
        secret_path: str,
    ) -> str:
        """Read a reviewed secret value from OpenBao."""


@dataclass(frozen=True)
class OpenBaoKVv2SecretTransport:
    request_timeout_seconds: float = 5.0

    def read_secret(
        self,
        *,
        address: str,
        token: str,
        mount: str,
        secret_path: str,
    ) -> str:
        normalized_address = address.strip().rstrip("/")
        normalized_mount = mount.strip().strip("/")
        normalized_path = secret_path.strip().strip("/")
        if normalized_address == "":
            raise ValueError("OpenBao address must not be empty")
        parsed_address = parse.urlsplit(normalized_address)
        if parsed_address.scheme not in {"http", "https"}:
            raise ValueError(
                "OpenBao address must use http or https, "
                f"got scheme: {parsed_address.scheme or '<none>'!r}"
            )
        if parsed_address.netloc == "":
            raise ValueError("OpenBao address must include a network location")
        if normalized_mount == "":
            raise ValueError("OpenBao KV mount must not be empty")
        if normalized_path == "":
            raise ValueError("OpenBao secret path must not be empty")

        encoded_mount = parse.quote(normalized_mount, safe="")
        encoded_path = "/".join(
            parse.quote(component, safe="")
            for component in normalized_path.split("/")
            if component
        )
        secret_url = f"{normalized_address}/v1/{encoded_mount}/data/{encoded_path}"
        backend_request = request.Request(
            secret_url,
            headers={
                "Accept": "application/json",
                "X-Vault-Token": token,
            },
            method="GET",
        )
        try:
            with request.urlopen(backend_request, timeout=self.request_timeout_seconds) as response:  # noqa: S310
                payload = json.load(response)
        except (OSError, ValueError, error.URLError) as exc:
            raise ValueError("OpenBao request failed") from exc

        if not isinstance(payload, Mapping):
            raise ValueError("OpenBao response must be a mapping")
        data = payload.get("data")
        if not isinstance(data, Mapping):
            raise ValueError("OpenBao response must include a data mapping")
        secret_data = data.get("data")
        if not isinstance(secret_data, Mapping):
            raise ValueError("OpenBao response must include a nested data mapping")
        secret_value = secret_data.get("value")
        if not isinstance(secret_value, str):
            raise ValueError("OpenBao secret payload must include a string value")
        return secret_value


def _load_env_or_file_string(
    source: Mapping[str, str],
    env_name: str,
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

    return value


def _load_bound_string(
    source: Mapping[str, str],
    env_name: str,
    default: str,
    *,
    secret_backend_transport: OpenBaoSecretTransport | None = None,
) -> str:
    value = _load_env_or_file_string(source, env_name)
    openbao_path = source.get(f"{env_name}_OPENBAO_PATH", "").strip()

    if value and openbao_path:
        raise ValueError(
            f"{env_name} and {env_name}_OPENBAO_PATH are mutually exclusive; provide exactly one binding"
        )
    if source.get(f"{env_name}_FILE", "").strip() and openbao_path:
        raise ValueError(
            f"{env_name}_FILE and {env_name}_OPENBAO_PATH are mutually exclusive; provide exactly one binding"
        )

    if openbao_path:
        if secret_backend_transport is None:
            raise ValueError(
                f"{env_name}_OPENBAO_PATH requires an OpenBao transport"
            )
        openbao_address = source.get("AEGISOPS_OPENBAO_ADDRESS", "").strip()
        openbao_token = _load_env_or_file_string(source, "AEGISOPS_OPENBAO_TOKEN")
        if openbao_address == "":
            raise ValueError(
                f"{env_name}_OPENBAO_PATH requires AEGISOPS_OPENBAO_ADDRESS"
            )
        if openbao_token == "":
            raise ValueError(
                f"{env_name}_OPENBAO_PATH requires "
                "AEGISOPS_OPENBAO_TOKEN or AEGISOPS_OPENBAO_TOKEN_FILE"
            )
        openbao_mount = source.get("AEGISOPS_OPENBAO_KV_MOUNT", "secret").strip() or "secret"
        try:
            openbao_value = secret_backend_transport.read_secret(
                address=openbao_address,
                token=openbao_token,
                mount=openbao_mount,
                secret_path=openbao_path,
            ).strip()
        except Exception as exc:  # noqa: BLE001
            raise ValueError(
                f"{env_name}_OPENBAO_PATH could not be read from OpenBao"
            ) from exc
        if openbao_value == "":
            raise ValueError(
                f"{env_name}_OPENBAO_PATH must not resolve to an empty value"
            )
        return openbao_value

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
    protected_surface_reviewed_identity_provider: str = ""
    admin_bootstrap_token: str = field(default="", repr=False)
    break_glass_token: str = field(default="", repr=False)

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        secret_backend_transport: OpenBaoSecretTransport | None = None,
    ) -> "RuntimeConfig":
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
                secret_backend_transport=secret_backend_transport,
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
                secret_backend_transport=secret_backend_transport,
            ),
            wazuh_ingest_reverse_proxy_secret=_load_bound_string(
                source,
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET",
                cls.wazuh_ingest_reverse_proxy_secret,
                secret_backend_transport=secret_backend_transport,
            ),
            wazuh_ingest_trusted_proxy_cidrs=trusted_proxy_cidrs,
            protected_surface_reverse_proxy_secret=_load_bound_string(
                source,
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET",
                cls.protected_surface_reverse_proxy_secret,
                secret_backend_transport=secret_backend_transport,
            ),
            protected_surface_trusted_proxy_cidrs=protected_surface_trusted_proxy_cidrs,
            protected_surface_proxy_service_account=source.get(
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT",
                cls.protected_surface_proxy_service_account,
            ).strip(),
            protected_surface_reviewed_identity_provider=source.get(
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER",
                cls.protected_surface_reviewed_identity_provider,
            ).strip(),
            admin_bootstrap_token=_load_bound_string(
                source,
                "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN",
                cls.admin_bootstrap_token,
                secret_backend_transport=secret_backend_transport,
            ),
            break_glass_token=_load_bound_string(
                source,
                "AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN",
                cls.break_glass_token,
                secret_backend_transport=secret_backend_transport,
            ),
        )
