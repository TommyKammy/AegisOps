#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0013-phase-52-5-2-package-scaffolding-and-compatibility-shim-policy.md"
control_plane_root="${repo_root}/control-plane"

required_imports=(
  "aegisops_control_plane.service:AegisOpsControlPlaneService"
  "aegisops_control_plane.models:AlertRecord"
  "aegisops_control_plane.ai_trace_lifecycle:AITraceLifecycleService"
  "aegisops_control_plane.assistant.ai_trace_lifecycle:AITraceLifecycleService"
  "aegisops_control_plane.assistant_advisory:AssistantAdvisoryCoordinator"
  "aegisops_control_plane.assistant.assistant_advisory:AssistantAdvisoryCoordinator"
  "aegisops_control_plane.assistant_context:AssistantContextAssembler"
  "aegisops_control_plane.assistant.assistant_context:AssistantContextAssembler"
  "aegisops_control_plane.assistant_provider:AssistantProviderAdapter"
  "aegisops_control_plane.assistant.assistant_provider:AssistantProviderAdapter"
  "aegisops_control_plane.live_assistant_workflow:LiveAssistantWorkflowCoordinator"
  "aegisops_control_plane.assistant.live_assistant_workflow:LiveAssistantWorkflowCoordinator"
  "aegisops_control_plane.audit_export:export_audit_retention_baseline"
  "aegisops_control_plane.reporting.audit_export:export_audit_retention_baseline"
  "aegisops_control_plane.pilot_reporting_export:export_pilot_executive_summary"
  "aegisops_control_plane.reporting.pilot_reporting_export:export_pilot_executive_summary"
  "aegisops_control_plane.action_review_chain:action_review_chains_for_scope"
  "aegisops_control_plane.actions.review.action_review_chain:action_review_chains_for_scope"
  "aegisops_control_plane.action_review_coordination:action_review_coordination_ticket_outcome"
  "aegisops_control_plane.actions.review.action_review_coordination:action_review_coordination_ticket_outcome"
  "aegisops_control_plane.action_review_index:build_action_review_record_index"
  "aegisops_control_plane.actions.review.action_review_index:build_action_review_record_index"
  "aegisops_control_plane.action_review_inspection:ActionReviewInspectionBoundary"
  "aegisops_control_plane.actions.review.action_review_inspection:ActionReviewInspectionBoundary"
  "aegisops_control_plane.action_review_path_health:action_review_path_health"
  "aegisops_control_plane.actions.review.action_review_path_health:action_review_path_health"
  "aegisops_control_plane.action_review_projection:build_action_review_record_index"
  "aegisops_control_plane.actions.review.action_review_projection:build_action_review_record_index"
  "aegisops_control_plane.action_review_timeline:action_review_timeline"
  "aegisops_control_plane.actions.review.action_review_timeline:action_review_timeline"
  "aegisops_control_plane.action_review_visibility:action_review_runtime_visibility"
  "aegisops_control_plane.actions.review.action_review_visibility:action_review_runtime_visibility"
  "aegisops_control_plane.action_review_write_surface:ActionReviewWriteSurface"
  "aegisops_control_plane.actions.review.action_review_write_surface:ActionReviewWriteSurface"
  "aegisops_control_plane.action_lifecycle_write_coordinator:ActionLifecycleWriteCoordinator"
  "aegisops_control_plane.actions.action_lifecycle_write_coordinator:ActionLifecycleWriteCoordinator"
  "aegisops_control_plane.action_policy:evaluate_action_policy_record"
  "aegisops_control_plane.actions.action_policy:evaluate_action_policy_record"
  "aegisops_control_plane.action_receipt_validation:MissingReceiptValueError"
  "aegisops_control_plane.actions.action_receipt_validation:MissingReceiptValueError"
  "aegisops_control_plane.action_reconciliation_orchestration:ActionOrchestrationBoundary"
  "aegisops_control_plane.actions.action_reconciliation_orchestration:ActionOrchestrationBoundary"
  "aegisops_control_plane.execution_coordinator:ExecutionCoordinator"
  "aegisops_control_plane.actions.execution_coordinator:ExecutionCoordinator"
  "aegisops_control_plane.execution_coordinator_action_requests:ReviewedActionRequestCoordinator"
  "aegisops_control_plane.actions.execution_coordinator_action_requests:ReviewedActionRequestCoordinator"
  "aegisops_control_plane.execution_coordinator_delegation:ApprovedActionDelegationCoordinator"
  "aegisops_control_plane.actions.execution_coordinator_delegation:ApprovedActionDelegationCoordinator"
  "aegisops_control_plane.execution_coordinator_reconciliation:ActionExecutionReconciliationCoordinator"
  "aegisops_control_plane.actions.execution_coordinator_reconciliation:ActionExecutionReconciliationCoordinator"
  "aegisops_control_plane.runtime_boundary:RuntimeBoundaryService"
  "aegisops_control_plane.runtime.runtime_boundary:RuntimeBoundaryService"
  "aegisops_control_plane.readiness_contracts:ReadinessDiagnosticsAggregates"
  "aegisops_control_plane.runtime.readiness_contracts:ReadinessDiagnosticsAggregates"
  "aegisops_control_plane.readiness_operability:ReadinessOperabilityHelper"
  "aegisops_control_plane.runtime.readiness_operability:ReadinessOperabilityHelper"
  "aegisops_control_plane.restore_readiness:RestoreReadinessService"
  "aegisops_control_plane.runtime.restore_readiness:RestoreReadinessService"
  "aegisops_control_plane.restore_readiness_projection:_ReadinessHealthProjection"
  "aegisops_control_plane.runtime.restore_readiness_projection:_ReadinessHealthProjection"
  "aegisops_control_plane.restore_readiness_backup_restore:_BackupRestoreFlow"
  "aegisops_control_plane.runtime.restore_readiness_backup_restore:_BackupRestoreFlow"
  "aegisops_control_plane.runtime_restore_readiness_diagnostics:RuntimeRestoreReadinessDiagnosticsService"
  "aegisops_control_plane.runtime.runtime_restore_readiness_diagnostics:RuntimeRestoreReadinessDiagnosticsService"
  "aegisops_control_plane.service_snapshots:RuntimeSnapshot"
  "aegisops_control_plane.runtime.service_snapshots:RuntimeSnapshot"
  "aegisops_control_plane.operations:RuntimeBoundaryService"
  "aegisops_control_plane.runtime.operations:RuntimeBoundaryService"
  "aegisops_control_plane.cli:build_parser"
  "aegisops_control_plane.api.cli:build_parser"
  "aegisops_control_plane.entrypoint_support:normalize_alert_id"
  "aegisops_control_plane.api.entrypoint_support:normalize_alert_id"
  "aegisops_control_plane.http_surface:HttpSurfaceContext"
  "aegisops_control_plane.api.http_surface:HttpSurfaceContext"
  "aegisops_control_plane.http_protected_surface:authenticate_protected_write"
  "aegisops_control_plane.api.http_protected_surface:authenticate_protected_write"
  "aegisops_control_plane.http_runtime_surface:runtime_read_response"
  "aegisops_control_plane.api.http_runtime_surface:runtime_read_response"
  "aegisops_control_plane.detection_lifecycle:DetectionIntakeService"
  "aegisops_control_plane.ingestion.detection_lifecycle:DetectionIntakeService"
  "aegisops_control_plane.detection_lifecycle_helpers:DetectionLifecycleTransitionHelper"
  "aegisops_control_plane.ingestion.detection_lifecycle_helpers:DetectionLifecycleTransitionHelper"
  "aegisops_control_plane.detection_native_context:NativeDetectionContextAttacher"
  "aegisops_control_plane.ingestion.detection_native_context:NativeDetectionContextAttacher"
  "aegisops_control_plane.case_workflow:CaseWorkflowService"
  "aegisops_control_plane.ingestion.case_workflow:CaseWorkflowService"
  "aegisops_control_plane.evidence_linkage:EvidenceLinkageService"
  "aegisops_control_plane.ingestion.evidence_linkage:EvidenceLinkageService"
  "aegisops_control_plane.external_evidence_boundary:ExternalEvidenceBoundary"
  "aegisops_control_plane.evidence.external_evidence_boundary:ExternalEvidenceBoundary"
  "aegisops_control_plane.external_evidence_facade:ExternalEvidenceFacade"
  "aegisops_control_plane.evidence.external_evidence_facade:ExternalEvidenceFacade"
  "aegisops_control_plane.external_evidence_misp:MispExternalEvidenceHelper"
  "aegisops_control_plane.evidence.external_evidence_misp:MispExternalEvidenceHelper"
  "aegisops_control_plane.external_evidence_osquery:OsqueryExternalEvidenceHelper"
  "aegisops_control_plane.evidence.external_evidence_osquery:OsqueryExternalEvidenceHelper"
  "aegisops_control_plane.external_evidence_endpoint:EndpointExternalEvidenceHelper"
  "aegisops_control_plane.evidence.external_evidence_endpoint:EndpointExternalEvidenceHelper"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.5.2 compatibility-shim policy: ${doc_path}" >&2
  exit 1
fi

if [[ ! -d "${control_plane_root}" || ! -r "${control_plane_root}" || ! -x "${control_plane_root}" ]]; then
  echo "Missing or unreadable Phase 52.5.2 control-plane root for import compatibility verifier: ${control_plane_root}" >&2
  exit 1
fi

for import_spec in "${required_imports[@]}"; do
  if ! grep -Fq -- "${import_spec}" "${doc_path}"; then
    echo "Missing Phase 52.5.2 documented legacy import compatibility check: ${import_spec}" >&2
    exit 1
  fi
done

export PHASE52_5_2_CONTROL_PLANE_ROOT="${control_plane_root}"
export PHASE52_5_2_REQUIRED_IMPORTS="$(printf '%s\n' "${required_imports[@]}")"

python3 - <<'PY'
from __future__ import annotations

import importlib
import os
import pathlib
import sys

control_plane_root = pathlib.Path(os.environ["PHASE52_5_2_CONTROL_PLANE_ROOT"])
if str(control_plane_root) not in sys.path:
    sys.path.insert(0, str(control_plane_root))

required_imports = [
    line
    for line in os.environ["PHASE52_5_2_REQUIRED_IMPORTS"].splitlines()
    if line.strip()
]

for import_spec in required_imports:
    module_name, attribute_name = import_spec.split(":", 1)
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - shell verifier reports detail.
        print(
            f"Phase 52.5.2 legacy import failed: {module_name}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    if not hasattr(module, attribute_name):
        print(
            f"Phase 52.5.2 legacy import missing attribute: {import_spec}",
            file=sys.stderr,
        )
        sys.exit(1)

print(
    "Phase 52.5.2 import compatibility verifier preserved stable legacy imports: "
    + ", ".join(required_imports)
)
PY
