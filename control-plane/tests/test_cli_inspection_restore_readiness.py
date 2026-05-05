from __future__ import annotations

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _cli_inspection_support import *  # noqa: F403
from _cli_inspection_support import _approved_payload_binding_hash, _load_wazuh_fixture


class CliInspectionRestoreReadinessTests(ControlPlaneCliInspectionTestBase):
    def test_backup_and_restore_drill_commands_render_recovery_payloads(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        base_now = datetime.now(timezone.utc)
        expires_at = base_now + timedelta(hours=4)
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
                approval_decision_id="approval-cli-restore-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=base_now + timedelta(minutes=5),
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
        service.reconcile_action_execution(
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
        backup_stdout = io.StringIO()
        drill_stdout = io.StringIO()

        main.main(["backup-authoritative-record-chain"], stdout=backup_stdout, service=service)
        main.main(["run-authoritative-restore-drill"], stdout=drill_stdout, service=service)

        backup_payload = json.loads(backup_stdout.getvalue())
        drill_payload = json.loads(drill_stdout.getvalue())
        self.assertEqual(
            backup_payload["backup_schema_version"],
            "phase23.authoritative-record-chain.v2",
        )
        self.assertEqual(backup_payload["record_counts"]["action_execution"], 1)
        self.assertTrue(drill_payload["drill_passed"])
        self.assertIn(
            approval_decision.approval_decision_id,
            drill_payload["verified_approval_decision_ids"],
        )
        self.assertIn(
            recommendation.recommendation_id,
            drill_payload["verified_recommendation_ids"],
        )

    def test_backup_authoritative_record_chain_reports_usage_error_on_invalid_backup(
        self,
    ) -> None:
        service = mock.Mock()
        service.export_authoritative_record_chain_backup.side_effect = ValueError(
            "backup invariants failed closed"
        )
        stderr = io.StringIO()

        with mock.patch.object(sys, "stderr", stderr):
            with self.assertRaises(SystemExit) as exc:
                main.main(["backup-authoritative-record-chain"], service=service)

        self.assertEqual(exc.exception.code, 2)
        self.assertIn("backup invariants failed closed", stderr.getvalue())

    def test_restore_authoritative_record_chain_reports_usage_error_on_lookup_failure(
        self,
    ) -> None:
        service = mock.Mock()
        service.restore_authoritative_record_chain_backup.side_effect = LookupError(
            "restore drill failed closed"
        )
        stderr = io.StringIO()

        with mock.patch.object(main, "_read_json_file", return_value={}):
            with mock.patch.object(sys, "stderr", stderr):
                with self.assertRaises(SystemExit) as exc:
                    main.main(
                        [
                            "restore-authoritative-record-chain",
                            "--input",
                            "authoritative-backup.json",
                        ],
                        service=service,
                    )

        self.assertEqual(exc.exception.code, 2)
        self.assertIn("restore drill failed closed", stderr.getvalue())

    def test_long_running_runtime_surface_exposes_operator_readiness_diagnostics_http_view(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        reviewed_at = datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc)
        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",  # noqa: S106 - test fixture secret
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        evidence_id = promoted_case.evidence_ids[0]
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        base_now = datetime.now(timezone.utc)
        expires_at = base_now + timedelta(hours=4)
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
                approval_decision_id="approval-http-readiness-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=base_now + timedelta(minutes=5),
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
            delegated_at=base_now + timedelta(minutes=10),
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
                    "observed_at": base_now + timedelta(minutes=15),
                    "status": "success",
                },
            ),
            compared_at=base_now + timedelta(minutes=16),
            stale_after=base_now + timedelta(hours=1),
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
        ):
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

                base_url = f"http://127.0.0.1:{servers[0].server_port}"
                diagnostics_payload = json.loads(
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        f"{base_url}/diagnostics/readiness",
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertTrue(diagnostics_payload["read_only"])
                self.assertEqual(diagnostics_payload["status"], "ready")
                self.assertTrue(diagnostics_payload["booted"])
                self.assertTrue(diagnostics_payload["startup"]["startup_ready"])
                self.assertFalse(diagnostics_payload["shutdown"]["shutdown_ready"])
                self.assertEqual(
                    diagnostics_payload["metrics"]["action_requests"]["approved"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["action_executions"]["terminal"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["reconciliations"]["matched"],
                    2,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["phase20_notify_identity_owner"]["approved_action_requests"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["phase20_notify_identity_owner"]["reconciled_executions"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["review_path_health"]["overall_state"],
                    "healthy",
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["review_path_health"]["review_count"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["source_health"]["tracked_sources"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["source_health"]["sources"][
                        "github_audit"
                    ]["state"],
                    "healthy",
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["automation_substrate_health"][
                        "tracked_surfaces"
                    ],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["automation_substrate_health"][
                        "surfaces"
                    ]["automation_substrate:shuffle"]["state"],
                    "healthy",
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["review_path_health"]["paths"],
                    {
                        "ingest": {
                            "state": "healthy",
                            "reason": "observations_current",
                            "affected_reviews": 0,
                            "by_state": {
                                "healthy": 1,
                                "delayed": 0,
                                "degraded": 0,
                                "failed": 0,
                            },
                        },
                        "delegation": {
                            "state": "healthy",
                            "reason": "delegated",
                            "affected_reviews": 0,
                            "by_state": {
                                "healthy": 1,
                                "delayed": 0,
                                "degraded": 0,
                                "failed": 0,
                            },
                        },
                        "provider": {
                            "state": "healthy",
                            "reason": "execution_succeeded",
                            "affected_reviews": 0,
                            "by_state": {
                                "healthy": 1,
                                "delayed": 0,
                                "degraded": 0,
                                "failed": 0,
                            },
                        },
                        "persistence": {
                            "state": "healthy",
                            "reason": "reconciliation_matched",
                            "affected_reviews": 0,
                            "by_state": {
                                "healthy": 1,
                                "delayed": 0,
                                "degraded": 0,
                                "failed": 0,
                            },
                        },
                    },
                )
                self.assertEqual(
                    diagnostics_payload["latest_reconciliation"]["reconciliation_id"],
                    reconciliation.reconciliation_id,
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)
