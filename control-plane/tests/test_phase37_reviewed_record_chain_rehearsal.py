from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
import json
import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _service_persistence_support import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    EvidenceRecord,
    ReconciliationRecord,
    ServicePersistenceTestBase,
    make_store,
)
import _service_persistence_support as support


FIXTURE_PATH = (
    TESTS_ROOT
    / "fixtures"
    / "phase37"
    / "reviewed-record-chain-rehearsal.json"
)


def _load_rehearsal_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _parse_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO datetime")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return parsed


def _require_mapping(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_number(value: object, field_name: str) -> int | float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a number")
    return value


def _validate_release_gate_manifest(
    *,
    manifest: dict[str, object],
    evidence: EvidenceRecord,
    action_request: ActionRequestRecord | None,
    approval_decision: ApprovalDecisionRecord | None,
    execution: ActionExecutionRecord | None,
    reconciliation: ReconciliationRecord | None,
) -> None:
    required_records = manifest.get("required_release_gate_records")
    if not isinstance(required_records, list):
        raise ValueError("release-gate manifest requires required_release_gate_records")
    for record_family in (
        "approval_decision",
        "action_execution",
        "reconciliation",
    ):
        if record_family not in required_records:
            raise ValueError(f"release-gate manifest missing {record_family}")

    if action_request is None or action_request.lifecycle_state != "approved":
        raise ValueError("release-gate chain requires an approved action request")
    if approval_decision is None or approval_decision.lifecycle_state != "approved":
        raise ValueError("release-gate chain requires a recorded approval decision")
    if execution is None or execution.execution_run_id.startswith("pending-dispatch-"):
        raise ValueError("release-gate chain requires an execution receipt")
    if reconciliation is None or reconciliation.lifecycle_state != "matched":
        raise ValueError("release-gate chain requires matched reconciliation")

    if approval_decision.approval_decision_id != action_request.approval_decision_id:
        raise ValueError("approval decision must bind to the action request")
    if execution.approval_decision_id != approval_decision.approval_decision_id:
        raise ValueError("execution receipt must bind to the approval decision")
    if execution.action_request_id != action_request.action_request_id:
        raise ValueError("execution receipt must bind to the action request")
    if reconciliation.execution_run_id != execution.execution_run_id:
        raise ValueError("reconciliation must bind to the execution receipt")
    if evidence.evidence_id not in reconciliation.subject_linkage.get("evidence_ids", ()):
        raise ValueError("reconciliation must preserve linked evidence")

    if evidence.content.get("external_ticket_authority") != "subordinate_evidence_only":
        raise ValueError("external ticket references must remain subordinate evidence")
    if "external_ticket_reference" in action_request.target_scope:
        raise ValueError("external ticket reference must not become action authority")


class Phase37ReviewedRecordChainRehearsalTests(ServicePersistenceTestBase):
    def test_seeded_rehearsal_replays_reviewed_record_chain_end_to_end(self) -> None:
        fixture = _load_rehearsal_fixture()
        detection = _require_mapping(fixture.get("detection"), "detection")
        evidence_fixture = _require_mapping(fixture.get("evidence"), "evidence")
        case_workflow = _require_mapping(fixture.get("case_workflow"), "case_workflow")
        action = _require_mapping(fixture.get("action"), "action")
        approval = _require_mapping(fixture.get("approval"), "approval")
        execution_fixture = _require_mapping(fixture.get("execution"), "execution")
        reconciliation_fixture = _require_mapping(
            fixture.get("reconciliation"),
            "reconciliation",
        )
        manifest = _require_mapping(fixture.get("manifest"), "manifest")

        store, _ = make_store()
        service = support.AegisOpsControlPlaneService(
            support.RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="phase37-reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="phase37-reviewed-proxy-secret",
            ),
            store=store,
        )
        self.assertEqual(detection.get("reviewed_source_family"), "wazuh_github_audit")
        reviewed_context = _require_mapping(
            detection.get("reviewed_context"),
            "reviewed_context",
        )
        admitted = service.ingest_wazuh_alert(
            raw_alert=support._load_wazuh_fixture(
                _require_string(detection.get("source_fixture"), "source_fixture")
            ),
            authorization_header="Bearer phase37-reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="phase37-reviewed-proxy-secret",
            peer_addr="127.0.0.1",
        )
        source_evidence = tuple(
            record
            for record in store.list(EvidenceRecord)
            if record.alert_id == admitted.alert.alert_id
        )
        if not source_evidence:
            raise AssertionError("expected Wazuh-backed rehearsal to persist evidence")
        first_seen_at = service.list_lifecycle_transitions(
            "alert",
            admitted.alert.alert_id,
        )[-1].transitioned_at
        evidence = service.persist_record(
            replace(
                source_evidence[0],
                evidence_id=_require_string(
                    evidence_fixture.get("evidence_id"),
                    "evidence_id",
                ),
                source_system=_require_string(
                    evidence_fixture.get("source_system"),
                    "source_system",
                ),
                collector_identity=_require_string(
                    evidence_fixture.get("collector_identity"),
                    "collector_identity",
                ),
                derivation_relationship=_require_string(
                    evidence_fixture.get("derivation_relationship"),
                    "derivation_relationship",
                ),
                content={
                    **_require_mapping(evidence_fixture.get("content"), "content"),
                    "reviewed_rehearsal_context": reviewed_context,
                },
            ),
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        evidence = service.persist_record(
            replace(evidence, case_id=promoted_case.case_id)
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity=_require_string(
                case_workflow.get("triage_owner"),
                "triage_owner",
            ),
            observed_at=first_seen_at,
            scope_statement=_require_string(
                case_workflow.get("observation_scope_statement"),
                "observation_scope_statement",
            ),
            supporting_evidence_ids=(evidence.evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner=_require_string(case_workflow.get("triage_owner"), "triage_owner"),
            triage_rationale=_require_string(
                case_workflow.get("triage_rationale"),
                "triage_rationale",
            ),
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner=_require_string(case_workflow.get("review_owner"), "review_owner"),
            intended_outcome=_require_string(
                case_workflow.get("intended_outcome"),
                "intended_outcome",
            ),
            lead_id=lead.lead_id,
        )

        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity=_require_string(
                action.get("requester_identity"),
                "requester_identity",
            ),
            recipient_identity=_require_string(
                action.get("recipient_identity"),
                "recipient_identity",
            ),
            message_intent=_require_string(
                action.get("message_intent"),
                "message_intent",
            ),
            escalation_reason=_require_string(
                action.get("escalation_reason"),
                "escalation_reason",
            ),
            expires_at=support.datetime.now(support.timezone.utc)
            + timedelta(
                hours=_require_number(action.get("expires_in_hours"), "expires_in_hours")
            ),
        )
        decided_at = action_request.requested_at + timedelta(
            minutes=_require_number(
                approval.get("decision_offset_minutes"),
                "decision_offset_minutes",
            )
        )
        approval_decision = service.record_action_approval_decision(
            action_request_id=action_request.action_request_id,
            approver_identity=_require_string(
                approval.get("approver_identity"),
                "approver_identity",
            ),
            authenticated_approver_identity=_require_string(
                approval.get("approver_identity"),
                "approver_identity",
            ),
            decision=_require_string(approval.get("decision"), "decision"),
            decision_rationale=_require_string(
                approval.get("decision_rationale"),
                "decision_rationale",
            ),
            decided_at=decided_at,
            approval_decision_id=_require_string(
                approval.get("approval_decision_id"),
                "approval_decision_id",
            ),
        )
        approved_request = service.get_record(
            ActionRequestRecord,
            action_request.action_request_id,
        )
        self.assertIsNotNone(approved_request)
        assert approved_request is not None

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=action_request.requested_at
            + timedelta(
                minutes=_require_number(
                    execution_fixture.get("delegation_offset_minutes"),
                    "delegation_offset_minutes",
                )
            ),
            delegation_issuer=_require_string(
                execution_fixture.get("delegation_issuer"),
                "delegation_issuer",
            ),
            evidence_ids=(evidence.evidence_id,),
        )
        observed_at = action_request.requested_at + timedelta(
            minutes=_require_number(
                reconciliation_fixture.get("observed_offset_minutes"),
                "observed_offset_minutes",
            )
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": observed_at,
                    "status": _require_string(
                        reconciliation_fixture.get("status"),
                        "status",
                    ),
                },
            ),
            compared_at=action_request.requested_at
            + timedelta(
                minutes=_require_number(
                    reconciliation_fixture.get("compared_offset_minutes"),
                    "compared_offset_minutes",
                )
            ),
            stale_after=action_request.requested_at
            + timedelta(
                hours=_require_number(
                    reconciliation_fixture.get("stale_after_offset_hours"),
                    "stale_after_offset_hours",
                )
            ),
        )

        _validate_release_gate_manifest(
            manifest=manifest,
            evidence=evidence,
            action_request=approved_request,
            approval_decision=approval_decision,
            execution=service.get_record(
                ActionExecutionRecord,
                execution.action_execution_id,
            ),
            reconciliation=reconciliation,
        )
        self.assertEqual(approved_request.lifecycle_state, "approved")
        self.assertEqual(approval_decision.lifecycle_state, "approved")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(
            reconciliation.subject_linkage["approval_decision_ids"],
            (approval_decision.approval_decision_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["action_request_ids"],
            (approved_request.action_request_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["evidence_ids"],
            (evidence.evidence_id,),
        )
        self.assertEqual(
            execution.provenance["downstream_binding"]["approval_decision_id"],
            approval_decision.approval_decision_id,
        )

    def test_release_gate_manifest_fails_closed_without_required_chain_records(
        self,
    ) -> None:
        fixture = _load_rehearsal_fixture()
        manifest = _require_mapping(fixture.get("manifest"), "manifest")
        acquired_at = datetime.fromisoformat("2026-04-24T09:00:00+00:00")
        evidence = EvidenceRecord(
            evidence_id="evidence-phase37-fail-closed-001",
            source_record_id="substrate-phase37-fail-closed-001",
            alert_id="alert-phase37-fail-closed-001",
            case_id="case-phase37-fail-closed-001",
            source_system="synthetic-rehearsal-signal",
            collector_identity="collector://phase37/rehearsal",
            acquired_at=acquired_at,
            derivation_relationship="admitted_analytic_signal",
            lifecycle_state="collected",
            content={"external_ticket_authority": "subordinate_evidence_only"},
        )

        with self.assertRaisesRegex(
            ValueError,
            "release-gate chain requires an approved action request",
        ):
            _validate_release_gate_manifest(
                manifest=manifest,
                evidence=evidence,
                action_request=None,
                approval_decision=None,
                execution=None,
                reconciliation=None,
            )

        incomplete_manifest = dict(manifest)
        incomplete_manifest["required_release_gate_records"] = [
            "approval_decision",
            "action_execution",
        ]
        with self.assertRaisesRegex(
            ValueError,
            "release-gate manifest missing reconciliation",
        ):
            _validate_release_gate_manifest(
                manifest=incomplete_manifest,
                evidence=evidence,
                action_request=None,
                approval_decision=None,
                execution=None,
                reconciliation=None,
            )


if __name__ == "__main__":
    unittest.main()
