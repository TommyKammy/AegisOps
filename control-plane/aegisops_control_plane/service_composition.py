from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Type

from .adapters.endpoint_evidence import EndpointEvidencePackAdapter
from .adapters.executor import IsolatedExecutorAdapter
from .adapters.misp import MispContextAdapter
from .adapters.n8n import N8NReconciliationAdapter
from .adapters.osquery import OsqueryHostContextAdapter
from .adapters.postgres import PostgresControlPlaneStore
from .adapters.shuffle import ShuffleActionAdapter
from .ai_trace_lifecycle import AITraceLifecycleService
from .assistant_advisory import AssistantAdvisoryCoordinator
from .assistant_context import (
    AssistantContextAssembler,
    _advisory_text_claims_authority_or_scope_expansion,
)
from .assistant_provider import AssistantProviderAdapter
from .action_lifecycle_write_coordinator import ActionLifecycleWriteCoordinator
from .action_reconciliation_orchestration import (
    ActionOrchestrationBoundary,
    ReconciliationOrchestrationBoundary,
)
from .action_review_write_surface import ActionReviewWriteSurface
from .case_workflow import CaseWorkflowService
from .config import RuntimeConfig
from .detection_lifecycle import DetectionIntakeService
from .evidence_linkage import EvidenceLinkageService
from .execution_coordinator import ExecutionCoordinator
from .external_evidence_boundary import ExternalEvidenceBoundary
from .live_assistant_workflow import LiveAssistantWorkflowCoordinator
from .models import ControlPlaneRecord, ReconciliationRecord
from .operator_inspection import OperatorInspectionReadSurface
from .readiness_operability import ReadinessOperabilityHelper
from .restore_readiness import RestoreReadinessService
from .reviewed_slice_policy import ReviewedSlicePolicy
from .runtime_boundary import RuntimeBoundaryService
from .runtime_restore_readiness_diagnostics import (
    RuntimeRestoreReadinessDiagnosticsService,
)


@dataclass(frozen=True)
class ControlPlaneServiceCompositionDependencies:
    runtime_snapshot_factory: Callable[..., Any]
    authenticated_principal_factory: Callable[..., Any]
    reviewed_summary_transport_factory: Callable[[], Any]
    workflow_family: str
    workflow_prompt_versions: Mapping[str, str]
    record_types_by_family: Mapping[str, Type[ControlPlaneRecord]]
    authoritative_record_chain_record_types: tuple[Type[ControlPlaneRecord], ...]
    authoritative_record_chain_backup_schema_version: str
    authoritative_primary_id_field_by_family: Mapping[str, str]
    normalize_admission_provenance: Callable[[object], dict[str, str] | None]
    merge_reviewed_context: Callable[
        [Mapping[str, object], Mapping[str, object]],
        dict[str, object],
    ]
    case_lifecycle_state_by_triage_disposition: Mapping[str, str]
    record_to_dict: Callable[[ControlPlaneRecord], dict[str, object]]
    json_ready: Callable[[object], object]
    redacted_reconciliation_payload: Callable[
        [ReconciliationRecord],
        dict[str, object],
    ]
    coordination_reference_payload: Callable[
        [Mapping[str, object]],
        dict[str, object] | None,
    ]
    coordination_reference_signature: Callable[[Mapping[str, object]], str | None]
    dedupe_strings: Callable[[Iterable[str]], tuple[str, ...]]
    analyst_queue_snapshot_factory: Callable[..., Any]
    alert_detail_snapshot_factory: Callable[..., Any]
    case_detail_snapshot_factory: Callable[..., Any]
    action_review_detail_snapshot_factory: Callable[..., Any]
    assistant_context_snapshot_factory: Callable[..., Any]
    advisory_snapshot_from_context: Callable[[Any], Any]
    recommendation_draft_snapshot_from_context: Callable[[Any], Any]
    live_assistant_snapshot_factory: Callable[..., Any]
    live_assistant_citations_from_context: Callable[[Any], Any]
    live_assistant_unresolved_reasons: Callable[[Any], Any]
    live_assistant_prompt_injection_flags: Callable[[object], tuple[str, ...]]
    startup_status_snapshot_factory: Callable[..., Any]
    readiness_diagnostics_snapshot_factory: Callable[..., Any]
    restore_drill_snapshot_factory: Callable[..., Any]
    restore_summary_snapshot_factory: Callable[..., Any]
    shutdown_status_snapshot_factory: Callable[..., Any]
    derive_readiness_status: Callable[..., str]
    find_duplicate_strings: Callable[[tuple[str, ...]], tuple[str, ...]]


@dataclass(frozen=True)
class ControlPlaneServiceComposition:
    store: Any
    reconciliation: N8NReconciliationAdapter
    shuffle: ShuffleActionAdapter
    isolated_executor: IsolatedExecutorAdapter
    assistant_provider_adapter: AssistantProviderAdapter
    reviewed_slice_policy: ReviewedSlicePolicy
    ai_trace_lifecycle_service: AITraceLifecycleService
    assistant_context_assembler: AssistantContextAssembler
    assistant_advisory_coordinator: AssistantAdvisoryCoordinator
    live_assistant_workflow_coordinator: LiveAssistantWorkflowCoordinator
    operator_inspection_read_surface: OperatorInspectionReadSurface
    action_review_write_surface: ActionReviewWriteSurface
    evidence_linkage_service: EvidenceLinkageService
    case_workflow_service: CaseWorkflowService
    detection_intake_service: DetectionIntakeService
    execution_coordinator: ExecutionCoordinator
    action_orchestration_boundary: ActionOrchestrationBoundary
    reconciliation_orchestration_boundary: ReconciliationOrchestrationBoundary
    action_lifecycle_write_coordinator: ActionLifecycleWriteCoordinator
    endpoint_evidence_pack_adapter: EndpointEvidencePackAdapter
    misp_context_adapter: MispContextAdapter
    external_evidence_boundary: ExternalEvidenceBoundary
    osquery_host_context_adapter: OsqueryHostContextAdapter
    runtime_boundary_service: RuntimeBoundaryService
    readiness_operability_helper: ReadinessOperabilityHelper
    restore_readiness_service: RestoreReadinessService
    runtime_restore_readiness_diagnostics_service: (
        RuntimeRestoreReadinessDiagnosticsService
    )


def build_control_plane_service_composition(
    *,
    service: Any,
    config: RuntimeConfig,
    store: Any | None,
    dependencies: ControlPlaneServiceCompositionDependencies,
) -> ControlPlaneServiceComposition:
    resolved_store = (
        store if store is not None else PostgresControlPlaneStore(config.postgres_dsn)
    )
    reconciliation = N8NReconciliationAdapter(config.n8n_base_url)
    shuffle = ShuffleActionAdapter(config.shuffle_base_url)
    isolated_executor = IsolatedExecutorAdapter(config.isolated_executor_base_url)
    assistant_provider_adapter = AssistantProviderAdapter(
        provider_identity="reviewed_local",
        model_identity="bounded_reviewed_summary",
        prompt_version=dependencies.workflow_prompt_versions["case_summary"],
        request_timeout_seconds=5.0,
        max_attempts=1,
        transport=dependencies.reviewed_summary_transport_factory(),
    )
    reviewed_slice_policy = ReviewedSlicePolicy(
        service,
        normalize_admission_provenance=dependencies.normalize_admission_provenance,
    )
    ai_trace_lifecycle_service = AITraceLifecycleService(resolved_store)
    assistant_context_assembler = AssistantContextAssembler(
        service,
        record_types_by_family=dependencies.record_types_by_family,
        record_to_dict=dependencies.record_to_dict,
        merge_reviewed_context=dependencies.merge_reviewed_context,
        assistant_context_snapshot_factory=(
            dependencies.assistant_context_snapshot_factory
        ),
        advisory_snapshot_from_context=dependencies.advisory_snapshot_from_context,
        recommendation_draft_snapshot_from_context=(
            dependencies.recommendation_draft_snapshot_from_context
        ),
        ai_trace_lifecycle=ai_trace_lifecycle_service,
    )
    assistant_advisory_coordinator = AssistantAdvisoryCoordinator(
        assistant_context_assembler
    )
    live_assistant_workflow_coordinator = LiveAssistantWorkflowCoordinator(
        service,
        workflow_family=dependencies.workflow_family,
        workflow_prompt_versions=dependencies.workflow_prompt_versions,
        json_ready=lambda value: dependencies.json_ready(value),
        dedupe_strings=lambda values: dependencies.dedupe_strings(values),
        advisory_scope_expansion_flags=(
            lambda text: _advisory_text_claims_authority_or_scope_expansion(text)
        ),
        snapshot_factory=(
            lambda **kwargs: dependencies.live_assistant_snapshot_factory(**kwargs)
        ),
        citations_from_context=(
            lambda snapshot: dependencies.live_assistant_citations_from_context(
                snapshot
            )
        ),
        unresolved_reasons_from_flags=(
            lambda flags: dependencies.live_assistant_unresolved_reasons(flags)
        ),
        prompt_injection_flags=(
            lambda text: dependencies.live_assistant_prompt_injection_flags(text)
        ),
        ai_trace_lifecycle=ai_trace_lifecycle_service,
    )
    operator_inspection_read_surface = OperatorInspectionReadSurface(
        service,
        analyst_queue_snapshot_factory=dependencies.analyst_queue_snapshot_factory,
        alert_detail_snapshot_factory=dependencies.alert_detail_snapshot_factory,
        case_detail_snapshot_factory=dependencies.case_detail_snapshot_factory,
        action_review_detail_snapshot_factory=(
            dependencies.action_review_detail_snapshot_factory
        ),
        record_to_dict=dependencies.record_to_dict,
        redacted_reconciliation_payload=(
            dependencies.redacted_reconciliation_payload
        ),
        normalize_admission_provenance=dependencies.normalize_admission_provenance,
        coordination_reference_payload=dependencies.coordination_reference_payload,
        coordination_reference_signature=dependencies.coordination_reference_signature,
        dedupe_strings=dependencies.dedupe_strings,
    )
    action_review_write_surface = ActionReviewWriteSurface(service)
    evidence_linkage_service = EvidenceLinkageService(
        store=resolved_store,
        require_non_empty_string=service._require_non_empty_string,
        merge_linked_ids=service._merge_linked_ids,
    )
    case_workflow_service = CaseWorkflowService(
        service,
        evidence_linkage_service=evidence_linkage_service,
        merge_reviewed_context=dependencies.merge_reviewed_context,
    )
    detection_intake_service = DetectionIntakeService(
        service,
        merge_reviewed_context=dependencies.merge_reviewed_context,
        normalize_admission_provenance=dependencies.normalize_admission_provenance,
        case_lifecycle_state_by_triage_disposition=(
            dependencies.case_lifecycle_state_by_triage_disposition
        ),
    )
    execution_coordinator = ExecutionCoordinator(service)
    action_orchestration_boundary = ActionOrchestrationBoundary(service)
    reconciliation_orchestration_boundary = ReconciliationOrchestrationBoundary(
        service
    )
    action_lifecycle_write_coordinator = ActionLifecycleWriteCoordinator(
        service,
        action_orchestration_boundary=action_orchestration_boundary,
        reconciliation_orchestration_boundary=reconciliation_orchestration_boundary,
    )
    endpoint_evidence_pack_adapter = EndpointEvidencePackAdapter()
    misp_context_adapter = MispContextAdapter(
        enabled=config.misp_enrichment_enabled
    )
    external_evidence_boundary = ExternalEvidenceBoundary(service)
    osquery_host_context_adapter = OsqueryHostContextAdapter()
    runtime_boundary_service = RuntimeBoundaryService(
        config=config,
        store=resolved_store,
        reconciliation_adapter=reconciliation,
        shuffle_adapter=shuffle,
        isolated_executor_adapter=isolated_executor,
        runtime_snapshot_factory=dependencies.runtime_snapshot_factory,
        authenticated_principal_factory=(
            dependencies.authenticated_principal_factory
        ),
    )
    readiness_operability_helper = ReadinessOperabilityHelper(
        service=service,
        config=config,
        store=resolved_store,
    )
    restore_readiness_service = RestoreReadinessService(
        config=config,
        store=resolved_store,
        runtime_boundary_service=runtime_boundary_service,
        startup_status_snapshot_factory=dependencies.startup_status_snapshot_factory,
        readiness_diagnostics_snapshot_factory=(
            dependencies.readiness_diagnostics_snapshot_factory
        ),
        restore_drill_snapshot_factory=dependencies.restore_drill_snapshot_factory,
        restore_summary_snapshot_factory=dependencies.restore_summary_snapshot_factory,
        record_to_dict=dependencies.record_to_dict,
        json_ready=dependencies.json_ready,
        redacted_reconciliation_payload=(
            dependencies.redacted_reconciliation_payload
        ),
        readiness_operability_helper=readiness_operability_helper,
        shutdown_status_snapshot_factory=(
            dependencies.shutdown_status_snapshot_factory
        ),
        derive_readiness_status=dependencies.derive_readiness_status,
        authoritative_record_chain_record_types=(
            dependencies.authoritative_record_chain_record_types
        ),
        authoritative_record_chain_backup_schema_version=(
            dependencies.authoritative_record_chain_backup_schema_version
        ),
        authoritative_primary_id_field_by_family=(
            dependencies.authoritative_primary_id_field_by_family
        ),
        record_types_by_family=dependencies.record_types_by_family,
        find_duplicate_strings=dependencies.find_duplicate_strings,
        synthesize_lifecycle_transition_record=(
            lambda record, initial_transitioned_at_fallback=None: service._build_lifecycle_transition_record(
                record,
                existing_record=None,
                initial_transitioned_at_fallback=initial_transitioned_at_fallback,
            )
        ),
        assistant_ids_from_mapping=service._assistant_ids_from_mapping,
        inspect_case_detail=lambda case_id: service.inspect_case_detail(case_id),
        inspect_assistant_context=(
            lambda record_family, record_id: service.inspect_assistant_context(
                record_family,
                record_id,
            )
        ),
        inspect_reconciliation_status=lambda: service.inspect_reconciliation_status(),
    )
    runtime_restore_readiness_diagnostics_service = (
        RuntimeRestoreReadinessDiagnosticsService(
            runtime_boundary_service=runtime_boundary_service,
            restore_readiness_service=restore_readiness_service,
        )
    )

    return ControlPlaneServiceComposition(
        store=resolved_store,
        reconciliation=reconciliation,
        shuffle=shuffle,
        isolated_executor=isolated_executor,
        assistant_provider_adapter=assistant_provider_adapter,
        reviewed_slice_policy=reviewed_slice_policy,
        ai_trace_lifecycle_service=ai_trace_lifecycle_service,
        assistant_context_assembler=assistant_context_assembler,
        assistant_advisory_coordinator=assistant_advisory_coordinator,
        live_assistant_workflow_coordinator=live_assistant_workflow_coordinator,
        operator_inspection_read_surface=operator_inspection_read_surface,
        action_review_write_surface=action_review_write_surface,
        evidence_linkage_service=evidence_linkage_service,
        case_workflow_service=case_workflow_service,
        detection_intake_service=detection_intake_service,
        execution_coordinator=execution_coordinator,
        action_orchestration_boundary=action_orchestration_boundary,
        reconciliation_orchestration_boundary=reconciliation_orchestration_boundary,
        action_lifecycle_write_coordinator=action_lifecycle_write_coordinator,
        endpoint_evidence_pack_adapter=endpoint_evidence_pack_adapter,
        misp_context_adapter=misp_context_adapter,
        external_evidence_boundary=external_evidence_boundary,
        osquery_host_context_adapter=osquery_host_context_adapter,
        runtime_boundary_service=runtime_boundary_service,
        readiness_operability_helper=readiness_operability_helper,
        restore_readiness_service=restore_readiness_service,
        runtime_restore_readiness_diagnostics_service=(
            runtime_restore_readiness_diagnostics_service
        ),
    )


__all__ = [
    "ControlPlaneServiceComposition",
    "ControlPlaneServiceCompositionDependencies",
    "build_control_plane_service_composition",
]
