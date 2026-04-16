from __future__ import annotations

import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _service_persistence_support import (
    AITraceRecord,
    ActionRequestRecord,
    AegisOpsControlPlaneService,
    AlertRecord,
    AnalyticSignalRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    EvidenceRecord,
    RecommendationRecord,
    ReconciliationRecord,
    RuntimeConfig,
    ServicePersistenceTestBase,
    WazuhAlertAdapter,
    _approved_binding_hash,
    _load_wazuh_fixture,
    _phase20_notify_identity_owner_payload,
    datetime,
    make_store,
    mock,
    replace,
    timedelta,
    timezone,
)


class AssistantAdvisoryPersistenceTests(ServicePersistenceTestBase):
    def test_service_delegates_assistant_context_and_advisory_rendering_to_assembler(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        service._assistant_context_assembler = mock.Mock()
        service._assistant_context_assembler.inspect_assistant_context.return_value = (
            mock.sentinel.assistant_context_snapshot
        )
        service._assistant_context_assembler.inspect_advisory_output.return_value = (
            mock.sentinel.advisory_output_snapshot
        )
        service._assistant_context_assembler.render_recommendation_draft.return_value = (
            mock.sentinel.recommendation_draft_snapshot
        )

        self.assertIs(
            service.inspect_assistant_context("case", "case-delegated-001"),
            mock.sentinel.assistant_context_snapshot,
        )
        self.assertIs(
            service.inspect_advisory_output("case", "case-delegated-001"),
            mock.sentinel.advisory_output_snapshot,
        )
        self.assertIs(
            service.render_recommendation_draft("case", "case-delegated-001"),
            mock.sentinel.recommendation_draft_snapshot,
        )
        service._assistant_context_assembler.inspect_assistant_context.assert_called_once_with(
            "case",
            "case-delegated-001",
        )
        service._assistant_context_assembler.inspect_advisory_output.assert_called_once_with(
            "case",
            "case-delegated-001",
        )
        service._assistant_context_assembler.render_recommendation_draft.assert_called_once_with(
            "case",
            "case-delegated-001",
        )

    def test_service_routes_reviewed_slice_checks_through_policy_module(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        service._reviewed_slice_policy = mock.Mock()
        service._reviewed_slice_policy.require_operator_case.return_value = (
            mock.sentinel.case_record
        )
        service._reviewed_slice_policy.require_operator_case_record.return_value = (
            mock.sentinel.validated_case_record
        )
        service._reviewed_slice_policy.context_declares_out_of_scope_provenance.return_value = (
            True
        )
        context_snapshot = mock.sentinel.context_snapshot

        self.assertIs(
            service._require_reviewed_operator_case("case-reviewed-001"),
            mock.sentinel.case_record,
        )
        self.assertIs(
            service._require_reviewed_operator_case_record(mock.sentinel.case_record),
            mock.sentinel.validated_case_record,
        )
        service._require_reviewed_case_scoped_advisory_read(context_snapshot)
        self.assertTrue(
            service._reviewed_context_declares_out_of_scope_provenance(
                mock.sentinel.reviewed_context
            )
        )

        service._reviewed_slice_policy.require_operator_case.assert_called_once_with(
            "case-reviewed-001"
        )
        (
            service._reviewed_slice_policy.require_operator_case_record
            .assert_called_once_with(mock.sentinel.case_record)
        )
        (
            service._reviewed_slice_policy.require_case_scoped_advisory_read
            .assert_called_once_with(context_snapshot)
        )
        (
            service._reviewed_slice_policy.context_declares_out_of_scope_provenance
            .assert_called_once_with(mock.sentinel.reviewed_context)
        )

    def test_service_admits_wazuh_fixture_through_substrate_adapter_boundary(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        native_record = adapter.build_native_detection_record(
            _load_wazuh_fixture("agent-origin-alert.json")
        )

        admitted = service.ingest_native_detection_record(adapter, native_record)

        self.assertEqual(admitted.disposition, "created")
        self.assertIsNotNone(admitted.alert.analytic_signal_id)
        self.assertEqual(
            admitted.alert.finding_id,
            "finding:wazuh:rule:5710:source:agent:007:alert:1731594986.4931506",
        )
        self.assertTrue(
            admitted.alert.analytic_signal_id.startswith("analytic-signal-")
        )

        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 1)
        self.assertEqual(
            signals[0].substrate_detection_record_id,
            "wazuh:1731594986.4931506",
        )
        self.assertEqual(
            signals[0].correlation_key,
            (
                "wazuh:rule:5710:source:agent:007"
                ":location=%2Fvar%2Flog%2Fauth.log"
                ":data.srcip=198.51.100.24"
                ":data.srcuser=invalid-user"
            ),
        )
        self.assertEqual(
            signals[0].first_seen_at,
            datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            signals[0].last_seen_at,
            datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(signals[0].alert_ids, (admitted.alert.alert_id,))

        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(reconciliation.ingest_disposition, "created")
        self.assertEqual(
            reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("wazuh:1731594986.4931506",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["analytic_signal_ids"],
            (admitted.alert.analytic_signal_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "/var/log/auth.log",
                "data.srcip": "198.51.100.24",
                "data.srcuser": "invalid-user",
            },
        )
        self.assertEqual(
            reconciliation.subject_linkage["admission_provenance"],
            {
                "admission_channel": "fixture_replay",
                "admission_kind": "replay",
            },
        )
        self.assertEqual(
            admitted.alert.reviewed_context,
            {
                "location": "/var/log/auth.log",
                "data.srcip": "198.51.100.24",
                "data.srcuser": "invalid-user",
                "provenance": {
                    "admission_kind": "replay",
                    "admission_channel": "fixture_replay",
                },
            },
        )

    def test_service_preserves_reviewed_context_across_identity_centric_records(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "asset_type": "repository",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-001",
                "identity_type": "service_account",
                "aliases": ("svc-001",),
                "owner": "identity-operations",
            },
            "privilege": {
                "privilege_scope": "repository_admin",
                "delegated_authority": "reviewed",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-identity-001",
            analytic_signal_id="signal-identity-001",
            substrate_detection_record_id="substrate-detection-identity-001",
            correlation_key="claim:asset-repo-001:privilege-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-identity-001",
                source_record_id="substrate-detection-identity-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-identity-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="approve reviewed identity-sensitive follow-up",
                lifecycle_state="under_review",
                reviewed_context=reviewed_context,
            )
        )

        self.assertEqual(admitted.alert.reviewed_context, reviewed_context)
        self.assertEqual(
            service.get_record(AnalyticSignalRecord, admitted.alert.analytic_signal_id).reviewed_context,
            reviewed_context,
        )
        self.assertEqual(
            service.get_record(AlertRecord, admitted.alert.alert_id).reviewed_context,
            reviewed_context,
        )
        self.assertEqual(
            service.get_record(CaseRecord, promoted_case.case_id).reviewed_context,
            reviewed_context,
        )
        self.assertEqual(
            service.get_record(RecommendationRecord, recommendation.recommendation_id).reviewed_context,
            reviewed_context,
        )

    def test_service_exposes_analyst_assistant_context_with_linked_evidence(self) -> None:
        _, service, promoted_case, evidence_id, first_seen_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-assistant-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="follow reviewed evidence",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        colliding_recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id=promoted_case.case_id,
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-002",
                intended_outcome="keep reviewed evidence visible",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        colliding_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id=promoted_case.case_id,
                subject_linkage={
                    "alert_ids": (promoted_case.alert_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-collision-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:case-collision",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
                ingest_disposition="matched",
                mismatch_summary="case-id collision across record families",
                compared_at=first_seen_at,
                lifecycle_state="matched",
            )
        )

        snapshot = service.inspect_assistant_context("case", promoted_case.case_id)

        self.assertTrue(snapshot.read_only)
        self.assertEqual(snapshot.record_family, "case")
        self.assertEqual(snapshot.record_id, promoted_case.case_id)
        self.assertEqual(snapshot.record["case_id"], promoted_case.case_id)
        self.assertEqual(snapshot.reviewed_context, promoted_case.reviewed_context)
        self.assertEqual(snapshot.linked_evidence_ids, (evidence_id,))
        self.assertEqual(
            snapshot.linked_evidence_records[0]["evidence_id"],
            evidence_id,
        )
        self.assertEqual(
            snapshot.linked_evidence_records[0]["alert_id"],
            promoted_case.alert_id,
        )
        self.assertIn(promoted_case.alert_id, snapshot.linked_alert_ids)
        self.assertIn(
            recommendation.recommendation_id,
            snapshot.linked_recommendation_ids,
        )
        self.assertIn(
            colliding_recommendation.recommendation_id,
            snapshot.linked_recommendation_ids,
        )
        self.assertTrue(snapshot.linked_reconciliation_ids)
        self.assertIn(
            colliding_reconciliation.reconciliation_id,
            snapshot.linked_reconciliation_ids,
        )

    def test_service_exposes_citation_ready_context_for_recommendation_and_ai_trace(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-citation-001",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-citation-001",
                "owner": "identity-operations",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-citation-001",
            analytic_signal_id="signal-citation-001",
            substrate_detection_record_id="substrate-detection-citation-001",
            correlation_key="claim:asset-repo-citation-001:assistant-citation-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-citation-001",
                source_record_id="substrate-detection-citation-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-citation-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-citation-001",
                review_owner="reviewer-001",
                intended_outcome="draft advisory triage summary",
                lifecycle_state="under_review",
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-citation-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(evidence.evidence_id, recommendation.recommendation_id),
                reviewer_identity="reviewer-001",
                lifecycle_state="accepted_for_reference",
            )
        )

        recommendation_snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )
        ai_trace_snapshot = service.inspect_assistant_context("ai_trace", ai_trace.ai_trace_id)

        self.assertEqual(recommendation_snapshot.reviewed_context, reviewed_context)
        self.assertEqual(
            recommendation_snapshot.linked_evidence_ids,
            (evidence.evidence_id,),
        )
        self.assertEqual(
            recommendation_snapshot.linked_evidence_records[0]["evidence_id"],
            evidence.evidence_id,
        )
        self.assertIn(admitted.alert.alert_id, recommendation_snapshot.linked_alert_ids)
        self.assertIn(promoted_case.case_id, recommendation_snapshot.linked_case_ids)
        self.assertEqual(
            recommendation_snapshot.linked_alert_records[0]["alert_id"],
            admitted.alert.alert_id,
        )
        self.assertEqual(
            recommendation_snapshot.linked_case_records[0]["case_id"],
            promoted_case.case_id,
        )

        self.assertEqual(ai_trace_snapshot.reviewed_context, reviewed_context)
        self.assertIn(
            recommendation.recommendation_id,
            ai_trace_snapshot.linked_recommendation_ids,
        )
        self.assertIn(admitted.alert.alert_id, ai_trace_snapshot.linked_alert_ids)
        self.assertIn(promoted_case.case_id, ai_trace_snapshot.linked_case_ids)
        self.assertEqual(
            ai_trace_snapshot.linked_alert_records[0]["alert_id"],
            admitted.alert.alert_id,
        )
        self.assertEqual(
            ai_trace_snapshot.linked_case_records[0]["case_id"],
            promoted_case.case_id,
        )
        self.assertEqual(
            set(ai_trace_snapshot.linked_evidence_ids),
            {evidence.evidence_id},
        )
        self.assertEqual(
            {record["evidence_id"] for record in ai_trace_snapshot.linked_evidence_records},
            {evidence.evidence_id},
        )
        self.assertEqual(
            recommendation_snapshot.advisory_output["output_kind"],
            "recommendation_draft",
        )
        self.assertEqual(
            recommendation_snapshot.advisory_output["status"],
            "ready",
        )
        self.assertIn(
            recommendation.recommendation_id,
            recommendation_snapshot.advisory_output["citations"],
        )
        self.assertIn(
            evidence.evidence_id,
            recommendation_snapshot.advisory_output["citations"],
        )
        self.assertTrue(
            recommendation_snapshot.advisory_output["cited_summary"]["text"]
        )
        self.assertTrue(
            recommendation_snapshot.advisory_output["candidate_recommendations"]
        )
        self.assertIn(
            "advisory_only",
            recommendation_snapshot.advisory_output["uncertainty_flags"],
        )

    def test_service_projects_assistant_context_into_advisory_and_draft_views(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-projection-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        advisory_snapshot = service.inspect_advisory_output("case", promoted_case.case_id)
        recommendation_draft = service.render_recommendation_draft(
            "case",
            promoted_case.case_id,
        )

        self.assertTrue(advisory_snapshot.read_only)
        self.assertEqual(advisory_snapshot.record_family, "case")
        self.assertEqual(advisory_snapshot.record_id, promoted_case.case_id)
        self.assertEqual(advisory_snapshot.output_kind, "case_summary")
        self.assertEqual(advisory_snapshot.status, "ready")
        self.assertEqual(advisory_snapshot.reviewed_context, promoted_case.reviewed_context)
        self.assertIn(evidence_id, advisory_snapshot.citations)
        self.assertIn("advisory_only", advisory_snapshot.uncertainty_flags)
        self.assertIn(promoted_case.alert_id, advisory_snapshot.linked_alert_ids)
        self.assertEqual(advisory_snapshot.linked_evidence_ids, (evidence_id,))
        self.assertIn(
            recommendation.recommendation_id,
            advisory_snapshot.linked_recommendation_ids,
        )
        self.assertTrue(advisory_snapshot.linked_reconciliation_ids)

        self.assertTrue(recommendation_draft.read_only)
        self.assertEqual(
            recommendation_draft.recommendation_draft["source_output_kind"],
            "case_summary",
        )
        self.assertEqual(
            recommendation_draft.recommendation_draft["status"],
            "ready",
        )
        self.assertTrue(
            recommendation_draft.recommendation_draft["candidate_recommendations"]
        )
        self.assertIn(
            evidence_id,
            recommendation_draft.recommendation_draft["citations"],
        )
        self.assertIn(
            "advisory_only",
            recommendation_draft.recommendation_draft["uncertainty_flags"],
        )
        self.assertEqual(
            recommendation_draft.reviewed_context,
            promoted_case.reviewed_context,
        )
        self.assertEqual(
            recommendation_draft.linked_evidence_ids,
            (evidence_id,),
        )
        self.assertIn(
            recommendation.recommendation_id,
            recommendation_draft.linked_recommendation_ids,
        )

    def test_service_materializes_assistant_advisory_drafts_on_review_records(self) -> None:
        _, service, promoted_case, evidence_id, first_seen_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-advisory-review-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-advisory-review-001",
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-advisory-review-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(evidence_id,),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )

        attached_recommendation = service.attach_assistant_advisory_draft(
            "recommendation",
            recommendation.recommendation_id,
        )
        attached_ai_trace = service.attach_assistant_advisory_draft(
            "ai_trace",
            ai_trace.ai_trace_id,
        )

        self.assertEqual(
            attached_recommendation.assistant_advisory_draft["draft_id"],
            "assistant-advisory-draft:recommendation:recommendation-advisory-review-001",
        )
        self.assertEqual(
            attached_recommendation.assistant_advisory_draft["source_record_family"],
            "recommendation",
        )
        self.assertEqual(
            attached_recommendation.assistant_advisory_draft["source_record_id"],
            recommendation.recommendation_id,
        )
        self.assertEqual(
            attached_recommendation.assistant_advisory_draft["review_lifecycle_state"],
            "under_review",
        )
        self.assertEqual(
            attached_recommendation.assistant_advisory_draft["status"],
            "ready",
        )
        self.assertIn(
            evidence_id,
            attached_recommendation.assistant_advisory_draft["citations"],
        )

        self.assertEqual(
            attached_ai_trace.assistant_advisory_draft["draft_id"],
            "assistant-advisory-draft:ai_trace:ai-trace-advisory-review-001",
        )
        self.assertEqual(
            attached_ai_trace.assistant_advisory_draft["source_record_family"],
            "ai_trace",
        )
        self.assertEqual(
            attached_ai_trace.assistant_advisory_draft["source_record_id"],
            ai_trace.ai_trace_id,
        )
        self.assertEqual(
            attached_ai_trace.assistant_advisory_draft["review_lifecycle_state"],
            "under_review",
        )
        self.assertIn(
            recommendation.recommendation_id,
            attached_ai_trace.assistant_advisory_draft["citations"],
        )

        accepted_recommendation = service.persist_record(
            replace(attached_recommendation, lifecycle_state="accepted")
        )
        rejected_ai_trace = service.persist_record(
            replace(attached_ai_trace, lifecycle_state="rejected_for_reference")
        )

        self.assertEqual(
            accepted_recommendation.assistant_advisory_draft["review_lifecycle_state"],
            "under_review",
        )
        self.assertEqual(
            rejected_ai_trace.assistant_advisory_draft["review_lifecycle_state"],
            "under_review",
        )
        self.assertEqual(
            service.get_record(
                RecommendationRecord,
                recommendation.recommendation_id,
            ).assistant_advisory_draft["draft_id"],
            "assistant-advisory-draft:recommendation:recommendation-advisory-review-001",
        )
        self.assertEqual(
            service.get_record(
                AITraceRecord,
                ai_trace.ai_trace_id,
            ).assistant_advisory_draft["draft_id"],
            "assistant-advisory-draft:ai_trace:ai-trace-advisory-review-001",
        )

    def test_service_preserves_prior_assistant_advisory_draft_revisions_on_repeat_attachment(
        self,
    ) -> None:
        _, service, promoted_case, _, first_seen_at = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-advisory-history-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the draft history",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        initial_attachment = service.attach_assistant_advisory_draft(
            "recommendation",
            recommendation.recommendation_id,
        )
        initial_snapshot = dict(initial_attachment.assistant_advisory_draft)

        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-advisory-history-001",
                source_record_id="artifact-advisory-history-001",
                alert_id=recommendation.alert_id,
                case_id=recommendation.case_id,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="original",
                lifecycle_state="collected",
            )
        )

        updated_attachment = service.attach_assistant_advisory_draft(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertIn(
            evidence.evidence_id,
            updated_attachment.assistant_advisory_draft["citations"],
        )
        self.assertEqual(
            updated_attachment.assistant_advisory_draft["revision_history"][0],
            initial_snapshot,
        )

    def test_service_renders_recommendation_draft_with_current_review_outcome(self) -> None:
        _, service, promoted_case, evidence_id, first_seen_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-advisory-render-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-advisory-render-001",
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-advisory-render-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(evidence_id,),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )

        recommendation_under_review = service.render_recommendation_draft(
            "recommendation",
            recommendation.recommendation_id,
        )
        ai_trace_under_review = service.render_recommendation_draft(
            "ai_trace",
            ai_trace.ai_trace_id,
        )

        self.assertIn(
            "remains under review",
            recommendation_under_review.recommendation_draft["cited_summary"]["text"],
        )
        self.assertIn(
            "remains under review",
            ai_trace_under_review.recommendation_draft["cited_summary"]["text"],
        )

        accepted_recommendation = service.persist_record(
            replace(recommendation, lifecycle_state="accepted")
        )
        rejected_ai_trace = service.persist_record(
            replace(ai_trace, lifecycle_state="rejected_for_reference")
        )

        accepted_recommendation_draft = service.render_recommendation_draft(
            "recommendation",
            accepted_recommendation.recommendation_id,
        )
        rejected_ai_trace_draft = service.render_recommendation_draft(
            "ai_trace",
            rejected_ai_trace.ai_trace_id,
        )

        self.assertIn(
            "has been accepted and is anchored",
            accepted_recommendation_draft.recommendation_draft["cited_summary"]["text"],
        )
        self.assertEqual(
            accepted_recommendation_draft.recommendation_draft["review_lifecycle_state"],
            "accepted",
        )
        self.assertNotIn(
            "remains under review",
            accepted_recommendation_draft.recommendation_draft["cited_summary"]["text"],
        )
        self.assertIn(
            "has been rejected for reference",
            rejected_ai_trace_draft.recommendation_draft["cited_summary"]["text"],
        )
        self.assertEqual(
            rejected_ai_trace_draft.recommendation_draft["review_lifecycle_state"],
            "rejected_for_reference",
        )
        self.assertNotIn(
            "remains under review",
            rejected_ai_trace_draft.recommendation_draft["cited_summary"]["text"],
        )

    def test_service_rejects_case_scoped_advisory_reads_without_linked_case(
        self,
    ) -> None:
        service, recommendation, ai_trace = (
            self._build_case_scoped_advisory_records_without_case_lineage()
        )

        for record_family, record_id in (
            ("recommendation", recommendation.recommendation_id),
            ("ai_trace", ai_trace.ai_trace_id),
        ):
            with self.subTest(record_family=record_family):
                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.inspect_advisory_output(record_family, record_id)

                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.render_recommendation_draft(record_family, record_id)

    def test_service_includes_evidence_derived_recommendations_in_ai_trace_context(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {"asset_id": "asset-ai-trace-evidence-001"},
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-ai-trace-evidence-001",
            analytic_signal_id="signal-ai-trace-evidence-001",
            substrate_detection_record_id="substrate-detection-ai-trace-evidence-001",
            correlation_key="claim:ai-trace:evidence:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-ai-trace-evidence-001",
                source_record_id="substrate-detection-ai-trace-evidence-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="detached_review_input",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-ai-trace-evidence-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="use evidence-derived lineage",
                lifecycle_state="under_review",
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-evidence-001",
                subject_linkage={
                    "evidence_ids": (evidence.evidence_id,),
                },
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(evidence.evidence_id,),
                reviewer_identity="reviewer-001",
                lifecycle_state="accepted_for_reference",
            )
        )

        snapshot = service.inspect_assistant_context("ai_trace", ai_trace.ai_trace_id)

        self.assertIn(recommendation.recommendation_id, snapshot.linked_recommendation_ids)
        self.assertEqual(snapshot.reviewed_context, reviewed_context)
        self.assertIn(admitted.alert.alert_id, snapshot.linked_alert_ids)
        self.assertIn(promoted_case.case_id, snapshot.linked_case_ids)
        self.assertEqual(
            snapshot.linked_alert_records[0]["alert_id"],
            admitted.alert.alert_id,
        )
        self.assertEqual(
            snapshot.linked_case_records[0]["case_id"],
            promoted_case.case_id,
        )
        self.assertEqual(
            {record["evidence_id"] for record in snapshot.linked_evidence_records},
            {evidence.evidence_id},
        )

    def test_service_fails_closed_when_reviewed_context_is_internally_inconsistent(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-conflict-001",
            analytic_signal_id="signal-conflict-001",
            substrate_detection_record_id="substrate-detection-conflict-001",
            correlation_key="claim:conflict:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={
                "asset": {"asset_id": "asset-reviewed-001"},
            },
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-conflict-001",
                source_record_id="substrate-detection-conflict-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-conflict-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the conflicting identifiers",
                lifecycle_state="under_review",
                reviewed_context={
                    "asset": {"asset_id": "asset-reviewed-999"},
                },
            )
        )

        snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertEqual(snapshot.linked_evidence_ids, (evidence.evidence_id,))
        self.assertEqual(snapshot.advisory_output["status"], "unresolved")
        self.assertIn(
            "conflicting_reviewed_context",
            snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertIn(
            "asset.asset_id",
            snapshot.advisory_output["unresolved_questions"][0]["text"],
        )

    def test_service_fails_closed_when_identity_context_is_alias_only(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-alias-only-001",
            analytic_signal_id="signal-alias-only-001",
            substrate_detection_record_id="substrate-detection-alias-only-001",
            correlation_key="claim:alias-only:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={
                "identity": {
                    "aliases": ("svc-prod-shared",),
                },
            },
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-alias-only-001",
                source_record_id="substrate-detection-alias-only-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-alias-only-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited identity lineage",
                lifecycle_state="under_review",
                reviewed_context={
                    "identity": {
                        "aliases": ("svc-prod-shared",),
                    },
                },
            )
        )

        snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertEqual(snapshot.advisory_output["status"], "unresolved")
        self.assertIn(
            "ambiguous_identity_alias_only",
            snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertTrue(
            any(
                "stable identity identifier" in question.get("text", "")
                for question in snapshot.advisory_output["unresolved_questions"]
            )
        )

    def test_service_fails_closed_when_recommendation_text_claims_authority_or_scope_expansion(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-overreach-001",
            analytic_signal_id="signal-overreach-001",
            substrate_detection_record_id="substrate-detection-overreach-001",
            correlation_key="claim:overreach:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={
                "asset": {"asset_id": "asset-overreach-001"},
                "identity": {"identity_id": "principal-overreach-001"},
            },
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-overreach-001",
                source_record_id="substrate-detection-overreach-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-overreach-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome=(
                    "Approval granted to execute tenant-wide containment and reconcile "
                    "the incident as closed."
                ),
                lifecycle_state="under_review",
            )
        )

        snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertEqual(snapshot.linked_evidence_ids, (evidence.evidence_id,))
        self.assertEqual(snapshot.advisory_output["status"], "unresolved")
        self.assertIn(
            "authority_overreach",
            snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertIn(
            "scope_expansion_attempt",
            snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertTrue(
            all(
                "Approval granted" not in candidate.get("text", "")
                for candidate in snapshot.advisory_output.get(
                    "candidate_recommendations",
                    (),
                )
            )
        )

    def test_service_does_not_treat_unresolved_as_resolution_authority(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-unresolved-001",
            analytic_signal_id="signal-unresolved-001",
            substrate_detection_record_id="substrate-detection-unresolved-001",
            correlation_key="claim:unresolved:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={
                "asset": {"asset_id": "asset-unresolved-001"},
                "identity": {"identity_id": "principal-unresolved-001"},
            },
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-unresolved-001",
                source_record_id="substrate-detection-unresolved-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-unresolved-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="keep unresolved evidence visible",
                lifecycle_state="under_review",
            )
        )

        snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertEqual(snapshot.advisory_output["status"], "ready")
        self.assertNotIn(
            "authority_overreach",
            snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertTrue(
            any(
                "keep unresolved evidence visible" in candidate.get("text", "")
                for candidate in snapshot.advisory_output["candidate_recommendations"]
            )
        )

    def test_service_keeps_anchored_recommendation_context_from_absorbing_sibling_anchors(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        first_admitted = service.ingest_finding_alert(
            finding_id="finding-anchored-001",
            analytic_signal_id="signal-anchored-001",
            substrate_detection_record_id="substrate-detection-anchored-001",
            correlation_key="claim:anchored:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={"asset": {"asset_id": "asset-anchored-001"}},
        )
        first_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-anchored-001",
                source_record_id="substrate-detection-anchored-001",
                alert_id=first_admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        first_case = service.promote_alert_to_case(first_admitted.alert.alert_id)
        anchored_recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-anchored-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=first_admitted.alert.alert_id,
                case_id=first_case.case_id,
                ai_trace_id="ai-trace-shared-001",
                review_owner="reviewer-001",
                intended_outcome="keep the anchored context narrow",
                lifecycle_state="under_review",
            )
        )

        second_admitted = service.ingest_finding_alert(
            finding_id="finding-anchored-002",
            analytic_signal_id="signal-anchored-002",
            substrate_detection_record_id="substrate-detection-anchored-002",
            correlation_key="claim:anchored:002",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={"asset": {"asset_id": "asset-anchored-002"}},
        )
        second_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-anchored-002",
                source_record_id="substrate-detection-anchored-002",
                alert_id=second_admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        second_case = service.promote_alert_to_case(second_admitted.alert.alert_id)
        sibling_recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-anchored-002",
                lead_id=None,
                hunt_run_id=None,
                alert_id=second_admitted.alert.alert_id,
                case_id=second_case.case_id,
                ai_trace_id="ai-trace-shared-001",
                review_owner="reviewer-002",
                intended_outcome="different anchored lineage",
                lifecycle_state="under_review",
            )
        )

        snapshot = service.inspect_assistant_context(
            "recommendation",
            anchored_recommendation.recommendation_id,
        )

        self.assertIn(first_admitted.alert.alert_id, snapshot.linked_alert_ids)
        self.assertIn(first_case.case_id, snapshot.linked_case_ids)
        self.assertEqual(
            snapshot.linked_evidence_ids,
            (first_evidence.evidence_id,),
        )
        self.assertIn(
            sibling_recommendation.recommendation_id,
            snapshot.linked_recommendation_ids,
        )
        self.assertNotIn(
            anchored_recommendation.recommendation_id,
            snapshot.linked_recommendation_ids,
        )
        self.assertNotIn(second_admitted.alert.alert_id, snapshot.linked_alert_ids)
        self.assertNotIn(second_case.case_id, snapshot.linked_case_ids)
        self.assertNotIn(second_evidence.evidence_id, snapshot.linked_evidence_ids)

    def test_service_uses_ai_trace_subject_linkage_and_material_inputs_for_citation_context(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-ai-trace-001",
            analytic_signal_id="signal-ai-trace-001",
            substrate_detection_record_id="substrate-detection-ai-trace-001",
            correlation_key="claim:ai-trace:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={"asset": {"asset_id": "asset-ai-trace-001"}},
        )
        detached_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-ai-trace-001",
                source_record_id="substrate-detection-ai-trace-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="detached_review_input",
                lifecycle_state="collected",
            )
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-ai-trace-001",
                lead_id="lead-ai-trace-001",
                hunt_run_id=None,
                alert_id=None,
                case_id=None,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="use detached evidence in advisory context",
                lifecycle_state="under_review",
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-001",
                subject_linkage={
                    "recommendation_ids": (recommendation.recommendation_id,),
                    "evidence_ids": (detached_evidence.evidence_id,),
                },
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(detached_evidence.evidence_id,),
                reviewer_identity="reviewer-001",
                lifecycle_state="accepted_for_reference",
            )
        )

        snapshot = service.inspect_assistant_context("ai_trace", ai_trace.ai_trace_id)

        self.assertIn(recommendation.recommendation_id, snapshot.linked_recommendation_ids)
        self.assertEqual(
            snapshot.linked_evidence_ids,
            (detached_evidence.evidence_id,),
        )
        self.assertEqual(
            snapshot.linked_evidence_records[0]["evidence_id"],
            detached_evidence.evidence_id,
        )

    def test_service_exposes_assistant_context_for_action_approvals_and_executions(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-approval-001",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-approval-001",
                "owner": "identity-operations",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-assistant-approval-001",
            analytic_signal_id="signal-assistant-approval-001",
            substrate_detection_record_id="substrate-detection-assistant-approval-001",
            correlation_key="claim:asset-repo-approval-001:assistant-approval-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-assistant-approval-001",
                source_record_id="substrate-detection-assistant-approval-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-assistant-approval-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="follow reviewed evidence",
                lifecycle_state="under_review",
                reviewed_context=reviewed_context,
            )
        )
        approval_target_scope = {"asset_id": "asset-repo-approval-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id=promoted_case.case_id,
            alert_id=admitted.alert.alert_id,
            finding_id=admitted.alert.finding_id,
            source_record_id=recommendation.recommendation_id,
            recommendation_id=recommendation.recommendation_id,
            linked_evidence_ids=(evidence.evidence_id,),
        )
        payload_hash = _approved_binding_hash(
            target_scope=approval_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-assistant-approval-001",
                action_request_id="action-request-assistant-approval-001",
                approver_identities=("approver-001",),
                target_snapshot=approval_target_scope,
                payload_hash=payload_hash,
                decided_at=first_seen_at,
                lifecycle_state="approved",
            )
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-assistant-approval-001",
                approval_decision_id=approval_decision.approval_decision_id,
                case_id=promoted_case.case_id,
                alert_id=admitted.alert.alert_id,
                finding_id=admitted.alert.finding_id,
                idempotency_key="idempotency-assistant-approval-001",
                target_scope=approval_target_scope,
                payload_hash=payload_hash,
                requested_at=first_seen_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=action_request.action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-assistant-approval-missing-001",),
        )

        approval_snapshot = service.inspect_assistant_context(
            "approval_decision",
            approval_decision.approval_decision_id,
        )
        execution_snapshot = service.inspect_assistant_context(
            "action_execution",
            execution.action_execution_id,
        )
        action_request_snapshot = service.inspect_assistant_context(
            "action_request",
            action_request.action_request_id,
        )
        reconciliation_snapshot = service.inspect_assistant_context(
            "reconciliation",
            admitted.reconciliation.reconciliation_id,
        )

        self.assertTrue(approval_snapshot.read_only)
        self.assertEqual(approval_snapshot.linked_alert_ids, (admitted.alert.alert_id,))
        self.assertEqual(approval_snapshot.linked_case_ids, (promoted_case.case_id,))
        self.assertEqual(approval_snapshot.linked_evidence_ids, (evidence.evidence_id,))
        self.assertEqual(
            approval_snapshot.linked_evidence_records[0]["evidence_id"],
            evidence.evidence_id,
        )
        self.assertIn(
            recommendation.recommendation_id,
            approval_snapshot.linked_recommendation_ids,
        )
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            approval_snapshot.linked_reconciliation_ids,
        )
        self.assertEqual(approval_snapshot.reviewed_context, reviewed_context)
        self.assertEqual(action_request_snapshot.reviewed_context, reviewed_context)

        self.assertTrue(execution_snapshot.read_only)
        self.assertEqual(execution_snapshot.reviewed_context, reviewed_context)
        self.assertEqual(execution_snapshot.linked_alert_ids, (admitted.alert.alert_id,))
        self.assertEqual(execution_snapshot.linked_case_ids, (promoted_case.case_id,))
        self.assertEqual(
            execution_snapshot.linked_evidence_ids,
            (
                "evidence-assistant-approval-missing-001",
                evidence.evidence_id,
            ),
        )
        self.assertEqual(len(execution_snapshot.linked_evidence_records), 1)
        self.assertEqual(
            execution_snapshot.linked_evidence_records[0]["evidence_id"],
            evidence.evidence_id,
        )
        self.assertIn(
            recommendation.recommendation_id,
            execution_snapshot.linked_recommendation_ids,
        )
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            execution_snapshot.linked_reconciliation_ids,
        )
        self.assertEqual(reconciliation_snapshot.reviewed_context, reviewed_context)

    def test_service_includes_lifecycle_transition_history_in_generic_assistant_context(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        alert = service.get_record(AlertRecord, promoted_case.alert_id)
        self.assertIsNotNone(alert)

        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep the reviewed workflow aligned with operator history.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="owner-001",
            message_intent="Notify the accountable owner.",
            escalation_reason="Reviewed response requires prompt owner contact.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-assistant-transitions-001",
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-decision-assistant-transitions-001",
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
        reconciliation = next(
            record
            for record in store.list(ReconciliationRecord)
            if record.alert_id == promoted_case.alert_id
            and record.finding_id == alert.finding_id
        )

        subject_ids = {
            "recommendation": recommendation.recommendation_id,
            "action_request": approved_request.action_request_id,
            "approval_decision": approval_decision.approval_decision_id,
            "action_execution": execution.action_execution_id,
            "reconciliation": reconciliation.reconciliation_id,
        }

        for family, record_id in subject_ids.items():
            snapshot = service.inspect_assistant_context(family, record_id)
            self.assertEqual(
                [entry["lifecycle_state"] for entry in snapshot.lifecycle_transitions],
                [
                    transition.lifecycle_state
                    for transition in service.list_lifecycle_transitions(
                        family,
                        record_id,
                    )
                ],
            )
            self.assertEqual(
                snapshot.lifecycle_transitions[-1]["lifecycle_state"],
                snapshot.record["lifecycle_state"],
            )

    def test_service_matches_reconciliations_via_direct_action_linkage(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-reconciliation-001",
                "ownership": "platform-security",
            },
            "identity": {
                "identity_id": "principal-reconciliation-001",
                "owner": "identity-operations",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-assistant-reconciliation-001",
            analytic_signal_id="signal-assistant-reconciliation-001",
            substrate_detection_record_id="substrate-detection-assistant-reconciliation-001",
            correlation_key="claim:asset-repo-reconciliation-001:assistant-reconciliation-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-assistant-reconciliation-001",
                source_record_id="substrate-detection-assistant-reconciliation-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-assistant-reconciliation-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="follow reviewed evidence",
                lifecycle_state="under_review",
                reviewed_context=reviewed_context,
            )
        )
        approval_target_scope = {"asset_id": "asset-repo-reconciliation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id=promoted_case.case_id,
            alert_id=admitted.alert.alert_id,
            finding_id=admitted.alert.finding_id,
            source_record_id=recommendation.recommendation_id,
            recommendation_id=recommendation.recommendation_id,
            linked_evidence_ids=("evidence-assistant-reconciliation-001",),
        )
        payload_hash = _approved_binding_hash(
            target_scope=approval_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-assistant-reconciliation-001",
                action_request_id="action-request-assistant-reconciliation-001",
                approver_identities=("approver-001",),
                target_snapshot=approval_target_scope,
                payload_hash=payload_hash,
                decided_at=first_seen_at,
                lifecycle_state="approved",
            )
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-assistant-reconciliation-001",
                approval_decision_id=approval_decision.approval_decision_id,
                case_id=promoted_case.case_id,
                alert_id=admitted.alert.alert_id,
                finding_id=admitted.alert.finding_id,
                idempotency_key="idempotency-assistant-reconciliation-001",
                target_scope=approval_target_scope,
                payload_hash=payload_hash,
                requested_at=first_seen_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=action_request.action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-assistant-reconciliation-missing-001",),
        )

        action_request_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-action-request-001",
                subject_linkage={
                    "action_request_ids": (action_request.action_request_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-action-request-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:action-request",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="direct action request linkage",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        approval_decision_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-approval-decision-001",
                subject_linkage={
                    "approval_decision_ids": (approval_decision.approval_decision_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-approval-decision-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:approval-decision",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="direct approval decision linkage",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        action_execution_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-action-execution-001",
                subject_linkage={
                    "action_execution_ids": (execution.action_execution_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-action-execution-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:action-execution",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="direct action execution linkage",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        delegation_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-delegation-001",
                subject_linkage={
                    "delegation_ids": (execution.delegation_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-delegation-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:delegation",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="direct delegation linkage",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        subject_alert_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-subject-alert-001",
                subject_linkage={
                    "alert_ids": (admitted.alert.alert_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-subject-alert-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:subject-alert",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="subject-linkage alert association",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        subject_analytic_signal_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-subject-signal-001",
                subject_linkage={
                    "analytic_signal_ids": (admitted.alert.analytic_signal_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-subject-signal-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:subject-signal",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="subject-linkage analytic signal association",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        subject_finding_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-subject-finding-001",
                subject_linkage={
                    "finding_ids": (admitted.alert.finding_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-subject-finding-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:subject-finding",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="subject-linkage finding association",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )

        execution_snapshot = service.inspect_assistant_context(
            "action_execution",
            execution.action_execution_id,
        )
        alert_snapshot = service.inspect_assistant_context("alert", admitted.alert.alert_id)

        self.assertIn(
            action_request_reconciliation.reconciliation_id,
            execution_snapshot.linked_reconciliation_ids,
        )
        self.assertIn(
            approval_decision_reconciliation.reconciliation_id,
            execution_snapshot.linked_reconciliation_ids,
        )
        self.assertIn(
            action_execution_reconciliation.reconciliation_id,
            execution_snapshot.linked_reconciliation_ids,
        )
        self.assertIn(
            delegation_reconciliation.reconciliation_id,
            execution_snapshot.linked_reconciliation_ids,
        )
        self.assertIn(
            subject_alert_reconciliation.reconciliation_id,
            alert_snapshot.linked_reconciliation_ids,
        )
        self.assertIn(
            subject_analytic_signal_reconciliation.reconciliation_id,
            alert_snapshot.linked_reconciliation_ids,
        )

        subject_alert_snapshot = service.inspect_assistant_context(
            "reconciliation",
            subject_alert_reconciliation.reconciliation_id,
        )
        subject_signal_snapshot = service.inspect_assistant_context(
            "reconciliation",
            subject_analytic_signal_reconciliation.reconciliation_id,
        )

        self.assertEqual(
            subject_alert_snapshot.linked_alert_ids,
            (admitted.alert.alert_id,),
        )
        self.assertIn(
            recommendation.recommendation_id,
            subject_alert_snapshot.linked_recommendation_ids,
        )
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            subject_alert_snapshot.linked_reconciliation_ids,
        )
        self.assertEqual(
            subject_alert_snapshot.linked_case_ids,
            (promoted_case.case_id,),
        )
        self.assertIn(
            subject_finding_reconciliation.reconciliation_id,
            subject_alert_snapshot.linked_reconciliation_ids,
        )
        self.assertEqual(subject_alert_snapshot.reviewed_context, reviewed_context)

        self.assertEqual(
            subject_signal_snapshot.linked_alert_ids,
            (admitted.alert.alert_id,),
        )
        self.assertEqual(
            subject_signal_snapshot.linked_case_ids,
            (promoted_case.case_id,),
        )
        self.assertIn(
            recommendation.recommendation_id,
            subject_signal_snapshot.linked_recommendation_ids,
        )
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            subject_signal_snapshot.linked_reconciliation_ids,
        )
        self.assertEqual(subject_signal_snapshot.reviewed_context, reviewed_context)

    def test_service_renders_reconciliation_assistant_context_for_isolated_executor_lineage(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 12, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-isolated-001",
                "ownership": "platform-security",
            },
            "identity": {
                "identity_id": "principal-isolated-001",
                "owner": "identity-operations",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-assistant-isolated-001",
            analytic_signal_id="signal-assistant-isolated-001",
            substrate_detection_record_id="substrate-detection-assistant-isolated-001",
            correlation_key="claim:asset-repo-isolated-001:assistant-isolated-review",
            first_seen_at=requested_at,
            last_seen_at=requested_at,
            reviewed_context=reviewed_context,
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-assistant-isolated-001",
                source_record_id="substrate-detection-assistant-isolated-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=requested_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        approval_target_scope = {"asset_id": "critical-host-003"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-003",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approval_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-isolated-lineage-001",
                action_request_id="action-request-isolated-lineage-001",
                approver_identities=("approver-001",),
                target_snapshot=approval_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-isolated-lineage-001",
                approval_decision_id=approval_decision.approval_decision_id,
                case_id=promoted_case.case_id,
                alert_id=admitted.alert.alert_id,
                finding_id=admitted.alert.finding_id,
                idempotency_key="idempotency-isolated-lineage-001",
                target_scope=approval_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        execution = service.delegate_approved_action_to_isolated_executor(
            action_request_id=action_request.action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-assistant-isolated-missing-001",),
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=action_request.action_request_id,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "isolated-executor",
                    "idempotency_key": execution.idempotency_key,
                    "observed_at": compared_at,
                    "status": "failed",
                },
            ),
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )
        delegation_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-isolated-delegation-001",
                subject_linkage={
                    "delegation_ids": (execution.delegation_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-isolated-delegation-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:isolated-delegation",
                first_seen_at=requested_at,
                last_seen_at=compared_at,
                ingest_disposition="matched",
                mismatch_summary="direct delegation linkage",
                compared_at=compared_at,
                lifecycle_state="matched",
            )
        )

        snapshot = service.inspect_assistant_context(
            "reconciliation",
            reconciliation.reconciliation_id,
        )

        self.assertEqual(
            reconciliation.subject_linkage["delegation_ids"],
            (execution.delegation_id,),
        )
        self.assertEqual(snapshot.linked_alert_ids, (admitted.alert.alert_id,))
        self.assertEqual(snapshot.linked_case_ids, (promoted_case.case_id,))
        self.assertEqual(snapshot.reviewed_context, reviewed_context)
        self.assertIn(
            delegation_reconciliation.reconciliation_id,
            snapshot.linked_reconciliation_ids,
        )
        self.assertNotIn(
            reconciliation.reconciliation_id,
            snapshot.linked_reconciliation_ids,
        )

    def test_service_preserves_declared_missing_evidence_ids_in_assistant_context(
        self,
    ) -> None:
        _, service, case, evidence_id, _ = self._build_phase19_in_scope_case()
        case = service.persist_record(
            replace(
                case,
                evidence_ids=(
                    "evidence-assistant-missing-001",
                    evidence_id,
                ),
            )
        )

        snapshot = service.inspect_assistant_context("case", case.case_id)

        self.assertEqual(
            snapshot.linked_evidence_ids,
            (
                "evidence-assistant-missing-001",
                evidence_id,
            ),
        )
        self.assertEqual(len(snapshot.linked_evidence_records), 1)
        self.assertEqual(
            snapshot.linked_evidence_records[0]["evidence_id"],
            evidence_id,
        )
