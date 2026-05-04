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


class RestoreValidationTests(ServicePersistenceTestBase):
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

    def test_service_phase21_restore_rejects_invalid_new_family_record_shapes(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Keep reviewed observation linkage in the authoritative restore set.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Keep reviewed lead linkage in the authoritative restore set.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep reviewed recommendation linkage in the authoritative restore set.",
            lead_id=lead.lead_id,
        )
        backup = service.export_authoritative_record_chain_backup()
        mutated_families = (
            (
                "observation",
                observation.observation_id,
                "observation_id",
                lambda record: record.update({"supporting_evidence_ids": []}),
                (
                    rf"observation record '{observation.observation_id}' requires "
                    r"non-empty supporting_evidence_ids"
                ),
            ),
            (
                "lead",
                lead.lead_id,
                "lead_id",
                lambda record: record.update(
                    {
                        "observation_id": None,
                        "finding_id": None,
                        "hunt_run_id": None,
                    }
                ),
                (
                    rf"lead record '{lead.lead_id}' requires at least one linkage "
                    r"field: observation_id, finding_id, hunt_run_id"
                ),
            ),
            (
                "recommendation",
                recommendation.recommendation_id,
                "recommendation_id",
                lambda record: record.update(
                    {
                        "lead_id": None,
                        "hunt_run_id": None,
                        "alert_id": None,
                        "case_id": None,
                    }
                ),
                (
                    rf"recommendation record '{recommendation.recommendation_id}' "
                    r"requires at least one linkage field: lead_id, hunt_run_id, "
                    r"alert_id, case_id"
                ),
            ),
        )

        for family, record_id, id_field, mutate_record, error_pattern in mutated_families:
            with self.subTest(family=family):
                invalid_backup = copy.deepcopy(backup)
                mutated_record = next(
                    record
                    for record in invalid_backup["record_families"][family]
                    if record[id_field] == record_id
                )
                mutate_record(mutated_record)

                restored_store, _ = make_store()
                restored_service = AegisOpsControlPlaneService(
                    RuntimeConfig(
                        postgres_dsn="postgresql://control-plane.local/aegisops"
                    ),
                    store=restored_store,
                )

                with self.assertRaisesRegex(ValueError, error_pattern):
                    restored_service.restore_authoritative_record_chain_backup(
                        invalid_backup
                    )
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

    def test_service_phase21_restore_fails_closed_when_transition_repeats_prior_state(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        investigating_case = replace(
            promoted_case,
            lifecycle_state="investigating",
        )
        closed_case = replace(
            investigating_case,
            lifecycle_state="closed",
        )
        service.persist_record(investigating_case)
        service.persist_record(closed_case)
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
        self.assertEqual(len(ordered_case_transitions), 3)
        repeated_state = ordered_case_transitions[1]["previous_lifecycle_state"]
        self.assertIsNotNone(repeated_state)
        ordered_case_transitions[1]["lifecycle_state"] = repeated_state
        ordered_case_transitions[2]["previous_lifecycle_state"] = repeated_state

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                rf"lifecycle transition chain for case record '{promoted_case.case_id}' "
                r"contains no-op transition: "
                r".* previous_lifecycle_state 'open' matches lifecycle_state 'open'"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_unsupported_transition_subject_family(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        mutated_transition = dict(backup["record_families"]["lifecycle_transition"][0])
        mutated_transition["subject_record_family"] = "unsupported_family"
        mutated_transition["subject_record_id"] = "unsupported-subject-001"
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
                r"subject_record_family 'unsupported_family'"
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

    def test_service_phase21_restore_rejects_null_mapping_payload_fields(self) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["reconciliation"][0]["subject_linkage"] = None

        restored_store, _ = support.make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "reconciliation.subject_linkage must be a JSON object in restore payload",
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
                    "execution_surface_type": "automation_substrate",
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
