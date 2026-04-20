from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import pathlib
import sys
import unittest


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from support.service_persistence import ServicePersistenceTestBase
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    ActionExecutionRecord,
    ApprovalDecisionRecord,
)
from postgres_test_support import make_store

import test_phase21_runtime_auth_validation as runtime_auth_tests
import test_runtime_secret_boundary as secret_boundary_tests


class Phase27Day2RuntimeContractTests(ServicePersistenceTestBase):
    def test_phase27_restore_runtime_contract_fails_closed_without_post_restore_bindings(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        restore_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )
        readiness = restored_service.inspect_readiness_diagnostics()

        self.assertGreater(restore_summary.restored_record_counts["case"], 0)
        self.assertIn(promoted_case.case_id, restore_summary.restore_drill.verified_case_ids)
        self.assertFalse(restore_summary.restore_drill.drill_passed)
        self.assertEqual(readiness.status, "failing_closed")
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET",
            readiness.startup["missing_bindings"],
        )
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN",
            readiness.startup["missing_bindings"],
        )

    def test_phase27_readiness_contract_surfaces_degraded_source_and_automation_state(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep degraded health visible on the reviewed readiness path.",
        )
        requested_at = reviewed_at - timedelta(hours=2)
        delegated_at = reviewed_at - timedelta(hours=1, minutes=50)
        expired_at = reviewed_at - timedelta(hours=1)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Preserve degraded-mode visibility for source and automation health.",
            escalation_reason="Operators must not infer healthy runtime state from silence.",
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase27-day2-readiness-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase27-day2-readiness-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expired_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                requested_at=requested_at,
                expires_at=expired_at,
                lifecycle_state="executing",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase27-day2-readiness-001",
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-phase27-day2-readiness-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase27-day2-readiness-001",
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=delegated_at,
                expires_at=expired_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="dispatching",
            )
        )

        readiness = service.inspect_readiness_diagnostics()
        source_health = readiness.metrics["source_health"]
        automation_health = readiness.metrics["automation_substrate_health"]

        self.assertEqual(readiness.status, "failing_closed")
        self.assertEqual(source_health["overall_state"], "degraded")
        self.assertEqual(
            source_health["sources"]["github_audit"]["reason"],
            "ingest_signal_timeout",
        )
        self.assertEqual(
            automation_health["overall_state"],
            "degraded",
        )
        self.assertEqual(
            automation_health["surfaces"]["automation_substrate:shuffle"]["state"],
            "degraded",
        )

    def test_phase27_identity_contract_fails_closed_for_missing_or_unreviewed_provider_boundary(
        self,
    ) -> None:
        store, _ = make_store()
        startup_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host=runtime_auth_tests.TEST_NON_LOOPBACK_HOST,
                port=8080,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=runtime_auth_tests.REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=(
                    runtime_auth_tests.REVIEWED_WAZUH_PROXY_SECRET
                ),
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_reverse_proxy_secret=(
                    runtime_auth_tests.REVIEWED_SURFACE_PROXY_SECRET
                ),
                protected_surface_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_proxy_service_account=(
                    runtime_auth_tests.REVIEWED_PROXY_SERVICE_ACCOUNT
                ),
                admin_bootstrap_token=runtime_auth_tests.REVIEWED_ADMIN_BOOTSTRAP_TOKEN,
            ),
            store=store,
        )

        startup = startup_service.describe_startup_status()
        readiness = startup_service.inspect_readiness_diagnostics()

        self.assertFalse(startup.startup_ready)
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER",
            startup.missing_bindings,
        )
        self.assertEqual(readiness.status, "failing_closed")

        request_service = runtime_auth_tests._build_service(
            host=runtime_auth_tests.TEST_NON_LOOPBACK_HOST
        )
        with self.assertRaisesRegex(
            PermissionError,
            "protected control-plane surfaces require the reviewed identity provider boundary",
        ):
            request_service.authenticate_protected_surface_request(
                peer_addr="10.10.0.5",
                forwarded_proto="https",
                reverse_proxy_secret_header=(
                    runtime_auth_tests.REVIEWED_SURFACE_PROXY_SECRET
                ),
                proxy_service_account_header=(
                    runtime_auth_tests.REVIEWED_PROXY_SERVICE_ACCOUNT
                ),
                authenticated_identity_provider_header="entra-id",
                authenticated_subject_header="entra-user-001",
                authenticated_identity_header="analyst-001",
                authenticated_role_header="analyst",
                allowed_roles=("analyst",),
            )

    def test_phase27_secret_contract_requires_fresh_read_and_blocks_backend_outage(
        self,
    ) -> None:
        transport = secret_boundary_tests._MutableOpenBaoTransport(
            {
                "kv/aegisops/control-plane/wazuh-ingest-shared-secret": (
                    "reviewed-shared-secret-v1"
                ),
            }
        )

        initial = RuntimeConfig.from_env(
            {
                "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH": (
                    "kv/aegisops/control-plane/wazuh-ingest-shared-secret"
                ),
            },
            secret_backend_transport=transport,
        )

        transport._secrets["kv/aegisops/control-plane/wazuh-ingest-shared-secret"] = (
            "reviewed-shared-secret-v2"
        )

        rotated = RuntimeConfig.from_env(
            {
                "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH": (
                    "kv/aegisops/control-plane/wazuh-ingest-shared-secret"
                ),
            },
            secret_backend_transport=transport,
        )

        failing_transport = secret_boundary_tests._MutableOpenBaoTransport(
            error=RuntimeError("backend unavailable")
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH could not be read from OpenBao",
        ):
            RuntimeConfig.from_env(
                {
                    "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                    "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                    "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH": (
                        "kv/aegisops/control-plane/postgres-dsn"
                    ),
                },
                secret_backend_transport=failing_transport,
            )

        self.assertEqual(initial.wazuh_ingest_shared_secret, "reviewed-shared-secret-v1")
        self.assertEqual(rotated.wazuh_ingest_shared_secret, "reviewed-shared-secret-v2")


if __name__ == "__main__":
    unittest.main()
