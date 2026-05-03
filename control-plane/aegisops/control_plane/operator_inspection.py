from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol, Type, TypeVar

from .models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    AnalyticSignalRecord,
    AITraceRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    LifecycleTransitionRecord,
    ObservationRecord,
    LeadRecord,
    RecommendationRecord,
    ReconciliationRecord,
)


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


_QUEUE_LANES = (
    "action_required",
    "reconciliation_mismatch",
    "stale_receipt",
    "optional_extension_degraded",
    "clean",
)


class InspectionStore(Protocol):
    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        ...

    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        ...

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        ...


class OperatorInspectionServiceDependencies(Protocol):
    _assistant_context_assembler: Any
    _store: InspectionStore

    def _require_reviewed_operator_alert_record(self, alert: AlertRecord) -> AlertRecord:
        ...

    def _alert_is_in_reviewed_operator_slice(self, alert: AlertRecord) -> bool:
        ...

    def _latest_detection_reconciliations_by_alert_id(
        self,
    ) -> dict[str, ReconciliationRecord]:
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

    def _alert_escalation_boundary(self, alert: AlertRecord) -> str:
        ...

    _ai_trace_lifecycle_service: Any

    def _require_non_empty_string(self, value: str, field_name: str) -> str:
        ...

    def _require_reviewed_operator_case(self, case_id: str) -> CaseRecord:
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
        action_review_inspection_boundary: Any,
        analyst_queue_snapshot_factory: Callable[..., object],
        alert_detail_snapshot_factory: Callable[..., object],
        case_detail_snapshot_factory: Callable[..., object],
        action_review_detail_snapshot_factory: Callable[..., object],
        record_to_dict: Callable[[object], dict[str, object]],
        redacted_reconciliation_payload: Callable[[ReconciliationRecord], dict[str, object]],
        normalize_admission_provenance: Callable[[object], dict[str, str] | None],
        coordination_reference_payload: Callable[[object], dict[str, object] | None],
        coordination_reference_signature: Callable[[object], tuple[object, ...] | None],
        dedupe_strings: Callable[[tuple[str, ...]], tuple[str, ...]],
    ) -> None:
        self._service = service
        self._action_review_inspection_boundary = action_review_inspection_boundary
        self._analyst_queue_snapshot_factory = analyst_queue_snapshot_factory
        self._alert_detail_snapshot_factory = alert_detail_snapshot_factory
        self._case_detail_snapshot_factory = case_detail_snapshot_factory
        self._action_review_detail_snapshot_factory = action_review_detail_snapshot_factory
        self._record_to_dict = record_to_dict
        self._redacted_reconciliation_payload = redacted_reconciliation_payload
        self._normalize_admission_provenance = normalize_admission_provenance
        self._coordination_reference_payload = coordination_reference_payload
        self._coordination_reference_signature = coordination_reference_signature
        self._dedupe_strings = dedupe_strings

    @staticmethod
    def _optional_string_from_mapping(
        mapping: Mapping[str, object],
        key: str,
    ) -> str | None:
        value = mapping.get(key)
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _string_tuple_from_object(value: object) -> tuple[str, ...]:
        if isinstance(value, str) and value.strip():
            return (value.strip(),)
        if isinstance(value, (tuple, list)):
            return tuple(
                entry.strip()
                for entry in value
                if isinstance(entry, str) and entry.strip()
            )
        return ()

    def _observations_for_case(self, case_id: str) -> tuple[ObservationRecord, ...]:
        return tuple(
            sorted(
                (
                    record
                    for record in self._service._store.list(ObservationRecord)
                    if record.case_id == case_id
                ),
                key=lambda record: (record.observed_at, record.observation_id),
            )
        )

    def _leads_for_case(self, case_id: str) -> tuple[LeadRecord, ...]:
        return tuple(
            sorted(
                (
                    record
                    for record in self._service._store.list(LeadRecord)
                    if record.case_id == case_id
                ),
                key=lambda record: record.lead_id,
            )
        )

    @staticmethod
    def _alert_review_state(alert: AlertRecord) -> str:
        if alert.lifecycle_state in {"new", "reopened"}:
            return "pending_review"
        if alert.lifecycle_state == "escalated_to_case":
            return "case_required"
        if alert.lifecycle_state == "investigating":
            return "investigating"
        return "triaged"

    def _ai_trace_review_states(
        self,
        *,
        lifecycle_state: str,
        provider_status: str | None,
        provider_operational_quality: str | None,
        draft_status: str | None,
        unresolved_reasons: tuple[str, ...],
    ) -> tuple[str, ...]:
        states: list[str] = []
        if "conflicting_reviewed_context" in unresolved_reasons:
            states.append("conflict")
        if (
            "missing_supporting_citations" in unresolved_reasons
            or "missing_evidence_citation" in unresolved_reasons
        ):
            states.append("citation_failure")
        if (
            provider_status in {"failed", "timeout"}
            or provider_operational_quality == "degraded"
            or "provider_generation_failed" in unresolved_reasons
        ):
            states.append("provider_degraded")
        if lifecycle_state == "under_review" or draft_status == "unresolved":
            states.append("unresolved")
        return tuple(dict.fromkeys(states))

    def _ai_trace_review_groups_for_queue_record(
        self,
        *,
        alert_id: str,
        case_id: str | None,
        ai_trace_records: tuple[AITraceRecord, ...],
    ) -> tuple[dict[str, object], ...]:
        groups_by_scope: dict[str, dict[str, object]] = {}
        for ai_trace in ai_trace_records:
            subject_linkage = ai_trace.subject_linkage
            linked_alert_id = self._optional_string_from_mapping(
                subject_linkage,
                "source_alert_id",
            )
            linked_case_id = self._optional_string_from_mapping(
                subject_linkage,
                "source_case_id",
            )
            if linked_alert_id != alert_id and (
                case_id is None or linked_case_id != case_id
            ):
                continue

            assistant_advisory_draft = ai_trace.assistant_advisory_draft
            draft_status = self._optional_string_from_mapping(
                assistant_advisory_draft,
                "status",
            )
            unresolved_reasons = self._string_tuple_from_object(
                assistant_advisory_draft.get("unresolved_reasons")
            )
            provider_status = self._optional_string_from_mapping(
                subject_linkage,
                "provider_status",
            )
            provider_operational_quality = self._optional_string_from_mapping(
                subject_linkage,
                "provider_operational_quality",
            )
            states = self._ai_trace_review_states(
                lifecycle_state=ai_trace.lifecycle_state,
                provider_status=provider_status,
                provider_operational_quality=provider_operational_quality,
                draft_status=draft_status,
                unresolved_reasons=unresolved_reasons,
            )
            if not states:
                continue

            group_case_id = linked_case_id or case_id
            group_key = group_case_id or alert_id
            group = groups_by_scope.setdefault(
                group_key,
                {
                    "alert_id": alert_id,
                    "case_id": group_case_id,
                    "states": [],
                    "traces": [],
                },
            )
            group["states"] = list(
                dict.fromkeys([*group["states"], *states])  # type: ignore[arg-type]
            )
            traces = group["traces"]
            if not isinstance(traces, list):
                continue
            traces.append(
                {
                    "ai_trace_id": ai_trace.ai_trace_id,
                    "lifecycle_state": ai_trace.lifecycle_state,
                    "draft_status": draft_status,
                    "provider_status": provider_status,
                    "provider_operational_quality": provider_operational_quality,
                    "unresolved_reasons": unresolved_reasons,
                    "material_input_refs": ai_trace.material_input_refs,
                    "trace_link": f"/operator/assistant/ai_trace/{ai_trace.ai_trace_id}",
                }
            )

        groups: list[dict[str, object]] = []
        for group in groups_by_scope.values():
            traces = group["traces"]
            if not isinstance(traces, list) or not traces:
                continue
            sorted_traces = sorted(
                traces,
                key=lambda trace: str(trace.get("ai_trace_id", "")),
            )
            first_trace = sorted_traces[0]
            group["traces"] = tuple(sorted_traces)
            group["trace_count"] = len(sorted_traces)
            group["trace_link"] = first_trace.get("trace_link")
            groups.append(group)

        return tuple(
            sorted(
                groups,
                key=lambda group: (
                    str(group.get("case_id") or ""),
                    str(group.get("alert_id") or ""),
                ),
            )
        )

    @staticmethod
    def _queue_age_bucket(age_seconds: int) -> str:
        if age_seconds >= 24 * 60 * 60:
            return "stale"
        return "fresh"

    @staticmethod
    def _queue_severity_from_reviewed_context(
        reviewed_context: Mapping[str, object],
    ) -> str:
        provenance = reviewed_context.get("provenance")
        rule_level = (
            provenance.get("rule_level")
            if isinstance(provenance, Mapping)
            else None
        )
        if isinstance(rule_level, int):
            if rule_level >= 12:
                return "critical"
            if rule_level >= 7:
                return "high"
            if rule_level >= 4:
                return "medium"
            return "low"

        explicit_severity = reviewed_context.get("severity")
        if isinstance(explicit_severity, str) and explicit_severity in {
            "low",
            "medium",
            "high",
            "critical",
        }:
            return explicit_severity

        return "medium"

    def _queue_owner(
        self,
        *,
        alert_id: str,
        case_id: str | None,
        reviewed_context: Mapping[str, object],
        action_reviews: tuple[dict[str, object], ...],
    ) -> str | None:
        if action_reviews:
            requester_identity = action_reviews[0].get("requester_identity")
            if isinstance(requester_identity, str) and requester_identity.strip():
                return requester_identity.strip()

        recommendations = [
            recommendation
            for recommendation in self._service._store.list(RecommendationRecord)
            if recommendation.alert_id == alert_id
            or (case_id is not None and recommendation.case_id == case_id)
        ]
        if recommendations:
            latest_recommendation = sorted(
                recommendations,
                key=lambda recommendation: recommendation.recommendation_id,
                reverse=True,
            )[0]
            return latest_recommendation.review_owner

        leads = [
            lead
            for lead in self._service._store.list(LeadRecord)
            if lead.alert_id == alert_id
            or (case_id is not None and lead.case_id == case_id)
        ]
        if leads:
            latest_lead = sorted(
                leads,
                key=lambda lead: lead.lead_id,
                reverse=True,
            )[0]
            return latest_lead.triage_owner

        handoff = reviewed_context.get("handoff")
        if isinstance(handoff, Mapping):
            handoff_owner = handoff.get("handoff_owner")
            if isinstance(handoff_owner, str) and handoff_owner.strip():
                return handoff_owner.strip()

        return None

    def _queue_next_action(
        self,
        *,
        alert_id: str,
        case_id: str | None,
        review_state: str,
        action_reviews: tuple[dict[str, object], ...],
    ) -> str:
        if action_reviews:
            next_expected_action = action_reviews[0].get("next_expected_action")
            if isinstance(next_expected_action, str) and next_expected_action.strip():
                return next_expected_action.strip()

        recommendations = [
            recommendation
            for recommendation in self._service._store.list(RecommendationRecord)
            if recommendation.alert_id == alert_id
            or (case_id is not None and recommendation.case_id == case_id)
        ]
        if recommendations:
            latest_recommendation = sorted(
                recommendations,
                key=lambda recommendation: recommendation.recommendation_id,
                reverse=True,
            )[0]
            return latest_recommendation.intended_outcome

        if case_id is None:
            return "Promote alert to case"
        if review_state == "case_required":
            return "Review linked case"
        return "Review queue record"

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
        action_review_index = self._action_review_inspection_boundary.build_record_index()
        ai_trace_records = self._service._store.list(AITraceRecord)
        queue_records: list[dict[str, object]] = []
        for alert in self._service._store.list(AlertRecord):
            if alert.lifecycle_state not in active_alert_states:
                continue
            reconciliation = latest_reconciliation_by_alert_id.get(alert.alert_id)
            if reconciliation is None:
                continue

            if not self._service._reconciliation_is_wazuh_origin(reconciliation):
                continue
            queue_records.append(
                self._queue_record_for_alert(
                    alert=alert,
                    reconciliation=reconciliation,
                    action_review_index=action_review_index,
                    ai_trace_records=ai_trace_records,
                )
            )

        queue_records = self._sorted_queue_records(queue_records)
        return self._analyst_queue_snapshot_factory(
            read_only=True,
            queue_name="analyst_review",
            total_records=len(queue_records),
            lane_counts=self._queue_lane_counts(queue_records),
            records=tuple(queue_records),
        )

    def _queue_record_for_alert(
        self,
        *,
        alert: AlertRecord,
        reconciliation: ReconciliationRecord,
        action_review_index: object,
        ai_trace_records: tuple[AITraceRecord, ...],
    ) -> dict[str, object]:
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
        action_reviews = self._action_review_inspection_boundary.chains_for_scope(
            case_id=alert.case_id,
            alert_id=alert.alert_id,
            record_index=action_review_index,
        )
        review_state = self._alert_review_state(alert)
        ai_trace_review_groups = self._ai_trace_review_groups_for_queue_record(
            alert_id=alert.alert_id,
            case_id=alert.case_id,
            ai_trace_records=ai_trace_records,
        )
        queue_lanes, queue_lane_details = self._queue_lanes_for_record(
            alert=alert,
            reconciliation=reconciliation,
            review_state=review_state,
            action_reviews=action_reviews,
        )
        now = datetime.now(timezone.utc)
        first_seen_at = reconciliation.first_seen_at
        age_seconds = (
            max(0, int((now - first_seen_at).total_seconds()))
            if first_seen_at is not None
            else 0
        )
        last_activity_at = reconciliation.last_seen_at or first_seen_at
        owner_reviewed_context = (
            case_record.reviewed_context if case_record is not None else alert.reviewed_context
        )
        return {
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
                reconciliation.subject_linkage.get("accountable_source_identities"),
                None,
            ),
            "reviewed_context": dict(alert.reviewed_context),
            "native_rule": reconciliation.subject_linkage.get("latest_native_rule"),
            "evidence_ids": self._service._merge_linked_ids(
                reconciliation.subject_linkage.get("evidence_ids"),
                None,
            ),
            "correlation_key": reconciliation.correlation_key,
            "first_seen_at": reconciliation.first_seen_at,
            "last_seen_at": reconciliation.last_seen_at,
            "owner": self._queue_owner(
                alert_id=alert.alert_id,
                case_id=alert.case_id,
                reviewed_context=owner_reviewed_context,
                action_reviews=action_reviews,
            ),
            "age_seconds": age_seconds,
            "age_bucket": self._queue_age_bucket(age_seconds),
            "severity": self._queue_severity_from_reviewed_context(alert.reviewed_context),
            "last_activity_at": last_activity_at,
            "next_action": self._queue_next_action(
                alert_id=alert.alert_id,
                case_id=alert.case_id,
                review_state=review_state,
                action_reviews=action_reviews,
            ),
            "queue_lanes": queue_lanes,
            "queue_lane_details": queue_lane_details,
            "current_action_review": dict(action_reviews[0]) if action_reviews else None,
            "ai_trace_review_groups": ai_trace_review_groups,
        }

    @staticmethod
    def _sorted_queue_records(
        queue_records: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        return sorted(
            queue_records,
            key=lambda record: (
                record["last_seen_at"]
                or datetime.min.replace(tzinfo=timezone.utc),
                record["alert_id"],
            ),
            reverse=True,
        )

    def _queue_lanes_for_record(
        self,
        *,
        alert: AlertRecord,
        reconciliation: ReconciliationRecord,
        review_state: str,
        action_reviews: tuple[dict[str, object], ...],
    ) -> tuple[tuple[str, ...], dict[str, object]]:
        lanes: list[str] = []
        details: dict[str, object] = {}

        if review_state in {"pending_review", "case_required", "investigating", "degraded"}:
            lanes.append("action_required")

        if action_reviews:
            current_review_state = action_reviews[0].get("review_state")
            if current_review_state not in {None, "approved", "completed", "matched"}:
                if "action_required" not in lanes:
                    lanes.append("action_required")

        if reconciliation.lifecycle_state == "mismatched":
            lanes.append("reconciliation_mismatch")
            details["reconciliation_mismatch"] = {
                "state": reconciliation.lifecycle_state,
                "summary": reconciliation.mismatch_summary,
            }

        stale_receipt_state = None
        if reconciliation.lifecycle_state == "stale":
            stale_receipt_state = reconciliation.lifecycle_state
        elif reconciliation.ingest_disposition == "stale":
            stale_receipt_state = reconciliation.ingest_disposition

        if stale_receipt_state is not None:
            lanes.append("stale_receipt")
            details["stale_receipt"] = {
                "state": stale_receipt_state,
                "lifecycle_state": reconciliation.lifecycle_state,
                "ingest_disposition": reconciliation.ingest_disposition,
                "summary": reconciliation.mismatch_summary,
            }

        degraded_optional_extensions = self._degraded_optional_extensions(alert.reviewed_context)
        if degraded_optional_extensions:
            lanes.append("optional_extension_degraded")
            details["optional_extension_degraded"] = degraded_optional_extensions

        if not lanes:
            lanes.append("clean")

        return tuple(lanes), details

    @staticmethod
    def _degraded_optional_extensions(
        reviewed_context: Mapping[str, object],
    ) -> dict[str, object]:
        optional_extensions = reviewed_context.get("optional_extensions")
        if not isinstance(optional_extensions, Mapping):
            return {}

        degraded_extensions: dict[str, object] = {}
        for extension_name, extension_state in optional_extensions.items():
            if not isinstance(extension_state, Mapping):
                continue
            if extension_state.get("readiness") == "degraded":
                degraded_extensions[str(extension_name)] = dict(extension_state)
        return degraded_extensions

    @staticmethod
    def _queue_lane_counts(
        queue_records: list[dict[str, object]],
    ) -> dict[str, int]:
        lane_counts = {lane: 0 for lane in _QUEUE_LANES}
        for record in queue_records:
            queue_lanes = record.get("queue_lanes")
            if not isinstance(queue_lanes, tuple):
                continue
            for lane in queue_lanes:
                if isinstance(lane, str) and lane in lane_counts:
                    lane_counts[lane] += 1
        return lane_counts

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
        evidence_records = (
            self._service._ai_trace_lifecycle_service.evidence_records_for_context(
                alert_ids=(alert.alert_id,),
                case_ids=(),
                evidence_ids=self._service._ai_trace_lifecycle_service.ids_from_mapping(
                    reconciliation.subject_linkage,
                    "evidence_ids",
                ),
                exclude_evidence_id=None,
            )
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
        action_reviews = self._action_review_inspection_boundary.chains_for_scope(
            case_id=alert.case_id,
            alert_id=alert.alert_id,
            record_index=self._action_review_inspection_boundary.build_record_index(),
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
            review_state=self._alert_review_state(alert),
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
                for transition in self._service._store.list_lifecycle_transitions(
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
        context_snapshot = (
            self._service._assistant_context_assembler.inspect_assistant_context(
                "case",
                case_id,
            )
        )
        observation_records = tuple(
            self._record_to_dict(record)
            for record in self._observations_for_case(case_id)
        )
        lead_records = tuple(
            self._record_to_dict(record) for record in self._leads_for_case(case_id)
        )
        action_reviews = self._action_review_inspection_boundary.chains_for_scope(
            case_id=case_id,
            alert_id=case.alert_id,
            record_index=self._action_review_inspection_boundary.build_record_index(),
        )
        cross_source_timeline, provenance_summary = self._build_case_cross_source_surfaces(
            case=case,
            linked_alert_records=context_snapshot.linked_alert_records,
            linked_evidence_records=context_snapshot.linked_evidence_records,
            linked_observation_records=observation_records,
        )
        case_timeline_projection = self._build_case_timeline_projection(
            case=case,
            linked_alert_records=context_snapshot.linked_alert_records,
            linked_evidence_records=context_snapshot.linked_evidence_records,
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
            case_timeline_projection=case_timeline_projection,
            provenance_summary=provenance_summary,
            current_action_review=dict(action_reviews[0]) if action_reviews else None,
            action_reviews=action_reviews,
            external_ticket_reference=self._build_case_external_ticket_reference_surface(
                case=case,
                linked_alert_records=context_snapshot.linked_alert_records,
            ),
        )

    def _build_case_timeline_projection(
        self,
        *,
        case: CaseRecord,
        linked_alert_records: tuple[dict[str, object], ...],
        linked_evidence_records: tuple[dict[str, object], ...],
    ) -> dict[str, object]:
        alert_id = case.alert_id
        directly_linked_alert = next(
            (
                record
                for record in linked_alert_records
                if isinstance(record.get("alert_id"), str)
                and record.get("alert_id") == alert_id
            ),
            None,
        )
        evidence_records = tuple(
            record
            for record in linked_evidence_records
            if record.get("case_id") == case.case_id or record.get("alert_id") == alert_id
        )
        ai_trace = self._latest_direct_case_ai_trace(
            case=case,
            evidence_records=evidence_records,
        )
        recommendation = self._latest_direct_case_recommendation(case)
        action_request = self._latest_direct_case_action_request(case)
        approval = (
            self._service._store.get(
                ApprovalDecisionRecord,
                action_request.approval_decision_id,
            )
            if action_request is not None
            and action_request.approval_decision_id is not None
            else None
        )
        execution = (
            self._latest_direct_action_execution(action_request)
            if action_request is not None
            else None
        )
        reconciliation = self._latest_direct_case_reconciliation(
            case=case,
            action_request=action_request,
            execution=execution,
        )
        segments = (
            self._case_wazuh_signal_timeline_segment(reconciliation),
            self._case_timeline_segment(
                segment="aegisops_alert",
                authority_posture="authoritative_aegisops_record",
                record_family="alert",
                record_id=alert_id if directly_linked_alert is not None else None,
                state="normal" if directly_linked_alert is not None else "missing",
                incomplete_reason=(
                    None
                    if directly_linked_alert is not None
                    else "missing_authoritative_alert"
                ),
                truth_source="aegisops_alert_record",
            ),
            self._case_evidence_timeline_segment(evidence_records),
            self._case_timeline_segment(
                segment="ai_summary",
                authority_posture="subordinate_context",
                record_family="ai_trace",
                record_id=None if ai_trace is None else ai_trace.ai_trace_id,
                state="normal" if ai_trace is not None else "missing",
                incomplete_reason=(
                    None if ai_trace is not None else "missing_direct_ai_trace_binding"
                ),
                truth_source="aegisops_case_record",
            ),
            self._case_timeline_segment(
                segment="recommendation",
                authority_posture="subordinate_context",
                record_family="recommendation",
                record_id=(
                    None
                    if recommendation is None
                    else recommendation.recommendation_id
                ),
                state="normal" if recommendation is not None else "missing",
                incomplete_reason=(
                    None
                    if recommendation is not None
                    else "missing_direct_recommendation_binding"
                ),
                truth_source="aegisops_recommendation_record",
            ),
            self._case_timeline_segment(
                segment="action_request",
                authority_posture="authoritative_aegisops_record",
                record_family="action_request",
                record_id=(
                    None if action_request is None else action_request.action_request_id
                ),
                state="normal" if action_request is not None else "missing",
                incomplete_reason=(
                    None
                    if action_request is not None
                    else "missing_direct_action_request_binding"
                ),
                truth_source="aegisops_action_request_record",
            ),
            self._case_timeline_segment(
                segment="approval",
                authority_posture="authoritative_aegisops_record",
                record_family="approval_decision",
                record_id=(
                    None if approval is None else approval.approval_decision_id
                ),
                state="normal" if approval is not None else "missing",
                incomplete_reason=(
                    None if approval is not None else "missing_direct_approval_binding"
                ),
                truth_source="aegisops_approval_decision_record",
            ),
            self._case_shuffle_receipt_timeline_segment(execution),
            self._case_reconciliation_timeline_segment(reconciliation),
        )
        return {
            "contract_version": "phase-56-3",
            "case_id": case.case_id,
            "authority_boundary": (
                "Case timeline projection is derived display context only; "
                "AegisOps records remain authoritative for alert, case, evidence, "
                "approval, action request, receipt, reconciliation, audit, gate, "
                "release, and closeout truth."
            ),
            "projection_authority_allowed": False,
            "inferred_linkage_allowed": False,
            "segments": segments,
        }

    @staticmethod
    def _case_timeline_segment(
        *,
        segment: str,
        authority_posture: str,
        record_family: str,
        record_id: str | None,
        state: str,
        incomplete_reason: str | None,
        truth_source: str,
    ) -> dict[str, object]:
        return {
            "segment": segment,
            "authority_posture": authority_posture,
            "state": state,
            "operator_visible": True,
            "backend_record_binding": {
                "record_family": record_family,
                "record_id": record_id,
                "direct_binding_required": True,
            },
            "truth_source": truth_source,
            "projection_can_complete_segment": False,
            "incomplete_reason": incomplete_reason,
        }

    def _case_wazuh_signal_timeline_segment(
        self,
        reconciliation: ReconciliationRecord | None,
    ) -> dict[str, object]:
        is_wazuh_origin = (
            reconciliation is not None
            and self._service._reconciliation_is_wazuh_origin(reconciliation)
        )
        if is_wazuh_origin:
            state = "normal"
            reason = None
        elif reconciliation is None:
            state = "missing"
            reason = "missing_wazuh_signal_binding"
        else:
            state = "unsupported"
            reason = "unsupported_wazuh_binding"
        return self._case_timeline_segment(
            segment="wazuh_signal",
            authority_posture="subordinate_context",
            record_family="reconciliation",
            record_id=(
                None if not is_wazuh_origin else reconciliation.reconciliation_id
            ),
            state=state,
            incomplete_reason=reason,
            truth_source="aegisops_alert_admission_record",
        )

    def _case_shuffle_receipt_timeline_segment(
        self,
        execution: ActionExecutionRecord | None,
    ) -> dict[str, object]:
        if execution is None:
            state = "missing"
            reason = "missing_direct_shuffle_receipt_binding"
        elif execution.execution_surface_id == "shuffle":
            state = "normal"
            reason = None
        else:
            state = "unsupported"
            reason = f"unsupported_execution_surface:{execution.execution_surface_id}"
        return self._case_timeline_segment(
            segment="shuffle_receipt",
            authority_posture="subordinate_context",
            record_family="action_execution",
            record_id=None if execution is None else execution.action_execution_id,
            state=state,
            incomplete_reason=reason,
            truth_source="aegisops_action_execution_record",
        )

    def _case_evidence_timeline_segment(
        self,
        evidence_records: tuple[dict[str, object], ...],
    ) -> dict[str, object]:
        first_record = evidence_records[0] if evidence_records else None
        degraded_reason = next(
            (
                reason
                for record in evidence_records
                for reason in (self._case_evidence_degraded_reason(record),)
                if reason is not None
            ),
            None,
        )
        if not evidence_records:
            state = "missing"
            reason = "missing_direct_evidence_binding"
        elif degraded_reason is not None:
            state = "degraded"
            reason = degraded_reason
        else:
            state = "normal"
            reason = None
        return self._case_timeline_segment(
            segment="evidence",
            authority_posture="authoritative_aegisops_record",
            record_family="evidence",
            record_id=(
                None
                if first_record is None
                else self._service._normalize_optional_string(
                    first_record.get("evidence_id"),
                    "evidence.evidence_id",
                )
            ),
            state=state,
            incomplete_reason=reason,
            truth_source="aegisops_evidence_record",
        )

    @staticmethod
    def _case_evidence_degraded_reason(record: Mapping[str, object]) -> str | None:
        blocking_reason = record.get("blocking_reason")
        if isinstance(blocking_reason, str) and blocking_reason:
            return blocking_reason
        provenance = record.get("provenance")
        if not isinstance(provenance, Mapping) or not provenance:
            return "missing_provenance"
        required_fields = ("classification", "source_id", "timestamp", "reviewed_by")
        if any(
            not isinstance(provenance.get(field), str) or not provenance.get(field)
            for field in required_fields
        ):
            return "missing_or_invalid_required_provenance_fields"
        return None

    def _case_reconciliation_timeline_segment(
        self,
        reconciliation: ReconciliationRecord | None,
    ) -> dict[str, object]:
        if reconciliation is None:
            state = "missing"
            reason = "missing_direct_reconciliation_binding"
        elif reconciliation.lifecycle_state == "matched":
            state = "normal"
            reason = None
        elif reconciliation.lifecycle_state in {"mismatched", "pending"}:
            state = "mismatch"
            reason = reconciliation.mismatch_summary or reconciliation.lifecycle_state
        elif reconciliation.lifecycle_state == "stale":
            state = "stale"
            reason = reconciliation.mismatch_summary or "stale_reconciliation"
        else:
            state = "unsupported"
            reason = reconciliation.lifecycle_state
        return self._case_timeline_segment(
            segment="reconciliation",
            authority_posture="authoritative_aegisops_record",
            record_family="reconciliation",
            record_id=(
                None if reconciliation is None else reconciliation.reconciliation_id
            ),
            state=state,
            incomplete_reason=reason,
            truth_source="aegisops_reconciliation_record",
        )

    def _latest_direct_case_ai_trace(
        self,
        *,
        case: CaseRecord,
        evidence_records: tuple[dict[str, object], ...],
    ) -> AITraceRecord | None:
        evidence_ids = {
            evidence_id
            for record in evidence_records
            for evidence_id in (record.get("evidence_id"),)
            if isinstance(evidence_id, str)
        }
        candidates = [
            record
            for record in self._service._store.list(AITraceRecord)
            if self._ai_trace_directly_binds_case(
                record,
                case=case,
                evidence_ids=evidence_ids,
            )
        ]
        candidates.sort(
            key=lambda record: (record.generated_at, record.ai_trace_id),
            reverse=True,
        )
        return candidates[0] if candidates else None

    @staticmethod
    def _ai_trace_directly_binds_case(
        record: AITraceRecord,
        *,
        case: CaseRecord,
        evidence_ids: set[str],
    ) -> bool:
        linkage = record.subject_linkage
        case_ids = linkage.get("case_ids")
        alert_ids = linkage.get("alert_ids")
        linked_evidence_ids = linkage.get("evidence_ids")
        if isinstance(case_ids, (list, tuple)) and case.case_id in case_ids:
            return True
        if isinstance(alert_ids, (list, tuple)) and case.alert_id in alert_ids:
            return True
        if (
            evidence_ids
            and isinstance(linked_evidence_ids, (list, tuple))
            and any(evidence_id in evidence_ids for evidence_id in linked_evidence_ids)
        ):
            return True
        return False

    def _latest_direct_case_recommendation(
        self,
        case: CaseRecord,
    ) -> RecommendationRecord | None:
        candidates = [
            record
            for record in self._service._store.list(RecommendationRecord)
            if record.case_id == case.case_id or record.alert_id == case.alert_id
        ]
        candidates.sort(key=lambda record: record.recommendation_id, reverse=True)
        return candidates[0] if candidates else None

    def _latest_direct_case_action_request(
        self,
        case: CaseRecord,
    ) -> ActionRequestRecord | None:
        candidates = [
            record
            for record in self._service._store.list(ActionRequestRecord)
            if record.case_id == case.case_id or record.alert_id == case.alert_id
        ]
        candidates.sort(
            key=lambda record: (record.requested_at, record.action_request_id),
            reverse=True,
        )
        return candidates[0] if candidates else None

    def _latest_direct_action_execution(
        self,
        action_request: ActionRequestRecord,
    ) -> ActionExecutionRecord | None:
        candidates = [
            record
            for record in self._service._store.list(ActionExecutionRecord)
            if record.action_request_id == action_request.action_request_id
        ]
        candidates.sort(
            key=lambda record: (record.delegated_at, record.action_execution_id),
            reverse=True,
        )
        return candidates[0] if candidates else None

    def _latest_direct_case_reconciliation(
        self,
        *,
        case: CaseRecord,
        action_request: ActionRequestRecord | None,
        execution: ActionExecutionRecord | None,
    ) -> ReconciliationRecord | None:
        candidates = [
            record
            for record in self._service._store.list(ReconciliationRecord)
            if self._reconciliation_directly_binds_case(
                record,
                case=case,
                action_request=action_request,
                execution=execution,
            )
        ]
        candidates.sort(
            key=lambda record: (record.compared_at, record.reconciliation_id),
            reverse=True,
        )
        return candidates[0] if candidates else None

    @staticmethod
    def _reconciliation_directly_binds_case(
        record: ReconciliationRecord,
        *,
        case: CaseRecord,
        action_request: ActionRequestRecord | None,
        execution: ActionExecutionRecord | None,
    ) -> bool:
        if record.alert_id == case.alert_id or record.finding_id == case.finding_id:
            return True
        linkage = record.subject_linkage
        case_ids = linkage.get("case_ids")
        alert_ids = linkage.get("alert_ids")
        action_request_ids = linkage.get("action_request_ids")
        action_execution_ids = linkage.get("action_execution_ids")
        if isinstance(case_ids, (list, tuple)) and case.case_id in case_ids:
            return True
        if isinstance(alert_ids, (list, tuple)) and case.alert_id in alert_ids:
            return True
        if (
            action_request is not None
            and isinstance(action_request_ids, (list, tuple))
            and action_request.action_request_id in action_request_ids
        ):
            return True
        if (
            execution is not None
            and isinstance(action_execution_ids, (list, tuple))
            and execution.action_execution_id in action_execution_ids
        ):
            return True
        return False

    def inspect_action_review_detail(self, action_request_id: str) -> object:
        action_request_id = self._service._require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        action_request = self._service._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(
                f"Missing action request {action_request_id!r} for review inspection"
            )

        case_record = None
        if action_request.case_id is not None:
            case = self._service._store.get(CaseRecord, action_request.case_id)
            if case is not None:
                case_record = self._service._require_reviewed_operator_case(
                    action_request.case_id
                )

        alert_record = None
        if action_request.alert_id is not None:
            alert = self._service._store.get(AlertRecord, action_request.alert_id)
            if alert is not None:
                alert_record = self._service._require_reviewed_operator_alert_record(
                    alert
                )

        if case_record is None and alert_record is None:
            raise LookupError(
                "Action review inspection requires an authoritative reviewed case or alert scope"
            )

        action_reviews = self._action_review_inspection_boundary.chains_for_scope(
            case_id=action_request.case_id,
            alert_id=action_request.alert_id,
            record_index=self._action_review_inspection_boundary.build_record_index(),
        )
        selected_review = next(
            (
                review
                for review in action_reviews
                if review.get("action_request_id") == action_request_id
            ),
            None,
        )
        if selected_review is None:
            raise LookupError(
                f"Missing authoritative action review projection for {action_request_id!r}"
            )

        return self._action_review_detail_snapshot_factory(
            read_only=True,
            action_request_id=action_request_id,
            action_review=dict(selected_review),
            current_action_review=dict(action_reviews[0]) if action_reviews else None,
            case_record=(
                self._record_to_dict(case_record) if case_record is not None else None
            ),
            alert_record=(
                self._record_to_dict(alert_record) if alert_record is not None else None
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
