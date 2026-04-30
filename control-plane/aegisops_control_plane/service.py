from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from collections import Counter
from dataclasses import fields, replace
from datetime import datetime, timezone
import hashlib
import json
import logging
import uuid
from typing import Iterable, Iterator, Mapping, Protocol, Type, TypeVar

_DATETIME_TYPE = datetime

from . import action_review_projection as _action_review_projection
from .action_policy import evaluate_action_policy_record
from . import assistant_advisory as _assistant_advisory
from . import live_assistant_workflow as _live_assistant_workflow
from .assistant_provider import (
    AssistantProviderFailure,
    AssistantProviderResult,
    AssistantProviderTransport,
)
from .audit_export import export_audit_retention_baseline
from .config import OpenBaoKVv2SecretTransport, RuntimeConfig
from .models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AnalyticSignalAdmission,
    AnalyticSignalRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    FindingAlertIngestResult,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    LifecycleTransitionRecord,
    NativeDetectionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)
from .readiness_contracts import (
    ReadinessDiagnosticsAggregates,
    resolve_current_readiness_runtime_status,
)
from .runtime_boundary import RuntimeBoundaryService
from .reviewed_slice_policy import (
    REVIEWED_LIVE_SLICE_LABEL,
    ReviewedSlicePolicy,
)
from .case_workflow import CaseWorkflowFacade
from .detection_lifecycle_helpers import LATEST_LIFECYCLE_TRANSITION_UNSET
from .external_evidence_facade import ExternalEvidenceFacade
from .service_composition import (
    ControlPlaneServiceCompositionDependencies,
    build_control_plane_service_composition,
    install_control_plane_service_composition,
)
from .service_snapshots import (
    ActionReviewDetailSnapshot,
    AdvisoryInspectionSnapshot,
    AlertDetailSnapshot,
    AnalystAssistantContextSnapshot,
    AnalystQueueSnapshot,
    AuthenticatedRuntimePrincipal,
    CaseDetailSnapshot,
    LiveAssistantWorkflowSnapshot,
    ReadinessDiagnosticsSnapshot,
    RecommendationDraftSnapshot,
    ReconciliationStatusSnapshot,
    RecordInspectionSnapshot,
    RestoreDrillSnapshot,
    RestoreSummarySnapshot,
    RuntimeSnapshot,
    ShutdownStatusSnapshot,
    StartupStatusSnapshot,
    _json_ready,
)
from .structured_events import sanitize_structured_event_fields


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)

_CASE_CLOSED_TRIAGE_DISPOSITIONS = frozenset(
    {
        "closed_benign",
        "closed_duplicate",
        "closed_resolved",
        "closed_accepted_risk",
    }
)
_CASE_PENDING_ACTION_TRIAGE_DISPOSITIONS = frozenset(
    {
        "business_hours_handoff",
        "awaiting_business_hours_review",
        "pending_external_validation",
        "pending_approval",
    }
)
_CASE_LIFECYCLE_STATE_BY_TRIAGE_DISPOSITION = {
    **{
        disposition: "closed"
        for disposition in _CASE_CLOSED_TRIAGE_DISPOSITIONS
    },
    **{
        disposition: "pending_action"
        for disposition in _CASE_PENDING_ACTION_TRIAGE_DISPOSITIONS
    },
    "investigating": "investigating",
}

_LATEST_LIFECYCLE_TRANSITION_UNSET = LATEST_LIFECYCLE_TRANSITION_UNSET
_PHASE24_WORKFLOW_FAMILY = "first_live_assistant_summary_family"
_PHASE24_WORKFLOW_PROMPT_VERSIONS = {
    "case_summary": "phase24-case-summary-v1",
    "queue_triage_summary": "phase24-queue-summary-v1",
}


def _build_control_plane_service_composition_dependencies(
) -> ControlPlaneServiceCompositionDependencies:
    return ControlPlaneServiceCompositionDependencies(
        runtime_snapshot_factory=RuntimeSnapshot,
        authenticated_principal_factory=AuthenticatedRuntimePrincipal,
        reviewed_summary_transport_factory=_ReviewedSummaryTransport,
        workflow_family=_PHASE24_WORKFLOW_FAMILY,
        workflow_prompt_versions=_PHASE24_WORKFLOW_PROMPT_VERSIONS,
        record_types_by_family=RECORD_TYPES_BY_FAMILY,
        authoritative_record_chain_record_types=(
            AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES
        ),
        authoritative_record_chain_backup_schema_version=(
            AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION
        ),
        authoritative_primary_id_field_by_family=(
            _AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY
        ),
        normalize_admission_provenance=_normalize_admission_provenance,
        merge_reviewed_context=_merge_reviewed_context,
        case_lifecycle_state_by_triage_disposition=(
            _CASE_LIFECYCLE_STATE_BY_TRIAGE_DISPOSITION
        ),
        record_to_dict=_record_to_dict,
        json_ready=_json_ready,
        redacted_reconciliation_payload=_redacted_reconciliation_payload,
        coordination_reference_payload=_coordination_reference_payload,
        coordination_reference_signature=_coordination_reference_signature,
        dedupe_strings=_dedupe_strings,
        analyst_queue_snapshot_factory=AnalystQueueSnapshot,
        alert_detail_snapshot_factory=AlertDetailSnapshot,
        case_detail_snapshot_factory=CaseDetailSnapshot,
        action_review_detail_snapshot_factory=ActionReviewDetailSnapshot,
        assistant_context_snapshot_factory=AnalystAssistantContextSnapshot,
        advisory_snapshot_from_context=(
            _assistant_advisory.advisory_inspection_snapshot_from_context
        ),
        recommendation_draft_snapshot_from_context=(
            _assistant_advisory.recommendation_draft_snapshot_from_context
        ),
        live_assistant_snapshot_factory=(
            _live_assistant_workflow.phase24_live_assistant_snapshot
        ),
        live_assistant_citations_from_context=(
            lambda snapshot: _live_assistant_workflow.phase24_live_assistant_citations_from_context(
                snapshot
            )
        ),
        live_assistant_unresolved_reasons=(
            _live_assistant_workflow.phase24_live_assistant_unresolved_reasons
        ),
        live_assistant_prompt_injection_flags=(
            _live_assistant_workflow.phase24_live_assistant_prompt_injection_flags
        ),
        startup_status_snapshot_factory=StartupStatusSnapshot,
        readiness_diagnostics_snapshot_factory=ReadinessDiagnosticsSnapshot,
        restore_drill_snapshot_factory=RestoreDrillSnapshot,
        restore_summary_snapshot_factory=RestoreSummarySnapshot,
        shutdown_status_snapshot_factory=ShutdownStatusSnapshot,
        derive_readiness_status=_derive_readiness_status,
        find_duplicate_strings=_find_duplicate_strings,
    )


class _ReviewedSummaryTransport(AssistantProviderTransport):
    """Deterministic reviewed-only transport for the first live workflow family."""

    def send_request(self, *, request: Mapping[str, object]) -> Mapping[str, object]:
        metadata = request.get("request_metadata")
        if not isinstance(metadata, Mapping):
            raise ValueError("provider request metadata must be a mapping")
        output_text = metadata.get("bounded_summary_text")
        if not isinstance(output_text, str) or output_text.strip() == "":
            raise ValueError("provider request metadata must include bounded_summary_text")
        workflow_task = str(request.get("workflow_task") or "summary")
        request_id = f"reviewed-provider-request:{uuid.uuid4()}"
        response_id = f"reviewed-provider-response:{uuid.uuid4()}"
        transcript_id = f"reviewed-provider-transcript:{uuid.uuid4()}"
        return {
            "provider_request_id": request_id,
            "provider_response_id": response_id,
            "provider_transcript_id": transcript_id,
            "model_version": f"reviewed-local-{workflow_task}-v1",
            "output_text": output_text.strip(),
        }


class ControlPlaneStore(Protocol):
    dsn: str
    persistence_mode: str

    def save(self, record: RecordT) -> RecordT:
        ...

    def create_action_request_if_absent(
        self,
        record: ActionRequestRecord,
    ) -> tuple[ActionRequestRecord, bool]:
        ...

    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        ...

    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        ...

    def latest_ai_trace_record(self) -> AITraceRecord | None:
        ...

    def latest_reconciliation_for_correlation_key(
        self,
        correlation_key: str,
        *,
        require_alert_id: bool = False,
    ) -> ReconciliationRecord | None:
        ...

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        ...

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        ...

    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> AbstractContextManager[None]:
        ...

    def inspect_readiness_aggregates(self) -> ReadinessDiagnosticsAggregates:
        ...


class NativeDetectionRecordAdapter(Protocol):
    substrate_key: str

    def build_analytic_signal_admission(
        self,
        record: NativeDetectionRecord,
    ) -> AnalyticSignalAdmission:
        ...


def _derive_readiness_status(
    *,
    startup_ready: bool,
    reconciliation_lifecycle_counts: Mapping[str, int],
    review_path_health_overall_state: str | None = None,
    control_plane_authority_frozen: bool = False,
) -> str:
    return resolve_current_readiness_runtime_status(
        startup_ready=startup_ready,
        reconciliation_lifecycle_counts=reconciliation_lifecycle_counts,
        review_path_health_overall_state=review_path_health_overall_state,
        control_plane_authority_frozen=control_plane_authority_frozen,
    ).status


RECORD_TYPES_BY_FAMILY: dict[str, Type[ControlPlaneRecord]] = {
    record_type.record_family: record_type
    for record_type in (
        AlertRecord,
        AnalyticSignalRecord,
        CaseRecord,
        EvidenceRecord,
        LifecycleTransitionRecord,
        ObservationRecord,
        LeadRecord,
        RecommendationRecord,
        ApprovalDecisionRecord,
        ActionRequestRecord,
        ActionExecutionRecord,
        HuntRecord,
        HuntRunRecord,
        AITraceRecord,
        ReconciliationRecord,
    )
}

AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES: tuple[Type[ControlPlaneRecord], ...] = (
    AnalyticSignalRecord,
    AlertRecord,
    EvidenceRecord,
    ObservationRecord,
    LeadRecord,
    CaseRecord,
    RecommendationRecord,
    LifecycleTransitionRecord,
    ApprovalDecisionRecord,
    ActionRequestRecord,
    ActionExecutionRecord,
    HuntRecord,
    HuntRunRecord,
    AITraceRecord,
    ReconciliationRecord,
)
AUTHORITATIVE_RECORD_CHAIN_FAMILIES: tuple[str, ...] = tuple(
    record_type.record_family for record_type in AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES
)
AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION = (
    "phase23.authoritative-record-chain.v2"
)
_AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY: dict[str, str] = {
    "analytic_signal": "analytic_signal_id",
    "alert": "alert_id",
    "evidence": "evidence_id",
    "observation": "observation_id",
    "lead": "lead_id",
    "case": "case_id",
    "recommendation": "recommendation_id",
    "lifecycle_transition": "transition_id",
    "approval_decision": "approval_decision_id",
    "action_request": "action_request_id",
    "action_execution": "action_execution_id",
    "hunt": "hunt_id",
    "hunt_run": "hunt_run_id",
    "ai_trace": "ai_trace_id",
    "reconciliation": "reconciliation_id",
}

def _record_to_dict(record: ControlPlaneRecord) -> dict[str, object]:
    return {
        field.name: getattr(record, field.name)
        for field in fields(record)
    }


def _coordination_reference_payload(
    record: Mapping[str, object] | ControlPlaneRecord | None,
) -> dict[str, str] | None:
    if record is None:
        return None
    if isinstance(record, Mapping):
        payload = record
    else:
        payload = _record_to_dict(record)

    coordination_reference_id = payload.get("coordination_reference_id")
    coordination_target_type = payload.get("coordination_target_type")
    coordination_target_id = payload.get("coordination_target_id")
    ticket_reference_url = payload.get("ticket_reference_url")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (
            coordination_reference_id,
            coordination_target_type,
            coordination_target_id,
            ticket_reference_url,
        )
    ):
        return None
    return {
        "coordination_reference_id": coordination_reference_id.strip(),
        "coordination_target_type": coordination_target_type.strip(),
        "coordination_target_id": coordination_target_id.strip(),
        "ticket_reference_url": ticket_reference_url.strip(),
    }


def _coordination_reference_signature(
    record: Mapping[str, object] | ControlPlaneRecord | None,
) -> tuple[str, str, str, str] | None:
    payload = _coordination_reference_payload(record)
    if payload is None:
        return None
    return (
        payload["coordination_reference_id"],
        payload["coordination_target_type"],
        payload["coordination_target_id"],
        payload["ticket_reference_url"],
    )


def _redacted_reconciliation_payload(
    reconciliation: ReconciliationRecord,
) -> dict[str, object]:
    payload = _record_to_dict(reconciliation)
    subject_linkage_payload = payload.get("subject_linkage")
    if isinstance(subject_linkage_payload, Mapping):
        redacted_subject_linkage = dict(subject_linkage_payload)
        redacted_subject_linkage.pop("latest_native_payload", None)
        payload["subject_linkage"] = redacted_subject_linkage
    return payload


def _merge_reviewed_context(
    existing_context: Mapping[str, object] | None,
    incoming_context: Mapping[str, object] | None,
) -> dict[str, object]:
    merged: dict[str, object] = {}
    if isinstance(existing_context, Mapping):
        merged.update({str(key): value for key, value in existing_context.items()})
    if not isinstance(incoming_context, Mapping):
        return merged

    for key, value in incoming_context.items():
        normalized_key = str(key)
        existing_value = merged.get(normalized_key)
        if isinstance(existing_value, Mapping) and isinstance(value, Mapping):
            merged[normalized_key] = _merge_reviewed_context(existing_value, value)
        else:
            merged[normalized_key] = value
    return merged


def _find_duplicate_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(value for value, count in Counter(values).items() if count > 1)
    )


def _dedupe_strings(values: Iterable[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return tuple(deduped)


def _normalize_admission_provenance(
    value: object,
) -> dict[str, str] | None:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, str] = {}
    for field_name in ("admission_kind", "admission_channel"):
        field_value = value.get(field_name)
        if isinstance(field_value, str):
            normalized_value = field_value.strip()
            if normalized_value:
                normalized[field_name] = normalized_value
    if len(normalized) != 2:
        return None
    return normalized


class AegisOpsControlPlaneService(CaseWorkflowFacade, ExternalEvidenceFacade):
    """Minimal local runtime skeleton for the first control-plane service."""

    def __init__(
        self,
        config: RuntimeConfig,
        store: ControlPlaneStore | None = None,
    ) -> None:
        self._config = config
        self._logger = logging.getLogger("aegisops.control_plane")
        composition = build_control_plane_service_composition(
            service=self,
            config=config,
            store=store,
            dependencies=_build_control_plane_service_composition_dependencies(),
        )
        install_control_plane_service_composition(
            service=self,
            composition=composition,
        )

    def describe_runtime(self) -> RuntimeSnapshot:
        return self._runtime_restore_readiness_diagnostics_service.describe_runtime()

    def persist_record(
        self,
        record: RecordT,
        *,
        transitioned_at: datetime | None = None,
    ) -> RecordT:
        return self._persistence_lifecycle_service.persist_record(
            record,
            transitioned_at=transitioned_at,
        )

    def _lock_lifecycle_transition_subject(
        self,
        record_family: str,
        record_id: str,
    ) -> None:
        self._detection_intake_service.lifecycle_transition_helper.lock_lifecycle_transition_subject(
            record_family,
            record_id,
        )

    def _linked_alert_case_lifecycle_lock_subject(
        self,
        record: ControlPlaneRecord,
    ) -> tuple[str, str] | None:
        return self._detection_intake_service.lifecycle_transition_helper.linked_alert_case_lifecycle_lock_subject(
            record
        )

    def _lifecycle_transition_id(
        self,
        *,
        transition_timestamp: str,
        transitioned_at: datetime,
        latest_transition: LifecycleTransitionRecord | None,
    ) -> str:
        return self._detection_intake_service.lifecycle_transition_helper.lifecycle_transition_id(
            transition_timestamp=transition_timestamp,
            transitioned_at=transitioned_at,
            latest_transition=latest_transition,
        )

    def _initial_lifecycle_transitioned_at(
        self,
        record: ControlPlaneRecord,
        *,
        fallback: datetime | None = None,
    ) -> datetime:
        return self._detection_intake_service.lifecycle_transition_helper.initial_lifecycle_transitioned_at(
            record,
            fallback=fallback,
        )

    def _reviewed_context_transitioned_at(
        self,
        record: AlertRecord | CaseRecord,
    ) -> datetime | None:
        return self._detection_intake_service.reviewed_context_transitioned_at(record)

    def _triage_disposition_matches_current_state(
        self,
        record: AlertRecord | CaseRecord,
        disposition: object,
    ) -> bool:
        return self._detection_intake_service.triage_disposition_matches_current_state(
            record,
            disposition,
        )

    def _case_lifecycle_state_for_triage_disposition(
        self,
        disposition: object,
    ) -> str | None:
        return self._detection_intake_service.case_lifecycle_state_for_triage_disposition(
            disposition
        )

    def _latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        return self._detection_intake_service.lifecycle_transition_helper.latest_lifecycle_transition(
            record_family,
            record_id,
        )

    def _lifecycle_transition_attribution(
        self,
        record: ControlPlaneRecord,
    ) -> dict[str, object]:
        return self._detection_intake_service.lifecycle_transition_helper.lifecycle_transition_attribution(
            record
        )

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        normalized_record_family = self._require_non_empty_string(
            record_family,
            "record_family",
        )
        normalized_record_id = self._require_non_empty_string(record_id, "record_id")
        return self._store.list_lifecycle_transitions(
            normalized_record_family,
            normalized_record_id,
        )

    def _emit_structured_event(
        self,
        level: int,
        event: str,
        **fields: object,
    ) -> None:
        payload = {
            "event": event,
            "service_name": "aegisops-control-plane",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            **sanitize_structured_event_fields(fields),
        }
        self._logger.log(level, json.dumps(payload, sort_keys=True, separators=(",", ":")))

    def _emit_action_execution_delegated_event(
        self,
        execution: ActionExecutionRecord,
    ) -> None:
        self._emit_structured_event(
            logging.INFO,
            "action_execution_delegated",
            action_execution_id=execution.action_execution_id,
            action_request_id=execution.action_request_id,
            approval_decision_id=execution.approval_decision_id,
            execution_surface_type=execution.execution_surface_type,
            execution_surface_id=execution.execution_surface_id,
            execution_run_id=execution.execution_run_id,
            lifecycle_state=execution.lifecycle_state,
        )

    def get_record(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        return self._store.get(record_type, record_id)

    def validate_wazuh_ingest_runtime(self) -> None:
        self._runtime_restore_readiness_diagnostics_service.validate_wazuh_ingest_runtime()

    def validate_protected_surface_runtime(self) -> None:
        self._runtime_restore_readiness_diagnostics_service.validate_protected_surface_runtime()

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
    ) -> AuthenticatedRuntimePrincipal:
        diagnostics_service = self._runtime_restore_readiness_diagnostics_service
        return diagnostics_service.authenticate_protected_surface_request(
            peer_addr=peer_addr,
            forwarded_proto=forwarded_proto,
            reverse_proxy_secret_header=reverse_proxy_secret_header,
            proxy_service_account_header=proxy_service_account_header,
            authenticated_identity_provider_header=authenticated_identity_provider_header,
            authenticated_subject_header=authenticated_subject_header,
            authenticated_identity_header=authenticated_identity_header,
            authenticated_role_header=authenticated_role_header,
            allowed_roles=allowed_roles,
        )

    def require_admin_bootstrap_token(self, supplied_token: str | None) -> None:
        self._runtime_restore_readiness_diagnostics_service.require_admin_bootstrap_token(
            supplied_token
        )

    def require_break_glass_token(self, supplied_token: str | None) -> None:
        self._runtime_restore_readiness_diagnostics_service.require_break_glass_token(
            supplied_token
        )

    def ingest_wazuh_alert(
        self,
        *,
        raw_alert: Mapping[str, object],
        authorization_header: str | None,
        forwarded_proto: str | None,
        reverse_proxy_secret_header: str | None,
        peer_addr: str | None,
    ) -> FindingAlertIngestResult:
        return self._detection_intake_service.ingest_wazuh_alert(
            raw_alert=raw_alert,
            authorization_header=authorization_header,
            forwarded_proto=forwarded_proto,
            reverse_proxy_secret_header=reverse_proxy_secret_header,
            peer_addr=peer_addr,
        )

    def _listener_is_loopback(self) -> bool:
        return self._runtime_boundary_service.listener_is_loopback()

    def _is_trusted_wazuh_ingest_peer(self, peer_addr: str | None) -> bool:
        return self._runtime_boundary_service.is_trusted_wazuh_ingest_peer(peer_addr)

    def _is_trusted_protected_surface_peer(self, peer_addr: str | None) -> bool:
        return self._runtime_boundary_service.is_trusted_protected_surface_peer(
            peer_addr
        )

    def _is_trusted_peer_for_proxy_cidrs(
        self,
        peer_addr: str | None,
        trusted_proxy_cidrs: tuple[str, ...],
    ) -> bool:
        return self._runtime_boundary_service.is_trusted_peer_for_proxy_cidrs(
            peer_addr,
            trusted_proxy_cidrs,
        )

    @staticmethod
    def _peer_addr_is_loopback(peer_addr: str | None) -> bool:
        return RuntimeBoundaryService.peer_addr_is_loopback(peer_addr)

    def delegate_approved_action_to_shuffle(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> ActionExecutionRecord:
        return self._action_lifecycle_write_coordinator.delegate_approved_action_to_shuffle(
            action_request_id=action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer=delegation_issuer,
            evidence_ids=evidence_ids,
        )

    def delegate_approved_action_to_isolated_executor(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> ActionExecutionRecord:
        return self._action_lifecycle_write_coordinator.delegate_approved_action_to_isolated_executor(
            action_request_id=action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer=delegation_issuer,
            evidence_ids=evidence_ids,
        )

    def evaluate_action_policy(self, action_request_id: str) -> ActionRequestRecord:
        action_request_id = self._require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        action_request = self._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(f"Missing action request {action_request_id!r}")

        evaluated = evaluate_action_policy_record(action_request)
        return self.persist_record(evaluated)

    def inspect_records(self, record_family: str) -> RecordInspectionSnapshot:
        record_type = RECORD_TYPES_BY_FAMILY.get(record_family)
        if record_type is None:
            known_families = ", ".join(sorted(RECORD_TYPES_BY_FAMILY))
            raise ValueError(
                f"Unsupported control-plane record family {record_family!r}; "
                f"expected one of: {known_families}"
            )

        records = tuple(_record_to_dict(record) for record in self._store.list(record_type))
        return RecordInspectionSnapshot(
            read_only=True,
            record_family=record_family,
            total_records=len(records),
            records=records,
        )

    def inspect_reconciliation_status(self) -> ReconciliationStatusSnapshot:
        records = self._store.list(ReconciliationRecord)
        latest_compared_at = max(
            (record.compared_at for record in records),
            default=None,
        )
        by_lifecycle_state = dict(
            sorted(Counter(record.lifecycle_state for record in records).items())
        )
        by_ingest_disposition = dict(
            sorted(Counter(record.ingest_disposition for record in records).items())
        )
        return ReconciliationStatusSnapshot(
            read_only=True,
            total_records=len(records),
            latest_compared_at=latest_compared_at,
            by_lifecycle_state=by_lifecycle_state,
            by_ingest_disposition=by_ingest_disposition,
            records=tuple(
                _redacted_reconciliation_payload(record) for record in records
            ),
        )

    def export_audit_retention_baseline(
        self,
        *,
        export_id: str,
        exported_at: datetime,
    ) -> dict[str, object]:
        export_id = self._require_non_empty_string(export_id, "export_id")
        exported_at = self._require_aware_datetime(
            exported_at,
            "exported_at",
        )
        return export_audit_retention_baseline(
            store=self._store,
            record_types=AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES,
            export_id=export_id,
            exported_at=exported_at,
        )

    def describe_startup_status(self) -> StartupStatusSnapshot:
        return (
            self._runtime_restore_readiness_diagnostics_service.describe_startup_status()
        )

    def describe_shutdown_status(self) -> ShutdownStatusSnapshot:
        return (
            self._runtime_restore_readiness_diagnostics_service.describe_shutdown_status()
        )

    def inspect_readiness_diagnostics(self) -> ReadinessDiagnosticsSnapshot:
        return (
            self._runtime_restore_readiness_diagnostics_service.inspect_readiness_diagnostics()
        )

    def control_plane_change_authority_freeze_status(self) -> dict[str, object]:
        change_state = self._config.control_plane_change_state.strip()
        evidence_id = self._config.control_plane_change_evidence_id.strip()
        normalized_state = change_state or "unknown"
        is_verified = normalized_state in {"verified_current", "verified_safe"}
        return {
            "state": "verified" if is_verified else "frozen",
            "change_state": normalized_state,
            "evidence_id": evidence_id or None,
            "authority_sensitive_progression_allowed": is_verified,
            "reason": (
                "control_plane_state_verified"
                if is_verified
                else "control_plane_upgrade_or_rollback_verification_incomplete"
            ),
        }

    def _require_control_plane_change_authority_unfrozen(self) -> None:
        freeze_status = self.control_plane_change_authority_freeze_status()
        if freeze_status["authority_sensitive_progression_allowed"] is True:
            return
        raise PermissionError(
            "control-plane upgrade or rollback verification is not complete"
        )

    def _inspect_readiness_aggregates(self) -> ReadinessDiagnosticsAggregates:
        return (
            self._runtime_restore_readiness_diagnostics_service.inspect_readiness_aggregates()
        )

    def export_authoritative_record_chain_backup(self) -> dict[str, object]:
        diagnostics_service = self._runtime_restore_readiness_diagnostics_service
        return diagnostics_service.export_authoritative_record_chain_backup()

    def restore_authoritative_record_chain_backup(
        self,
        backup_payload: Mapping[str, object],
    ) -> RestoreSummarySnapshot:
        diagnostics_service = self._runtime_restore_readiness_diagnostics_service
        return diagnostics_service.restore_authoritative_record_chain_backup(
            backup_payload
        )

    @contextmanager
    def _restore_drill_snapshot_transaction(self) -> Iterator[None]:
        diagnostics_service = self._runtime_restore_readiness_diagnostics_service
        with diagnostics_service.restore_drill_snapshot_transaction():
            yield

    def run_authoritative_restore_drill(self) -> RestoreDrillSnapshot:
        return (
            self._runtime_restore_readiness_diagnostics_service.run_authoritative_restore_drill()
        )

    def _run_authoritative_restore_drill_snapshot(self) -> RestoreDrillSnapshot:
        diagnostics_service = self._runtime_restore_readiness_diagnostics_service
        return diagnostics_service.run_authoritative_restore_drill_snapshot()

    def inspect_analyst_queue(self) -> AnalystQueueSnapshot:
        return self._operator_inspection_read_surface.inspect_analyst_queue()

    def inspect_alert_detail(self, alert_id: str) -> AlertDetailSnapshot:
        return self._operator_inspection_read_surface.inspect_alert_detail(alert_id)

    def inspect_assistant_context(
        self,
        record_family: str,
        record_id: str,
    ) -> AnalystAssistantContextSnapshot:
        return self._assistant_context_assembler.inspect_assistant_context(
            record_family,
            record_id,
        )

    def inspect_case_detail(self, case_id: str) -> CaseDetailSnapshot:
        return self._operator_inspection_read_surface.inspect_case_detail(case_id)

    def inspect_action_review_detail(
        self,
        action_request_id: str,
    ) -> ActionReviewDetailSnapshot:
        return self._operator_inspection_read_surface.inspect_action_review_detail(
            action_request_id
        )

    def record_action_review_manual_fallback(
        self,
        *,
        action_request_id: str,
        fallback_at: datetime,
        fallback_actor_identity: str,
        authority_boundary: str,
        reason: str,
        action_taken: str,
        verification_evidence_ids: tuple[str, ...] = (),
        residual_uncertainty: str | None = None,
    ) -> CaseRecord | AlertRecord:
        return self._action_review_write_surface.record_action_review_manual_fallback(
            action_request_id=action_request_id,
            fallback_at=fallback_at,
            fallback_actor_identity=fallback_actor_identity,
            authority_boundary=authority_boundary,
            reason=reason,
            action_taken=action_taken,
            verification_evidence_ids=verification_evidence_ids,
            residual_uncertainty=residual_uncertainty,
        )

    def record_action_review_escalation_note(
        self,
        *,
        action_request_id: str,
        escalated_at: datetime,
        escalated_by_identity: str,
        escalated_to: str,
        note: str,
    ) -> CaseRecord | AlertRecord:
        return self._action_review_write_surface.record_action_review_escalation_note(
            action_request_id=action_request_id,
            escalated_at=escalated_at,
            escalated_by_identity=escalated_by_identity,
            escalated_to=escalated_to,
            note=note,
        )

    def inspect_advisory_output(
        self,
        record_family: str,
        record_id: str,
    ) -> AdvisoryInspectionSnapshot:
        return self._assistant_advisory_coordinator.inspect_advisory_output(
            record_family,
            record_id,
        )

    def render_recommendation_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationDraftSnapshot:
        return self._assistant_advisory_coordinator.render_recommendation_draft(
            record_family,
            record_id,
        )

    def run_live_assistant_workflow(
        self,
        *,
        workflow_task: str,
        record_family: str,
        record_id: str,
    ) -> LiveAssistantWorkflowSnapshot:
        return self._live_assistant_workflow_coordinator.run_live_assistant_workflow(
            workflow_task=workflow_task,
            record_family=record_family,
            record_id=record_id,
        )

    def _assistant_primary_linked_id(self, linked_ids: tuple[str, ...]) -> str | None:
        return self._ai_trace_lifecycle_service.primary_linked_id(linked_ids)

    def create_reviewed_action_request_from_advisory(
        self,
        *,
        record_family: str,
        record_id: str,
        requester_identity: str,
        recipient_identity: str,
        message_intent: str,
        escalation_reason: str,
        expires_at: datetime,
        action_request_id: str | None = None,
    ) -> ActionRequestRecord:
        return self._action_lifecycle_write_coordinator.create_reviewed_action_request_from_advisory(
            record_family=record_family,
            record_id=record_id,
            requester_identity=requester_identity,
            recipient_identity=recipient_identity,
            message_intent=message_intent,
            escalation_reason=escalation_reason,
            expires_at=expires_at,
            action_request_id=action_request_id,
        )

    def create_reviewed_tracking_ticket_request_from_advisory(
        self,
        *,
        record_family: str,
        record_id: str,
        requester_identity: str,
        coordination_reference_id: str,
        coordination_target_type: str,
        ticket_title: str,
        ticket_description: str,
        expires_at: datetime,
        ticket_severity: str = "medium",
        action_request_id: str | None = None,
    ) -> ActionRequestRecord:
        return self._action_lifecycle_write_coordinator.create_reviewed_tracking_ticket_request_from_advisory(
            record_family=record_family,
            record_id=record_id,
            requester_identity=requester_identity,
            coordination_reference_id=coordination_reference_id,
            coordination_target_type=coordination_target_type,
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            expires_at=expires_at,
            ticket_severity=ticket_severity,
            action_request_id=action_request_id,
        )

    def record_action_approval_decision(
        self,
        *,
        action_request_id: str,
        approver_identity: str,
        authenticated_approver_identity: str | None = None,
        decision: str,
        decision_rationale: str,
        decided_at: datetime,
        approval_decision_id: str | None = None,
    ) -> ApprovalDecisionRecord:
        return self._action_lifecycle_write_coordinator.record_action_approval_decision(
            action_request_id=action_request_id,
            approver_identity=approver_identity,
            authenticated_approver_identity=authenticated_approver_identity,
            decision=decision,
            decision_rationale=decision_rationale,
            decided_at=decided_at,
            approval_decision_id=approval_decision_id,
        )

    def attach_assistant_advisory_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationRecord | AITraceRecord:
        return self._assistant_advisory_coordinator.attach_assistant_advisory_draft(
            record_family,
            record_id,
        )

    def _reconciliation_has_detection_lineage(
        self, record: ReconciliationRecord
    ) -> bool:
        return self._detection_intake_service.reconciliation_resolver.reconciliation_has_detection_lineage(
            record
        )

    def _latest_detection_reconciliation_for_alert(
        self,
        alert_id: str,
    ) -> ReconciliationRecord | None:
        return self._detection_intake_service.reconciliation_resolver.latest_detection_reconciliation_for_alert(
            alert_id
        )

    def _latest_detection_reconciliations_by_alert_id(
        self,
    ) -> dict[str, ReconciliationRecord]:
        return self._detection_intake_service.reconciliation_resolver.latest_detection_reconciliations_by_alert_id()

    def _reconciliation_is_wazuh_origin(self, record: ReconciliationRecord) -> bool:
        return self._detection_intake_service.reconciliation_resolver.reconciliation_is_wazuh_origin(
            record
        )

    def _assistant_ids_from_value(self, value: object) -> tuple[str, ...]:
        return self._ai_trace_lifecycle_service.ids_from_value(value)

    def _assistant_ids_from_mapping(
        self,
        mapping: Mapping[str, object],
        key: str,
    ) -> tuple[str, ...]:
        return self._ai_trace_lifecycle_service.ids_from_mapping(mapping, key)

    def _assistant_merge_ids(
        self,
        existing_values: object,
        incoming_values: object,
    ) -> tuple[str, ...]:
        return self._ai_trace_lifecycle_service.merge_ids(
            existing_values,
            incoming_values,
        )

    def _assistant_action_lineage_ids(
        self,
        record: ControlPlaneRecord,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        return self._ai_trace_lifecycle_service.action_lineage_ids(record)

    def _assistant_merge_action_request_linkage(
        self,
        *,
        linked_alert_ids: tuple[str, ...],
        linked_case_ids: tuple[str, ...],
        linked_finding_ids: tuple[str, ...],
        action_request: ActionRequestRecord,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        return self._ai_trace_lifecycle_service.merge_action_request_linkage(
            linked_alert_ids=linked_alert_ids,
            linked_case_ids=linked_case_ids,
            linked_finding_ids=linked_finding_ids,
            action_request=action_request,
        )

    def _assistant_action_execution_for_delegation_id(
        self,
        delegation_id: str,
    ) -> ActionExecutionRecord | None:
        return self._ai_trace_lifecycle_service.action_execution_for_delegation_id(
            delegation_id
        )

    def _assistant_ai_trace_records_for_context(
        self,
        record: ControlPlaneRecord,
    ) -> tuple[AITraceRecord, ...]:
        return self._ai_trace_lifecycle_service.ai_trace_records_for_context(record)

    def _assistant_ai_trace_evidence_ids(
        self,
        ai_trace_record: AITraceRecord,
    ) -> tuple[str, ...]:
        return self._ai_trace_lifecycle_service.ai_trace_evidence_ids(ai_trace_record)

    def _assistant_linked_evidence_ids(self, record: ControlPlaneRecord) -> tuple[str, ...]:
        return self._ai_trace_lifecycle_service.linked_evidence_ids(record)

    def _assistant_evidence_siblings(self, record: EvidenceRecord) -> tuple[str, ...]:
        return self._ai_trace_lifecycle_service.evidence_siblings(record)

    def _assistant_evidence_records_for_context(
        self,
        *,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        exclude_evidence_id: str | None,
    ) -> tuple[EvidenceRecord, ...]:
        return self._ai_trace_lifecycle_service.evidence_records_for_context(
            alert_ids=alert_ids,
            case_ids=case_ids,
            evidence_ids=evidence_ids,
            exclude_evidence_id=exclude_evidence_id,
        )

    def _assistant_recommendation_records_for_context(
        self,
        *,
        record: ControlPlaneRecord,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        ai_trace_records: tuple[AITraceRecord, ...],
        exclude_recommendation_id: str | None,
    ) -> tuple[RecommendationRecord, ...]:
        return self._ai_trace_lifecycle_service.recommendation_records_for_context(
            record=record,
            alert_ids=alert_ids,
            case_ids=case_ids,
            ai_trace_records=ai_trace_records,
            exclude_recommendation_id=exclude_recommendation_id,
        )

    def _assistant_reconciliation_records_for_context(
        self,
        *,
        record: ControlPlaneRecord,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        finding_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        exclude_reconciliation_id: str | None,
    ) -> tuple[ReconciliationRecord, ...]:
        return self._ai_trace_lifecycle_service.reconciliation_records_for_context(
            record=record,
            alert_ids=alert_ids,
            case_ids=case_ids,
            finding_ids=finding_ids,
            evidence_ids=evidence_ids,
            exclude_reconciliation_id=exclude_reconciliation_id,
        )

    @staticmethod
    def _require_aware_datetime(value: object, field_name: str) -> datetime:
        if not isinstance(value, _DATETIME_TYPE):
            raise ValueError(f"{field_name} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware")
        return value

    @staticmethod
    def _require_non_empty_string(value: object, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value

    @staticmethod
    def _normalize_optional_string(value: object, field_name: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string when provided")
        if not value.strip():
            return None
        return value

    def _resolve_new_record_identifier(
        self,
        record_type: Type[RecordT],
        requested_id: object,
        field_name: str,
        prefix: str,
    ) -> str:
        normalized_id = self._normalize_optional_string(requested_id, field_name)
        if normalized_id is None:
            generated_id = self._next_identifier(prefix)
            if self._store.get(record_type, generated_id) is not None:
                raise ValueError(f"{field_name} {generated_id!r} already exists")
            return generated_id
        if self._store.get(record_type, normalized_id) is not None:
            raise ValueError(f"{field_name} {normalized_id!r} already exists")
        return normalized_id

    def ingest_finding_alert(
        self,
        *,
        finding_id: str,
        analytic_signal_id: str | None,
        substrate_detection_record_id: str | None = None,
        correlation_key: str,
        first_seen_at: datetime,
        last_seen_at: datetime,
        materially_new_work: bool = False,
        reviewed_context: Mapping[str, object] | None = None,
    ) -> FindingAlertIngestResult:
        return self._detection_intake_service.ingest_finding_alert(
            finding_id=finding_id,
            analytic_signal_id=analytic_signal_id,
            substrate_detection_record_id=substrate_detection_record_id,
            correlation_key=correlation_key,
            first_seen_at=first_seen_at,
            last_seen_at=last_seen_at,
            materially_new_work=materially_new_work,
            reviewed_context=reviewed_context,
        )

    def promote_alert_to_case(
        self,
        alert_id: str,
        *,
        case_id: str | None = None,
        case_lifecycle_state: str = "open",
    ) -> CaseRecord:
        return self._detection_intake_service.promote_alert_to_case(
            alert_id,
            case_id=case_id,
            case_lifecycle_state=case_lifecycle_state,
        )

    def ingest_native_detection_record(
        self,
        adapter: NativeDetectionRecordAdapter,
        record: NativeDetectionRecord,
    ) -> FindingAlertIngestResult:
        return self._detection_intake_service.ingest_native_detection_record(
            adapter,
            record,
        )

    def reconcile_action_execution(
        self,
        *,
        action_request_id: str,
        execution_surface_type: str,
        execution_surface_id: str,
        observed_executions: tuple[Mapping[str, object], ...],
        compared_at: datetime,
        stale_after: datetime,
    ) -> ReconciliationRecord:
        return self._action_lifecycle_write_coordinator.reconcile_action_execution(
            action_request_id=action_request_id,
            execution_surface_type=execution_surface_type,
            execution_surface_id=execution_surface_id,
            observed_executions=observed_executions,
            compared_at=compared_at,
            stale_after=stale_after,
        )

    @staticmethod
    def _merge_linked_ids(
        existing_values: object,
        incoming_value: str | None,
    ) -> tuple[str, ...]:
        merged: list[str] = []
        if isinstance(existing_values, (list, tuple)):
            for value in existing_values:
                if isinstance(value, str) and value not in merged:
                    merged.append(value)
        if incoming_value is not None and incoming_value not in merged:
            merged.append(incoming_value)
        return tuple(merged)

    @staticmethod
    def _linked_id_exists(existing_values: object, candidate: str) -> bool:
        return isinstance(existing_values, (list, tuple)) and candidate in existing_values

    def _require_empty_authoritative_restore_target(self) -> None:
        diagnostics_service = self._runtime_restore_readiness_diagnostics_service
        diagnostics_service.require_empty_authoritative_restore_target()

    def _validate_authoritative_record_chain_restore(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        *,
        restored_record_counts: Mapping[str, int] | None = None,
    ) -> None:
        diagnostics_service = self._runtime_restore_readiness_diagnostics_service
        diagnostics_service.validate_authoritative_record_chain_restore(
            records_by_family,
            restored_record_counts=restored_record_counts,
        )

    def _require_case_record(self, case_id: str) -> CaseRecord:
        case_id = self._require_non_empty_string(case_id, "case_id")
        case = self._store.get(CaseRecord, case_id)
        if case is None:
            raise LookupError(f"Missing case {case_id!r}")
        return case

    def _require_action_request_record(self, action_request_id: str) -> ActionRequestRecord:
        action_request_id = self._require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        action_request = self._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(f"Missing action request {action_request_id!r}")
        return action_request

    def _require_review_bound_action_request(
        self,
        action_request_id: str,
    ) -> ActionRequestRecord:
        action_request = self._require_action_request_record(action_request_id)
        if not _action_review_projection._action_request_is_review_bound(
            action_request
        ):
            raise ValueError(
                "action_request_id must reference a reviewed action request"
            )
        return action_request

    def _require_action_review_visibility_context_record(
        self,
        action_request: ActionRequestRecord,
    ) -> CaseRecord | AlertRecord:
        if action_request.case_id is not None:
            return self._require_reviewed_operator_case(action_request.case_id)
        if action_request.alert_id is None:
            raise ValueError(
                "reviewed action request must be linked to a case or alert before "
                "recording runtime visibility"
            )
        alert = self._store.get(AlertRecord, action_request.alert_id)
        if alert is None:
            raise LookupError(f"Missing alert {action_request.alert_id!r}")
        return alert

    def _persist_action_review_visibility_context_record(
        self,
        *,
        context_record: CaseRecord | AlertRecord,
        reviewed_context_update: Mapping[str, object],
    ) -> CaseRecord | AlertRecord:
        updated_reviewed_context = _merge_reviewed_context(
            context_record.reviewed_context,
            reviewed_context_update,
        )
        return self.persist_record(
            replace(
                context_record,
                reviewed_context=updated_reviewed_context,
            )
        )

    def _require_reviewed_operator_case(self, case_id: str) -> CaseRecord:
        return self._reviewed_slice_policy.require_operator_case(case_id)

    @staticmethod
    def _require_single_linked_case_id(linked_case_ids: tuple[str, ...]) -> str:
        if len(linked_case_ids) != 1:
            raise ValueError(
                "reviewed advisory context must bind exactly one case before creating an action request"
            )
        return linked_case_ids[0]

    @staticmethod
    def _require_single_recommendation_binding(
        *,
        record_family: str,
        record_id: str,
        linked_recommendation_ids: tuple[str, ...],
    ) -> str:
        recommendation_ids = linked_recommendation_ids
        if record_family == "recommendation":
            recommendation_ids = (record_id,)
        if len(recommendation_ids) != 1:
            raise ValueError(
                "reviewed advisory context must bind exactly one recommendation before creating an action request"
            )
        return recommendation_ids[0]

    def _require_reviewed_case_scoped_advisory_read(
        self,
        context_snapshot: AnalystAssistantContextSnapshot,
    ) -> None:
        self._reviewed_slice_policy.require_case_scoped_advisory_read(context_snapshot)

    def _require_reviewed_alert_scoped_queue_summary_read(
        self,
        context_snapshot: AnalystAssistantContextSnapshot,
    ) -> None:
        self._reviewed_slice_policy.require_alert_scoped_queue_summary_read(
            context_snapshot
        )

    @staticmethod
    def _reviewed_case_scoped_read_error(record_family: str, record_id: str) -> str:
        return ReviewedSlicePolicy.case_scoped_read_error(record_family, record_id)

    def _require_reviewed_case_scoped_recommendation_payload(
        self,
        payload: Mapping[str, object],
        *,
        approved_cases: Mapping[str, CaseRecord],
        error_message: str,
    ) -> None:
        self._reviewed_slice_policy.require_case_scoped_recommendation_payload(
            payload,
            approved_cases=approved_cases,
            error_message=error_message,
        )

    @staticmethod
    def _reviewed_operator_source_family(context: object) -> str | None:
        return ReviewedSlicePolicy.source_family(context)

    @staticmethod
    def _reviewed_context_explicitly_declares_provenance(context: object) -> bool:
        return ReviewedSlicePolicy.context_explicitly_declares_provenance(context)

    def _require_reviewed_operator_case_record(self, case: CaseRecord) -> CaseRecord:
        return self._reviewed_slice_policy.require_operator_case_record(case)

    def _require_reviewed_operator_alert_record(self, alert: AlertRecord) -> AlertRecord:
        return self._reviewed_slice_policy.require_operator_alert_record(alert)

    def _case_is_in_reviewed_operator_slice(self, case: CaseRecord) -> bool:
        return self._reviewed_slice_policy.case_is_in_operator_slice(case)

    def _alert_is_in_reviewed_operator_slice(self, alert: AlertRecord) -> bool:
        return self._reviewed_slice_policy.alert_is_in_operator_slice(alert)

    def _reviewed_context_declares_out_of_scope_provenance(self, context: object) -> bool:
        return self._reviewed_slice_policy.context_declares_out_of_scope_provenance(
            context
        )

    def _normalize_linked_record_ids(
        self,
        record_ids: tuple[str, ...],
        field_name: str,
    ) -> tuple[str, ...]:
        return self._evidence_linkage_service.normalize_linked_record_ids(
            record_ids,
            field_name,
        )

    def _validate_case_evidence_linkage(
        self,
        *,
        case: CaseRecord,
        evidence_ids: tuple[str, ...],
        field_name: str,
    ) -> None:
        self._evidence_linkage_service.validate_case_evidence_linkage(
            case=case,
            evidence_ids=evidence_ids,
            field_name=field_name,
        )

    def _validate_alert_evidence_linkage(
        self,
        *,
        alert: AlertRecord,
        evidence_ids: tuple[str, ...],
        field_name: str,
    ) -> None:
        self._evidence_linkage_service.validate_alert_evidence_linkage(
            alert=alert,
            evidence_ids=evidence_ids,
            field_name=field_name,
        )

    def _observations_for_case(self, case_id: str) -> tuple[ObservationRecord, ...]:
        return tuple(
            sorted(
                (
                    record
                    for record in self._store.list(ObservationRecord)
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
                    for record in self._store.list(LeadRecord)
                    if record.case_id == case_id
                ),
                key=lambda record: record.lead_id,
            )
        )

    def _case_lifecycle_for_disposition(self, disposition: str) -> str:
        return self._detection_intake_service.case_lifecycle_for_disposition(
            disposition
        )

    @staticmethod
    def _next_identifier(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4()}"

    @staticmethod
    def _alert_review_state(alert: AlertRecord) -> str:
        if alert.lifecycle_state in {"new", "reopened"}:
            return "pending_review"
        if alert.lifecycle_state == "escalated_to_case":
            return "case_required"
        if alert.lifecycle_state == "investigating":
            return "investigating"
        return "triaged"

    @staticmethod
    def _alert_escalation_boundary(alert: AlertRecord) -> str:
        if alert.lifecycle_state == "escalated_to_case":
            return "tracked_case"
        return "next_business_hours_review"

    @staticmethod
    def _require_mapping(value: object, field_name: str) -> dict[str, object]:
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")
        return {str(key): item for key, item in value.items()}


def build_runtime_snapshot(environ: Mapping[str, str] | None = None) -> RuntimeSnapshot:
    config = RuntimeConfig.from_env(
        environ,
        secret_backend_transport=OpenBaoKVv2SecretTransport(),
    )
    service = AegisOpsControlPlaneService(config)
    return service.describe_runtime()


def build_runtime_service(
    environ: Mapping[str, str] | None = None,
) -> AegisOpsControlPlaneService:
    config = RuntimeConfig.from_env(
        environ,
        secret_backend_transport=OpenBaoKVv2SecretTransport(),
    )
    return AegisOpsControlPlaneService(config)
