from __future__ import annotations

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _cli_inspection_support import *  # noqa: F403
from _cli_inspection_support import _approved_payload_binding_hash, _load_wazuh_fixture


class CliInspectionRuntimeSurfaceTests(ControlPlaneCliInspectionTestBase):
    def test_runtime_command_uses_runtime_service_builder_when_not_injected(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stdout = io.StringIO()

        with mock.patch.object(
            main,
            "build_runtime_service",
            return_value=service,
        ) as build_runtime_service:
            main.main(["runtime"], stdout=stdout)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["persistence_mode"], "postgresql")
        build_runtime_service.assert_called_once_with()

    def test_runtime_command_honors_injected_service_snapshot(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=9411,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        stdout = io.StringIO()

        main.main(["runtime"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["bind_host"], "127.0.0.1")
        self.assertEqual(payload["bind_port"], 9411)
        self.assertEqual(payload["postgres_dsn"], "postgresql://control-plane.local/aegisops")
        self.assertEqual(payload["persistence_mode"], "postgresql")

    def test_serve_command_uses_long_running_runtime_surface(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with mock.patch.object(
            main,
            "build_runtime_service",
            return_value=service,
        ) as build_runtime_service, mock.patch.object(
            main,
            "run_control_plane_service",
            return_value=0,
        ) as run_control_plane_service:
            exit_code = main.main(["serve"])

        self.assertEqual(exit_code, 0)
        build_runtime_service.assert_called_once_with()
        run_control_plane_service.assert_called_once_with(service, stderr=mock.ANY)

    def test_startup_and_shutdown_status_commands_render_reviewed_contracts(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_reverse_proxy_secret="reviewed-surface-secret",  # noqa: S106 - test fixture secret
                protected_surface_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
                protected_surface_reviewed_identity_provider="authentik",
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        service.persist_record(
            CaseRecord(
                case_id="case-shutdown-001",
                alert_id="alert-shutdown-001",
                finding_id="finding-shutdown-001",
                evidence_ids=("evidence-shutdown-001",),
                lifecycle_state="open",
            )
        )
        startup_stdout = io.StringIO()
        shutdown_stdout = io.StringIO()

        main.main(["startup-status"], stdout=startup_stdout, service=service)
        main.main(["shutdown-status"], stdout=shutdown_stdout, service=service)

        startup_payload = json.loads(startup_stdout.getvalue())
        shutdown_payload = json.loads(shutdown_stdout.getvalue())
        self.assertTrue(startup_payload["startup_ready"])
        self.assertEqual(
            startup_payload["validated_surfaces"],
            ["wazuh_ingest", "protected_surface"],
        )
        self.assertFalse(shutdown_payload["shutdown_ready"])
        self.assertEqual(shutdown_payload["open_case_ids"], ["case-shutdown-001"])

    def test_startup_status_allows_loopback_protected_surface_without_proxy_bindings(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        startup_stdout = io.StringIO()

        main.main(["startup-status"], stdout=startup_stdout, service=service)

        startup_payload = json.loads(startup_stdout.getvalue())
        self.assertTrue(startup_payload["startup_ready"])
        self.assertNotIn(
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET",
            startup_payload["required_bindings"],
        )
        self.assertEqual(
            startup_payload["validated_surfaces"],
            ["wazuh_ingest", "protected_surface"],
        )

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

    def test_long_running_runtime_surface_starts_http_server(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )

        with mock.patch.object(main, "ThreadingHTTPServer") as server_cls:
            server = server_cls.return_value

            exit_code = main.run_control_plane_service(service)

        self.assertEqual(exit_code, 0)
        server_cls.assert_called_once_with(("127.0.0.1", 8089), mock.ANY)
        server.serve_forever.assert_called_once_with()
        server.server_close.assert_called_once_with()

    def test_long_running_runtime_surface_exposes_runtime_and_inspection_http_views(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            AlertRecord(
                alert_id="alert-http-001",
                finding_id="finding-http-001",
                analytic_signal_id="signal-http-001",
                case_id=None,
                lifecycle_state="new",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-http-001",
                subject_linkage={
                    "alert_ids": ("alert-http-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id="alert-http-001",
                finding_id="finding-http-001",
                analytic_signal_id="signal-http-001",
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="claim:host-001:http-runtime",
                first_seen_at=compared_at,
                last_seen_at=compared_at,
                ingest_disposition="created",
                mismatch_summary="created during HTTP inspection test",
                compared_at=compared_at,
                lifecycle_state="matched",
            )
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_PLATFORM_ADMIN_PRINCIPAL,
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
                runtime_payload = json.loads(
                    request.urlopen(f"{base_url}/runtime", timeout=2).read().decode("utf-8")
                )
                records_payload = json.loads(
                    request.urlopen(
                        f"{base_url}/inspect-records?family=alert",
                        timeout=2,
                    ).read().decode("utf-8")
                )
                status_payload = json.loads(
                    request.urlopen(
                        f"{base_url}/inspect-reconciliation-status",
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertEqual(runtime_payload["persistence_mode"], "postgresql")
                self.assertEqual(records_payload["record_family"], "alert")
                self.assertEqual(records_payload["records"][0]["alert_id"], "alert-http-001")
                self.assertEqual(status_payload["by_ingest_disposition"], {"created": 1})
                self.assertNotIn(
                    "latest_native_payload",
                    status_payload["records"][0]["subject_linkage"],
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

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

    def test_service_emits_structured_observability_logs_for_live_path_and_fail_closed_rejection(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        base_now = datetime.now(timezone.utc)
        expires_at = base_now + timedelta(hours=4)

        with self.assertLogs("aegisops.control_plane", level="INFO") as log_output:
            service.ingest_wazuh_alert(
                raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
                authorization_header="Bearer reviewed-shared-secret",  # noqa: S106 - test fixture secret
                forwarded_proto="https",
                reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                peer_addr="127.0.0.1",
            )
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
                    approval_decision_id="approval-observability-log-001",
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
                        "observed_at": base_now + timedelta(minutes=15),
                        "status": "success",
                    },
                ),
                compared_at=base_now + timedelta(minutes=16),
                stale_after=base_now + timedelta(hours=1),
            )

        structured_events = [
            json.loads(entry.split(":", 2)[2]) for entry in log_output.output
        ]
        self.assertEqual(
            [event["event"] for event in structured_events],
            [
                "wazuh_ingest_admitted",
                "action_request_created",
                "action_execution_delegated",
                "action_execution_reconciled",
            ],
        )
        self.assertEqual(structured_events[0]["disposition"], "deduplicated")
        self.assertEqual(structured_events[0]["peer_addr_class"], "loopback")
        self.assertNotIn("peer_addr", structured_events[0])
        self.assertEqual(
            structured_events[1]["action_type"],
            "notify_identity_owner",
        )
        self.assertTrue(structured_events[1]["requester_identity_present"])
        self.assertNotIn("requester_identity", structured_events[1])
        self.assertEqual(structured_events[2]["execution_surface_id"], "shuffle")
        self.assertEqual(structured_events[3]["lifecycle_state"], "matched")

        with self.assertLogs("aegisops.control_plane", level="WARNING") as rejected_logs:
            with self.assertRaisesRegex(
                PermissionError,
                "reviewed reverse proxy boundary credential",
            ):
                service.ingest_wazuh_alert(
                    raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
                    authorization_header="Bearer reviewed-shared-secret",  # noqa: S106 - test fixture secret
                    forwarded_proto="https",
                    reverse_proxy_secret_header="invalid-secret",  # noqa: S106 - intentional negative test fixture
                    peer_addr="127.0.0.1",
                )

        rejection_event = json.loads(rejected_logs.output[0].split(":", 2)[2])
        self.assertEqual(rejection_event["event"], "wazuh_ingest_rejected")
        self.assertEqual(rejection_event["reason"], "reverse_proxy_secret_mismatch")
        self.assertEqual(rejection_event["peer_addr_class"], "loopback")
        self.assertNotIn("peer_addr", rejection_event)

    def test_long_running_runtime_surface_exposes_analyst_queue_alert_detail_and_case_detail_http_views(
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
            ),
            store=store,
        )
        alert = _load_wazuh_fixture("github-audit-alert.json")
        admitted = service.ingest_wazuh_alert(
            raw_alert=alert,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

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
                queue_payload = json.loads(
                    request.urlopen(
                        f"{base_url}/inspect-analyst-queue",
                        timeout=2,
                    ).read().decode("utf-8")
                )
                detail_payload = json.loads(
                    request.urlopen(
                        (
                            f"{base_url}/inspect-alert-detail"
                            f"?alert_id={admitted.alert.alert_id}"
                        ),
                        timeout=2,
                    ).read().decode("utf-8")
                )
                case_payload = json.loads(
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        (
                            f"{base_url}/inspect-case-detail"
                            f"?case_id={promoted_case.case_id}"
                        ),
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertTrue(queue_payload["read_only"])
                self.assertEqual(queue_payload["queue_name"], "analyst_review")
                self.assertEqual(queue_payload["total_records"], 1)
                self.assertEqual(
                    queue_payload["records"][0]["alert_id"],
                    admitted.alert.alert_id,
                )

                self.assertTrue(detail_payload["read_only"])
                self.assertEqual(detail_payload["alert_id"], admitted.alert.alert_id)
                self.assertEqual(detail_payload["alert"]["alert_id"], admitted.alert.alert_id)
                self.assertEqual(detail_payload["case_record"]["case_id"], promoted_case.case_id)
                self.assertEqual(
                    detail_payload["latest_reconciliation"]["reconciliation_id"],
                    admitted.reconciliation.reconciliation_id,
                )
                self.assertEqual(
                    detail_payload["provenance"],
                    {
                        "admission_kind": "live",
                        "admission_channel": "live_wazuh_webhook",
                    },
                )
                self.assertEqual(
                    detail_payload["lineage"]["substrate_detection_record_ids"],
                    ["wazuh:1731595300.1234567"],
                )
                self.assertEqual(
                    detail_payload["lineage"]["accountable_source_identities"],
                    ["manager:wazuh-manager-github-1"],
                )
                self.assertEqual(
                    detail_payload["reviewed_context"]["source"]["source_family"],
                    "github_audit",
                )
                self.assertTrue(case_payload["read_only"])
                self.assertEqual(case_payload["case_id"], promoted_case.case_id)
                self.assertEqual(
                    case_payload["case_record"]["case_id"],
                    promoted_case.case_id,
                )
                self.assertEqual(
                    case_payload["linked_evidence_ids"],
                    [detail_payload["linked_evidence_records"][0]["evidence_id"]],
                )
                self.assertEqual(
                    case_payload["advisory_output"]["output_kind"],
                    "case_summary",
                )
                self.assertEqual(
                    case_payload["advisory_output"]["status"],
                    "ready",
                )
                self.assertEqual(
                    case_payload["reviewed_context"]["source"]["source_family"],
                    "github_audit",
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_blank_alert_detail_query(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=store,
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

                with self.assertRaises(error.HTTPError) as exc_info:
                    request.urlopen(
                        (
                            "http://127.0.0.1:"
                            f"{servers[0].server_port}/inspect-alert-detail?alert_id=%20%20"
                        ),
                        timeout=2,
                    )

                self.assertEqual(exc_info.exception.code, 400)
                error_payload = json.loads(exc_info.exception.read().decode("utf-8"))
                self.assertEqual(error_payload["error"], "invalid_request")
                self.assertEqual(
                    error_payload["message"],
                    "alert_id query parameter is required",
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_direct_backend_wazuh_ingest_bypass(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
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

                alert = _load_wazuh_fixture("github-audit-alert.json")
                request_body = json.dumps(alert).encode("utf-8")
                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=request_body,
                    method="POST",
                    headers={
                        "Authorization": "Bearer reviewed-shared-secret",
                        "Content-Type": "application/json",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_missing_wazuh_shared_secret(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET must be set",
        ):
            main.run_control_plane_service(service)

    def test_long_running_runtime_surface_rejects_missing_wazuh_reverse_proxy_secret(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET must be set",
        ):
            main.run_control_plane_service(service)

    def test_long_running_runtime_surface_rejects_non_loopback_wazuh_ingest_without_trusted_proxies(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS must be set",
        ):
            main.run_control_plane_service(service)

    def test_long_running_runtime_surface_rejects_wazuh_ingest_without_bearer_auth(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
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

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("github-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_wazuh_ingest_with_wrong_bearer_secret(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
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

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("github-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Authorization": "Bearer wrong-secret",
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_wazuh_ingest_without_https_forwarding(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
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

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("github-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Authorization": "Bearer reviewed-shared-secret",
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_non_github_wazuh_family(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
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

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("microsoft-365-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Authorization": "Bearer reviewed-shared-secret",
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "400"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_service_rejects_non_loopback_wazuh_ingest_from_untrusted_proxy_peer(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",  # noqa: S104 - intentional non-loopback test coverage
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            PermissionError,
            "reviewed reverse proxy peer boundary",
        ):
            service.ingest_wazuh_alert(
                raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
                authorization_header="Bearer reviewed-shared-secret",
                forwarded_proto="https",
                reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                peer_addr="10.10.0.6",
            )

    def test_service_admits_non_loopback_wazuh_ingest_from_trusted_proxy_peer(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",  # noqa: S104 - intentional non-loopback test coverage
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            ),
            store=store,
        )

        ingest_result = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="10.10.0.5",
        )

        self.assertEqual(ingest_result.disposition, "created")
        self.assertEqual(len(store.list(AlertRecord)), 1)
        self.assertEqual(len(store.list(AnalyticSignalRecord)), 1)

    def test_service_admits_trusted_proxy_peer_with_surrounding_whitespace(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",  # noqa: S104 - intentional non-loopback test coverage
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            ),
            store=store,
        )

        ingest_result = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr=" 10.10.0.5 ",
        )

        self.assertEqual(ingest_result.disposition, "created")
        self.assertEqual(len(store.list(AlertRecord)), 1)
        self.assertEqual(len(store.list(AnalyticSignalRecord)), 1)

    def test_long_running_runtime_surface_rejects_oversized_wazuh_ingest_body(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
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

                connection = http.client.HTTPConnection(
                    "127.0.0.1",
                    servers[0].server_port,
                    timeout=2,
                )
                connection.putrequest("POST", "/intake/wazuh")
                connection.putheader("Authorization", "Bearer reviewed-shared-secret")
                connection.putheader("Content-Type", "application/json")
                connection.putheader("X-AegisOps-Proxy-Secret", "reviewed-proxy-secret")
                connection.putheader("X-Forwarded-Proto", "https")
                connection.putheader(
                    "Content-Length",
                    str(main.MAX_WAZUH_INGEST_BODY_BYTES + 1),
                )
                connection.endheaders()

                response = connection.getresponse()
                self.assertEqual(response.status, 413)
                response_body = json.loads(response.read().decode("utf-8"))
                connection.close()
                self.assertEqual(response_body["error"], "request_too_large")
                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)



if __name__ == "__main__":
    unittest.main()
