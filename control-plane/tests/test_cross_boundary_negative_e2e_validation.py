from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
for candidate in (CONTROL_PLANE_ROOT, TESTS_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


from _cli_inspection_support import ControlPlaneCliInspectionTestBase
from aegisops_control_plane.assistant_provider import AssistantProviderAdapter
from aegisops_control_plane.models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    EvidenceRecord,
    LeadRecord,
    ObservationRecord,
    RecommendationRecord,
    ReconciliationRecord,
)
from aegisops_control_plane.phase29_evidently_drift_visibility import (
    build_phase29_evidently_drift_visibility_report,
)
from aegisops_control_plane.phase29_shadow_dataset import Phase29ShadowDatasetSnapshot
from aegisops_control_plane.phase29_shadow_scoring import (
    Phase29ShadowScoringError,
    score_shadow_dataset_offline,
)
from aegisops_control_plane.service import AegisOpsControlPlaneService
import _cli_inspection_support as cli_support
import test_phase28_endpoint_evidence_pack_validation as phase28_tests
import test_phase29_no_authority_ml_and_optional_network_validation as phase29_tests


_AUTHORITATIVE_RECORD_TYPES = (
    AlertRecord,
    CaseRecord,
    EvidenceRecord,
    ObservationRecord,
    LeadRecord,
    RecommendationRecord,
    ApprovalDecisionRecord,
    ActionRequestRecord,
    ActionExecutionRecord,
    ReconciliationRecord,
)


class CrossBoundaryNegativeE2EValidationTests(unittest.TestCase):
    def test_assistant_unresolved_and_degraded_optional_extension_paths_stay_fail_closed(
        self,
    ) -> None:
        phase28_helper = phase28_tests.Phase28EndpointEvidencePackValidationTests()
        store, seeded_service, promoted_case, anchor_evidence_id, reviewed_at = (
            phase28_helper._build_host_bound_case()
        )
        service = AegisOpsControlPlaneService(
            replace(
                seeded_service._config,
                isolated_executor_base_url="https://executor.internal",
            ),
            store=store,
        )
        baseline_case = store.get(CaseRecord, promoted_case.case_id)
        baseline_reconciliation_count = len(store.list(ReconciliationRecord))
        self.assertIsNotNone(baseline_case)

        service._assistant_provider_adapter = mock.Mock()
        service._assistant_provider_adapter.generate.side_effect = RuntimeError(
            "provider transport failed"
        )
        provider_adapter = AssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            request_timeout_seconds=5.0,
            max_attempts=1,
            transport=mock.Mock(),
        )
        service._assistant_provider_adapter.build_ai_trace_record.side_effect = (
            provider_adapter.build_ai_trace_record
        )

        workflow_snapshot = service.run_live_assistant_workflow(
            workflow_task="case_summary",
            record_family="case",
            record_id=promoted_case.case_id,
        )

        action_request = service.create_endpoint_evidence_collection_request(
            case_id=promoted_case.case_id,
            admitting_evidence_id=anchor_evidence_id,
            requester_identity="analyst-001",
            host_identifier="host-001",
            evidence_gap="Need endpoint evidence to resolve the reviewed host-state gap.",
            artifact_classes=("collection_manifest", "triage_bundle"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cross-boundary-endpoint-001",
        )
        service.record_action_approval_decision(
            action_request_id=action_request.action_request_id,
            approver_identity="reviewer-001",
            decision="grant",
            decision_rationale="Approved bounded read-only endpoint evidence collection.",
            decided_at=action_request.requested_at + timedelta(minutes=5),
        )
        approved_request = service.get_record(
            ActionRequestRecord,
            action_request.action_request_id,
        )
        assert approved_request is not None
        service.persist_record(
            replace(
                approved_request,
                requested_at=reviewed_at - timedelta(hours=2),
                expires_at=reviewed_at - timedelta(hours=1),
                lifecycle_state="executing",
            )
        )

        readiness = service.inspect_readiness_diagnostics()
        optional_extensions = readiness.metrics["optional_extensions"]
        assistant_extension = optional_extensions["extensions"]["assistant"]
        endpoint_extension = optional_extensions["extensions"]["endpoint_evidence"]
        network_extension = optional_extensions["extensions"]["network_evidence"]
        ml_shadow_extension = optional_extensions["extensions"]["ml_shadow"]

        ai_traces = store.list(AITraceRecord)
        recommendations = store.list(RecommendationRecord)
        current_case = store.get(CaseRecord, promoted_case.case_id)

        self.assertEqual(workflow_snapshot.status, "unresolved")
        self.assertEqual(
            workflow_snapshot.unresolved_reasons,
            (
                "the bounded live assistant did not return a trusted summary within the reviewed retry budget",
            ),
        )
        self.assertEqual(len(ai_traces), 1)
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(ai_traces[0].lifecycle_state, "under_review")
        self.assertEqual(recommendations[0].lifecycle_state, "under_review")
        self.assertEqual(
            recommendations[0].assistant_advisory_draft["status"],
            "unresolved",
        )
        self.assertIsNotNone(current_case)
        self.assertEqual(current_case.lifecycle_state, baseline_case.lifecycle_state)
        self.assertEqual(current_case.evidence_ids, baseline_case.evidence_ids)
        self.assertEqual(optional_extensions["overall_state"], "degraded")
        self.assertEqual(assistant_extension["authority_mode"], "advisory_only")
        self.assertEqual(assistant_extension["readiness"], "degraded")
        self.assertEqual(assistant_extension["reason"], "assistant_provider_unavailable")
        self.assertEqual(assistant_extension["provider_status"], "failed")
        self.assertEqual(assistant_extension["retry_policy"], "retry_exhausted")
        self.assertEqual(endpoint_extension["enablement"], "enabled")
        self.assertEqual(endpoint_extension["readiness"], "degraded")
        self.assertEqual(network_extension["enablement"], "disabled_by_default")
        self.assertEqual(network_extension["readiness"], "not_applicable")
        self.assertEqual(ml_shadow_extension["enablement"], "disabled_by_default")
        self.assertEqual(ml_shadow_extension["readiness"], "not_applicable")
        self.assertEqual(store.list(ActionExecutionRecord), ())
        self.assertEqual(
            len(store.list(ReconciliationRecord)),
            baseline_reconciliation_count,
        )

    def test_soft_write_receipt_mismatch_stays_non_authoritative_in_case_detail_surface(
        self,
    ) -> None:
        cli_helper = cli_support.ControlPlaneCliInspectionTestBase()
        store, service, promoted_case, _evidence_id, reviewed_at = (
            cli_helper._build_phase19_in_scope_case()
        )
        seeded = cli_helper._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="cross-boundary-mismatch-001",
            coordination_reference_id="coord-ref-cross-boundary-mismatch-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=reviewed_at + timedelta(minutes=15),
            delegation_issuer="control-plane-service",
        )
        downstream_binding = execution.provenance["downstream_binding"]
        service.reconcile_action_execution(
            action_request_id=seeded["action_request"].action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": seeded["action_request"].idempotency_key,
                    "approval_decision_id": seeded["approval"].approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": seeded["payload_hash"],
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": "shuffle-receipt-cross-boundary-drift-001",
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": reviewed_at + timedelta(minutes=20),
                    "status": "success",
                },
            ),
            compared_at=reviewed_at + timedelta(minutes=20),
            stale_after=reviewed_at + timedelta(hours=1),
        )

        case_detail = service.inspect_case_detail(promoted_case.case_id).to_dict()
        current_case = store.get(CaseRecord, promoted_case.case_id)
        current_alert = store.get(AlertRecord, promoted_case.alert_id)
        current_execution = store.get(
            ActionExecutionRecord,
            execution.action_execution_id,
        )

        self.assertEqual(
            case_detail["current_action_review"]["coordination_ticket_outcome"]["status"],
            "mismatch",
        )
        self.assertEqual(
            case_detail["current_action_review"]["coordination_ticket_outcome"][
                "mismatch"
            ]["mismatch_summary"],
            "coordination receipt mismatch between authoritative action execution and observed downstream execution",
        )
        self.assertEqual(
            case_detail["external_ticket_reference"]["authority"],
            "non_authoritative",
        )
        self.assertEqual(case_detail["external_ticket_reference"]["status"], "missing")
        self.assertIsNotNone(current_case)
        self.assertIsNotNone(current_alert)
        self.assertIsNotNone(current_execution)
        self.assertIsNone(current_case.coordination_reference_id)
        self.assertIsNone(current_alert.coordination_reference_id)
        self.assertEqual(current_execution.lifecycle_state, "queued")
        self.assertEqual(
            current_execution.provenance["downstream_binding"]["external_receipt_id"],
            downstream_binding["external_receipt_id"],
        )

    def test_external_ticket_stale_or_closed_observation_does_not_auto_close_case(
        self,
    ) -> None:
        for observed_status in ("success", "closed"):
            with self.subTest(observed_status=observed_status):
                cli_helper = cli_support.ControlPlaneCliInspectionTestBase()
                store, service, promoted_case, _evidence_id, reviewed_at = (
                    cli_helper._build_phase19_in_scope_case()
                )
                seeded = cli_helper._seed_create_tracking_ticket_request(
                    service=service,
                    promoted_case=promoted_case,
                    reviewed_at=reviewed_at,
                    suffix=f"cross-boundary-ticket-{observed_status}-001",
                    coordination_reference_id=(
                        f"coord-ref-cross-boundary-ticket-{observed_status}-001"
                    ),
                )
                baseline_case = store.get(CaseRecord, promoted_case.case_id)
                baseline_alert = store.get(AlertRecord, promoted_case.alert_id)
                self.assertIsNotNone(baseline_case)
                self.assertIsNotNone(baseline_alert)

                execution = service.delegate_approved_action_to_shuffle(
                    action_request_id=seeded["action_request"].action_request_id,
                    approved_payload=seeded["approved_payload"],
                    delegated_at=reviewed_at + timedelta(minutes=15),
                    delegation_issuer="control-plane-service",
                )
                downstream_binding = execution.provenance["downstream_binding"]
                reconciliation = service.reconcile_action_execution(
                    action_request_id=seeded["action_request"].action_request_id,
                    execution_surface_type="automation_substrate",
                    execution_surface_id="shuffle",
                    observed_executions=(
                        {
                            "execution_run_id": execution.execution_run_id,
                            "execution_surface_id": "shuffle",
                            "idempotency_key": seeded["action_request"].idempotency_key,
                            "approval_decision_id": seeded[
                                "approval"
                            ].approval_decision_id,
                            "delegation_id": execution.delegation_id,
                            "payload_hash": seeded["payload_hash"],
                            "coordination_reference_id": downstream_binding[
                                "coordination_reference_id"
                            ],
                            "coordination_target_type": downstream_binding[
                                "coordination_target_type"
                            ],
                            "external_receipt_id": downstream_binding[
                                "external_receipt_id"
                            ],
                            "coordination_target_id": downstream_binding[
                                "coordination_target_id"
                            ],
                            "ticket_reference_url": downstream_binding[
                                "ticket_reference_url"
                            ],
                            "observed_at": reviewed_at + timedelta(minutes=20),
                            "status": observed_status,
                        },
                    ),
                    compared_at=reviewed_at + timedelta(hours=2),
                    stale_after=reviewed_at + timedelta(hours=1),
                )

                current_case = store.get(CaseRecord, promoted_case.case_id)
                current_alert = store.get(AlertRecord, promoted_case.alert_id)
                current_execution = store.get(
                    ActionExecutionRecord,
                    execution.action_execution_id,
                )
                case_detail = service.inspect_case_detail(promoted_case.case_id).to_dict()

                self.assertEqual(reconciliation.lifecycle_state, "stale")
                self.assertEqual(reconciliation.ingest_disposition, "stale")
                self.assertIsNotNone(current_case)
                self.assertIsNotNone(current_alert)
                self.assertIsNotNone(current_execution)
                self.assertEqual(
                    current_case.lifecycle_state,
                    baseline_case.lifecycle_state,
                )
                self.assertEqual(
                    current_alert.lifecycle_state,
                    baseline_alert.lifecycle_state,
                )
                self.assertIsNone(current_case.coordination_reference_id)
                self.assertIsNone(current_alert.coordination_reference_id)
                self.assertEqual(current_execution.lifecycle_state, "queued")
                self.assertEqual(
                    case_detail["current_action_review"][
                        "coordination_ticket_outcome"
                    ]["status"],
                    "pending",
                )
                self.assertNotEqual(current_case.lifecycle_state, "closed")

    def test_endpoint_evidence_missing_provenance_is_not_promoted(self) -> None:
        phase28_helper = phase28_tests.Phase28EndpointEvidencePackValidationTests()
        store, service, promoted_case, anchor_evidence_id, reviewed_at = (
            phase28_helper._build_host_bound_case()
        )
        action_request = service.create_endpoint_evidence_collection_request(
            case_id=promoted_case.case_id,
            admitting_evidence_id=anchor_evidence_id,
            requester_identity="analyst-001",
            host_identifier="host-001",
            evidence_gap="Need endpoint evidence to resolve the reviewed host-state gap.",
            artifact_classes=("collection_manifest",),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
        )
        phase28_helper._approve_action_request(
            service,
            action_request.action_request_id,
            decided_at=action_request.requested_at + timedelta(minutes=5),
        )
        baseline_case = store.get(CaseRecord, promoted_case.case_id)
        baseline_evidence_ids = {record.evidence_id for record in store.list(EvidenceRecord)}
        self.assertIsNotNone(baseline_case)

        with self.assertRaisesRegex(ValueError, "artifact.source_boundary"):
            service.ingest_endpoint_evidence_artifacts(
                action_request_id=action_request.action_request_id,
                artifacts=(
                    {
                        "artifact_class": "collection_manifest",
                        "artifact_id": "manifest-missing-provenance-001",
                        "source_artifact_id": "collector-manifest-missing-provenance-001",
                        "collected_at": reviewed_at,
                        "collector_identity": "velociraptor",
                        "tool_name": "Velociraptor",
                        "citation_kind": "raw_collected_output",
                        "description": "Missing boundary provenance must stay blocked.",
                        "content": {"query_names": ("Artifact.Windows.System.Pslist",)},
                    },
                ),
                admitted_by="analyst-001",
            )

        current_case = store.get(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(current_case)
        self.assertEqual(current_case.lifecycle_state, baseline_case.lifecycle_state)
        self.assertEqual(current_case.evidence_ids, baseline_case.evidence_ids)
        self.assertEqual(
            {record.evidence_id for record in store.list(EvidenceRecord)},
            baseline_evidence_ids,
        )

    def test_expired_delegation_fails_closed_before_action_execution_dispatch(self) -> None:
        phase28_helper = phase28_tests.Phase28EndpointEvidencePackValidationTests()
        store, service, promoted_case, anchor_evidence_id, reviewed_at = (
            phase28_helper._build_host_bound_case()
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        action_request = service.create_endpoint_evidence_collection_request(
            case_id=promoted_case.case_id,
            admitting_evidence_id=anchor_evidence_id,
            requester_identity="analyst-001",
            host_identifier="host-001",
            evidence_gap="Need endpoint evidence to resolve the reviewed host-state gap.",
            artifact_classes=("collection_manifest",),
            expires_at=expires_at,
        )
        phase28_helper._approve_action_request(
            service,
            action_request.action_request_id,
            decided_at=action_request.requested_at + timedelta(minutes=5),
        )
        approved_request = store.get(ActionRequestRecord, action_request.action_request_id)
        baseline_case = store.get(CaseRecord, promoted_case.case_id)
        baseline_execution_ids = {
            record.action_execution_id for record in store.list(ActionExecutionRecord)
        }
        self.assertIsNotNone(approved_request)
        self.assertIsNotNone(baseline_case)

        with self.assertRaisesRegex(
            ValueError,
            "expired before isolated executor delegation",
        ):
            service.delegate_approved_action_to_isolated_executor(
                action_request_id=approved_request.action_request_id,
                approved_payload=approved_request.requested_payload,
                delegated_at=expires_at + timedelta(seconds=1),
                delegation_issuer="control-plane-service",
            )

        current_case = store.get(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(current_case)
        self.assertEqual(current_case.lifecycle_state, baseline_case.lifecycle_state)
        self.assertEqual(current_case.evidence_ids, baseline_case.evidence_ids)
        self.assertEqual(
            {
                record.action_execution_id
                for record in store.list(ActionExecutionRecord)
            },
            baseline_execution_ids,
        )

    def test_ml_shadow_and_optional_network_failure_signals_leave_authoritative_state_clean(
        self,
    ) -> None:
        phase29_helper = (
            phase29_tests.Phase29NoAuthorityMlAndOptionalNetworkValidationTests()
        )
        (
            store,
            service,
            linked_case,
            accepted_recommendation,
            reference_snapshot,
            candidate_snapshot,
            rendered_at,
        ) = phase29_helper._build_phase29_shadow_and_optional_network_context()
        baseline_counts = self._record_counts(store)
        baseline_case = store.get(CaseRecord, linked_case.case_id)
        baseline_recommendation = store.get(
            RecommendationRecord,
            accepted_recommendation.recommendation_id,
        )
        self.assertIsNotNone(baseline_case)
        self.assertIsNotNone(baseline_recommendation)

        example = candidate_snapshot.examples[0]
        broken_snapshot = Phase29ShadowDatasetSnapshot(
            snapshot_id=candidate_snapshot.snapshot_id,
            extraction_spec_version=candidate_snapshot.extraction_spec_version,
            snapshot_timestamp=candidate_snapshot.snapshot_timestamp,
            example_count=1,
            examples=(
                {
                    **example,
                    "label": {
                        **example["label"],
                        "provenance": {
                            key: value
                            for key, value in example["label"]["provenance"].items()
                            if key != "label_record_id"
                        },
                    },
                },
            ),
        )

        with self.assertRaisesRegex(
            Phase29ShadowScoringError,
            "missing required label provenance: label_record_id",
        ):
            score_shadow_dataset_offline(
                dataset_snapshot=broken_snapshot,
                scoring_spec_version="phase29-shadow-scoring-v1",
                model_family="baseline-isolation-forest",
                model_version="candidate-2026-04-20",
                training_data_snapshot_id=broken_snapshot.snapshot_id,
                feature_schema_version="phase29-shadow-features-v1",
                label_schema_version="phase29-shadow-labels-v1",
                lineage_review_note_id="note-phase29-shadow-001",
                scored_at=rendered_at,
            )

        drift_report = build_phase29_evidently_drift_visibility_report(
            reference_snapshot=reference_snapshot,
            candidate_snapshot=candidate_snapshot,
            rendered_at=rendered_at,
            stale_feature_after=timedelta(minutes=30),
        )
        readiness = service.inspect_readiness_diagnostics()
        optional_extensions = readiness.metrics["optional_extensions"]["extensions"]
        current_case = store.get(CaseRecord, linked_case.case_id)
        current_recommendation = store.get(
            RecommendationRecord,
            accepted_recommendation.recommendation_id,
        )

        self.assertEqual(drift_report.status, "degraded")
        self.assertEqual(drift_report.authority_posture, "non-authoritative")
        self.assertEqual(optional_extensions["network_evidence"]["enablement"], "disabled_by_default")
        self.assertEqual(optional_extensions["network_evidence"]["readiness"], "not_applicable")
        self.assertEqual(optional_extensions["ml_shadow"]["enablement"], "disabled_by_default")
        self.assertEqual(optional_extensions["ml_shadow"]["readiness"], "not_applicable")
        self.assertIsNotNone(current_case)
        self.assertIsNotNone(current_recommendation)
        self.assertEqual(current_case.lifecycle_state, baseline_case.lifecycle_state)
        self.assertEqual(current_case.evidence_ids, baseline_case.evidence_ids)
        self.assertEqual(
            current_recommendation.lifecycle_state,
            baseline_recommendation.lifecycle_state,
        )
        self.assertEqual(self._record_counts(store), baseline_counts)

    @staticmethod
    def _record_counts(store: object) -> dict[str, int]:
        return {
            record_type.__name__: len(store.list(record_type))
            for record_type in _AUTHORITATIVE_RECORD_TYPES
        }


if __name__ == "__main__":
    unittest.main()
