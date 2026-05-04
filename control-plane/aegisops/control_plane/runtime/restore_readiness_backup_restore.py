from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterator, Mapping, Type

from ..models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    AnalyticSignalRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    LifecycleTransitionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)
from .restore_backup_codec import BackupPayloadCodec
from .restore_backup_validation import RestoreValidationBoundary
from .runtime_boundary import ControlPlaneStore


_LEGACY_PHASE21_MISSING_RECORD_FAMILIES = frozenset(
    {
        ObservationRecord.record_family,
        LeadRecord.record_family,
        RecommendationRecord.record_family,
        LifecycleTransitionRecord.record_family,
        HuntRecord.record_family,
        HuntRunRecord.record_family,
        AITraceRecord.record_family,
    }
)
_LEGACY_RESTORE_FALLBACK_TRANSITION_ANCHOR = datetime(
    2000,
    1,
    1,
    tzinfo=timezone.utc,
)
_NESTED_TRANSACTION_ISOLATION_LEVEL_ERROR_SNIPPETS = (
    "isolation_level",
    "active transaction",
)
def _is_nested_transaction_isolation_level_error(exc: ValueError) -> bool:
    normalized_message = str(exc).lower()
    return all(
        snippet in normalized_message
        for snippet in _NESTED_TRANSACTION_ISOLATION_LEVEL_ERROR_SNIPPETS
    )

@dataclass(frozen=True)
class _RestoreDrillVerifiedIds:
    case_ids: tuple[str, ...]
    recommendation_ids: tuple[str, ...]
    approval_decision_ids: tuple[str, ...]
    action_execution_ids: tuple[str, ...]
    reconciliation_ids: tuple[str, ...]


class _BackupRestoreFlow:
    def __init__(
        self,
        *,
        store: ControlPlaneStore,
        restore_drill_snapshot_factory: Callable[..., Any],
        restore_summary_snapshot_factory: Callable[..., Any],
        record_to_dict: Callable[[ControlPlaneRecord], dict[str, object]],
        json_ready: Callable[[object], object],
        collect_readiness_review_snapshots: Callable[[Any], list[dict[str, object]]],
        build_readiness_review_path_health: Callable[
            [Any, list[dict[str, object]]], dict[str, object]
        ],
        derive_readiness_status: Callable[..., str],
        authoritative_record_chain_record_types: tuple[Type[ControlPlaneRecord], ...],
        authoritative_record_chain_backup_schema_version: str,
        authoritative_primary_id_field_by_family: Mapping[str, str],
        find_duplicate_strings: Callable[[tuple[str, ...]], tuple[str, ...]],
        synthesize_lifecycle_transition_record: Callable[
            [ControlPlaneRecord, datetime | None],
            LifecycleTransitionRecord | None,
        ],
        assistant_ids_from_mapping: Callable[[Mapping[str, object], str], tuple[str, ...]],
        inspect_case_detail: Callable[[str], Any],
        inspect_assistant_context: Callable[[str, str], Any],
        inspect_reconciliation_status: Callable[[], Any],
        describe_startup_status: Callable[[], Any],
        inspect_readiness_aggregates: Callable[[], Any],
    ) -> None:
        self._store = store
        self._restore_drill_snapshot_factory = restore_drill_snapshot_factory
        self._restore_summary_snapshot_factory = restore_summary_snapshot_factory
        self._record_to_dict = record_to_dict
        self._json_ready = json_ready
        self._collect_readiness_review_snapshots = (
            collect_readiness_review_snapshots
        )
        self._build_readiness_review_path_health = (
            build_readiness_review_path_health
        )
        self._derive_readiness_status = derive_readiness_status
        self._backup_payload_codec = BackupPayloadCodec()
        self._authoritative_record_chain_record_types = (
            authoritative_record_chain_record_types
        )
        self._authoritative_record_chain_backup_schema_version = (
            authoritative_record_chain_backup_schema_version
        )
        self._authoritative_primary_id_field_by_family = (
            authoritative_primary_id_field_by_family
        )
        self._find_duplicate_strings = find_duplicate_strings
        self._synthesize_lifecycle_transition_record = (
            synthesize_lifecycle_transition_record
        )
        self._assistant_ids_from_mapping = assistant_ids_from_mapping
        self._restore_validation_boundary = RestoreValidationBoundary(
            authoritative_primary_id_field_by_family=(
                self._authoritative_primary_id_field_by_family
            ),
            find_duplicate_strings=self._find_duplicate_strings,
            assistant_ids_from_mapping=self._assistant_ids_from_mapping,
        )
        self._inspect_case_detail = inspect_case_detail
        self._inspect_assistant_context = inspect_assistant_context
        self._inspect_reconciliation_status = inspect_reconciliation_status
        self._describe_startup_status = describe_startup_status
        self._inspect_readiness_aggregates = inspect_readiness_aggregates

    def export_authoritative_record_chain_backup(self) -> dict[str, object]:
        record_families: dict[str, list[dict[str, object]]] = {}
        record_counts: dict[str, int] = {}
        with self._store.transaction(isolation_level="REPEATABLE READ"):
            authoritative_records = self._list_authoritative_record_chain_records()
            record_counts = {
                family: len(persisted_records)
                for family, persisted_records in authoritative_records.items()
            }
            self.validate_authoritative_record_chain_restore(
                authoritative_records,
                require_lifecycle_transition_history=True,
                restored_record_counts=record_counts,
            )
            for family, persisted_records in authoritative_records.items():
                records = [
                    self._json_ready(self._record_to_dict(record))
                    for record in persisted_records
                ]
                record_families[family] = records
        return {
            "backup_schema_version": self._authoritative_record_chain_backup_schema_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "persistence_mode": self._store.persistence_mode,
            "record_families": record_families,
            "record_counts": record_counts,
        }

    def restore_authoritative_record_chain_backup(
        self,
        backup_payload: Mapping[str, object],
    ) -> Any:
        if not isinstance(backup_payload, Mapping):
            raise ValueError("restore payload must be a JSON object")
        backup_schema_version = backup_payload.get("backup_schema_version")
        legacy_phase21_backup = (
            backup_schema_version == "phase21.authoritative-record-chain.v1"
        )
        if not legacy_phase21_backup and (
            backup_schema_version
            != self._authoritative_record_chain_backup_schema_version
        ):
            raise ValueError(
                "restore payload must declare the reviewed authoritative record-chain schema version"
            )
        record_families_payload = backup_payload.get("record_families")
        if not isinstance(record_families_payload, Mapping):
            raise ValueError("restore payload must contain record_families")
        record_counts_payload = backup_payload.get("record_counts")
        if not isinstance(record_counts_payload, Mapping):
            raise ValueError("restore payload must contain record_counts")
        expected_families = frozenset(
            record_type.record_family
            for record_type in self._authoritative_record_chain_record_types
        )
        unexpected_record_families = self._backup_payload_codec.unexpected_restore_record_family_keys(
            record_families_payload,
            expected_families=expected_families,
        )
        unexpected_record_counts = self._backup_payload_codec.unexpected_restore_record_family_keys(
            record_counts_payload,
            expected_families=expected_families,
        )
        if unexpected_record_families or unexpected_record_counts:
            raise ValueError(
                "restore payload contains unsupported record family keys: "
                f"record_families={list(unexpected_record_families)!r}, "
                f"record_counts={list(unexpected_record_counts)!r}"
            )
        backup_created_at = self._backup_payload_codec.parse_optional_backup_created_at(
            backup_payload.get("created_at")
        )

        parsed_records: dict[str, tuple[ControlPlaneRecord, ...]] = {}
        restored_record_counts: dict[str, int] = {}
        for record_type in self._authoritative_record_chain_record_types:
            family = record_type.record_family
            raw_records = record_families_payload.get(family)
            expected_count = record_counts_payload.get(family)
            if (
                legacy_phase21_backup
                and family in _LEGACY_PHASE21_MISSING_RECORD_FAMILIES
            ):
                raw_records = [] if raw_records is None else raw_records
                expected_count = 0 if expected_count is None else expected_count
            if not isinstance(raw_records, list):
                raise ValueError(
                    f"restore payload must contain a JSON array for record family {family!r}"
                )
            if not self._backup_payload_codec.is_valid_restore_record_count(expected_count):
                raise ValueError(
                    f"restore payload record count for {family!r} must be an integer"
                )
            if expected_count != len(raw_records):
                raise ValueError(
                    f"restore payload record count mismatch for {family!r}: "
                    f"expected {expected_count!r}, found {len(raw_records)}"
                )
            parsed = tuple(
                self._backup_payload_codec.record_from_backup_payload(record_type, raw_record)
                for raw_record in raw_records
            )
            parsed_records[family] = parsed
            restored_record_counts[family] = len(parsed)

        if legacy_phase21_backup:
            synthesized_transitions = self._synthesize_missing_lifecycle_transition_records(
                parsed_records,
                backup_created_at=backup_created_at,
            )
            parsed_records["lifecycle_transition"] = synthesized_transitions
            restored_record_counts["lifecycle_transition"] = len(synthesized_transitions)

        self.validate_authoritative_record_chain_restore(
            parsed_records,
            require_lifecycle_transition_history=True,
            restored_record_counts=restored_record_counts,
        )
        with self._store.transaction(isolation_level="SERIALIZABLE"):
            self.require_empty_authoritative_restore_target()
            for record_type in self._authoritative_record_chain_record_types:
                for record in parsed_records[record_type.record_family]:
                    self._store.save(record)
            restore_drill = self.run_authoritative_restore_drill(
                require_lifecycle_transition_history=True
            )
        return self._restore_summary_snapshot_factory(
            read_only=True,
            restored_record_counts=restored_record_counts,
            restore_drill=restore_drill,
        )

    @contextmanager
    def restore_drill_snapshot_transaction(self) -> Iterator[None]:
        try:
            with self._store.transaction(isolation_level="REPEATABLE READ"):
                yield
                return
        except ValueError as exc:
            if not _is_nested_transaction_isolation_level_error(exc):
                raise
        with self._store.transaction():
            yield

    def run_authoritative_restore_drill(
        self,
        *,
        require_lifecycle_transition_history: bool = True,
    ) -> Any:
        with self.restore_drill_snapshot_transaction():
            return self.run_authoritative_restore_drill_snapshot(
                require_lifecycle_transition_history=require_lifecycle_transition_history
            )

    def run_authoritative_restore_drill_snapshot(
        self,
        *,
        require_lifecycle_transition_history: bool = True,
    ) -> Any:
        self.validate_authoritative_record_chain_restore(
            self._list_authoritative_record_chain_records(),
            require_lifecycle_transition_history=require_lifecycle_transition_history,
        )
        verified_ids = self._collect_restore_drill_verified_ids()
        self._probe_restore_drill_verified_surfaces(verified_ids)
        readiness_status = self._derive_restore_drill_readiness_status()

        return self._restore_drill_snapshot_factory(
            read_only=True,
            drill_passed=readiness_status == "ready",
            verified_case_ids=verified_ids.case_ids,
            verified_recommendation_ids=verified_ids.recommendation_ids,
            verified_approval_decision_ids=verified_ids.approval_decision_ids,
            verified_action_execution_ids=verified_ids.action_execution_ids,
            verified_reconciliation_ids=verified_ids.reconciliation_ids,
        )

    def _collect_restore_drill_verified_ids(self) -> _RestoreDrillVerifiedIds:
        return _RestoreDrillVerifiedIds(
            case_ids=tuple(record.case_id for record in self._store.list(CaseRecord)),
            recommendation_ids=tuple(
                record.recommendation_id
                for record in self._store.list(RecommendationRecord)
            ),
            approval_decision_ids=tuple(
                record.approval_decision_id
                for record in self._store.list(ApprovalDecisionRecord)
            ),
            action_execution_ids=tuple(
                record.action_execution_id
                for record in self._store.list(ActionExecutionRecord)
            ),
            reconciliation_ids=tuple(
                record.reconciliation_id
                for record in self._store.list(ReconciliationRecord)
            ),
        )

    def _probe_restore_drill_verified_surfaces(
        self,
        verified_ids: _RestoreDrillVerifiedIds,
    ) -> None:
        for case_id in verified_ids.case_ids:
            self._inspect_case_detail(case_id)
        for recommendation_id in verified_ids.recommendation_ids:
            self._inspect_assistant_context("recommendation", recommendation_id)
        for approval_decision_id in verified_ids.approval_decision_ids:
            self._inspect_assistant_context("approval_decision", approval_decision_id)
        for action_execution_id in verified_ids.action_execution_ids:
            self._inspect_assistant_context("action_execution", action_execution_id)
        for reconciliation_id in verified_ids.reconciliation_ids:
            self._inspect_assistant_context("reconciliation", reconciliation_id)
        self._inspect_reconciliation_status()

    def _derive_restore_drill_readiness_status(self) -> str:
        startup = self._describe_startup_status()
        readiness_aggregates = self._inspect_readiness_aggregates()
        readiness_review_snapshots = self._collect_readiness_review_snapshots(
            readiness_aggregates
        )
        return self._derive_readiness_status(
            startup_ready=startup.startup_ready,
            reconciliation_lifecycle_counts=readiness_aggregates.reconciliation_lifecycle_counts,
            review_path_health_overall_state=self._build_readiness_review_path_health(
                readiness_aggregates,
                readiness_review_snapshots,
            )["overall_state"],
        )

    def _list_authoritative_record_chain_records(
        self,
    ) -> dict[str, tuple[ControlPlaneRecord, ...]]:
        authoritative_records: dict[str, tuple[ControlPlaneRecord, ...]] = {}
        authoritative_subject_ids_by_family: dict[str, set[str]] = {}
        persisted_records_by_family: dict[str, tuple[ControlPlaneRecord, ...]] = {}
        for record_type in self._authoritative_record_chain_record_types:
            family = record_type.record_family
            persisted_records_by_family[family] = tuple(self._store.list(record_type))
        for record_type in self._authoritative_record_chain_record_types:
            family = record_type.record_family
            persisted_records = persisted_records_by_family[family]
            if record_type is LifecycleTransitionRecord:
                continue
            authoritative_subject_ids_by_family[family] = {
                getattr(record, self._authoritative_primary_id_field_by_family[family])
                for record in persisted_records
            }
        for record_type in self._authoritative_record_chain_record_types:
            family = record_type.record_family
            persisted_records = persisted_records_by_family[family]
            if record_type is LifecycleTransitionRecord:
                for record in persisted_records:
                    subject_ids = authoritative_subject_ids_by_family.get(
                        record.subject_record_family
                    )
                    if subject_ids is None:
                        raise ValueError(
                            "lifecycle transition "
                            f"{record.transition_id!r} references unsupported "
                            f"subject_record_family {record.subject_record_family!r}"
                        )
                    if record.subject_record_id not in subject_ids:
                        raise ValueError(
                            "missing "
                            f"{record.subject_record_family} record "
                            f"{record.subject_record_id!r} required by lifecycle "
                            f"transition {record.transition_id!r}"
                        )
                authoritative_records[family] = persisted_records
                continue
            authoritative_records[family] = persisted_records
        return authoritative_records

    def _synthesize_missing_lifecycle_transition_records(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        *,
        backup_created_at: datetime | None,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        synthesized_transitions = list(
            record
            for record in records_by_family.get("lifecycle_transition", ())
            if isinstance(record, LifecycleTransitionRecord)
        )
        covered_subjects = {
            (record.subject_record_family, record.subject_record_id)
            for record in synthesized_transitions
        }
        pending_subject_records: list[ControlPlaneRecord] = []
        for record_type in self._authoritative_record_chain_record_types:
            if record_type is LifecycleTransitionRecord:
                continue
            for record in records_by_family.get(record_type.record_family, ()):
                subject_key = (record.record_family, record.record_id)
                if subject_key in covered_subjects:
                    continue
                pending_subject_records.append(record)
                covered_subjects.add(subject_key)
        fallback_anchor = (
            backup_created_at
            if backup_created_at is not None
            else _LEGACY_RESTORE_FALLBACK_TRANSITION_ANCHOR
        )
        pending_count = len(pending_subject_records)
        for index, record in enumerate(pending_subject_records):
            fallback_transitioned_at = fallback_anchor - timedelta(
                microseconds=pending_count - index
            )
            synthesized_transition = self._synthesize_lifecycle_transition_record(
                record,
                fallback_transitioned_at,
            )
            if synthesized_transition is None:
                continue
            synthesized_transitions.append(synthesized_transition)
        synthesized_transitions.sort(
            key=lambda transition: (
                transition.transitioned_at,
                transition.transition_id,
            )
        )
        return tuple(synthesized_transitions)

    def require_empty_authoritative_restore_target(self) -> None:
        authoritative_subject_families = {
            record_type.record_family
            for record_type in self._authoritative_record_chain_record_types
            if record_type is not LifecycleTransitionRecord
        }
        populated_families: list[str] = []
        for record_type in self._authoritative_record_chain_record_types:
            family = record_type.record_family
            persisted_records = tuple(self._store.list(record_type))
            if record_type is LifecycleTransitionRecord:
                persisted_records = tuple(
                    record
                    for record in persisted_records
                    if record.subject_record_family in authoritative_subject_families
                )
            if persisted_records:
                populated_families.append(family)
        if populated_families:
            raise ValueError(
                "authoritative restore target must be empty before restore; found existing "
                f"records for {', '.join(populated_families)}"
            )

    def validate_authoritative_record_chain_restore(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        *,
        require_lifecycle_transition_history: bool = True,
        restored_record_counts: Mapping[str, int] | None = None,
    ) -> None:
        self._restore_validation_boundary.validate_authoritative_record_chain_restore(
            records_by_family,
            require_lifecycle_transition_history=require_lifecycle_transition_history,
            restored_record_counts=restored_record_counts,
        )
