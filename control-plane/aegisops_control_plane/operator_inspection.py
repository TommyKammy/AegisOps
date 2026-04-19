from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Mapping, Protocol, Type, TypeVar

from .models import (
    AlertRecord,
    AnalyticSignalRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    LifecycleTransitionRecord,
    ObservationRecord,
    LeadRecord,
    ReconciliationRecord,
)


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


class InspectionStore(Protocol):
    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        ...

    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        ...


class OperatorInspectionServiceDependencies(Protocol):
    _store: InspectionStore

    def _latest_detection_reconciliations_by_alert_id(
        self,
    ) -> dict[str, ReconciliationRecord]:
        ...

    def _build_action_review_record_index(self) -> object:
        ...

    def _reconciliation_is_wazuh_origin(
        self,
        reconciliation: ReconciliationRecord,
    ) -> bool:
        ...

    def _merge_linked_ids(
        self,
        linked_ids: object,
        additional_id: str | None,
    ) -> tuple[str, ...]:
        ...

    def _action_review_chains_for_scope(
        self,
        *,
        case_id: str | None,
        alert_id: str | None,
        record_index: object,
    ) -> tuple[dict[str, object], ...]:
        ...

    def _alert_review_state(self, alert: AlertRecord) -> str:
        ...

    def _alert_escalation_boundary(self, alert: AlertRecord) -> str:
        ...

    def _assistant_evidence_records_for_context(
        self,
        *,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        exclude_evidence_id: str | None,
    ) -> tuple[EvidenceRecord, ...]:
        ...

    def _assistant_ids_from_mapping(
        self,
        mapping: Mapping[str, object],
        key: str,
    ) -> tuple[str, ...]:
        ...

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        ...

    def _require_non_empty_string(self, value: str, field_name: str) -> str:
        ...

    def inspect_assistant_context(
        self,
        record_family: str,
        record_id: str,
    ) -> object:
        ...

    def _require_reviewed_operator_case(self, case_id: str) -> CaseRecord:
        ...

    def _observations_for_case(self, case_id: str) -> tuple[ObservationRecord, ...]:
        ...

    def _leads_for_case(self, case_id: str) -> tuple[LeadRecord, ...]:
        ...

    def _reviewed_operator_source_family(
        self,
        reviewed_context: object,
    ) -> str | None:
        ...

    def _normalize_optional_string(
        self,
        value: object,
        field_name: str,
    ) -> str | None:
        ...


class OperatorInspectionReadSurface:
    def __init__(
        self,
        service: OperatorInspectionServiceDependencies,
        *,
        analyst_queue_snapshot_factory: Callable[..., object],
        alert_detail_snapshot_factory: Callable[..., object],
        case_detail_snapshot_factory: Callable[..., object],
        record_to_dict: Callable[[object], dict[str, object]],
        redacted_reconciliation_payload: Callable[[ReconciliationRecord], dict[str, object]],
        normalize_admission_provenance: Callable[[object], dict[str, str] | None],
        coordination_reference_payload: Callable[[object], dict[str, object] | None],
        coordination_reference_signature: Callable[[object], tuple[object, ...] | None],
        dedupe_strings: Callable[[tuple[str, ...]], tuple[str, ...]],
    ) -> None:
        self._service = service
        self._analyst_queue_snapshot_factory = analyst_queue_snapshot_factory
        self._alert_detail_snapshot_factory = alert_detail_snapshot_factory
        self._case_detail_snapshot_factory = case_detail_snapshot_factory
        self._record_to_dict = record_to_dict
        self._redacted_reconciliation_payload = redacted_reconciliation_payload
        self._normalize_admission_provenance = normalize_admission_provenance
        self._coordination_reference_payload = coordination_reference_payload
        self._coordination_reference_signature = coordination_reference_signature
        self._dedupe_strings = dedupe_strings

    def inspect_analyst_queue(self) -> object:
        active_alert_states = {
            "new",
            "triaged",
            "investigating",
            "escalated_to_case",
            "reopened",
        }
        latest_reconciliation_by_alert_id = (
            self._service._latest_detection_reconciliations_by_alert_id()
        )
        action_review_index = self._service._build_action_review_record_index()
        queue_records: list[dict[str, object]] = []
        for alert in self._service._store.list(AlertRecord):
            if alert.lifecycle_state not in active_alert_states:
                continue
            reconciliation = latest_reconciliation_by_alert_id.get(alert.alert_id)
            if reconciliation is None:
                continue

            if not self._service._reconciliation_is_wazuh_origin(reconciliation):
                continue

            source_systems = self._service._merge_linked_ids(
                reconciliation.subject_linkage.get("source_systems"),
                None,
            )
            substrate_detection_record_ids = self._service._merge_linked_ids(
                reconciliation.subject_linkage.get("substrate_detection_record_ids"),
                None,
            )
            case_record = (
                self._service._store.get(CaseRecord, alert.case_id)
                if alert.case_id is not None
                else None
            )
            action_reviews = self._service._action_review_chains_for_scope(
                case_id=alert.case_id,
                alert_id=alert.alert_id,
                record_index=action_review_index,
            )
            review_state = self._service._alert_review_state(alert)
            queue_records.append(
                {
                    "alert_id": alert.alert_id,
                    "finding_id": alert.finding_id,
                    "analytic_signal_id": alert.analytic_signal_id,
                    "case_id": alert.case_id,
                    "case_lifecycle_state": (
                        case_record.lifecycle_state if case_record is not None else None
                    ),
                    "queue_selection": "business_hours_triage",
                    "review_state": review_state,
                    "escalation_boundary": self._service._alert_escalation_boundary(alert),
                    "source_system": (
                        "wazuh"
                        if self._service._reconciliation_is_wazuh_origin(reconciliation)
                        else (source_systems[0] if source_systems else "wazuh")
                    ),
                    "substrate_detection_record_ids": substrate_detection_record_ids,
                    "accountable_source_identities": self._service._merge_linked_ids(
                        reconciliation.subject_linkage.get(
                            "accountable_source_identities"
                        ),
                        None,
                    ),
                    "reviewed_context": dict(alert.reviewed_context),
                    "native_rule": reconciliation.subject_linkage.get(
                        "latest_native_rule"
                    ),
                    "evidence_ids": self._service._merge_linked_ids(
                        reconciliation.subject_linkage.get("evidence_ids"),
                        None,
                    ),
                    "correlation_key": reconciliation.correlation_key,
                    "first_seen_at": reconciliation.first_seen_at,
                    "last_seen_at": reconciliation.last_seen_at,
                    "current_action_review": (
                        dict(action_reviews[0]) if action_reviews else None
                    ),
                }
            )

        queue_records.sort(
            key=lambda record: (
                record["last_seen_at"]
                or datetime.min.replace(tzinfo=timezone.utc),
                record["alert_id"],
            ),
            reverse=True,
        )
        return self._analyst_queue_snapshot_factory(
            read_only=True,
            queue_name="analyst_review",
            total_records=len(queue_records),
            records=tuple(queue_records),
        )

    def inspect_alert_detail(self, alert_id: str) -> object:
        alert_id = self._service._require_non_empty_string(alert_id, "alert_id")
        alert = self._service._store.get(AlertRecord, alert_id)
        if alert is None:
            raise LookupError(f"Missing alert record {alert_id!r} for detail inspection")

        reconciliation = self._service._latest_detection_reconciliations_by_alert_id().get(
            alert.alert_id
        )
        if reconciliation is None or not self._service._reconciliation_is_wazuh_origin(
            reconciliation
        ):
            raise LookupError(
                f"Missing reviewed Wazuh-backed reconciliation for alert {alert_id!r}"
            )

        case_record = (
            self._service._store.get(CaseRecord, alert.case_id)
            if alert.case_id is not None
            else None
        )
        analytic_signal_record = (
            self._service._store.get(AnalyticSignalRecord, alert.analytic_signal_id)
            if alert.analytic_signal_id is not None
            else None
        )
        evidence_records = self._service._assistant_evidence_records_for_context(
            alert_ids=(alert.alert_id,),
            case_ids=(),
            evidence_ids=self._service._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "evidence_ids",
            ),
            exclude_evidence_id=None,
        )
        source_systems = self._service._merge_linked_ids(
            reconciliation.subject_linkage.get("source_systems"),
            None,
        )
        substrate_detection_record_ids = self._service._merge_linked_ids(
            reconciliation.subject_linkage.get("substrate_detection_record_ids"),
            None,
        )
        source_system = (
            "wazuh"
            if self._service._reconciliation_is_wazuh_origin(reconciliation)
            else (
                "wazuh"
                if "wazuh" in source_systems
                else (source_systems[0] if source_systems else "wazuh")
            )
        )
        latest_reconciliation_payload = self._redacted_reconciliation_payload(
            reconciliation
        )
        lineage = {
            "finding_id": alert.finding_id,
            "analytic_signal_id": alert.analytic_signal_id,
            "case_id": alert.case_id,
            "reconciliation_id": reconciliation.reconciliation_id,
            "correlation_key": reconciliation.correlation_key,
            "source_systems": source_systems,
            "substrate_detection_record_ids": substrate_detection_record_ids,
            "accountable_source_identities": self._service._merge_linked_ids(
                reconciliation.subject_linkage.get("accountable_source_identities"),
                None,
            ),
            "evidence_ids": tuple(evidence.evidence_id for evidence in evidence_records),
            "first_seen_at": reconciliation.first_seen_at,
            "last_seen_at": reconciliation.last_seen_at,
        }
        action_reviews = self._service._action_review_chains_for_scope(
            case_id=alert.case_id,
            alert_id=alert.alert_id,
            record_index=self._service._build_action_review_record_index(),
        )

        return self._alert_detail_snapshot_factory(
            read_only=True,
            alert_id=alert.alert_id,
            alert=self._record_to_dict(alert),
            case_record=(
                self._record_to_dict(case_record) if case_record is not None else None
            ),
            analytic_signal_record=(
                self._record_to_dict(analytic_signal_record)
                if analytic_signal_record is not None
                else None
            ),
            latest_reconciliation=latest_reconciliation_payload,
            linked_evidence_records=tuple(
                self._record_to_dict(evidence) for evidence in evidence_records
            ),
            reviewed_context=dict(alert.reviewed_context),
            review_state=self._service._alert_review_state(alert),
            escalation_boundary=self._service._alert_escalation_boundary(alert),
            source_system=source_system,
            native_rule=(
                dict(reconciliation.subject_linkage.get("latest_native_rule"))
                if isinstance(
                    reconciliation.subject_linkage.get("latest_native_rule"),
                    Mapping,
                )
                else None
            ),
            provenance=self._normalize_admission_provenance(
                reconciliation.subject_linkage.get("admission_provenance")
            ),
            lineage=lineage,
            lifecycle_transitions=tuple(
                self._record_to_dict(transition)
                for transition in self._service.list_lifecycle_transitions(
                    "alert", alert.alert_id
                )
            ),
            current_action_review=dict(action_reviews[0]) if action_reviews else None,
            action_reviews=action_reviews,
            external_ticket_reference=self._build_alert_external_ticket_reference_surface(
                alert=alert,
                case_record=case_record,
            ),
        )

    def inspect_case_detail(self, case_id: str) -> object:
        case = self._service._require_reviewed_operator_case(case_id)
        case_id = case.case_id
        context_snapshot = self._service.inspect_assistant_context("case", case_id)
        observation_records = tuple(
            self._record_to_dict(record)
            for record in self._service._observations_for_case(case_id)
        )
        lead_records = tuple(
            self._record_to_dict(record) for record in self._service._leads_for_case(case_id)
        )
        action_reviews = self._service._action_review_chains_for_scope(
            case_id=case_id,
            alert_id=case.alert_id,
            record_index=self._service._build_action_review_record_index(),
        )
        cross_source_timeline, provenance_summary = self._build_case_cross_source_surfaces(
            case=case,
            linked_alert_records=context_snapshot.linked_alert_records,
            linked_evidence_records=context_snapshot.linked_evidence_records,
            linked_observation_records=observation_records,
        )
        return self._case_detail_snapshot_factory(
            read_only=True,
            case_id=case_id,
            case_record=dict(context_snapshot.record),
            advisory_output=dict(context_snapshot.advisory_output),
            reviewed_context=dict(context_snapshot.reviewed_context),
            linked_alert_ids=context_snapshot.linked_alert_ids,
            linked_observation_ids=tuple(
                record["observation_id"] for record in observation_records
            ),
            linked_lead_ids=tuple(record["lead_id"] for record in lead_records),
            linked_evidence_ids=context_snapshot.linked_evidence_ids,
            linked_recommendation_ids=context_snapshot.linked_recommendation_ids,
            linked_reconciliation_ids=context_snapshot.linked_reconciliation_ids,
            linked_alert_records=context_snapshot.linked_alert_records,
            linked_observation_records=observation_records,
            linked_lead_records=lead_records,
            linked_evidence_records=context_snapshot.linked_evidence_records,
            linked_recommendation_records=context_snapshot.linked_recommendation_records,
            linked_reconciliation_records=context_snapshot.linked_reconciliation_records,
            lifecycle_transitions=context_snapshot.lifecycle_transitions,
            cross_source_timeline=cross_source_timeline,
            provenance_summary=provenance_summary,
            current_action_review=dict(action_reviews[0]) if action_reviews else None,
            action_reviews=action_reviews,
            external_ticket_reference=self._build_case_external_ticket_reference_surface(
                case=case,
                linked_alert_records=context_snapshot.linked_alert_records,
            ),
        )

    def _build_alert_external_ticket_reference_surface(
        self,
        *,
        alert: AlertRecord,
        case_record: CaseRecord | None,
    ) -> dict[str, object]:
        alert_reference = self._coordination_reference_payload(alert)
        case_reference = self._coordination_reference_payload(case_record)
        if alert_reference is None and case_reference is None:
            status = "missing"
        elif alert_reference is None:
            status = "linked_case_reference_only"
        elif case_record is None:
            status = "present"
        elif case_reference is None:
            status = "linked_case_reference_missing"
        elif self._coordination_reference_signature(
            alert
        ) != self._coordination_reference_signature(case_record):
            status = "linked_case_reference_mismatch"
        else:
            status = "present"
        return {
            "authority": "non_authoritative",
            "status": status,
            "coordination_reference_id": (
                alert_reference["coordination_reference_id"]
                if alert_reference is not None
                else None
            ),
            "coordination_target_type": (
                alert_reference["coordination_target_type"]
                if alert_reference is not None
                else None
            ),
            "coordination_target_id": (
                alert_reference["coordination_target_id"]
                if alert_reference is not None
                else None
            ),
            "ticket_reference_url": (
                alert_reference["ticket_reference_url"]
                if alert_reference is not None
                else None
            ),
            "linked_case_id": case_record.case_id if case_record is not None else None,
            "linked_case_reference": case_reference,
        }

    def _build_case_external_ticket_reference_surface(
        self,
        *,
        case: CaseRecord,
        linked_alert_records: tuple[dict[str, object], ...],
    ) -> dict[str, object]:
        case_reference = self._coordination_reference_payload(case)
        linked_alert_references = tuple(
            {
                "alert_id": str(record.get("alert_id")),
                **reference,
            }
            for record in linked_alert_records
            for reference in (self._coordination_reference_payload(record),)
            if reference is not None
        )
        linked_alert_signatures = {
            (
                reference["coordination_reference_id"],
                reference["coordination_target_type"],
                reference["coordination_target_id"],
                reference["ticket_reference_url"],
            )
            for reference in linked_alert_references
        }
        linked_alert_ids = {
            str(record.get("alert_id"))
            for record in linked_alert_records
            if isinstance(record.get("alert_id"), str)
        }
        linked_alert_ids_with_reference = {
            reference["alert_id"] for reference in linked_alert_references
        }
        missing_linked_alert_ids = linked_alert_ids - linked_alert_ids_with_reference
        if case_reference is None and not linked_alert_references:
            status = "missing"
        elif case_reference is None and missing_linked_alert_ids:
            status = "linked_alert_reference_missing"
        elif case_reference is None and len(linked_alert_signatures) > 1:
            status = "linked_alert_reference_mismatch"
        elif case_reference is None:
            status = "linked_alert_reference_only"
        else:
            if missing_linked_alert_ids:
                status = "linked_alert_reference_missing"
            elif linked_alert_signatures and linked_alert_signatures != {
                self._coordination_reference_signature(case)
            }:
                status = "linked_alert_reference_mismatch"
            else:
                status = "present"

        return {
            "authority": "non_authoritative",
            "status": status,
            "coordination_reference_id": (
                case_reference["coordination_reference_id"]
                if case_reference is not None
                else None
            ),
            "coordination_target_type": (
                case_reference["coordination_target_type"]
                if case_reference is not None
                else None
            ),
            "coordination_target_id": (
                case_reference["coordination_target_id"]
                if case_reference is not None
                else None
            ),
            "ticket_reference_url": (
                case_reference["ticket_reference_url"]
                if case_reference is not None
                else None
            ),
            "linked_alert_references": linked_alert_references,
        }

    def _build_case_cross_source_surfaces(
        self,
        *,
        case: CaseRecord,
        linked_alert_records: tuple[dict[str, object], ...],
        linked_evidence_records: tuple[dict[str, object], ...],
        linked_observation_records: tuple[dict[str, object], ...],
    ) -> tuple[tuple[dict[str, object], ...], dict[str, object]]:
        anchor = self._build_case_cross_source_anchor(
            case=case,
            linked_alert_records=linked_alert_records,
        )
        attached_entries = [
            entry
            for entry in (
                *(
                    self._build_case_cross_source_attached_entry(
                        record_family="evidence",
                        record=record,
                        case_id=case.case_id,
                    )
                    for record in linked_evidence_records
                ),
                *(
                    self._build_case_cross_source_attached_entry(
                        record_family="observation",
                        record=record,
                        case_id=case.case_id,
                    )
                    for record in linked_observation_records
                ),
            )
            if entry is not None
        ]
        attached_entries.sort(
            key=lambda entry: (
                entry.get("_sort_occurred_at")
                or datetime.max.replace(tzinfo=timezone.utc),
                str(entry["record_family"]),
                str(entry["record_id"]),
            )
        )
        timeline = tuple(
            self._case_cross_source_public_entry(entry)
            for entry in (anchor, *attached_entries)
        )
        source_families = self._dedupe_strings(
            tuple(
                str(source_family)
                for source_family in (
                    entry.get("source_family") for entry in (anchor, *attached_entries)
                )
                if isinstance(source_family, str) and source_family.strip()
            )
        )
        provenance_summary = {
            "authoritative_anchor": {
                "record_family": anchor["record_family"],
                "record_id": anchor["record_id"],
                "source_family": anchor["source_family"],
                "provenance_classification": anchor["provenance_classification"],
                "reviewed_linkage": anchor["reviewed_linkage"],
            },
            "source_families": source_families,
            "attached_records": tuple(
                {
                    "record_family": entry["record_family"],
                    "record_id": entry["record_id"],
                    "source_family": entry["source_family"],
                    "evidence_origin": entry["evidence_origin"],
                    "provenance_classification": entry["provenance_classification"],
                    "ambiguity_badge": entry["ambiguity_badge"],
                    "reviewed_linkage": entry["reviewed_linkage"],
                    "blocking_reason": entry["blocking_reason"],
                }
                for entry in attached_entries
            ),
        }
        return timeline, provenance_summary

    def _build_case_cross_source_anchor(
        self,
        *,
        case: CaseRecord,
        linked_alert_records: tuple[dict[str, object], ...],
    ) -> dict[str, object]:
        anchor_record = next(
            (
                dict(record)
                for record in linked_alert_records
                if record.get("alert_id") == case.alert_id
            ),
            {
                "alert_id": case.alert_id,
                "case_id": case.case_id,
                "reviewed_context": dict(case.reviewed_context),
            },
        )
        source_family = self._service._reviewed_operator_source_family(
            anchor_record.get("reviewed_context")
        ) or self._service._reviewed_operator_source_family(case.reviewed_context)
        return {
            "record_family": "alert",
            "record_id": case.alert_id,
            "source_family": source_family or "unknown",
            "evidence_origin": case.alert_id,
            "provenance_classification": "authoritative-anchor",
            "ambiguity_badge": None,
            "reviewed_linkage": {
                "case_id": case.case_id,
                "alert_id": case.alert_id,
            },
            "blocking_reason": None,
            "occurred_at": None,
            "_sort_occurred_at": None,
        }

    def _build_case_cross_source_attached_entry(
        self,
        *,
        record_family: str,
        record: Mapping[str, object],
        case_id: str,
    ) -> dict[str, object] | None:
        raw_provenance = record.get("provenance")
        provenance_missing = not isinstance(raw_provenance, Mapping) or not raw_provenance
        provenance = raw_provenance if isinstance(raw_provenance, Mapping) else {}

        def _safe_optional_string(value: object, field_name: str) -> str | None:
            if isinstance(value, str):
                value = value.strip()
            try:
                return self._service._normalize_optional_string(value, field_name)
            except ValueError:
                return None

        record_id_field = f"{record_family}_id"
        record_id = self._service._normalize_optional_string(
            record.get(record_id_field),
            record_id_field,
        )
        if record_id is None:
            return None

        explicit_source_family = _safe_optional_string(
            provenance.get("source_family"),
            f"{record_family}.provenance.source_family",
        )
        source_system = _safe_optional_string(
            provenance.get("source_system"),
            f"{record_family}.provenance.source_system",
        ) or _safe_optional_string(
            record.get("source_system"),
            f"{record_family}.source_system",
        )
        source_family = explicit_source_family or source_system or "unknown"

        classification = _safe_optional_string(
            provenance.get("classification"),
            f"{record_family}.provenance.classification",
        )
        source_id = _safe_optional_string(
            provenance.get("source_id"),
            f"{record_family}.provenance.source_id",
        )
        timestamp = _safe_optional_string(
            provenance.get("timestamp"),
            f"{record_family}.provenance.timestamp",
        )
        reviewed_by = _safe_optional_string(
            provenance.get("reviewed_by"),
            f"{record_family}.provenance.reviewed_by",
        )
        blocking_reason = _safe_optional_string(
            provenance.get("blocking_reason"),
            f"{record_family}.provenance.blocking_reason",
        )
        if None in (classification, source_id, timestamp, reviewed_by):
            classification = "unresolved-linkage"
            if blocking_reason is None:
                blocking_reason = (
                    "missing_provenance"
                    if provenance_missing
                    else "missing_or_invalid_required_provenance_fields"
                )

        ambiguity_badge = _safe_optional_string(
            provenance.get("ambiguity_badge"),
            f"{record_family}.provenance.ambiguity_badge",
        )
        if ambiguity_badge not in {"same-entity", "related-entity", "unresolved"}:
            ambiguity_badge = "unresolved"

        occurred_at = None
        if isinstance(record.get("acquired_at"), datetime):
            occurred_at = record.get("acquired_at")
        elif isinstance(record.get("observed_at"), datetime):
            occurred_at = record.get("observed_at")

        reviewed_linkage: dict[str, object] = {"case_id": case_id}
        if record_family == "observation":
            supporting_evidence_ids = tuple(record.get("supporting_evidence_ids", ()))
            reviewed_linkage["supporting_evidence_ids"] = supporting_evidence_ids

        evidence_origin = self._service._normalize_optional_string(
            record.get("source_record_id"),
            f"{record_family}.source_record_id",
        ) or source_id

        return {
            "record_family": record_family,
            "record_id": record_id,
            "source_family": source_family,
            "evidence_origin": evidence_origin,
            "provenance_classification": classification,
            "ambiguity_badge": ambiguity_badge,
            "reviewed_linkage": reviewed_linkage,
            "blocking_reason": blocking_reason,
            "occurred_at": occurred_at,
            "_sort_occurred_at": occurred_at,
        }

    @staticmethod
    def _case_cross_source_public_entry(entry: Mapping[str, object]) -> dict[str, object]:
        return {
            "record_family": entry["record_family"],
            "record_id": entry["record_id"],
            "occurred_at": entry["occurred_at"],
            "source_family": entry["source_family"],
            "evidence_origin": entry["evidence_origin"],
            "provenance_classification": entry["provenance_classification"],
            "ambiguity_badge": entry["ambiguity_badge"],
            "reviewed_linkage": entry["reviewed_linkage"],
            "blocking_reason": entry["blocking_reason"],
        }
