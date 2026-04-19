from __future__ import annotations

from contextlib import AbstractContextManager
import hmac
import ipaddress
from typing import Any, Callable, Protocol, Type

from .config import RuntimeConfig
from .models import ControlPlaneRecord, LifecycleTransitionRecord


def _is_missing_runtime_binding(value: object) -> bool:
    if value is None:
        return True
    return str(value).strip() in {"", "<set-me>"}


class ControlPlaneStore(Protocol):
    dsn: str
    persistence_mode: str

    def save(self, record: ControlPlaneRecord) -> ControlPlaneRecord:
        ...

    def list(self, record_type: Type[ControlPlaneRecord]) -> tuple[ControlPlaneRecord, ...]:
        ...

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        ...

    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> AbstractContextManager[None]:
        ...


class RuntimeBoundaryService:
    def __init__(
        self,
        *,
        config: RuntimeConfig,
        store: ControlPlaneStore,
        reconciliation_adapter: Any,
        shuffle_adapter: Any,
        isolated_executor_adapter: Any,
        runtime_snapshot_factory: Callable[..., Any],
        authenticated_principal_factory: Callable[..., Any],
    ) -> None:
        self._config = config
        self._store = store
        self._reconciliation = reconciliation_adapter
        self._shuffle = shuffle_adapter
        self._isolated_executor = isolated_executor_adapter
        self._runtime_snapshot_factory = runtime_snapshot_factory
        self._authenticated_principal_factory = authenticated_principal_factory

    def describe_runtime(self) -> Any:
        return self._runtime_snapshot_factory(
            service_name="aegisops-control-plane",
            bind_host=self._config.host,
            bind_port=self._config.port,
            postgres_dsn=self._store.dsn,
            persistence_mode=self._store.persistence_mode,
            opensearch_url=self._config.opensearch_url,
            n8n_base_url=self._reconciliation.base_url,
            shuffle_base_url=self._shuffle.base_url,
            isolated_executor_base_url=self._isolated_executor.base_url,
            ownership_boundary={
                "runtime_root": "control-plane/",
                "postgres_contract_root": "postgres/control-plane/",
                "native_detection_intake": "substrate-adapters/",
                "admitted_signal_model": "control-plane/analytic-signals",
                "routine_automation_substrate": "shuffle/",
                "controlled_execution_surface": "executor/isolated-executor",
            },
        )

    def validate_wazuh_ingest_runtime(self) -> None:
        if _is_missing_runtime_binding(self._config.wazuh_ingest_shared_secret):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET must be set "
                "before starting the live Wazuh ingest runtime"
            )
        for cidr in self._config.wazuh_ingest_trusted_proxy_cidrs:
            try:
                ipaddress.ip_network(cidr, strict=False)
            except ValueError as exc:
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS must contain "
                    f"only valid IP networks, got: {cidr!r}"
                ) from exc
        if (
            not self.listener_is_loopback()
            and not self._config.wazuh_ingest_trusted_proxy_cidrs
        ):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS must be set "
                "before starting the live Wazuh ingest runtime on a non-loopback interface"
            )
        if _is_missing_runtime_binding(
            self._config.wazuh_ingest_reverse_proxy_secret
        ):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET must be set "
                "before starting the live Wazuh ingest runtime"
            )

    def validate_protected_surface_runtime(self) -> None:
        for cidr in self._config.protected_surface_trusted_proxy_cidrs:
            try:
                ipaddress.ip_network(cidr, strict=False)
            except ValueError as exc:
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS must contain "
                    f"only valid IP networks, got: {cidr!r}"
                ) from exc
        if (
            not self.listener_is_loopback()
            and not self._config.protected_surface_trusted_proxy_cidrs
        ):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS must be set "
                "before starting protected control-plane surfaces on a non-loopback interface"
            )
        if self._config.protected_surface_trusted_proxy_cidrs:
            if _is_missing_runtime_binding(
                self._config.protected_surface_reverse_proxy_secret
            ):
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET must be set "
                    "before admitting reviewed reverse-proxy traffic to protected control-plane surfaces"
                )
            if _is_missing_runtime_binding(
                self._config.protected_surface_proxy_service_account
            ):
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT must be set "
                    "before admitting reviewed reverse-proxy traffic to protected control-plane surfaces"
                )
            if _is_missing_runtime_binding(
                self._config.protected_surface_reviewed_identity_provider
            ):
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER must be set "
                    "before admitting reviewed reverse-proxy traffic to protected control-plane surfaces"
                )

    def authenticate_protected_surface_request(
        self,
        *,
        peer_addr: str | None,
        forwarded_proto: str | None,
        reverse_proxy_secret_header: str | None,
        proxy_service_account_header: str | None,
        authenticated_identity_provider_header: str | None,
        authenticated_subject_header: str | None,
        authenticated_identity_header: str | None,
        authenticated_role_header: str | None,
        allowed_roles: tuple[str, ...],
    ) -> Any:
        self.validate_protected_surface_runtime()

        if self.peer_addr_is_loopback(peer_addr):
            principal = self._authenticated_principal_factory(
                identity="loopback-local-operator",
                role="loopback_local",
                access_path="loopback_direct",
            )
        else:
            if not self.is_trusted_protected_surface_peer(peer_addr):
                raise PermissionError(
                    "protected control-plane surfaces reject requests that bypass the reviewed reverse proxy peer boundary"
                )
            if (forwarded_proto or "").strip().lower() != "https":
                raise PermissionError(
                    "protected control-plane surfaces require the reviewed reverse proxy HTTPS boundary"
                )
            if not hmac.compare_digest(
                (reverse_proxy_secret_header or "").strip(),
                self._config.protected_surface_reverse_proxy_secret,
            ):
                raise PermissionError(
                    "protected control-plane surfaces require the reviewed reverse proxy boundary credential"
                )
            supplied_proxy_service_account = (proxy_service_account_header or "").strip()
            if not hmac.compare_digest(
                supplied_proxy_service_account,
                self._config.protected_surface_proxy_service_account,
            ):
                raise PermissionError(
                    "protected control-plane surfaces require the reviewed reverse proxy service account identity"
                )
            reviewed_identity_provider = (
                self._config.protected_surface_reviewed_identity_provider.strip().lower()
            )
            supplied_identity_provider = (
                (authenticated_identity_provider_header or "").strip().lower()
            )
            if not supplied_identity_provider:
                raise PermissionError(
                    "protected control-plane surfaces require an attributed reviewed identity provider header"
                )
            if not hmac.compare_digest(
                supplied_identity_provider,
                reviewed_identity_provider,
            ):
                raise PermissionError(
                    "protected control-plane surfaces require the reviewed identity provider boundary"
                )
            authenticated_identity = (authenticated_identity_header or "").strip()
            if not authenticated_identity:
                raise PermissionError(
                    "protected control-plane surfaces require an attributed authenticated identity header"
                )
            authenticated_subject = (authenticated_subject_header or "").strip()
            if not authenticated_subject:
                raise PermissionError(
                    "protected control-plane surfaces require an attributed authenticated subject header"
                )
            authenticated_role = (authenticated_role_header or "").strip()
            if not authenticated_role:
                raise PermissionError(
                    "protected control-plane surfaces require an attributed authenticated role header"
                )
            principal = self._authenticated_principal_factory(
                identity=authenticated_identity,
                role=authenticated_role,
                access_path="reviewed_reverse_proxy",
                proxy_service_account=supplied_proxy_service_account,
                subject=authenticated_subject,
                identity_provider=supplied_identity_provider,
            )
        if allowed_roles and principal.role not in allowed_roles:
            raise PermissionError(
                "protected control-plane surface role is not authorized for this endpoint"
            )
        return principal

    def require_admin_bootstrap_token(self, supplied_token: str | None) -> None:
        expected_token = self._config.admin_bootstrap_token
        if _is_missing_runtime_binding(expected_token):
            raise PermissionError(
                "admin bootstrap contract is disabled until AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN is bound"
            )
        if not hmac.compare_digest((supplied_token or "").strip(), expected_token):
            raise PermissionError(
                "admin bootstrap token did not match the reviewed secret"
            )

    def require_break_glass_token(self, supplied_token: str | None) -> None:
        expected_token = self._config.break_glass_token
        if _is_missing_runtime_binding(expected_token):
            raise PermissionError(
                "break-glass contract is disabled until AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN is bound"
            )
        if not hmac.compare_digest((supplied_token or "").strip(), expected_token):
            raise PermissionError(
                "break-glass token did not match the reviewed secret"
            )

    def listener_is_loopback(self) -> bool:
        host = (self._config.host or "").strip()
        if not host:
            return False
        if host.lower() == "localhost":
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

    def is_trusted_wazuh_ingest_peer(self, peer_addr: str | None) -> bool:
        return self._is_trusted_proxy_peer(
            peer_addr,
            self._config.wazuh_ingest_trusted_proxy_cidrs,
        )

    def is_trusted_protected_surface_peer(self, peer_addr: str | None) -> bool:
        return self._is_trusted_proxy_peer(
            peer_addr,
            self._config.protected_surface_trusted_proxy_cidrs,
        )

    def _is_trusted_proxy_peer(
        self,
        peer_addr: str | None,
        trusted_proxy_cidrs: tuple[str, ...],
    ) -> bool:
        normalized_peer_addr = (peer_addr or "").strip()
        if not normalized_peer_addr:
            return False
        try:
            peer_ip = ipaddress.ip_address(normalized_peer_addr)
        except ValueError:
            return False
        if self.listener_is_loopback():
            return peer_ip.is_loopback
        for cidr in trusted_proxy_cidrs:
            if peer_ip in ipaddress.ip_network(cidr, strict=False):
                return True
        return False

    def is_trusted_peer_for_proxy_cidrs(
        self,
        peer_addr: str | None,
        trusted_proxy_cidrs: tuple[str, ...],
    ) -> bool:
        return self._is_trusted_proxy_peer(peer_addr, trusted_proxy_cidrs)

    @staticmethod
    def peer_addr_is_loopback(peer_addr: str | None) -> bool:
        if peer_addr is None or peer_addr.strip() == "":
            return False
        try:
            return ipaddress.ip_address(peer_addr.strip()).is_loopback
        except ValueError:
            return False


__all__ = [
    "ControlPlaneStore",
    "RuntimeBoundaryService",
]
