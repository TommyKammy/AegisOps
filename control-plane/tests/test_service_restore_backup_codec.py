from __future__ import annotations

import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _restore_readiness_test_support as support

for name, value in vars(support).items():
    if not (name.startswith("__") and name.endswith("__")):
        globals()[name] = value


class RestoreBackupCodecTests(ServicePersistenceTestBase):
    def test_service_phase21_genuine_legacy_restore_round_trips_into_v2_transition_history(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["backup_schema_version"] = "phase21.authoritative-record-chain.v1"
        for family in _PHASE21_LEGACY_MISSING_AUTHORITATIVE_FAMILIES:
            del backup["record_families"][family]
            del backup["record_counts"][family]

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
        for family in _PHASE21_LEGACY_MISSING_AUTHORITATIVE_FAMILIES:
            self.assertIn(family, round_trip_backup["record_families"])
            self.assertIn(family, round_trip_backup["record_counts"])
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

    def test_service_phase21_restore_ignores_triage_timestamp_when_case_state_mismatches(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        mismatched_triage_time = datetime(2031, 1, 2, 3, 4, tzinfo=timezone.utc)
        for record in backup["record_families"]["case"]:
            if record["case_id"] != promoted_case.case_id:
                continue
            record["reviewed_context"] = {
                **dict(record["reviewed_context"]),
                "triage": {
                    "disposition": "pending_approval",
                    "closure_rationale": "Reviewed approval still pending.",
                    "recorded_at": mismatched_triage_time.isoformat(),
                },
            }

        backup["backup_schema_version"] = "phase21.authoritative-record-chain.v1"
        for family in _PHASE21_LEGACY_MISSING_AUTHORITATIVE_FAMILIES:
            del backup["record_families"][family]
            del backup["record_counts"][family]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        restored_service.restore_authoritative_record_chain_backup(backup)

        restored_case_transitions = restored_service.list_lifecycle_transitions(
            "case",
            promoted_case.case_id,
        )

        self.assertEqual(len(restored_case_transitions), 1)
        self.assertEqual(restored_case_transitions[0].lifecycle_state, "open")
        self.assertNotEqual(
            restored_case_transitions[0].transitioned_at,
            mismatched_triage_time,
        )

    def test_service_phase21_restore_rejects_non_string_record_family_keys(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"][1] = []

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            r"restore payload contains non-string record family keys: \(1,\)",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

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
        hunt = service.persist_record(
            HuntRecord(
                hunt_id="hunt-phase21-restore-001",
                hypothesis_statement="Determine whether the reviewed repository change affected additional assets.",
                hypothesis_version="v1",
                owner_identity="hunter-001",
                scope_boundary="case-scoped",
                opened_at=reviewed_at + timedelta(minutes=20),
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                lifecycle_state="draft",
            )
        )
        hunt_run = service.persist_record(
            HuntRunRecord(
                hunt_run_id="hunt-run-phase21-restore-001",
                hunt_id=hunt.hunt_id,
                scope_snapshot={"case_id": promoted_case.case_id},
                execution_plan_reference="hunt-plan-phase21-restore-001",
                output_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                started_at=reviewed_at + timedelta(minutes=25),
                completed_at=reviewed_at + timedelta(minutes=35),
                lifecycle_state="planned",
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase21-restore-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-phase21-restore-v1",
                generated_at=reviewed_at + timedelta(minutes=40),
                material_input_refs=(evidence_id,),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
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
                    "execution_surface_type": "automation_substrate",
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
            ("observation", observation.observation_id),
            backup_transition_subjects,
        )
        self.assertIn(
            ("lead", lead.lead_id),
            backup_transition_subjects,
        )
        self.assertIn(
            ("hunt", hunt.hunt_id),
            backup_transition_subjects,
        )
        self.assertIn(
            ("hunt_run", hunt_run.hunt_run_id),
            backup_transition_subjects,
        )
        self.assertIn(
            ("ai_trace", ai_trace.ai_trace_id),
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
        self.assertEqual(backup["record_counts"]["observation"], 1)
        self.assertEqual(backup["record_counts"]["lead"], 1)
        self.assertEqual(backup["record_counts"]["recommendation"], 1)
        self.assertEqual(backup["record_counts"]["hunt"], 1)
        self.assertEqual(backup["record_counts"]["hunt_run"], 1)
        self.assertEqual(backup["record_counts"]["ai_trace"], 1)
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
        self.assertEqual(
            restore_summary.restore_drill.verified_recommendation_ids,
            (recommendation.recommendation_id,),
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
            ("observation", observation.observation_id),
            restored_transition_subjects,
        )
        self.assertIn(
            ("lead", lead.lead_id),
            restored_transition_subjects,
        )
        self.assertIn(
            ("hunt", hunt.hunt_id),
            restored_transition_subjects,
        )
        self.assertIn(
            ("hunt_run", hunt_run.hunt_run_id),
            restored_transition_subjects,
        )
        self.assertIn(
            ("ai_trace", ai_trace.ai_trace_id),
            restored_transition_subjects,
        )
        self.assertIn(
            ("reconciliation", reconciliation.reconciliation_id),
            restored_transition_subjects,
        )
        self.assertIsNotNone(
            restored_service.get_record(ObservationRecord, observation.observation_id)
        )
        self.assertIsNotNone(restored_service.get_record(LeadRecord, lead.lead_id))
        self.assertIsNotNone(restored_service.get_record(HuntRecord, hunt.hunt_id))
        self.assertIsNotNone(
            restored_service.get_record(HuntRunRecord, hunt_run.hunt_run_id)
        )
        self.assertIsNotNone(
            restored_service.get_record(AITraceRecord, ai_trace.ai_trace_id)
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

    def test_service_phase21_restore_rejects_wrong_family_records_from_parser(
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
        backup_payload_codec = (
            restored_service._restore_readiness_service._backup_restore_flow._backup_payload_codec
        )
        original_parser = backup_payload_codec.record_from_backup_payload

        def wrong_family_parser(
            record_type: type[ControlPlaneRecord],
            raw_record: Mapping[str, object],
        ) -> ControlPlaneRecord:
            parsed = original_parser(record_type, raw_record)
            if record_type is CaseRecord:
                return AlertRecord(
                    alert_id="unexpected-alert-from-case-parser",
                    finding_id="finding-unexpected-alert",
                    analytic_signal_id=None,
                    case_id=None,
                    lifecycle_state="open",
                )
            return parsed

        backup_payload_codec.record_from_backup_payload = wrong_family_parser

        with self.assertRaisesRegex(
            ValueError,
            (
                r"restore payload contains unexpected record types for 'case': "
                r"\('AlertRecord',\)"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_uses_deterministic_backup_anchors_for_missing_history(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup_created_at = reviewed_at + timedelta(hours=1)
        backup["created_at"] = backup_created_at.isoformat()
        backup["backup_schema_version"] = "phase21.authoritative-record-chain.v1"
        for family in _PHASE21_LEGACY_MISSING_AUTHORITATIVE_FAMILIES:
            del backup["record_families"][family]
            del backup["record_counts"][family]

        def restore_transition_times(
            restored_now: datetime,
        ) -> tuple[datetime, datetime]:
            restored_store, _ = make_store()
            restored_service = AegisOpsControlPlaneService(
                RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
                store=restored_store,
            )
            with mock.patch(
                "aegisops_control_plane.service.datetime",
                wraps=datetime,
            ) as mocked_datetime:
                mocked_datetime.now.return_value = restored_now
                restored_service.restore_authoritative_record_chain_backup(backup)
            case_transitions = restored_service.list_lifecycle_transitions(
                "case",
                promoted_case.case_id,
            )
            alert_transitions = restored_service.list_lifecycle_transitions(
                "alert",
                promoted_case.alert_id,
            )
            self.assertEqual(len(case_transitions), 1)
            self.assertEqual(len(alert_transitions), 1)
            return (
                case_transitions[0].transitioned_at,
                alert_transitions[0].transitioned_at,
            )

        first_case_at, first_alert_at = restore_transition_times(
            datetime(2035, 1, 2, 3, 4, tzinfo=timezone.utc)
        )
        second_case_at, second_alert_at = restore_transition_times(
            datetime(2036, 2, 3, 4, 5, tzinfo=timezone.utc)
        )

        self.assertEqual(first_case_at, second_case_at)
        self.assertEqual(first_alert_at, second_alert_at)
        self.assertLessEqual(first_case_at, backup_created_at)
        self.assertLessEqual(first_alert_at, backup_created_at)

    def test_service_phase21_restore_rejects_unknown_record_family_keys(self) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["unexpected_family"] = []
        backup["record_counts"]["unexpected_count_family"] = 0

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"restore payload contains unsupported record family keys: "
                r"record_families=\['unexpected_family'\], "
                r"record_counts=\['unexpected_count_family'\]"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_non_integer_record_counts(self) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()

        for invalid_count in (True, 1.0):
            invalid_backup = copy.deepcopy(backup)
            invalid_backup["record_counts"]["recommendation"] = invalid_count

            restored_store, _ = make_store()
            restored_service = AegisOpsControlPlaneService(
                RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
                store=restored_store,
            )

            with self.subTest(invalid_count=invalid_count):
                with self.assertRaisesRegex(
                    ValueError,
                    "restore payload record count for 'recommendation' must be an integer",
                ):
                    restored_service.restore_authoritative_record_chain_backup(
                        invalid_backup
                    )
                self._assert_authoritative_store_empty(restored_store)

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

    def test_service_phase21_restore_accepts_genuine_legacy_backup_shape(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["backup_schema_version"] = "phase21.authoritative-record-chain.v1"
        for family in _PHASE21_LEGACY_MISSING_AUTHORITATIVE_FAMILIES:
            del backup["record_families"][family]
            del backup["record_counts"][family]

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
        for family in _PHASE21_LEGACY_MISSING_AUTHORITATIVE_FAMILIES:
            if family == "lifecycle_transition":
                continue
            self.assertEqual(restore_summary.restored_record_counts[family], 0)
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

    def test_service_phase21_backup_preserves_reviewed_lifecycle_families_and_transition_subjects(
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
            scope_statement="Keep reviewed observation transitions in the authoritative restore set.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Keep reviewed lead linkage in the authoritative restore set.",
            observation_id=observation.observation_id,
        )
        hunt = service.persist_record(
            HuntRecord(
                hunt_id="hunt-phase21-authoritative-001",
                hypothesis_statement="Validate whether the reviewed observation affects additional repositories.",
                hypothesis_version="v1",
                owner_identity="hunter-001",
                scope_boundary="case-scoped",
                opened_at=reviewed_at + timedelta(minutes=3),
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                lifecycle_state="draft",
            )
        )
        hunt_run = service.persist_record(
            HuntRunRecord(
                hunt_run_id="hunt-run-phase21-authoritative-001",
                hunt_id=hunt.hunt_id,
                scope_snapshot={"case_id": promoted_case.case_id},
                execution_plan_reference="hunt-plan-phase21-authoritative-001",
                output_linkage={},
                started_at=reviewed_at + timedelta(minutes=4),
                completed_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="planned",
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase21-authoritative-001",
                subject_linkage={"case_ids": (promoted_case.case_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-phase21-authoritative-v1",
                generated_at=reviewed_at + timedelta(minutes=6),
                material_input_refs=(evidence_id,),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
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
        self.assertIn(
            ("observation", observation.observation_id),
            {
                (record["subject_record_family"], record["subject_record_id"])
                for record in backup["record_families"]["lifecycle_transition"]
            },
        )
        self.assertIn(
            observation.observation_id,
            {
                record["observation_id"]
                for record in backup["record_families"]["observation"]
            },
        )
        self.assertIn(
            lead.lead_id,
            {record["lead_id"] for record in backup["record_families"]["lead"]},
        )
        self.assertIn(
            hunt.hunt_id,
            {record["hunt_id"] for record in backup["record_families"]["hunt"]},
        )
        self.assertIn(
            hunt_run.hunt_run_id,
            {
                record["hunt_run_id"]
                for record in backup["record_families"]["hunt_run"]
            },
        )
        self.assertIn(
            ai_trace.ai_trace_id,
            {record["ai_trace_id"] for record in backup["record_families"]["ai_trace"]},
        )
