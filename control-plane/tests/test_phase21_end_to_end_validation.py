from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import pathlib
import sys
import threading
import unittest
from urllib import error, request
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import main
from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.models import ApprovalDecisionRecord, ReconciliationRecord
from aegisops.control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store
from support.fixtures import load_wazuh_fixture


REVIEWED_SHARED_SECRET = "reviewed-shared-secret"  # noqa: S105
REVIEWED_WAZUH_PROXY_SECRET = "reviewed-wazuh-proxy-secret"  # noqa: S105
REVIEWED_SURFACE_PROXY_SECRET = "reviewed-surface-proxy-secret"  # noqa: S105
REVIEWED_PROXY_SERVICE_ACCOUNT = "svc-aegisops-proxy-control-plane"  # noqa: S105
REVIEWED_ADMIN_BOOTSTRAP_TOKEN = "reviewed-admin-bootstrap-token"  # noqa: S105
REVIEWED_BREAK_GLASS_TOKEN = "reviewed-break-glass-token"  # noqa: S105


_load_wazuh_fixture = load_wazuh_fixture


class Phase21EndToEndValidationTests(unittest.TestCase):
    def _build_service(
        self,
        *,
        store: object | None = None,
        host: str = "127.0.0.1",
    ) -> tuple[object, AegisOpsControlPlaneService]:
        if store is None:
            store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host=host,
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_WAZUH_PROXY_SECRET,
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_reverse_proxy_secret=REVIEWED_SURFACE_PROXY_SECRET,
                protected_surface_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
                protected_surface_reviewed_identity_provider="authentik",
                admin_bootstrap_token=REVIEWED_ADMIN_BOOTSTRAP_TOKEN,
                break_glass_token=REVIEWED_BREAK_GLASS_TOKEN,
            ),
            store=store,
        )
        return store, service

    def _build_phase19_in_scope_case(
        self,
        *,
        service: AegisOpsControlPlaneService | None = None,
    ) -> tuple[AegisOpsControlPlaneService, object, str, datetime]:
        if service is None:
            _, service = self._build_service()
        reviewed_at = datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc)
        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_WAZUH_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        return service, promoted_case, promoted_case.evidence_ids[0], reviewed_at

    def _complete_phase20_live_path(
        self,
        service: AegisOpsControlPlaneService,
        *,
        case_id: str,
        alert_id: str,
        finding_id: str,
        evidence_id: str,
        reviewed_at: datetime,
    ) -> tuple[object, object, object, object]:
        observation = service.record_case_observation(
            case_id=case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-e2e-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=action_request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=action_request.requested_at + timedelta(minutes=10),
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": action_request.requested_at + timedelta(minutes=15),
                    "status": "success",
                },
            ),
            compared_at=action_request.requested_at + timedelta(minutes=16),
            stale_after=action_request.requested_at + timedelta(hours=1),
        )
        return approved_request, approval_decision, execution, reconciliation

    @contextmanager
    def _run_http_service(self, service: AegisOpsControlPlaneService) -> object:
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")
                yield f"http://127.0.0.1:{servers[0].server_port}"
            finally:
                if servers:
                    servers[0].shutdown()
                    servers[0].server_close()
                thread.join(timeout=2)

    def test_phase21_end_to_end_auth_boundaries_fail_closed_and_emit_observability(
        self,
    ) -> None:
        store, _ = make_store()
        invalid_surface_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",
                port=8080,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_WAZUH_PROXY_SECRET,
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS must be set",
        ):
            invalid_surface_service.validate_protected_surface_runtime()

        _, service = self._build_service()
        with self._run_http_service(service) as base_url, self.assertLogs(
            "aegisops.control_plane",
            level="INFO",
        ) as log_output:
            intake_request = request.Request(  # noqa: S310 - local in-process test HTTP server
                f"{base_url}/intake/wazuh",
                data=json.dumps(_load_wazuh_fixture("github-audit-alert.json")).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-Forwarded-Proto": "https",
                    "X-AegisOps-Proxy-Secret": REVIEWED_WAZUH_PROXY_SECRET,
                },
                method="POST",
            )

            with self.assertRaises(error.HTTPError) as intake_error:
                request.urlopen(intake_request, timeout=2)  # noqa: S310
            self.assertEqual(intake_error.exception.code, 403)
            intake_payload = json.loads(intake_error.exception.read().decode("utf-8"))
            self.assertEqual(
                intake_payload["message"],
                "live Wazuh ingest requires Authorization: Bearer <shared secret>",
            )

            with self.assertRaises(error.HTTPError) as diagnostics_error:
                request.urlopen(  # noqa: S310 - local in-process test HTTP server
                    f"{base_url}/diagnostics/readiness",
                    timeout=2,
                )
            self.assertEqual(diagnostics_error.exception.code, 403)
            diagnostics_payload = json.loads(
                diagnostics_error.exception.read().decode("utf-8")
            )
            self.assertIn("protected control-plane surface role is not authorized", diagnostics_payload["message"])

        joined_logs = "\n".join(log_output.output)
        self.assertIn('"event":"wazuh_ingest_rejected"', joined_logs)
        self.assertIn('"reason":"missing_bearer_secret"', joined_logs)

    def test_live_wazuh_ingest_accepts_case_insensitive_bearer_scheme(self) -> None:
        _store, service = self._build_service()

        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_WAZUH_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )

        self.assertEqual(admitted.disposition, "created")
        self.assertIsNotNone(admitted.alert.alert_id)

    def test_phase21_end_to_end_restore_and_readiness_preserve_phase20_live_path(
        self,
    ) -> None:
        _, service = self._build_service()
        service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case(
            service=service
        )
        _approved_request, approval_decision, execution, reconciliation = (
            self._complete_phase20_live_path(
                service,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_id=evidence_id,
                reviewed_at=reviewed_at,
            )
        )

        readiness = service.inspect_readiness_diagnostics()
        self.assertEqual(readiness.status, "ready")
        self.assertEqual(
            readiness.metrics["phase20_notify_identity_owner"]["approved_action_requests"],
            1,
        )
        self.assertEqual(
            readiness.metrics["phase20_notify_identity_owner"]["reconciled_executions"],
            1,
        )
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            reconciliation.reconciliation_id,
        )

        backup = service.export_authoritative_record_chain_backup()
        restored_store, _ = make_store()
        _, restored_service = self._build_service(store=restored_store)

        restore_summary = restored_service.restore_authoritative_record_chain_backup(backup)
        restored_readiness = restored_service.inspect_readiness_diagnostics()
        restored_case_detail = restored_service.inspect_case_detail(promoted_case.case_id)
        restored_reconciliation = restored_service.get_record(
            ReconciliationRecord,
            reconciliation.reconciliation_id,
        )

        self.assertTrue(restore_summary.restore_drill.drill_passed)
        self.assertEqual(
            restore_summary.restore_drill.verified_action_execution_ids,
            (execution.action_execution_id,),
        )
        self.assertEqual(
            restore_summary.restore_drill.verified_approval_decision_ids,
            (approval_decision.approval_decision_id,),
        )
        self.assertEqual(
            restored_readiness.metrics["phase20_notify_identity_owner"]["approved_action_requests"],
            1,
        )
        self.assertEqual(
            restored_readiness.metrics["phase20_notify_identity_owner"]["reconciled_executions"],
            1,
        )
        self.assertEqual(restored_readiness.status, "ready")
        self.assertEqual(
            restored_readiness.startup["validated_surfaces"],
            readiness.startup["validated_surfaces"],
        )
        self.assertEqual(restored_case_detail.case_id, promoted_case.case_id)
        self.assertEqual(restored_case_detail.linked_evidence_ids, (evidence_id,))
        self.assertIsNotNone(restored_reconciliation)
        self.assertEqual(
            restored_reconciliation.execution_run_id,
            execution.execution_run_id,
        )
        restored_approval_context = restored_service.inspect_assistant_context(
            "approval_decision",
            approval_decision.approval_decision_id,
        )
        self.assertEqual(restored_approval_context.linked_case_ids, (promoted_case.case_id,))
        self.assertIn(
            reconciliation.reconciliation_id,
            restored_approval_context.linked_reconciliation_ids,
        )

    def test_phase21_end_to_end_second_source_onboarding_stays_narrow(
        self,
    ) -> None:
        _, service = self._build_service()

        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("entra-id-alert.json"),
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_WAZUH_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        reviewed_at = datetime(2026, 4, 8, 9, 30, tzinfo=timezone.utc)
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed Entra ID directory privilege context requires reviewed follow-up.",
            supporting_evidence_ids=(promoted_case.evidence_ids[0],),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Preserve the reviewed Phase 19 casework contract for the approved second source.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review the Entra ID directory privilege change before any approval-bound action.",
            lead_id=lead.lead_id,
        )

        queue_view = service.inspect_analyst_queue()
        case_detail = service.inspect_case_detail(promoted_case.case_id)
        advisory_context = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(
            queue_view.records[0]["reviewed_context"]["source"]["source_family"],
            "entra_id",
        )
        self.assertEqual(case_detail.case_id, promoted_case.case_id)
        self.assertEqual(
            case_detail.reviewed_context["source"]["source_family"],
            "entra_id",
        )
        self.assertEqual(advisory_context.linked_case_ids, (promoted_case.case_id,))
        self.assertEqual(
            advisory_context.linked_evidence_ids,
            (promoted_case.evidence_ids[0],),
        )
        baseline_readiness = service.inspect_readiness_diagnostics()

        with self.assertRaisesRegex(
            ValueError,
            "live Wazuh ingest only admits the reviewed github_audit and entra_id live source families",
        ):
            service.ingest_wazuh_alert(
                raw_alert=_load_wazuh_fixture("microsoft-365-audit-alert.json"),
                authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
                forwarded_proto="https",
                reverse_proxy_secret_header=REVIEWED_WAZUH_PROXY_SECRET,
                peer_addr="127.0.0.1",
            )

        post_rejection_queue = service.inspect_analyst_queue()
        self.assertEqual(post_rejection_queue.total_records, queue_view.total_records)
        self.assertEqual(
            self._without_volatile_queue_age(post_rejection_queue.records),
            self._without_volatile_queue_age(queue_view.records),
        )
        post_rejection_readiness = service.inspect_readiness_diagnostics()
        self.assertEqual(
            post_rejection_readiness.metrics["alerts"],
            baseline_readiness.metrics["alerts"],
        )
        self.assertEqual(
            post_rejection_readiness.metrics["cases"],
            baseline_readiness.metrics["cases"],
        )

    @staticmethod
    def _without_volatile_queue_age(
        records: tuple[dict[str, object], ...],
    ) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                key: value
                for key, value in record.items()
                if key not in {"age_seconds", "age_bucket"}
            }
            for record in records
        )


if __name__ == "__main__":
    unittest.main()
