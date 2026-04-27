from __future__ import annotations

from collections.abc import Mapping
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
REVIEWED_SHARED_SECRET = "phase37-reviewed-shared-secret"  # noqa: S105 - test fixture secret
REVIEWED_PROXY_SECRET = "phase37-reviewed-proxy-secret"  # noqa: S105 - test fixture secret


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


def _require_sequence(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")
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
    execution_run_id = (
        ""
        if execution is None or not isinstance(execution.execution_run_id, str)
        else execution.execution_run_id.strip()
    )
    if not execution_run_id or execution_run_id.startswith("pending-dispatch-"):
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
    target_scope = action_request.target_scope
    if not isinstance(target_scope, Mapping):
        raise ValueError("external ticket reference must not become action authority")
    if "external_ticket_reference" in target_scope:
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
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
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
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
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

    def test_rehearsal_fixture_covers_denial_fallback_and_escalation_without_dispatch(
        self,
    ) -> None:
        fixture = _load_rehearsal_fixture()
        review_outcomes = _require_mapping(
            fixture.get("review_outcomes"),
            "review_outcomes",
        )
        required_outcomes = {"approved", "denied", "fallback", "escalation"}
        self.assertTrue(
            required_outcomes.issubset(set(review_outcomes)),
            "rehearsal fixture must name approved, denied, fallback, and escalation outcomes",
        )
        approved = _require_mapping(review_outcomes.get("approved"), "approved")
        denied = _require_mapping(review_outcomes.get("denied"), "denied")
        fallback = _require_mapping(review_outcomes.get("fallback"), "fallback")
        escalation = _require_mapping(review_outcomes.get("escalation"), "escalation")
        self.assertIn(
            "approval_decision",
            _require_sequence(
                approved.get("evidence_distinctions"),
                "evidence_distinctions",
            ),
        )
        self.assertIn(
            "execution_receipt",
            _require_sequence(
                approved.get("evidence_distinctions"),
                "evidence_distinctions",
            ),
        )

        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )

        def create_request(outcome: dict[str, object]) -> ActionRequestRecord:
            observation = service.record_case_observation(
                case_id=promoted_case.case_id,
                author_identity=_require_string(
                    outcome.get("requester_identity"),
                    "requester_identity",
                ),
                observed_at=reviewed_at,
                scope_statement=_require_string(
                    outcome.get("message_intent"),
                    "message_intent",
                ),
                supporting_evidence_ids=(evidence_id,),
            )
            lead = service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner=_require_string(
                    outcome.get("requester_identity"),
                    "requester_identity",
                ),
                triage_rationale=_require_string(
                    outcome.get("escalation_reason"),
                    "escalation_reason",
                ),
                observation_id=observation.observation_id,
            )
            recommendation = service.record_case_recommendation(
                case_id=promoted_case.case_id,
                review_owner=_require_string(
                    outcome.get("review_owner"),
                    "review_owner",
                ),
                intended_outcome=_require_string(
                    outcome.get("intended_outcome"),
                    "intended_outcome",
                ),
                lead_id=lead.lead_id,
            )
            return service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity=_require_string(
                    outcome.get("requester_identity"),
                    "requester_identity",
                ),
                recipient_identity=_require_string(
                    outcome.get("recipient_identity"),
                    "recipient_identity",
                ),
                message_intent=_require_string(
                    outcome.get("message_intent"),
                    "message_intent",
                ),
                escalation_reason=_require_string(
                    outcome.get("escalation_reason"),
                    "escalation_reason",
                ),
                expires_at=reviewed_at
                + timedelta(
                    hours=_require_number(
                        outcome.get("expires_in_hours"),
                        "expires_in_hours",
                    )
                ),
                action_request_id=_require_string(
                    outcome.get("action_request_id"),
                    "action_request_id",
                ),
            )

        denied_request = create_request(denied)
        denied_decision = service.record_action_approval_decision(
            action_request_id=denied_request.action_request_id,
            approver_identity=_require_string(
                denied.get("approver_identity"),
                "approver_identity",
            ),
            authenticated_approver_identity=_require_string(
                denied.get("approver_identity"),
                "approver_identity",
            ),
            decision=_require_string(denied.get("decision"), "decision"),
            decision_rationale=_require_string(
                denied.get("decision_rationale"),
                "decision_rationale",
            ),
            decided_at=reviewed_at
            + timedelta(
                minutes=_require_number(
                    denied.get("decision_offset_minutes"),
                    "decision_offset_minutes",
                )
            ),
            approval_decision_id=_require_string(
                denied.get("approval_decision_id"),
                "approval_decision_id",
            ),
        )
        denied_request = service.get_record(
            ActionRequestRecord,
            denied_request.action_request_id,
        )
        self.assertIsNotNone(denied_request)
        assert denied_request is not None
        self.assertEqual(denied_decision.lifecycle_state, "rejected")
        self.assertEqual(denied_request.lifecycle_state, "rejected")
        self.assertEqual(store.list(ActionExecutionRecord), ())

        fallback_request = create_request(fallback)
        fallback_decision = service.record_action_approval_decision(
            action_request_id=fallback_request.action_request_id,
            approver_identity=_require_string(
                fallback.get("approver_identity"),
                "approver_identity",
            ),
            authenticated_approver_identity=_require_string(
                fallback.get("approver_identity"),
                "approver_identity",
            ),
            decision="grant",
            decision_rationale=_require_string(
                fallback.get("decision_rationale"),
                "decision_rationale",
            ),
            decided_at=reviewed_at
            + timedelta(
                minutes=_require_number(
                    fallback.get("decision_offset_minutes"),
                    "decision_offset_minutes",
                )
            ),
            approval_decision_id=_require_string(
                fallback.get("approval_decision_id"),
                "approval_decision_id",
            ),
        )
        fallback_request = service.get_record(
            ActionRequestRecord,
            fallback_request.action_request_id,
        )
        self.assertIsNotNone(fallback_request)
        assert fallback_request is not None
        service.record_action_review_manual_fallback(
            action_request_id=fallback_request.action_request_id,
            fallback_at=reviewed_at
            + timedelta(
                minutes=_require_number(
                    fallback.get("fallback_offset_minutes"),
                    "fallback_offset_minutes",
                )
            ),
            fallback_actor_identity=_require_string(
                fallback.get("fallback_actor_identity"),
                "fallback_actor_identity",
            ),
            authority_boundary=_require_string(
                fallback.get("authority_boundary"),
                "authority_boundary",
            ),
            reason=_require_string(fallback.get("reason"), "reason"),
            action_taken=_require_string(
                fallback.get("action_taken"),
                "action_taken",
            ),
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty=_require_string(
                fallback.get("residual_uncertainty"),
                "residual_uncertainty",
            ),
        )
        fallback_review = service.inspect_case_detail(
            promoted_case.case_id
        ).current_action_review
        fallback_visibility = fallback_review["runtime_visibility"]["manual_fallback"]
        self.assertEqual(
            fallback_visibility["approval_decision_id"],
            fallback_decision.approval_decision_id,
        )
        self.assertEqual(
            fallback_visibility["verification_evidence_ids"],
            (evidence_id,),
        )
        self.assertEqual(store.list(ActionExecutionRecord), ())

        escalation_request = create_request(escalation)
        service.record_action_review_escalation_note(
            action_request_id=escalation_request.action_request_id,
            escalated_at=reviewed_at
            + timedelta(
                minutes=_require_number(
                    escalation.get("escalated_offset_minutes"),
                    "escalated_offset_minutes",
                )
            ),
            escalated_by_identity=_require_string(
                escalation.get("escalated_by_identity"),
                "escalated_by_identity",
            ),
            escalated_to=_require_string(
                escalation.get("escalated_to"),
                "escalated_to",
            ),
            note=_require_string(escalation.get("note"), "note"),
        )
        escalation_review = service.inspect_case_detail(
            promoted_case.case_id
        ).current_action_review
        escalation_visibility = escalation_review["runtime_visibility"][
            "escalation_notes"
        ]
        self.assertEqual(escalation_visibility["review_state"], "pending")
        self.assertEqual(
            escalation_visibility["escalated_by_identity"],
            _require_string(
                escalation.get("escalated_by_identity"),
                "escalated_by_identity",
            ),
        )
        self.assertEqual(store.list(ActionExecutionRecord), ())

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

    def test_release_gate_manifest_rejects_missing_receipts_and_authority_drift(
        self,
    ) -> None:
        fixture = _load_rehearsal_fixture()
        manifest = _require_mapping(fixture.get("manifest"), "manifest")
        acquired_at = datetime.fromisoformat("2026-04-24T09:00:00+00:00")
        requested_at = datetime.fromisoformat("2026-04-24T09:05:00+00:00")
        evidence = EvidenceRecord(
            evidence_id="evidence-phase37-guarded-001",
            source_record_id="substrate-phase37-guarded-001",
            alert_id="alert-phase37-guarded-001",
            case_id="case-phase37-guarded-001",
            source_system="synthetic-rehearsal-signal",
            collector_identity="collector://phase37/rehearsal",
            acquired_at=acquired_at,
            derivation_relationship="admitted_analytic_signal",
            lifecycle_state="collected",
            content={"external_ticket_authority": "subordinate_evidence_only"},
        )
        action_request = ActionRequestRecord(
            action_request_id="action-request-phase37-guarded-001",
            approval_decision_id="approval-phase37-guarded-001",
            case_id=evidence.case_id,
            alert_id=evidence.alert_id,
            finding_id=None,
            idempotency_key="idempotency-phase37-guarded-001",
            target_scope={"asset_id": "asset-phase37-guarded-001"},
            payload_hash="payload-hash-phase37-guarded-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        approval_decision = ApprovalDecisionRecord(
            approval_decision_id="approval-phase37-guarded-001",
            action_request_id=action_request.action_request_id,
            approver_identities=("analyst://phase37/approver",),
            target_snapshot=action_request.target_scope,
            payload_hash=action_request.payload_hash,
            decided_at=requested_at + timedelta(minutes=5),
            lifecycle_state="approved",
        )
        execution = ActionExecutionRecord(
            action_execution_id="action-execution-phase37-guarded-001",
            action_request_id=action_request.action_request_id,
            approval_decision_id=approval_decision.approval_decision_id,
            delegation_id="delegation-phase37-guarded-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            execution_run_id="shuffle-run-phase37-guarded-001",
            idempotency_key=action_request.idempotency_key,
            target_scope=action_request.target_scope,
            approved_payload={"action": "notify_identity_owner"},
            payload_hash=action_request.payload_hash,
            delegated_at=requested_at + timedelta(minutes=7),
            expires_at=None,
            provenance={"downstream_binding": {}},
            lifecycle_state="delegated",
        )
        reconciliation = ReconciliationRecord(
            reconciliation_id="reconciliation-phase37-guarded-001",
            subject_linkage={
                "approval_decision_ids": (approval_decision.approval_decision_id,),
                "action_request_ids": (action_request.action_request_id,),
                "action_execution_ids": (execution.action_execution_id,),
                "evidence_ids": (evidence.evidence_id,),
            },
            alert_id=evidence.alert_id,
            finding_id=None,
            analytic_signal_id=None,
            execution_run_id=execution.execution_run_id,
            linked_execution_run_ids=(execution.execution_run_id,),
            correlation_key=action_request.idempotency_key,
            first_seen_at=requested_at,
            last_seen_at=requested_at + timedelta(minutes=8),
            ingest_disposition="matched",
            mismatch_summary="none",
            compared_at=requested_at + timedelta(minutes=10),
            lifecycle_state="matched",
        )

        with self.assertRaisesRegex(
            ValueError,
            "release-gate chain requires an execution receipt",
        ):
            _validate_release_gate_manifest(
                manifest=manifest,
                evidence=evidence,
                action_request=action_request,
                approval_decision=approval_decision,
                execution=replace(execution, execution_run_id="   "),
                reconciliation=replace(reconciliation, execution_run_id="   "),
            )

        bad_scope_request = replace(action_request)
        object.__setattr__(bad_scope_request, "target_scope", None)
        with self.assertRaisesRegex(
            ValueError,
            "external ticket reference must not become action authority",
        ):
            _validate_release_gate_manifest(
                manifest=manifest,
                evidence=evidence,
                action_request=bad_scope_request,
                approval_decision=approval_decision,
                execution=execution,
                reconciliation=reconciliation,
            )


if __name__ == "__main__":
    unittest.main()
