from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterator, Mapping, Type

from .adapters.postgres import _validate_lifecycle_state, _validate_record
from .models import (
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


def _parse_optional_backup_created_at(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _is_nested_transaction_isolation_level_error(exc: ValueError) -> bool:
    normalized_message = str(exc).lower()
    return all(
        snippet in normalized_message
        for snippet in _NESTED_TRANSACTION_ISOLATION_LEVEL_ERROR_SNIPPETS
    )


def _unexpected_restore_record_family_keys(
    payload: Mapping[str, object],
    *,
    expected_families: frozenset[str],
) -> tuple[str, ...]:
    non_string_keys = tuple(key for key in payload if not isinstance(key, str))
    if non_string_keys:
        raise ValueError(
            "restore payload contains non-string record family keys: "
            f"{non_string_keys!r}"
        )
    return tuple(sorted(set(payload) - expected_families))


def _is_valid_restore_record_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


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
        record_from_backup_payload: Callable[
            [Type[ControlPlaneRecord], Mapping[str, object]],
            ControlPlaneRecord,
        ],
        authoritative_record_chain_record_types: tuple[Type[ControlPlaneRecord], ...],
        authoritative_record_chain_backup_schema_version: str,
        authoritative_primary_id_field_by_family: Mapping[str, str],
        find_duplicate_strings: Callable[[tuple[str, ...]], tuple[str, ...]],
        synthesize_lifecycle_transition_record: Callable[
            [ControlPlaneRecord, datetime | None],
            LifecycleTransitionRecord | None,
        ],
        assistant_ids_from_mapping: Callable[[Mapping[str, object] | None, str], tuple[str, ...]],
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
        self._record_from_backup_payload = record_from_backup_payload
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
        unexpected_record_families = _unexpected_restore_record_family_keys(
            record_families_payload,
            expected_families=expected_families,
        )
        unexpected_record_counts = _unexpected_restore_record_family_keys(
            record_counts_payload,
            expected_families=expected_families,
        )
        if unexpected_record_families or unexpected_record_counts:
            raise ValueError(
                "restore payload contains unsupported record family keys: "
                f"record_families={list(unexpected_record_families)!r}, "
                f"record_counts={list(unexpected_record_counts)!r}"
            )
        backup_created_at = _parse_optional_backup_created_at(
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
            if not _is_valid_restore_record_count(expected_count):
                raise ValueError(
                    f"restore payload record count for {family!r} must be an integer"
                )
            if expected_count != len(raw_records):
                raise ValueError(
                    f"restore payload record count mismatch for {family!r}: "
                    f"expected {expected_count!r}, found {len(raw_records)}"
                )
            parsed = tuple(
                self._record_from_backup_payload(record_type, raw_record)
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
        verified_case_ids = tuple(
            record.case_id for record in self._store.list(CaseRecord)
        )
        verified_recommendation_ids = tuple(
            record.recommendation_id
            for record in self._store.list(RecommendationRecord)
        )
        verified_approval_decision_ids = tuple(
            record.approval_decision_id
            for record in self._store.list(ApprovalDecisionRecord)
        )
        verified_action_execution_ids = tuple(
            record.action_execution_id
            for record in self._store.list(ActionExecutionRecord)
        )
        verified_reconciliation_ids = tuple(
            record.reconciliation_id
            for record in self._store.list(ReconciliationRecord)
        )

        for case_id in verified_case_ids:
            self._inspect_case_detail(case_id)
        for recommendation_id in verified_recommendation_ids:
            self._inspect_assistant_context("recommendation", recommendation_id)
        for approval_decision_id in verified_approval_decision_ids:
            self._inspect_assistant_context("approval_decision", approval_decision_id)
        for action_execution_id in verified_action_execution_ids:
            self._inspect_assistant_context("action_execution", action_execution_id)
        for reconciliation_id in verified_reconciliation_ids:
            self._inspect_assistant_context("reconciliation", reconciliation_id)
        self._inspect_reconciliation_status()
        startup = self._describe_startup_status()
        readiness_aggregates = self._inspect_readiness_aggregates()
        readiness_review_snapshots = self._collect_readiness_review_snapshots(
            readiness_aggregates
        )
        readiness_status = self._derive_readiness_status(
            startup_ready=startup.startup_ready,
            reconciliation_lifecycle_counts=readiness_aggregates.reconciliation_lifecycle_counts,
            review_path_health_overall_state=self._build_readiness_review_path_health(
                readiness_aggregates,
                readiness_review_snapshots,
            )["overall_state"],
        )

        return self._restore_drill_snapshot_factory(
            read_only=True,
            drill_passed=readiness_status == "ready",
            verified_case_ids=verified_case_ids,
            verified_recommendation_ids=verified_recommendation_ids,
            verified_approval_decision_ids=verified_approval_decision_ids,
            verified_action_execution_ids=verified_action_execution_ids,
            verified_reconciliation_ids=verified_reconciliation_ids,
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
        def duplicate_restore_count_suffix(family: str) -> str:
            if restored_record_counts is None:
                return ""
            return (
                "; restored_record_counts"
                f"[{family!r}]={restored_record_counts.get(family)!r}"
            )

        def require_family_records(
            family: str,
            expected_type: Type[ControlPlaneRecord],
        ) -> tuple[ControlPlaneRecord, ...]:
            family_records = tuple(records_by_family.get(family, ()))
            unexpected_types = tuple(
                type(record).__name__
                for record in family_records
                if not isinstance(record, expected_type)
            )
            if unexpected_types:
                raise ValueError(
                    "restore payload contains unexpected record types for "
                    f"{family!r}: {unexpected_types!r}"
                )
            return family_records

        analytic_signal_records = tuple(
            require_family_records("analytic_signal", AnalyticSignalRecord)
        )
        alert_records = tuple(
            require_family_records("alert", AlertRecord)
        )
        evidence_record_family = tuple(
            require_family_records("evidence", EvidenceRecord)
        )
        observation_records = tuple(
            require_family_records("observation", ObservationRecord)
        )
        lead_records = tuple(
            require_family_records("lead", LeadRecord)
        )
        case_records = tuple(
            require_family_records("case", CaseRecord)
        )
        recommendation_records = tuple(
            require_family_records("recommendation", RecommendationRecord)
        )
        lifecycle_transition_records = tuple(
            require_family_records(
                "lifecycle_transition",
                LifecycleTransitionRecord,
            )
        )
        approval_decision_records = tuple(
            require_family_records("approval_decision", ApprovalDecisionRecord)
        )
        action_request_records = tuple(
            require_family_records("action_request", ActionRequestRecord)
        )
        action_execution_records = tuple(
            require_family_records("action_execution", ActionExecutionRecord)
        )
        hunt_records = tuple(
            require_family_records("hunt", HuntRecord)
        )
        hunt_run_records = tuple(
            require_family_records("hunt_run", HuntRunRecord)
        )
        ai_trace_records = tuple(
            require_family_records("ai_trace", AITraceRecord)
        )
        reconciliations = tuple(
            require_family_records("reconciliation", ReconciliationRecord)
        )
        for family, records in (
            ("analytic_signal", analytic_signal_records),
            ("alert", alert_records),
            ("evidence", evidence_record_family),
            ("observation", observation_records),
            ("lead", lead_records),
            ("case", case_records),
            ("recommendation", recommendation_records),
            ("lifecycle_transition", lifecycle_transition_records),
            ("approval_decision", approval_decision_records),
            ("action_request", action_request_records),
            ("action_execution", action_execution_records),
            ("hunt", hunt_records),
            ("hunt_run", hunt_run_records),
            ("ai_trace", ai_trace_records),
            ("reconciliation", reconciliations),
        ):
            duplicates = self._find_duplicate_strings(
                tuple(
                    getattr(record, self._authoritative_primary_id_field_by_family[family])
                    for record in records
                )
            )
            if duplicates:
                raise ValueError(
                    "restore payload contains duplicate "
                    f"{family} identifiers {duplicates!r}"
                    f"{duplicate_restore_count_suffix(family)}"
                )

        for record in (
            *observation_records,
            *lead_records,
            *recommendation_records,
        ):
            _validate_record(record)
        duplicate_execution_run_ids = self._find_duplicate_strings(
            tuple(
                record.execution_run_id
                for record in action_execution_records
                if record.execution_run_id is not None
            )
        )
        if duplicate_execution_run_ids:
            raise ValueError(
                "restore payload contains duplicate action_execution "
                f"execution_run_id values {duplicate_execution_run_ids!r}"
                f"{duplicate_restore_count_suffix('action_execution')}"
            )

        analytic_signals = {
            record.analytic_signal_id: record for record in analytic_signal_records
        }
        alerts = {record.alert_id: record for record in alert_records}
        evidence_records = {
            record.evidence_id: record for record in evidence_record_family
        }
        observations = {
            record.observation_id: record for record in observation_records
        }
        leads = {record.lead_id: record for record in lead_records}
        cases = {record.case_id: record for record in case_records}
        recommendations = {
            record.recommendation_id: record for record in recommendation_records
        }
        approval_decisions = {
            record.approval_decision_id: record
            for record in approval_decision_records
        }
        action_requests = {
            record.action_request_id: record for record in action_request_records
        }
        action_executions = {
            record.action_execution_id: record for record in action_execution_records
        }
        hunts = {record.hunt_id: record for record in hunt_records}
        hunt_runs = {record.hunt_run_id: record for record in hunt_run_records}
        ai_traces = {record.ai_trace_id: record for record in ai_trace_records}
        action_executions_by_run_id = {
            record.execution_run_id: record
            for record in action_execution_records
            if record.execution_run_id is not None
        }
        reconciliations_by_id = {
            record.reconciliation_id: record for record in reconciliations
        }
        authoritative_subject_ids_by_family: dict[str, set[str]] = {
            "analytic_signal": set(analytic_signals),
            "alert": set(alerts),
            "evidence": set(evidence_records),
            "observation": set(observations),
            "lead": set(leads),
            "case": set(cases),
            "recommendation": set(recommendations),
            "approval_decision": set(approval_decisions),
            "action_request": set(action_requests),
            "action_execution": set(action_executions),
            "hunt": set(hunts),
            "hunt_run": set(hunt_runs),
            "ai_trace": set(ai_traces),
            "reconciliation": set(reconciliations_by_id),
        }
        authoritative_subject_records_by_family: dict[
            str, Mapping[str, ControlPlaneRecord]
        ] = {
            "analytic_signal": analytic_signals,
            "alert": alerts,
            "evidence": evidence_records,
            "observation": observations,
            "lead": leads,
            "case": cases,
            "recommendation": recommendations,
            "approval_decision": approval_decisions,
            "action_request": action_requests,
            "action_execution": action_executions,
            "hunt": hunts,
            "hunt_run": hunt_runs,
            "ai_trace": ai_traces,
            "reconciliation": reconciliations_by_id,
        }

        for alert in alerts.values():
            if alert.analytic_signal_id and alert.analytic_signal_id not in analytic_signals:
                raise ValueError(
                    f"missing analytic_signal record {alert.analytic_signal_id!r} required by alert "
                    f"{alert.alert_id!r}"
                )
            if (
                alert.analytic_signal_id
                and alert.alert_id
                not in analytic_signals[alert.analytic_signal_id].alert_ids
            ):
                raise ValueError(
                    f"alert {alert.alert_id!r} does not match analytic signal binding "
                    f"{alert.analytic_signal_id!r}"
                )
            if alert.case_id and alert.case_id not in cases:
                raise ValueError(
                    f"missing case record {alert.case_id!r} required by alert {alert.alert_id!r}"
                )
            if alert.case_id and cases[alert.case_id].alert_id != alert.alert_id:
                raise ValueError(
                    f"alert {alert.alert_id!r} does not match case binding {alert.case_id!r}"
                )

        for analytic_signal in analytic_signals.values():
            for alert_id in analytic_signal.alert_ids:
                if alert_id not in alerts:
                    raise ValueError(
                        f"missing alert record {alert_id!r} required by analytic signal "
                        f"{analytic_signal.analytic_signal_id!r}"
                    )
                if alerts[alert_id].analytic_signal_id != analytic_signal.analytic_signal_id:
                    raise ValueError(
                        f"analytic signal {analytic_signal.analytic_signal_id!r} does not match "
                        f"alert binding {alert_id!r}"
                    )
            for case_id in analytic_signal.case_ids:
                if case_id not in cases:
                    raise ValueError(
                        f"missing case record {case_id!r} required by analytic signal "
                        f"{analytic_signal.analytic_signal_id!r}"
                    )

        for evidence in evidence_records.values():
            if evidence.alert_id and evidence.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {evidence.alert_id!r} required by evidence "
                    f"{evidence.evidence_id!r}"
                )
            if evidence.case_id and evidence.case_id not in cases:
                raise ValueError(
                    f"missing case record {evidence.case_id!r} required by evidence "
                    f"{evidence.evidence_id!r}"
                )

        for observation in observations.values():
            if observation.hunt_id and observation.hunt_id not in hunts:
                raise ValueError(
                    f"missing hunt record {observation.hunt_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            if observation.hunt_run_id and observation.hunt_run_id not in hunt_runs:
                raise ValueError(
                    f"missing hunt_run record {observation.hunt_run_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            if observation.alert_id and observation.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {observation.alert_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            if observation.case_id and observation.case_id not in cases:
                raise ValueError(
                    f"missing case record {observation.case_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            for evidence_id in observation.supporting_evidence_ids:
                if evidence_id not in evidence_records:
                    raise ValueError(
                        f"missing evidence record {evidence_id!r} required by observation "
                        f"{observation.observation_id!r}"
                    )

        for lead in leads.values():
            if lead.observation_id and lead.observation_id not in observations:
                raise ValueError(
                    f"missing observation record {lead.observation_id!r} required by lead "
                    f"{lead.lead_id!r}"
                )
            if lead.hunt_run_id and lead.hunt_run_id not in hunt_runs:
                raise ValueError(
                    f"missing hunt_run record {lead.hunt_run_id!r} required by lead "
                    f"{lead.lead_id!r}"
                )
            if lead.alert_id and lead.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {lead.alert_id!r} required by lead {lead.lead_id!r}"
                )
            if lead.case_id and lead.case_id not in cases:
                raise ValueError(
                    f"missing case record {lead.case_id!r} required by lead {lead.lead_id!r}"
                )

        for case in cases.values():
            if case.alert_id and case.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {case.alert_id!r} required by case {case.case_id!r}"
                )
            if case.alert_id and alerts[case.alert_id].case_id != case.case_id:
                raise ValueError(
                    f"case {case.case_id!r} does not match alert binding {case.alert_id!r}"
                )
            for evidence_id in case.evidence_ids:
                if evidence_id not in evidence_records:
                    raise ValueError(
                        f"missing evidence record {evidence_id!r} required by case {case.case_id!r}"
                    )

        for recommendation in recommendations.values():
            if recommendation.lead_id and recommendation.lead_id not in leads:
                raise ValueError(
                    "missing lead record "
                    f"{recommendation.lead_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.hunt_run_id and recommendation.hunt_run_id not in hunt_runs:
                raise ValueError(
                    "missing hunt_run record "
                    f"{recommendation.hunt_run_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.alert_id and recommendation.alert_id not in alerts:
                raise ValueError(
                    "missing alert record "
                    f"{recommendation.alert_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.case_id and recommendation.case_id not in cases:
                raise ValueError(
                    "missing case record "
                    f"{recommendation.case_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.ai_trace_id and recommendation.ai_trace_id not in ai_traces:
                raise ValueError(
                    "missing ai_trace record "
                    f"{recommendation.ai_trace_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )

        for hunt in hunts.values():
            if hunt.alert_id and hunt.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {hunt.alert_id!r} required by hunt {hunt.hunt_id!r}"
                )
            if hunt.case_id and hunt.case_id not in cases:
                raise ValueError(
                    f"missing case record {hunt.case_id!r} required by hunt {hunt.hunt_id!r}"
                )

        for hunt_run in hunt_runs.values():
            if hunt_run.hunt_id not in hunts:
                raise ValueError(
                    f"missing hunt record {hunt_run.hunt_id!r} required by hunt_run "
                    f"{hunt_run.hunt_run_id!r}"
                )

        for approval_decision in approval_decisions.values():
            action_request = action_requests.get(approval_decision.action_request_id)
            if action_request is None:
                raise ValueError(
                    f"missing action_request record {approval_decision.action_request_id!r} required by "
                    f"approval decision {approval_decision.approval_decision_id!r}"
                )
            if approval_decision.target_snapshot != action_request.target_scope:
                raise ValueError(
                    f"approval decision {approval_decision.approval_decision_id!r} does not match "
                    "action request target binding"
                )
            if approval_decision.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"approval decision {approval_decision.approval_decision_id!r} does not match "
                    "action request payload binding"
                )

        for action_request in action_requests.values():
            if action_request.case_id and action_request.case_id not in cases:
                raise ValueError(
                    f"missing case record {action_request.case_id!r} required by action request "
                    f"{action_request.action_request_id!r}"
                )
            if action_request.alert_id and action_request.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {action_request.alert_id!r} required by action request "
                    f"{action_request.action_request_id!r}"
                )
            if (
                action_request.approval_decision_id
                and action_request.approval_decision_id not in approval_decisions
            ):
                raise ValueError(
                    f"missing approval_decision record {action_request.approval_decision_id!r} "
                    f"required by action request {action_request.action_request_id!r}"
                )
            approval_decision = approval_decisions.get(action_request.approval_decision_id)
            if approval_decision is None:
                continue
            if approval_decision.action_request_id != action_request.action_request_id:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} does not match approval "
                    "decision binding"
                )
            if approval_decision.target_snapshot != action_request.target_scope:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} does not match approval "
                    "decision target binding"
                )
            if approval_decision.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} does not match approval "
                    "decision payload binding"
                )

        for action_execution in action_executions.values():
            action_request = action_requests.get(action_execution.action_request_id)
            if action_request is None:
                raise ValueError(
                    f"missing action_request record {action_execution.action_request_id!r} required by "
                    f"action execution {action_execution.action_execution_id!r}"
                )
            if action_execution.approval_decision_id not in approval_decisions:
                raise ValueError(
                    f"missing approval_decision record {action_execution.approval_decision_id!r} "
                    f"required by action execution {action_execution.action_execution_id!r}"
                )
            approval_decision = approval_decisions[action_execution.approval_decision_id]
            if action_request.approval_decision_id != action_execution.approval_decision_id:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    f"request approval binding"
                )
            if approval_decision.action_request_id != action_request.action_request_id:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision binding"
                )
            if action_execution.idempotency_key != action_request.idempotency_key:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request idempotency binding"
                )
            if action_execution.target_scope != action_request.target_scope:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request target binding"
                )
            if action_execution.approved_payload != action_request.requested_payload:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request approved payload binding"
                )
            if action_execution.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request payload binding"
                )
            policy_evaluation = action_request.policy_evaluation
            if (
                policy_evaluation.get("execution_surface_type")
                != action_execution.execution_surface_type
            ):
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request execution surface binding"
                )
            if (
                policy_evaluation.get("execution_surface_id")
                != action_execution.execution_surface_id
            ):
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request execution surface binding"
                )
            if approval_decision.target_snapshot != action_request.target_scope:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision target binding"
                )
            if approval_decision.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision payload binding"
                )
            if approval_decision.approved_expires_at != action_request.expires_at:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision expiry binding"
                )
            if action_execution.expires_at != action_request.expires_at:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request expiry binding"
                )
            if (
                approval_decision.approved_expires_at is not None
                and action_execution.delegated_at > approval_decision.approved_expires_at
            ):
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} exceeds approval "
                    "expiry binding"
                )

        for reconciliation in reconciliations:
            subject_action_execution_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_execution_ids",
            )
            subject_execution_run_ids = {
                action_executions[action_execution_id].execution_run_id
                for action_execution_id in subject_action_execution_ids
                if action_execution_id in action_executions
                and action_executions[action_execution_id].execution_run_id is not None
            }
            if reconciliation.alert_id and reconciliation.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {reconciliation.alert_id!r} required by reconciliation "
                    f"{reconciliation.reconciliation_id!r}"
                )
            if (
                reconciliation.analytic_signal_id
                and reconciliation.analytic_signal_id not in analytic_signals
            ):
                raise ValueError(
                    f"missing analytic_signal record {reconciliation.analytic_signal_id!r} required by "
                    f"reconciliation {reconciliation.reconciliation_id!r}"
                )
            if (
                reconciliation.execution_run_id
                and reconciliation.execution_run_id not in action_executions_by_run_id
            ):
                raise ValueError(
                    f"missing action execution run {reconciliation.execution_run_id!r} required by "
                    f"reconciliation {reconciliation.reconciliation_id!r}"
                )
            if (
                reconciliation.execution_run_id is not None
                and subject_execution_run_ids
                and reconciliation.execution_run_id not in subject_execution_run_ids
            ):
                raise ValueError(
                    f"reconciliation {reconciliation.reconciliation_id!r} does not match its action "
                    "execution run binding"
                )
            for linked_execution_run_id in reconciliation.linked_execution_run_ids:
                if linked_execution_run_id not in action_executions_by_run_id:
                    raise ValueError(
                        f"missing action execution run {linked_execution_run_id!r} required by "
                        f"reconciliation {reconciliation.reconciliation_id!r}"
                    )
                if (
                    subject_execution_run_ids
                    and linked_execution_run_id not in subject_execution_run_ids
                ):
                    raise ValueError(
                        f"reconciliation {reconciliation.reconciliation_id!r} does not match its linked "
                        "action execution runs"
                    )
            for field_name, known_ids in (
                ("analytic_signal_ids", analytic_signals),
                ("alert_ids", alerts),
                ("case_ids", cases),
                ("evidence_ids", evidence_records),
                ("approval_decision_ids", approval_decisions),
                ("action_request_ids", action_requests),
                ("action_execution_ids", action_executions),
            ):
                for linked_id in self._assistant_ids_from_mapping(
                    reconciliation.subject_linkage,
                    field_name,
                ):
                    if linked_id not in known_ids:
                        singular_name = (
                            field_name[:-4]
                            if field_name.endswith("_ids")
                            else field_name
                        )
                        raise ValueError(
                            f"missing {singular_name} record {linked_id!r} required by reconciliation "
                            f"{reconciliation.reconciliation_id!r}"
                        )

        lifecycle_transitions_by_subject: dict[
            tuple[str, str], list[LifecycleTransitionRecord]
        ] = {}
        for transition in lifecycle_transition_records:
            subject_ids = authoritative_subject_ids_by_family.get(
                transition.subject_record_family
            )
            if subject_ids is None:
                raise ValueError(
                    "lifecycle transition "
                    f"{transition.transition_id!r} references unsupported subject_record_family "
                    f"{transition.subject_record_family!r}"
                )
            if transition.subject_record_id not in subject_ids:
                raise ValueError(
                    "missing "
                    f"{transition.subject_record_family} record {transition.subject_record_id!r} "
                    f"required by lifecycle transition {transition.transition_id!r}"
                )
            _validate_lifecycle_state(transition)
            lifecycle_transitions_by_subject.setdefault(
                (
                    transition.subject_record_family,
                    transition.subject_record_id,
                ),
                [],
            ).append(transition)

        if require_lifecycle_transition_history:
            for subject_family, subject_records in authoritative_subject_records_by_family.items():
                for subject_id, subject_record in subject_records.items():
                    subject_lifecycle_state = getattr(
                        subject_record,
                        "lifecycle_state",
                        None,
                    )
                    if (
                        not isinstance(subject_lifecycle_state, str)
                        or not subject_lifecycle_state.strip()
                    ):
                        continue
                    if (subject_family, subject_id) not in lifecycle_transitions_by_subject:
                        raise ValueError(
                            f"missing lifecycle transition history for {subject_family} "
                            f"record {subject_id!r}"
                        )

        for (subject_family, subject_id), subject_transitions in (
            lifecycle_transitions_by_subject.items()
        ):
            ordered_transitions = sorted(
                subject_transitions,
                key=lambda transition: (
                    transition.transitioned_at,
                    transition.transition_id,
                ),
            )
            first_transition = ordered_transitions[0]
            if first_transition.previous_lifecycle_state is not None:
                raise ValueError(
                    "lifecycle transition chain for "
                    f"{subject_family} record {subject_id!r} must start with a "
                    "creation anchor: "
                    f"{first_transition.transition_id!r} has previous_lifecycle_state "
                    f"{first_transition.previous_lifecycle_state!r}"
                )
            prior_transition: LifecycleTransitionRecord | None = None
            for transition in ordered_transitions:
                if (
                    prior_transition is not None
                    and transition.previous_lifecycle_state
                    != prior_transition.lifecycle_state
                ):
                    raise ValueError(
                        "lifecycle transition chain for "
                        f"{subject_family} record {subject_id!r} is inconsistent: "
                        f"{transition.transition_id!r} previous_lifecycle_state "
                        f"{transition.previous_lifecycle_state!r} does not match prior "
                        f"lifecycle_state {prior_transition.lifecycle_state!r}"
                    )
                if transition.previous_lifecycle_state == transition.lifecycle_state:
                    raise ValueError(
                        "lifecycle transition chain for "
                        f"{subject_family} record {subject_id!r} contains no-op transition: "
                        f"{transition.transition_id!r} previous_lifecycle_state "
                        f"{transition.previous_lifecycle_state!r} matches lifecycle_state "
                        f"{transition.lifecycle_state!r}"
                    )
                prior_transition = transition

            latest_transition = ordered_transitions[-1]
            subject_record = authoritative_subject_records_by_family[subject_family][
                subject_id
            ]
            subject_lifecycle_state = getattr(subject_record, "lifecycle_state", None)
            if subject_lifecycle_state != latest_transition.lifecycle_state:
                raise ValueError(
                    f"{subject_family} record {subject_id!r} lifecycle_state "
                    f"{subject_lifecycle_state!r} does not match latest lifecycle transition "
                    f"{latest_transition.transition_id!r} state "
                    f"{latest_transition.lifecycle_state!r}"
                )
