from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Mapping

from .models import ControlPlaneRecord
from .readiness_contracts import ReadinessDiagnosticsAggregates
from .restore_readiness import RestoreReadinessService
from .runtime_boundary import RuntimeBoundaryService


class RuntimeRestoreReadinessDiagnosticsService:
    """Internal boundary for runtime, restore, and readiness diagnostics surfaces."""

    def __init__(
        self,
        *,
        runtime_boundary_service: RuntimeBoundaryService,
        restore_readiness_service: RestoreReadinessService,
    ) -> None:
        self._runtime_boundary_service = runtime_boundary_service
        self._restore_readiness_service = restore_readiness_service

    def describe_runtime(self) -> Any:
        return self._runtime_boundary_service.describe_runtime()

    def validate_wazuh_ingest_runtime(self) -> None:
        self._runtime_boundary_service.validate_wazuh_ingest_runtime()

    def validate_protected_surface_runtime(self) -> None:
        self._runtime_boundary_service.validate_protected_surface_runtime()

    def authenticate_protected_surface_request(self, **kwargs: object) -> Any:
        return self._runtime_boundary_service.authenticate_protected_surface_request(
            **kwargs
        )

    def require_admin_bootstrap_token(self, supplied_token: str | None) -> None:
        self._runtime_boundary_service.require_admin_bootstrap_token(supplied_token)

    def require_break_glass_token(self, supplied_token: str | None) -> None:
        self._runtime_boundary_service.require_break_glass_token(supplied_token)

    def describe_startup_status(self) -> Any:
        return self._restore_readiness_service.describe_startup_status()

    def describe_shutdown_status(self) -> Any:
        return self._restore_readiness_service.describe_shutdown_status()

    def inspect_readiness_diagnostics(self) -> Any:
        return self._restore_readiness_service.inspect_readiness_diagnostics()

    def inspect_readiness_aggregates(self) -> ReadinessDiagnosticsAggregates:
        return self._restore_readiness_service.inspect_readiness_aggregates()

    def export_authoritative_record_chain_backup(self) -> dict[str, object]:
        return self._restore_readiness_service.export_authoritative_record_chain_backup()

    def restore_authoritative_record_chain_backup(
        self,
        backup_payload: Mapping[str, object],
    ) -> Any:
        return self._restore_readiness_service.restore_authoritative_record_chain_backup(
            backup_payload
        )

    @contextmanager
    def restore_drill_snapshot_transaction(self) -> Iterator[None]:
        with self._restore_readiness_service.restore_drill_snapshot_transaction():
            yield

    def run_authoritative_restore_drill(self) -> Any:
        return self._restore_readiness_service.run_authoritative_restore_drill()

    def run_authoritative_restore_drill_snapshot(self) -> Any:
        return self._restore_readiness_service.run_authoritative_restore_drill_snapshot()

    def require_empty_authoritative_restore_target(self) -> None:
        self._restore_readiness_service.require_empty_authoritative_restore_target()

    def validate_authoritative_record_chain_restore(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        *,
        restored_record_counts: Mapping[str, int] | None = None,
    ) -> None:
        self._restore_readiness_service.validate_authoritative_record_chain_restore(
            records_by_family,
            restored_record_counts=restored_record_counts,
        )


__all__ = [
    "RuntimeRestoreReadinessDiagnosticsService",
]
