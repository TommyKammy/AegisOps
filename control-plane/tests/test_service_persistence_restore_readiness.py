from __future__ import annotations

import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _service_persistence_support as support
from _service_persistence_support import ServicePersistenceTestBase

for name, value in vars(support).items():
    if not (name.startswith("__") and name.endswith("__")):
        globals()[name] = value


class RestoreReadinessPersistenceTests(ServicePersistenceTestBase):
    def test_runtime_snapshot_reports_postgresql_authoritative_persistence_mode(self) -> None:
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops")
        )

        snapshot = service.describe_runtime()

        self.assertEqual(snapshot.persistence_mode, "postgresql")
        self.assertEqual(snapshot.postgres_dsn, "postgresql://control-plane.local/aegisops")

    def test_service_round_trips_records_by_control_plane_identifier(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="approved",
        )
        reconciliation = ReconciliationRecord(
            reconciliation_id="reconciliation-001",
            subject_linkage={"action_request_ids": ["action-request-001"]},
            alert_id=None,
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            execution_run_id="n8n-exec-001",
            linked_execution_run_ids=("n8n-exec-001",),
            correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
            first_seen_at=timestamp,
            last_seen_at=timestamp,
            ingest_disposition="matched",
            mismatch_summary="matched execution",
            compared_at=timestamp,
            lifecycle_state="matched",
        )

        service.persist_record(action_request)
        service.persist_record(reconciliation)

        self.assertEqual(
            service.get_record(ActionRequestRecord, "action-request-001"),
            action_request,
        )
        self.assertEqual(
            service.get_record(ReconciliationRecord, "reconciliation-001"),
            reconciliation,
        )
        self.assertIsNone(service.get_record(ActionRequestRecord, "approval-001"))
        self.assertIsNone(service.get_record(ReconciliationRecord, "n8n-exec-001"))

    def test_service_accepts_injected_store_for_runtime_snapshot(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://ignored.local/aegisops"),
            store=store,
        )

        snapshot = service.describe_runtime()

        self.assertEqual(snapshot.postgres_dsn, "postgresql://control-plane.local/aegisops")
        self.assertEqual(snapshot.persistence_mode, "postgresql")

    def test_service_returns_nested_immutable_json_backed_records(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        record = ActionRequestRecord(
            action_request_id="action-request-immutable-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={
                "asset_ids": ["asset-001"],
                "filters": {"environment": "prod"},
            },
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="approved",
        )

        service.persist_record(record)
        persisted = service.get_record(
            ActionRequestRecord, "action-request-immutable-001"
        )

        assert persisted is not None
        with self.assertRaises(TypeError):
            persisted.target_scope["asset_ids"] += ("asset-002",)
        with self.assertRaises(TypeError):
            persisted.target_scope["filters"]["environment"] = "dev"  # type: ignore[index]

    def test_service_exposes_read_only_record_and_reconciliation_inspection(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        first_compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        latest_compared_at = datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc)
        alert = AlertRecord(
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            case_id=None,
            lifecycle_state="triaged",
        )
        matched = ReconciliationRecord(
            reconciliation_id="reconciliation-001",
            subject_linkage={
                "alert_ids": ("alert-001",),
                "finding_ids": ("finding-001",),
                "latest_native_payload": {"secret": "keep-in-store"},
            },
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            execution_run_id=None,
            linked_execution_run_ids=(),
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_compared_at,
            last_seen_at=first_compared_at,
            ingest_disposition="matched",
            mismatch_summary="matched upstream signal into alert lifecycle",
            compared_at=first_compared_at,
            lifecycle_state="matched",
        )
        stale = ReconciliationRecord(
            reconciliation_id="reconciliation-002",
            subject_linkage={
                "alert_ids": ("alert-001",),
                "finding_ids": ("finding-001",),
                "execution_surface_types": ("automation_substrate",),
                "execution_surface_ids": ("n8n",),
                "latest_native_payload": {"secret": "keep-in-store"},
            },
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            execution_run_id="exec-001",
            linked_execution_run_ids=("exec-001",),
            correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
            first_seen_at=first_compared_at,
            last_seen_at=latest_compared_at,
            ingest_disposition="stale",
            mismatch_summary="stale downstream execution observation requires refresh",
            compared_at=latest_compared_at,
            lifecycle_state="stale",
        )

        service.persist_record(alert)
        service.persist_record(matched)
        service.persist_record(stale)

        records_view = service.inspect_records("alert")
        status_view = service.inspect_reconciliation_status()

        self.assertTrue(records_view.read_only)
        self.assertEqual(records_view.record_family, "alert")
        self.assertEqual(records_view.total_records, 1)
        self.assertEqual(records_view.records[0]["alert_id"], "alert-001")
        self.assertEqual(records_view.records[0]["lifecycle_state"], "triaged")

        self.assertTrue(status_view.read_only)
        self.assertEqual(status_view.total_records, 2)
        self.assertEqual(status_view.by_lifecycle_state, {"matched": 1, "stale": 1})
        self.assertEqual(status_view.by_ingest_disposition, {"matched": 1, "stale": 1})
        self.assertEqual(status_view.latest_compared_at, latest_compared_at)
        self.assertEqual(
            tuple(record["reconciliation_id"] for record in status_view.records),
            ("reconciliation-001", "reconciliation-002"),
        )
        self.assertNotIn(
            "latest_native_payload",
            status_view.records[0]["subject_linkage"],
        )
        self.assertNotIn(
            "latest_native_payload",
            status_view.records[1]["subject_linkage"],
        )
        stored_latest = service.get_record(type(stale), "reconciliation-002")
        self.assertIsNotNone(stored_latest)
        self.assertIn("latest_native_payload", stored_latest.subject_linkage)

    def test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
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
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-restore-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
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
            delegated_at=delegated_at,
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
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": observed_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=stale_after,
        )

        backup = service.export_authoritative_record_chain_backup()
        backup_transition_subjects = {
            (record["subject_record_family"], record["subject_record_id"])
            for record in backup["record_families"]["lifecycle_transition"]
        }

        self.assertIn(
            ("approval_decision", approval_decision.approval_decision_id),
            backup_transition_subjects,
        )
        self.assertIn(
            ("action_request", approved_request.action_request_id),
            backup_transition_subjects,
        )
        self.assertIn(
            ("action_execution", execution.action_execution_id),
            backup_transition_subjects,
        )
        self.assertIn(
            ("recommendation", recommendation.recommendation_id),
            backup_transition_subjects,
        )
        self.assertIn(
            ("reconciliation", reconciliation.reconciliation_id),
            backup_transition_subjects,
        )

        restored_store, restored_backend = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=restored_store,
        )
        statement_count_before_restore = len(restored_backend.statements)
        with mock.patch.object(
            restored_service,
            "inspect_assistant_context",
            wraps=restored_service.inspect_assistant_context,
        ) as inspect_assistant_context:
            restore_summary = restored_service.restore_authoritative_record_chain_backup(
                backup
            )

        self.assertEqual(
            restored_backend.statements[statement_count_before_restore][0],
            "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE",
        )

        self.assertEqual(
            backup["backup_schema_version"],
            "phase23.authoritative-record-chain.v2",
        )
        self.assertEqual(backup["record_counts"]["action_execution"], 1)
        self.assertEqual(backup["record_counts"]["recommendation"], 1)
        self.assertEqual(restore_summary.restored_record_counts["reconciliation"], 2)
        self.assertTrue(restore_summary.restore_drill.drill_passed)
        self.assertEqual(
            restore_summary.restore_drill.verified_action_execution_ids,
            (execution.action_execution_id,),
        )
        self.assertEqual(
            restore_summary.restore_drill.verified_approval_decision_ids,
            (approval_decision.approval_decision_id,),
        )
        self.assertIn(
            promoted_case.case_id,
            restore_summary.restore_drill.verified_case_ids,
        )
        self.assertIn(
            reconciliation.reconciliation_id,
            restore_summary.restore_drill.verified_reconciliation_ids,
        )
        restored_transition_subjects = {
            (record.subject_record_family, record.subject_record_id)
            for record in restored_service._store.list(LifecycleTransitionRecord)
        }
        self.assertIn(
            ("approval_decision", approval_decision.approval_decision_id),
            restored_transition_subjects,
        )
        self.assertIn(
            ("action_request", approved_request.action_request_id),
            restored_transition_subjects,
        )
        self.assertIn(
            ("action_execution", execution.action_execution_id),
            restored_transition_subjects,
        )
        self.assertIn(
            ("recommendation", recommendation.recommendation_id),
            restored_transition_subjects,
        )
        self.assertIn(
            ("reconciliation", reconciliation.reconciliation_id),
            restored_transition_subjects,
        )
        self.assertIsNotNone(
            restored_service.get_record(
                RecommendationRecord,
                recommendation.recommendation_id,
            )
        )
        self.assertCountEqual(
            restore_summary.restore_drill.verified_reconciliation_ids,
            tuple(
                record.reconciliation_id
                for record in service._store.list(ReconciliationRecord)
            ),
        )
        self.assertIn(
            mock.call("reconciliation", reconciliation.reconciliation_id),
            inspect_assistant_context.call_args_list,
        )

        restored_case_detail = restored_service.inspect_case_detail(promoted_case.case_id)
        self.assertEqual(
            restored_case_detail.case_record["case_id"],
            promoted_case.case_id,
        )
        self.assertEqual(restored_case_detail.linked_evidence_ids, (evidence_id,))

        restored_approval_context = restored_service.inspect_assistant_context(
            "approval_decision",
            approval_decision.approval_decision_id,
        )
        self.assertEqual(
            restored_approval_context.linked_case_ids,
            (promoted_case.case_id,),
        )
        self.assertIn(
            reconciliation.reconciliation_id,
            restored_approval_context.linked_reconciliation_ids,
        )

    def test_service_phase21_restore_accepts_legacy_backup_without_recommendation_or_transition_family(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["backup_schema_version"] = "phase21.authoritative-record-chain.v1"
        del backup["record_families"]["recommendation"]
        del backup["record_counts"]["recommendation"]
        del backup["record_families"]["lifecycle_transition"]
        del backup["record_counts"]["lifecycle_transition"]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        restore_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )
        expected_transition_count = sum(
            count
            for family, count in restore_summary.restored_record_counts.items()
            if family != "lifecycle_transition"
        )
        restored_transitions = restored_service._store.list(LifecycleTransitionRecord)

        self.assertIn(promoted_case.case_id, restore_summary.restore_drill.verified_case_ids)
        self.assertEqual(
            restore_summary.restored_record_counts["lifecycle_transition"],
            expected_transition_count,
        )
        self.assertEqual(len(restored_transitions), expected_transition_count)
        self.assertIn(
            (
                "case",
                promoted_case.case_id,
                None,
                promoted_case.lifecycle_state,
            ),
            {
                (
                    transition.subject_record_family,
                    transition.subject_record_id,
                    transition.previous_lifecycle_state,
                    transition.lifecycle_state,
                )
                for transition in restored_transitions
            },
        )

    def test_service_phase21_legacy_restore_round_trips_into_v2_transition_history(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["backup_schema_version"] = "phase21.authoritative-record-chain.v1"
        del backup["record_families"]["recommendation"]
        del backup["record_counts"]["recommendation"]
        del backup["record_families"]["lifecycle_transition"]
        del backup["record_counts"]["lifecycle_transition"]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        restored_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )
        round_trip_backup = restored_service.export_authoritative_record_chain_backup()

        self.assertEqual(
            round_trip_backup["backup_schema_version"],
            "phase23.authoritative-record-chain.v2",
        )
        self.assertEqual(
            round_trip_backup["record_counts"]["lifecycle_transition"],
            restored_summary.restored_record_counts["lifecycle_transition"],
        )
        self.assertGreater(round_trip_backup["record_counts"]["lifecycle_transition"], 0)

        round_trip_store, _ = make_store()
        round_trip_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=round_trip_store,
        )
        round_trip_summary = round_trip_service.restore_authoritative_record_chain_backup(
            round_trip_backup
        )

        self.assertIn(
            promoted_case.case_id,
            round_trip_summary.restore_drill.verified_case_ids,
        )
        self.assertEqual(
            round_trip_backup["record_counts"]["lifecycle_transition"],
            len(round_trip_store.list(LifecycleTransitionRecord)),
        )

    def test_service_phase21_restore_rejects_v2_backup_without_recommendation_family(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        del backup["record_families"]["recommendation"]
        del backup["record_counts"]["recommendation"]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "restore payload must contain a JSON array for record family 'recommendation'",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self.assertEqual(restored_service._store.list(RecommendationRecord), ())
        self.assertEqual(restored_service._store.list(CaseRecord), ())

    def test_service_phase21_restore_preserves_handoff_and_manual_fallback_runtime_visibility(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Waiting until the next business-hours cycle is unsafe for this repository owner change.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase21-restore-visibility-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-restore-visibility-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        promoted_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-002",
            handoff_note="Resume the unresolved approval review at next business-hours open.",
            follow_up_evidence_ids=(evidence_id,),
        )
        promoted_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Keep the unresolved action visible for the next analyst handoff.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )
        service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed automation path was unavailable after approval.",
            action_taken="Notified the accountable repository owner using the approved manual procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting written owner acknowledgement.",
        )
        service.record_action_review_escalation_note(
            action_request_id=action_request.action_request_id,
            escalated_at=reviewed_at + timedelta(minutes=15),
            escalated_by_identity="analyst-004",
            escalated_to="on-call-manager-001",
            note="On-call manager notified because the unresolved action could not be left unattended.",
        )

        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        restored_service.restore_authoritative_record_chain_backup(backup)
        restored_case_detail = restored_service.inspect_case_detail(promoted_case.case_id)
        runtime_visibility = restored_case_detail.current_action_review["runtime_visibility"]

        self.assertEqual(
            runtime_visibility["after_hours_handoff"]["handoff_owner"],
            "analyst-002",
        )
        self.assertEqual(
            runtime_visibility["after_hours_handoff"]["recorded_at"],
            (reviewed_at + timedelta(hours=8)).isoformat(),
        )
        self.assertEqual(
            runtime_visibility["after_hours_handoff"]["rationale"],
            "Keep the unresolved action visible for the next analyst handoff.",
        )
        self.assertEqual(
            runtime_visibility["manual_fallback"]["approval_decision_id"],
            approval.approval_decision_id,
        )
        self.assertEqual(
            runtime_visibility["manual_fallback"]["fallback_actor_identity"],
            "analyst-003",
        )
        self.assertEqual(
            runtime_visibility["escalation_notes"]["escalated_to"],
            "on-call-manager-001",
        )
        self.assertEqual(
            runtime_visibility["escalation_notes"]["escalated_by_identity"],
            "analyst-004",
        )

    def test_service_phase21_restore_prefers_canonical_manual_fallback_timestamp(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep legacy manual fallback timestamps auditable after restore.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Legacy fallback timestamps must not rewrite the reviewed record.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase21-restore-fallback-alias-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-restore-fallback-alias-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed automation path was unavailable after approval.",
            action_taken="Notified the accountable repository owner using the approved manual procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting written owner acknowledgement.",
        )

        case_with_fallback = service.get_record(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(case_with_fallback)
        assert case_with_fallback is not None
        action_review_visibility = dict(
            case_with_fallback.reviewed_context["action_review_visibility"]
        )
        scoped_visibility = dict(action_review_visibility[action_request.action_request_id])
        manual_fallback = dict(scoped_visibility["manual_fallback"])
        manual_fallback["performed_at"] = (
            reviewed_at + timedelta(minutes=50)
        ).isoformat()
        scoped_visibility["manual_fallback"] = manual_fallback
        action_review_visibility[action_request.action_request_id] = scoped_visibility
        service.persist_record(
            replace(
                case_with_fallback,
                reviewed_context={
                    **dict(case_with_fallback.reviewed_context),
                    "action_review_visibility": action_review_visibility,
                },
            )
        )

        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=restored_store,
        )

        restored_service.restore_authoritative_record_chain_backup(backup)
        restored_case_detail = restored_service.inspect_case_detail(promoted_case.case_id)
        runtime_visibility = restored_case_detail.current_action_review["runtime_visibility"]

        self.assertEqual(
            runtime_visibility["manual_fallback"]["fallback_at"],
            (reviewed_at + timedelta(minutes=45)).isoformat(),
        )
        self.assertEqual(
            runtime_visibility["manual_fallback"]["fallback_actor_identity"],
            "analyst-003",
        )

    def test_manual_fallback_requires_approved_post_approval_action_review(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep manual fallback approval-bound.",
        )
        pending_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Review before any fallback path is used.",
            escalation_reason="Pending approval must not masquerade as manual fallback.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase21-manual-fallback-pending-001",
        )

        with self.assertRaisesRegex(
            ValueError,
            "manual fallback requires an approved action review in a live post-approval state",
        ):
            service.record_action_review_manual_fallback(
                action_request_id=pending_request.action_request_id,
                fallback_at=reviewed_at + timedelta(minutes=15),
                fallback_actor_identity="analyst-001",
                authority_boundary="approved_human_fallback",
                reason="Pending approvals must not write fallback visibility.",
                action_taken="No manual action should be recorded.",
                verification_evidence_ids=(evidence_id,),
            )

        rejected_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-manual-fallback-rejected-001",
                action_request_id=pending_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(pending_request.target_scope),
                payload_hash=pending_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=20),
                lifecycle_state="rejected",
            )
        )
        rejected_request = service.persist_record(
            replace(
                pending_request,
                approval_decision_id=rejected_decision.approval_decision_id,
                lifecycle_state="rejected",
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "manual fallback requires an approved action review in a live post-approval state",
        ):
            service.record_action_review_manual_fallback(
                action_request_id=rejected_request.action_request_id,
                fallback_at=reviewed_at + timedelta(minutes=25),
                fallback_actor_identity="analyst-001",
                authority_boundary="approved_human_fallback",
                reason="Rejected approvals must not write fallback visibility.",
                action_taken="No manual action should be recorded.",
                verification_evidence_ids=(evidence_id,),
            )

        current_action_review = service.inspect_case_detail(promoted_case.case_id).current_action_review
        self.assertNotIn(
            "manual_fallback",
            current_action_review["runtime_visibility"] or {},
        )

    def test_manual_fallback_rejects_unrelated_alert_scoped_evidence(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep alert-scoped fallback evidence linked to the correct alert.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Record the approved alert-scoped fallback without borrowing other alerts' evidence.",
            escalation_reason="The approved alert-scoped follow-up cannot wait for the next shift.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase21-alert-scoped-fallback-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-alert-scoped-fallback-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        action_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                case_id=None,
                lifecycle_state="unresolved",
            )
        )

        unrelated_admission = service.ingest_finding_alert(
            finding_id="finding-phase21-alert-scoped-fallback-unrelated-001",
            analytic_signal_id="signal-phase21-alert-scoped-fallback-unrelated-001",
            substrate_detection_record_id=(
                "substrate-detection-phase21-alert-scoped-fallback-unrelated-001"
            ),
            correlation_key="claim:asset-phase21-alert-scoped-fallback-unrelated-001:synthetic",
            first_seen_at=reviewed_at + timedelta(minutes=1),
            last_seen_at=reviewed_at + timedelta(minutes=1),
            reviewed_context={
                "asset": {"asset_id": "asset-phase21-alert-scoped-fallback-unrelated-001"},
                "identity": {
                    "identity_id": "principal-phase21-alert-scoped-fallback-unrelated-001"
                },
                "source": {
                    "source_family": "synthetic_review_fixture",
                    "admission_kind": "synthetic",
                },
            },
        )
        unrelated_evidence_id = "evidence-phase21-alert-scoped-fallback-unrelated-001"
        service.persist_record(
            EvidenceRecord(
                evidence_id=unrelated_evidence_id,
                source_record_id=unrelated_admission.alert.finding_id,
                alert_id=unrelated_admission.alert.alert_id,
                case_id=None,
                source_system="synthetic",
                collector_identity="collector://synthetic/fixture",
                acquired_at=reviewed_at + timedelta(minutes=1),
                derivation_relationship="finding_alert",
                lifecycle_state="collected",
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            f"verification_evidence_ids contains evidence {unrelated_evidence_id!r} that is not linked to alert {promoted_case.alert_id!r}",
        ):
            service.record_action_review_manual_fallback(
                action_request_id=action_request.action_request_id,
                fallback_at=reviewed_at + timedelta(minutes=15),
                fallback_actor_identity="analyst-001",
                authority_boundary="approved_human_fallback",
                reason="Only evidence from the same alert or a real shared case should be allowed.",
                action_taken="No manual fallback should be recorded with unrelated evidence.",
                verification_evidence_ids=(evidence_id, unrelated_evidence_id),
            )

        current_action_review = service.inspect_case_detail(promoted_case.case_id).current_action_review
        self.assertNotIn(
            "manual_fallback",
            current_action_review["runtime_visibility"] or {},
        )

    def test_escalation_visibility_requires_recorded_note_and_preserves_recorded_state(self) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep escalation visibility record-driven.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Escalate the reviewed request if waiting is unsafe.",
            escalation_reason="The pending review cannot wait for the next shift.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase21-escalation-state-001",
        )

        initial_review = service.inspect_case_detail(promoted_case.case_id).current_action_review
        self.assertNotIn("escalation_notes", initial_review["runtime_visibility"] or {})

        service.record_action_review_escalation_note(
            action_request_id=action_request.action_request_id,
            escalated_at=reviewed_at + timedelta(minutes=10),
            escalated_by_identity="analyst-009",
            escalated_to="on-call-manager-001",
            note="Pending review escalated before any approval decision existed.",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-escalation-state-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=20),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        runtime_visibility = service.inspect_case_detail(promoted_case.case_id).current_action_review[
            "runtime_visibility"
        ]
        self.assertEqual(runtime_visibility["escalation_notes"]["review_state"], "pending")
        self.assertEqual(
            runtime_visibility["escalation_notes"]["escalated_by_identity"],
            "analyst-009",
        )

    def test_service_phase21_restore_drill_can_run_standalone_after_restore(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=restored_store,
        )

        restore_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )
        restore_drill = restored_service.run_authoritative_restore_drill()

        self.assertTrue(restore_drill.drill_passed)
        self.assertEqual(
            restore_drill.verified_case_ids,
            restore_summary.restore_drill.verified_case_ids,
        )
        self.assertEqual(
            restore_drill.verified_reconciliation_ids,
            restore_summary.restore_drill.verified_reconciliation_ids,
        )
        self.assertEqual(restore_drill.verified_case_ids, (promoted_case.case_id,))

        restored_case_detail = restored_service.inspect_case_detail(promoted_case.case_id)
        self.assertEqual(restored_case_detail.linked_evidence_ids, (evidence_id,))

    def test_service_phase21_restore_drill_filters_non_authoritative_transition_subjects(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement=(
                "Keep a reviewed observation transition in the live store while "
                "the restore drill validates only the authoritative subset."
            ),
            supporting_evidence_ids=(evidence_id,),
        )

        self.assertIn(
            ("observation", observation.observation_id),
            {
                (record.subject_record_family, record.subject_record_id)
                for record in store.list(LifecycleTransitionRecord)
            },
        )

        restore_drill = service.run_authoritative_restore_drill()

        self.assertEqual(restore_drill.verified_case_ids, (promoted_case.case_id,))

    def test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
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

    def test_service_phase21_restore_drill_uses_single_transaction_snapshot(
        self,
    ) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
            default=None,
        )
        if seed_reconciliation is None:
            self.fail("expected seeded reconciliation record before restore drill")

        concurrent_reconciliation = replace(
            seed_reconciliation,
            reconciliation_id="reconciliation-phase21-restore-drill-concurrent-001",
            compared_at=seed_reconciliation.compared_at + timedelta(minutes=30),
            lifecycle_state="stale",
        )
        snapshot_store = _ConcurrentListMutationStore(
            inner=base_store,
            mutate_once=lambda: concurrent_store.save(concurrent_reconciliation),
        )
        snapshot_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=snapshot_store,
        )

        statement_count_before_snapshot = len(backend.statements)
        restore_drill = snapshot_service.run_authoritative_restore_drill()

        self.assertEqual(
            backend.statements[statement_count_before_snapshot][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertTrue(restore_drill.drill_passed)
        self.assertEqual(
            restore_drill.verified_reconciliation_ids,
            (seed_reconciliation.reconciliation_id,),
        )
        self.assertEqual(len(base_store.list(ReconciliationRecord)), 2)
        self.assertEqual(
            concurrent_store.get(
                ReconciliationRecord,
                "reconciliation-phase21-restore-drill-concurrent-001",
            ),
            concurrent_reconciliation,
        )

    def test_service_phase21_backup_uses_single_transaction_snapshot(self) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_alert = service.get_record(AlertRecord, promoted_case.alert_id)
        if seed_alert is None:
            self.fail("expected seeded alert record before snapshot export")

        snapshot_store = _ConcurrentListMutationStore(
            inner=base_store,
            mutate_once=lambda: concurrent_store.save(
                replace(
                    seed_alert,
                    alert_id="alert-phase21-backup-concurrent-001",
                )
            ),
        )
        snapshot_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=snapshot_store,
        )

        statement_count_before_backup = len(backend.statements)
        backup = snapshot_service.export_authoritative_record_chain_backup()

        self.assertEqual(
            backend.statements[statement_count_before_backup][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertEqual(backup["record_counts"]["alert"], 1)
        self.assertEqual(len(backup["record_families"]["alert"]), 1)
        self.assertCountEqual(
            [record["alert_id"] for record in backup["record_families"]["alert"]],
            (promoted_case.alert_id,),
        )
        self.assertEqual(len(base_store.list(AlertRecord)), 2)
        self.assertEqual(
            concurrent_store.get(AlertRecord, "alert-phase21-backup-concurrent-001"),
            replace(
                seed_alert,
                alert_id="alert-phase21-backup-concurrent-001",
            ),
        )

    def test_service_phase21_readiness_uses_single_transaction_snapshot(self) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
            default=None,
        )
        if seed_reconciliation is None:
            self.fail("expected seeded reconciliation record before readiness snapshot")

        concurrent_reconciliation = replace(
            seed_reconciliation,
            reconciliation_id="reconciliation-phase21-readiness-concurrent-001",
            compared_at=seed_reconciliation.compared_at + timedelta(minutes=30),
            lifecycle_state="stale",
        )
        snapshot_store = _ConcurrentListMutationStore(
            inner=base_store,
            mutate_once=lambda: concurrent_store.save(concurrent_reconciliation),
        )
        snapshot_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=snapshot_store,
        )

        statement_count_before_snapshot = len(backend.statements)
        readiness = snapshot_service.inspect_readiness_diagnostics()

        self.assertEqual(
            backend.statements[statement_count_before_snapshot][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertEqual(readiness.status, "ready")
        self.assertEqual(readiness.metrics["reconciliations"]["stale"], 0)
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            seed_reconciliation.reconciliation_id,
        )
        self.assertEqual(len(base_store.list(ReconciliationRecord)), 2)
        self.assertEqual(
            concurrent_store.get(
                ReconciliationRecord,
                "reconciliation-phase21-readiness-concurrent-001",
            ),
            concurrent_reconciliation,
        )

    def test_store_phase21_readiness_aggregates_use_single_transaction_snapshot(self) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
            default=None,
        )
        if seed_reconciliation is None:
            self.fail("expected seeded reconciliation record before readiness aggregate snapshot")

        concurrent_reconciliation = replace(
            seed_reconciliation,
            reconciliation_id="reconciliation-phase21-aggregate-concurrent-001",
            compared_at=seed_reconciliation.compared_at + timedelta(minutes=30),
            lifecycle_state="stale",
        )
        original_count_grouped_by_field = base_store._count_grouped_by_field
        mutation_applied = False

        def count_grouped_by_field(
            record_type: object,
            field_name: str,
        ) -> dict[str, int]:
            nonlocal mutation_applied
            counts = original_count_grouped_by_field(record_type, field_name)
            if not mutation_applied:
                mutation_applied = True
                concurrent_store.save(concurrent_reconciliation)
            return counts

        statement_count_before_snapshot = len(backend.statements)
        with mock.patch.object(
            base_store,
            "_count_grouped_by_field",
            side_effect=count_grouped_by_field,
        ):
            aggregates = base_store.inspect_readiness_aggregates()

        self.assertEqual(
            backend.statements[statement_count_before_snapshot][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertEqual(aggregates.reconciliation_lifecycle_counts.get("stale", 0), 0)
        self.assertEqual(
            aggregates.latest_reconciliation.reconciliation_id
            if aggregates.latest_reconciliation is not None
            else None,
            seed_reconciliation.reconciliation_id,
        )
        self.assertEqual(len(base_store.list(ReconciliationRecord)), 2)
        self.assertEqual(
            concurrent_store.get(
                ReconciliationRecord,
                "reconciliation-phase21-aggregate-concurrent-001",
            ),
            concurrent_reconciliation,
        )

    def test_service_phase21_readiness_avoids_full_table_list_reads(self) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, _service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
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

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()

        self.assertEqual(readiness.status, "ready")
        self.assertEqual(store.list_calls, 0)

    def test_service_phase21_readiness_counts_distinct_execution_runs_and_redacts_payload(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        target_scope = {"asset_id": "asset-phase21-readiness-001"}
        latest_seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
        )
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id=promoted_case.case_id,
            alert_id=promoted_case.alert_id,
            finding_id=promoted_case.finding_id,
        )
        payload_hash = _approved_binding_hash(
            target_scope=target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        requested_at = latest_seed_reconciliation.compared_at + timedelta(minutes=10)
        delegated_at = requested_at + timedelta(minutes=5)
        expires_at = requested_at + timedelta(hours=1)
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-readiness-001",
                action_request_id="action-request-phase21-readiness-001",
                approver_identities=("approver-001",),
                target_snapshot=target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-phase21-readiness-001",
                approval_decision_id="approval-phase21-readiness-001",
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key="idempotency-phase21-readiness-001",
                target_scope=target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                requester_identity="analyst-001",
                requested_payload=approved_payload,
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_identity",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "routine_allowed",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-readiness-001",
                action_request_id="action-request-phase21-readiness-001",
                approval_decision_id="approval-phase21-readiness-001",
                delegation_id="delegation-phase21-readiness-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-readiness-001",
                idempotency_key="idempotency-phase21-readiness-001",
                target_scope=target_scope,
                approved_payload=approved_payload,
                payload_hash=payload_hash,
                delegated_at=delegated_at,
                expires_at=expires_at,
                provenance={"adapter": "shuffle"},
                lifecycle_state="queued",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase21-readiness-distinct-001",
                subject_linkage={
                    "action_request_ids": ("action-request-phase21-readiness-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id="execution-run-phase21-readiness-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:phase21-readiness:distinct-001",
                first_seen_at=requested_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="phase20 execution matched",
                compared_at=delegated_at + timedelta(minutes=1),
                lifecycle_state="matched",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase21-readiness-distinct-002",
                subject_linkage={
                    "action_request_ids": ("action-request-phase21-readiness-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id="execution-run-phase21-readiness-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:phase21-readiness:distinct-002",
                first_seen_at=requested_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="duplicate reconciliation for same execution run",
                compared_at=delegated_at + timedelta(minutes=2),
                lifecycle_state="matched",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase21-readiness-distinct-none-001",
                subject_linkage={
                    "action_request_ids": ("action-request-phase21-readiness-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="reconciliation:phase21-readiness:distinct-none-001",
                first_seen_at=requested_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="null execution run should stay out of phase20 metric",
                compared_at=delegated_at + timedelta(minutes=3),
                lifecycle_state="matched",
            )
        )

        readiness = service.inspect_readiness_diagnostics()

        self.assertEqual(
            readiness.metrics["phase20_notify_identity_owner"]["reconciled_executions"],
            1,
        )
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            "reconciliation-phase21-readiness-distinct-none-001",
        )
        self.assertNotIn(
            "latest_native_payload",
            readiness.latest_reconciliation["subject_linkage"],
        )
        stored_latest = service.get_record(
            ReconciliationRecord,
            "reconciliation-phase21-readiness-distinct-none-001",
        )
        self.assertIsNotNone(stored_latest)
        self.assertIn("latest_native_payload", stored_latest.subject_linkage)

    def test_service_phase21_readiness_treats_dispatching_executions_as_active(
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
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        execution = service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-dispatching-001",
                action_request_id="action-request-phase21-dispatching-001",
                approval_decision_id="approval-phase21-dispatching-001",
                delegation_id="delegation-phase21-dispatching-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="pending-dispatch-delegation-phase21-dispatching-001",
                idempotency_key="idempotency-phase21-dispatching-001",
                target_scope={"asset_id": "asset-phase21-dispatching-001"},
                approved_payload={
                    "action_type": "notify_identity_owner",
                    "recipient_identity": "repo-owner-001",
                },
                payload_hash="payload-hash-phase21-dispatching-001",
                delegated_at=delegated_at,
                expires_at=delegated_at + timedelta(hours=1),
                provenance={"delegation_issuer": "control-plane-service"},
                lifecycle_state="dispatching",
            )
        )

        readiness = service.inspect_readiness_diagnostics()
        aggregates = store.inspect_readiness_aggregates()

        self.assertFalse(readiness.shutdown["shutdown_ready"])
        self.assertEqual(
            readiness.shutdown["active_action_execution_ids"],
            [execution.action_execution_id],
        )
        self.assertEqual(
            aggregates.active_action_execution_ids,
            (execution.action_execution_id,),
        )
        self.assertEqual(readiness.metrics["action_executions"]["dispatching"], 1)
        self.assertEqual(readiness.metrics["action_executions"]["terminal"], 0)

    def test_service_phase21_readiness_prefers_higher_reconciliation_id_when_compared_at_ties(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertIsNotNone(reconciliation)

        preferred_reconciliation = replace(
            reconciliation,
            reconciliation_id=f"{reconciliation.reconciliation_id}-z",
            correlation_key=f"{reconciliation.correlation_key}:z",
        )
        service.persist_record(preferred_reconciliation)

        readiness = service.inspect_readiness_diagnostics()

        self.assertIsNotNone(readiness.latest_reconciliation)
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            preferred_reconciliation.reconciliation_id,
        )

    def test_service_phase21_restore_rejects_non_string_tuple_elements(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["case"][0]["evidence_ids"] = [
            backup["record_families"]["case"][0]["evidence_ids"][0],
            {"invalid": "evidence-id"},
        ]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "case.evidence_ids must contain only non-empty strings",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_on_duplicate_alert_identifiers(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["alert"].append(
            dict(backup["record_families"]["alert"][0])
        )
        backup["record_counts"]["alert"] = len(backup["record_families"]["alert"])

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            r"duplicate alert identifiers .*restored_record_counts\['alert'\]=2",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_on_duplicate_transition_identifiers(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["lifecycle_transition"].append(
            dict(backup["record_families"]["lifecycle_transition"][0])
        )
        backup["record_counts"]["lifecycle_transition"] = len(
            backup["record_families"]["lifecycle_transition"]
        )
        expected_transition_count = backup["record_counts"]["lifecycle_transition"]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"duplicate lifecycle_transition identifiers "
                r".*restored_record_counts\['lifecycle_transition'\]="
                f"{expected_transition_count}"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_when_transition_subject_is_missing(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        mutated_transition = next(
            record
            for record in backup["record_families"]["lifecycle_transition"]
            if record["subject_record_family"] == "case"
            and record["subject_record_id"] == promoted_case.case_id
        )
        mutated_transition["subject_record_id"] = "case-missing-001"

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"missing case record 'case-missing-001' required by lifecycle transition "
                r".*"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_invalid_subject_lifecycle_transition_state(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        mutated_transition = next(
            record
            for record in backup["record_families"]["lifecycle_transition"]
            if record["subject_record_family"] == "case"
            and record["subject_record_id"] == promoted_case.case_id
        )
        mutated_transition["lifecycle_state"] = "generated"

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"lifecycle_transition record .* has invalid lifecycle_state 'generated' "
                r"for subject_record_family 'case'"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_when_latest_transition_disagrees_with_current_state(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        updated_case = replace(
            promoted_case,
            lifecycle_state=(
                "closed"
                if promoted_case.lifecycle_state != "closed"
                else "reviewed"
            ),
        )
        service.persist_record(updated_case)
        backup = service.export_authoritative_record_chain_backup()
        latest_transition = max(
            (
                record
                for record in backup["record_families"]["lifecycle_transition"]
                if record["subject_record_family"] == "case"
                and record["subject_record_id"] == promoted_case.case_id
            ),
            key=lambda record: record["transitioned_at"],
        )
        latest_transition["lifecycle_state"] = "reopened"

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                rf"case record '{promoted_case.case_id}' lifecycle_state "
                rf"'{updated_case.lifecycle_state}' does not match "
                r"latest lifecycle transition .* state 'reopened'"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_when_authoritative_subject_loses_transition_history(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["lifecycle_transition"] = [
            record
            for record in backup["record_families"]["lifecycle_transition"]
            if not (
                record["subject_record_family"] == "case"
                and record["subject_record_id"] == promoted_case.case_id
            )
        ]
        backup["record_counts"]["lifecycle_transition"] = len(
            backup["record_families"]["lifecycle_transition"]
        )

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            rf"missing lifecycle transition history for case record '{promoted_case.case_id}'",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_when_earliest_transition_anchor_is_missing(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        updated_case = replace(
            promoted_case,
            lifecycle_state=(
                "closed"
                if promoted_case.lifecycle_state != "closed"
                else "reopened"
            ),
        )
        service.persist_record(updated_case)
        backup = service.export_authoritative_record_chain_backup()
        ordered_case_transitions = sorted(
            (
                record
                for record in backup["record_families"]["lifecycle_transition"]
                if record["subject_record_family"] == "case"
                and record["subject_record_id"] == promoted_case.case_id
            ),
            key=lambda record: (
                record["transitioned_at"],
                record["transition_id"],
            ),
        )
        self.assertEqual(len(ordered_case_transitions), 2)
        missing_anchor_transition = ordered_case_transitions[0]
        backup["record_families"]["lifecycle_transition"] = [
            record
            for record in backup["record_families"]["lifecycle_transition"]
            if record["transition_id"] != missing_anchor_transition["transition_id"]
        ]
        backup["record_counts"]["lifecycle_transition"] = len(
            backup["record_families"]["lifecycle_transition"]
        )

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                rf"lifecycle transition chain for case record '{promoted_case.case_id}' "
                r"must start with a creation anchor: .* has previous_lifecycle_state "
                rf"'{promoted_case.lifecycle_state}'"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_when_transition_chain_is_inconsistent(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        updated_case = replace(
            promoted_case,
            lifecycle_state=(
                "closed"
                if promoted_case.lifecycle_state != "closed"
                else "reviewed"
            ),
        )
        service.persist_record(updated_case)
        backup = service.export_authoritative_record_chain_backup()
        ordered_case_transitions = sorted(
            (
                record
                for record in backup["record_families"]["lifecycle_transition"]
                if record["subject_record_family"] == "case"
                and record["subject_record_id"] == promoted_case.case_id
            ),
            key=lambda record: record["transitioned_at"],
        )
        self.assertEqual(len(ordered_case_transitions), 2)
        prior_lifecycle_state = ordered_case_transitions[0]["lifecycle_state"]
        ordered_case_transitions[1]["previous_lifecycle_state"] = "closed"

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                rf"lifecycle transition chain for case record '{promoted_case.case_id}' "
                r"is inconsistent: "
                r".* previous_lifecycle_state 'closed' does not match prior "
                rf"lifecycle_state '{prior_lifecycle_state}'"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_persist_record_rejects_direct_authoritative_transition_rows(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        orphan_transition = LifecycleTransitionRecord(
            transition_id="transition-phase21-orphan-alert-001",
            subject_record_family="alert",
            subject_record_id="alert-phase21-orphan-001",
            previous_lifecycle_state="new",
            lifecycle_state="closed",
            transitioned_at=datetime(2026, 4, 16, 0, 5, tzinfo=timezone.utc),
            attribution={"source": "test-fixture", "actor_identities": ("analyst-001",)},
        )

        with self.assertRaisesRegex(
            ValueError,
            "persist_record does not accept direct lifecycle transition records",
        ):
            service.persist_record(orphan_transition)

        self.assertEqual(store.list(LifecycleTransitionRecord), ())

    def test_service_phase21_backup_preserves_recommendation_transitions_and_excludes_non_authoritative_subjects(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep a reviewed recommendation in the authoritative restore set.",
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Keep observation transitions outside the authoritative restore set.",
            supporting_evidence_ids=(evidence_id,),
        )

        self.assertIn(
            ("recommendation", recommendation.recommendation_id),
            {
                (record.subject_record_family, record.subject_record_id)
                for record in store.list(LifecycleTransitionRecord)
            },
        )

        backup = service.export_authoritative_record_chain_backup()

        self.assertIn(
            ("recommendation", recommendation.recommendation_id),
            {
                (record["subject_record_family"], record["subject_record_id"])
                for record in backup["record_families"]["lifecycle_transition"]
            },
        )
        self.assertIn(
            recommendation.recommendation_id,
            {
                record["recommendation_id"]
                for record in backup["record_families"]["recommendation"]
            },
        )
        self.assertNotIn(
            ("observation", observation.observation_id),
            {
                (record["subject_record_family"], record["subject_record_id"])
                for record in backup["record_families"]["lifecycle_transition"]
            },
        )

    def test_service_phase21_restore_rejects_unsupported_transition_subject_family(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Use an observation family to simulate an unsupported restore payload.",
            supporting_evidence_ids=(evidence_id,),
        )
        backup = service.export_authoritative_record_chain_backup()
        mutated_transition = dict(backup["record_families"]["lifecycle_transition"][0])
        mutated_transition["subject_record_family"] = "observation"
        mutated_transition["subject_record_id"] = observation.observation_id
        backup["record_families"]["lifecycle_transition"][0] = mutated_transition

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"lifecycle transition .* references unsupported "
                r"subject_record_family 'observation'"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_on_duplicate_execution_run_ids(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
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
                approval_decision_id="approval-phase21-duplicate-run-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
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
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-duplicate-run-001",
                action_request_id=approved_request.action_request_id,
                approval_decision_id=approval_decision.approval_decision_id,
                delegation_id="delegation-phase21-duplicate-run-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-duplicate-run-001",
                idempotency_key=approved_request.idempotency_key,
                target_scope=dict(approved_request.target_scope),
                approved_payload=dict(approved_request.requested_payload),
                payload_hash=approved_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=approved_request.expires_at,
                provenance={"evidence_ids": (evidence_id,)},
                lifecycle_state="queued",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        duplicate_execution = dict(backup["record_families"]["action_execution"][0])
        duplicate_execution["action_execution_id"] = (
            "action-execution-phase21-duplicate-run-002"
        )
        duplicate_execution["delegation_id"] = "delegation-phase21-duplicate-run-002"
        duplicate_execution["delegated_at"] = (
            reviewed_at + timedelta(minutes=2)
        ).isoformat()
        backup["record_families"]["action_execution"].append(duplicate_execution)
        backup["record_counts"]["action_execution"] = len(
            backup["record_families"]["action_execution"]
        )

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"duplicate action_execution execution_run_id values "
                r".*restored_record_counts\['action_execution'\]=2"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_when_approval_record_is_missing(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
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
                approval_decision_id="approval-phase21-missing-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
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
        execution = service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-missing-001",
                action_request_id=approved_request.action_request_id,
                approval_decision_id="approval-phase21-missing-001",
                delegation_id="delegation-phase21-missing-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-missing-001",
                idempotency_key=approved_request.idempotency_key,
                target_scope=dict(approved_request.target_scope),
                approved_payload=dict(approved_request.requested_payload),
                payload_hash=approved_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=approved_request.expires_at,
                provenance={"evidence_ids": (evidence_id,)},
                lifecycle_state="queued",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        self.assertEqual(len(backup["record_families"]["approval_decision"]), 1)
        backup["record_families"]["approval_decision"] = [
            record
            for record in backup["record_families"]["approval_decision"]
            if record["approval_decision_id"] != approval_decision.approval_decision_id
        ]
        backup["record_counts"]["approval_decision"] = len(
            backup["record_families"]["approval_decision"]
        )

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "missing approval_decision record 'approval-phase21-missing-001' required by action request",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)

        self._assert_authoritative_store_empty(restored_store)
        self.assertIsNone(
            restored_service.get_record(ActionExecutionRecord, execution.action_execution_id)
        )

    def test_service_phase21_restore_fails_closed_on_existing_recommendation(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )
        restored_service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-existing-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id="alert-existing-001",
                case_id="case-existing-001",
                ai_trace_id=None,
                review_owner="analyst-001",
                intended_outcome="Pre-existing recommendation should block restore.",
                lifecycle_state="under_review",
                reviewed_context={"reviewed_at": reviewed_at.isoformat()},
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"authoritative restore target must be empty before restore; "
                r"found existing records for .*recommendation"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)

        self.assertIsNone(restored_service.get_record(CaseRecord, promoted_case.case_id))
        self.assertIsNotNone(
            restored_service.get_record(
                RecommendationRecord, "recommendation-existing-001"
            )
        )

    def test_service_phase21_restore_fails_closed_when_analytic_signal_links_missing_alert(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        self.assertEqual(len(backup["record_families"]["analytic_signal"]), 1)
        backup["record_families"]["analytic_signal"][0]["alert_ids"] = [
            backup["record_families"]["alert"][0]["alert_id"],
            "alert-phase21-missing-analytic-signal-link-001"
        ]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "missing alert record 'alert-phase21-missing-analytic-signal-link-001' required by analytic signal",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_alert_analytic_signal_binding_mismatch(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        alert_payload = backup["record_families"]["alert"][0]
        self.assertIsNotNone(alert_payload["analytic_signal_id"])
        backup["record_families"]["analytic_signal"][0]["alert_ids"] = []

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                f"alert {alert_payload['alert_id']!r} does not match analytic signal "
                f"binding {alert_payload['analytic_signal_id']!r}"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_alert_case_binding_mismatch(self) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        original_alert_payload = dict(backup["record_families"]["alert"][0])
        mismatched_alert_payload = dict(original_alert_payload)
        mismatched_alert_payload["alert_id"] = "alert-phase21-mismatched-case-binding-001"
        mismatched_alert_payload["analytic_signal_id"] = None
        mismatched_alert_payload["case_id"] = None
        backup["record_families"]["alert"].append(mismatched_alert_payload)
        backup["record_counts"]["alert"] = len(backup["record_families"]["alert"])
        backup["record_families"]["case"][0]["alert_id"] = mismatched_alert_payload["alert_id"]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                f"alert {promoted_case.alert_id!r} does not match case binding "
                f"{promoted_case.case_id!r}"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_non_mapping_payload_fields(self) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["alert"][0]["reviewed_context"] = ["not-a-mapping"]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "alert.reviewed_context must be a JSON object in restore payload",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_approval_target_binding_mismatch(self) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
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
                approval_decision_id="approval-phase21-binding-mismatch-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["approval_decision"][0]["target_snapshot"] = {
            "record_family": "recommendation",
            "record_id": recommendation.recommendation_id,
            "case_id": promoted_case.case_id,
            "alert_id": promoted_case.alert_id,
            "finding_id": promoted_case.finding_id,
            "recipient_identity": "repo-owner-999",
        }

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "approval decision 'approval-phase21-binding-mismatch-001' does not match action request target binding",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_action_execution_surface_binding_mismatch(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
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
                approval_decision_id="approval-phase21-execution-binding-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
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
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-execution-binding-001",
                action_request_id=approved_request.action_request_id,
                approval_decision_id=approval_decision.approval_decision_id,
                delegation_id="delegation-phase21-execution-binding-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-execution-binding-001",
                idempotency_key=approved_request.idempotency_key,
                target_scope=dict(approved_request.target_scope),
                approved_payload=dict(approved_request.requested_payload),
                payload_hash=approved_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=approved_request.expires_at,
                provenance={"evidence_ids": (evidence_id,)},
                lifecycle_state="queued",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["action_execution"][0]["execution_surface_id"] = (
            "isolated-executor"
        )

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "action execution 'action-execution-phase21-execution-binding-001' does not match action request execution surface binding",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_action_execution_expiry_binding_mismatch(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
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
                approval_decision_id="approval-phase21-expiry-binding-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
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
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-expiry-binding-001",
                action_request_id=approved_request.action_request_id,
                approval_decision_id=approval_decision.approval_decision_id,
                delegation_id="delegation-phase21-expiry-binding-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-expiry-binding-001",
                idempotency_key=approved_request.idempotency_key,
                target_scope=dict(approved_request.target_scope),
                approved_payload=dict(approved_request.requested_payload),
                payload_hash=approved_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=approved_request.expires_at,
                provenance={"evidence_ids": (evidence_id,)},
                lifecycle_state="queued",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["action_execution"][0]["expires_at"] = (
            approved_request.expires_at + timedelta(minutes=5)
        ).isoformat()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "action execution 'action-execution-phase21-expiry-binding-001' does not match action request expiry binding",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_action_execution_delegation_after_approval_expiry(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
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
                approval_decision_id="approval-phase21-expiry-window-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
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
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-expiry-window-001",
                action_request_id=approved_request.action_request_id,
                approval_decision_id=approval_decision.approval_decision_id,
                delegation_id="delegation-phase21-expiry-window-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-expiry-window-001",
                idempotency_key=approved_request.idempotency_key,
                target_scope=dict(approved_request.target_scope),
                approved_payload=dict(approved_request.requested_payload),
                payload_hash=approved_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=approved_request.expires_at,
                provenance={"evidence_ids": (evidence_id,)},
                lifecycle_state="queued",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["action_execution"][0]["delegated_at"] = (
            approved_request.expires_at + timedelta(minutes=1)
        ).isoformat()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "action execution 'action-execution-phase21-expiry-window-001' exceeds approval expiry binding",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_reconciliation_run_binding_mismatch(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        primary_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        primary_decided_at = primary_request.requested_at + timedelta(minutes=1)
        primary_delegated_at = primary_request.requested_at + timedelta(minutes=2)
        primary_observed_at = primary_request.requested_at + timedelta(minutes=3)
        primary_compared_at = primary_request.requested_at + timedelta(minutes=4)
        primary_stale_after = primary_request.requested_at + timedelta(hours=1)
        primary_approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-reconciliation-primary-001",
                action_request_id=primary_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(primary_request.target_scope),
                payload_hash=primary_request.payload_hash,
                decided_at=primary_decided_at,
                lifecycle_state="approved",
                approved_expires_at=primary_request.expires_at,
            )
        )
        approved_primary_request = service.persist_record(
            replace(
                primary_request,
                approval_decision_id=primary_approval.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        primary_execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_primary_request.action_request_id,
            approved_payload=dict(approved_primary_request.requested_payload),
            delegated_at=primary_delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        primary_reconciliation = service.reconcile_action_execution(
            action_request_id=approved_primary_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": primary_execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_primary_request.idempotency_key,
                    "approval_decision_id": primary_execution.approval_decision_id,
                    "delegation_id": primary_execution.delegation_id,
                    "payload_hash": primary_execution.payload_hash,
                    "observed_at": primary_observed_at,
                    "status": "success",
                },
            ),
            compared_at=primary_compared_at,
            stale_after=primary_stale_after,
        )

        secondary_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-002",
            message_intent="Notify the backup repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at + timedelta(hours=1),
        )
        secondary_decided_at = secondary_request.requested_at + timedelta(minutes=1)
        secondary_delegated_at = secondary_request.requested_at + timedelta(minutes=2)
        secondary_approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-reconciliation-secondary-001",
                action_request_id=secondary_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(secondary_request.target_scope),
                payload_hash=secondary_request.payload_hash,
                decided_at=secondary_decided_at,
                lifecycle_state="approved",
                approved_expires_at=secondary_request.expires_at,
            )
        )
        approved_secondary_request = service.persist_record(
            replace(
                secondary_request,
                approval_decision_id=secondary_approval.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        secondary_execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_secondary_request.action_request_id,
            approved_payload=dict(approved_secondary_request.requested_payload),
            delegated_at=secondary_delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )

        backup = service.export_authoritative_record_chain_backup()
        for record in backup["record_families"]["reconciliation"]:
            if (
                record["reconciliation_id"]
                == primary_reconciliation.reconciliation_id
            ):
                record["execution_run_id"] = secondary_execution.execution_run_id
                record["linked_execution_run_ids"] = [
                    secondary_execution.execution_run_id
                ]
                break
        else:
            self.fail("expected primary reconciliation in authoritative backup")

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            f"reconciliation '{primary_reconciliation.reconciliation_id}' does not match its action execution run binding",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)
