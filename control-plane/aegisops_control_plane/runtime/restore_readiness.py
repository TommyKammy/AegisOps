from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterator, Mapping, Type

from ..config import RuntimeConfig
from ..models import (
    ControlPlaneRecord,
    LifecycleTransitionRecord,
    ReconciliationRecord,
)
from .restore_readiness_backup_restore import _BackupRestoreFlow
from .restore_readiness_projection import _ReadinessHealthProjection
from .readiness_contracts import ReadinessDiagnosticsAggregates
from .runtime_boundary import ControlPlaneStore, RuntimeBoundaryService


class RestoreReadinessService:
    def __init__(
        self,
        *,
        config: RuntimeConfig,
        store: ControlPlaneStore,
        runtime_boundary_service: RuntimeBoundaryService,
        startup_status_snapshot_factory: Callable[..., Any],
        readiness_diagnostics_snapshot_factory: Callable[..., Any],
        restore_drill_snapshot_factory: Callable[..., Any],
        restore_summary_snapshot_factory: Callable[..., Any],
        record_to_dict: Callable[[ControlPlaneRecord], dict[str, object]],
        json_ready: Callable[[object], object],
        redacted_reconciliation_payload: Callable[[ReconciliationRecord], dict[str, object]],
        readiness_operability_helper: Any,
        shutdown_status_snapshot_factory: Callable[..., Any],
        derive_readiness_status: Callable[..., str],
        authoritative_record_chain_record_types: tuple[Type[ControlPlaneRecord], ...],
        authoritative_record_chain_backup_schema_version: str,
        authoritative_primary_id_field_by_family: Mapping[str, str],
        record_types_by_family: Mapping[str, Type[ControlPlaneRecord]],
        find_duplicate_strings: Callable[[tuple[str, ...]], tuple[str, ...]],
        synthesize_lifecycle_transition_record: Callable[
            [ControlPlaneRecord, datetime | None],
            LifecycleTransitionRecord | None,
        ],
        assistant_ids_from_mapping: Callable[[Mapping[str, object], str], tuple[str, ...]],
        inspect_case_detail: Callable[[str], Any],
        inspect_assistant_context: Callable[[str, str], Any],
        inspect_reconciliation_status: Callable[[], Any],
    ) -> None:
        del record_types_by_family
        self._readiness_operability_helper = readiness_operability_helper
        self._collect_readiness_review_snapshots = (
            readiness_operability_helper._collect_readiness_review_snapshots
        )
        self._build_readiness_review_path_health = (
            readiness_operability_helper._build_readiness_review_path_health
        )
        self._build_readiness_source_health = (
            readiness_operability_helper._build_readiness_source_health
        )
        self._build_readiness_automation_substrate_health = (
            readiness_operability_helper._build_readiness_automation_substrate_health
        )
        self._build_optional_extension_operability = (
            readiness_operability_helper._build_optional_extension_operability
        )
        self._readiness_health_projection = _ReadinessHealthProjection(
            config=config,
            store=store,
            runtime_boundary_service=runtime_boundary_service,
            startup_status_snapshot_factory=startup_status_snapshot_factory,
            readiness_diagnostics_snapshot_factory=(
                readiness_diagnostics_snapshot_factory
            ),
            redacted_reconciliation_payload=redacted_reconciliation_payload,
            collect_readiness_review_snapshots=(
                lambda aggregates: self._collect_readiness_review_snapshots(
                    aggregates
                )
            ),
            build_readiness_review_path_health=(
                lambda aggregates, snapshots: self._build_readiness_review_path_health(
                    aggregates,
                    snapshots,
                )
            ),
            build_readiness_source_health=(
                lambda aggregates, snapshots: self._build_readiness_source_health(
                    aggregates,
                    snapshots,
                )
            ),
            build_readiness_automation_substrate_health=(
                lambda aggregates, snapshots: self._build_readiness_automation_substrate_health(
                    aggregates,
                    snapshots,
                )
            ),
            build_optional_extension_operability=(
                lambda aggregates, snapshots: self._build_optional_extension_operability(
                    aggregates,
                    snapshots,
                )
            ),
            shutdown_status_snapshot_factory=shutdown_status_snapshot_factory,
            derive_readiness_status=derive_readiness_status,
        )
        self._backup_restore_flow = _BackupRestoreFlow(
            store=store,
            restore_drill_snapshot_factory=restore_drill_snapshot_factory,
            restore_summary_snapshot_factory=restore_summary_snapshot_factory,
            record_to_dict=record_to_dict,
            json_ready=json_ready,
            collect_readiness_review_snapshots=(
                lambda aggregates: self._collect_readiness_review_snapshots(
                    aggregates
                )
            ),
            build_readiness_review_path_health=(
                lambda aggregates, snapshots: self._build_readiness_review_path_health(
                    aggregates,
                    snapshots,
                )
            ),
            derive_readiness_status=derive_readiness_status,
            authoritative_record_chain_record_types=(
                authoritative_record_chain_record_types
            ),
            authoritative_record_chain_backup_schema_version=(
                authoritative_record_chain_backup_schema_version
            ),
            authoritative_primary_id_field_by_family=(
                authoritative_primary_id_field_by_family
            ),
            find_duplicate_strings=find_duplicate_strings,
            synthesize_lifecycle_transition_record=(
                synthesize_lifecycle_transition_record
            ),
            assistant_ids_from_mapping=assistant_ids_from_mapping,
            inspect_case_detail=inspect_case_detail,
            inspect_assistant_context=inspect_assistant_context,
            inspect_reconciliation_status=inspect_reconciliation_status,
            describe_startup_status=self.describe_startup_status,
            inspect_readiness_aggregates=self.inspect_readiness_aggregates,
        )

    def describe_startup_status(self) -> Any:
        return self._readiness_health_projection.describe_startup_status()

    def describe_shutdown_status(self) -> Any:
        return self._readiness_health_projection.describe_shutdown_status()

    def inspect_readiness_diagnostics(self) -> Any:
        return self._readiness_health_projection.inspect_readiness_diagnostics()

    def inspect_readiness_aggregates(self) -> ReadinessDiagnosticsAggregates:
        return self._readiness_health_projection.inspect_readiness_aggregates()

    def export_authoritative_record_chain_backup(self) -> dict[str, object]:
        return self._backup_restore_flow.export_authoritative_record_chain_backup()

    def restore_authoritative_record_chain_backup(
        self,
        backup_payload: Mapping[str, object],
    ) -> Any:
        return self._backup_restore_flow.restore_authoritative_record_chain_backup(
            backup_payload
        )

    def restore_drill_snapshot_transaction(self) -> Iterator[None]:
        return self._backup_restore_flow.restore_drill_snapshot_transaction()

    def run_authoritative_restore_drill(
        self,
        *,
        require_lifecycle_transition_history: bool = True,
    ) -> Any:
        return self._backup_restore_flow.run_authoritative_restore_drill(
            require_lifecycle_transition_history=require_lifecycle_transition_history
        )

    def run_authoritative_restore_drill_snapshot(
        self,
        *,
        require_lifecycle_transition_history: bool = True,
    ) -> Any:
        return self._backup_restore_flow.run_authoritative_restore_drill_snapshot(
            require_lifecycle_transition_history=require_lifecycle_transition_history
        )

    def require_empty_authoritative_restore_target(self) -> None:
        self._backup_restore_flow.require_empty_authoritative_restore_target()

    def validate_authoritative_record_chain_restore(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        *,
        require_lifecycle_transition_history: bool = True,
        restored_record_counts: Mapping[str, int] | None = None,
    ) -> None:
        self._backup_restore_flow.validate_authoritative_record_chain_restore(
            records_by_family,
            require_lifecycle_transition_history=require_lifecycle_transition_history,
            restored_record_counts=restored_record_counts,
        )


__all__ = [
    "RestoreReadinessService",
]
