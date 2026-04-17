from __future__ import annotations

from dataclasses import replace
import pathlib
import sys
from unittest import mock


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _service_persistence_support import (
    AITraceRecord,
    RecommendationRecord,
    ServicePersistenceTestBase,
)
from aegisops_control_plane.assistant_provider import (
    AssistantProviderAdapter,
    AssistantProviderResult,
)
from aegisops_control_plane.service import _phase24_live_assistant_citations_from_context


class Phase24LiveAssistantFeedbackLoopValidationTests(ServicePersistenceTestBase):
    def test_live_assistant_workflow_persists_reviewable_feedback_loop_records(self) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        service._assistant_provider_adapter = mock.Mock()
        service._assistant_provider_adapter.generate.return_value = AssistantProviderResult(
            status="ready",
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            workflow_family="first_live_assistant_summary_family",
            workflow_task="case_summary",
            generated_at=reviewed_at,
            reviewed_input_refs=(promoted_case.case_id, promoted_case.alert_id, evidence_id),
            output_text="Reviewed case scope remains bounded to the cited evidence.",
            attempt_count=1,
            request_provenance={
                "memory_policy": "no_memory",
                "request_metadata": {
                    "record_family": "case",
                    "record_id": promoted_case.case_id,
                },
            },
            response_provenance={
                "provider_response_id": "provider-response-feedback-loop-001",
                "provider_transcript_id": "provider-transcript-feedback-loop-001",
                "model_version": "model-version-2026-04-17",
            },
            failures=(),
            failure_summary=None,
        )
        provider_adapter = AssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            request_timeout_seconds=5.0,
            max_attempts=1,
            transport=mock.Mock(),
        )
        service._assistant_provider_adapter.build_ai_trace_record.side_effect = (
            provider_adapter.build_ai_trace_record
        )

        snapshot = service.run_live_assistant_workflow(
            workflow_task="case_summary",
            record_family="case",
            record_id=promoted_case.case_id,
        )

        self.assertEqual(snapshot.status, "ready")

        ai_traces = store.list(AITraceRecord)
        self.assertEqual(len(ai_traces), 1)
        ai_trace = ai_traces[0]
        self.assertEqual(
            ai_trace.subject_linkage["source_record_family"],
            "case",
        )
        self.assertEqual(
            ai_trace.subject_linkage["source_record_id"],
            promoted_case.case_id,
        )

        recommendations = store.list(RecommendationRecord)
        self.assertEqual(len(recommendations), 1)
        recommendation = recommendations[0]
        self.assertEqual(recommendation.ai_trace_id, ai_trace.ai_trace_id)
        self.assertEqual(recommendation.case_id, promoted_case.case_id)
        self.assertEqual(recommendation.alert_id, promoted_case.alert_id)
        self.assertEqual(recommendation.lifecycle_state, "under_review")
        self.assertEqual(
            recommendation.assistant_advisory_draft["status"],
            "ready",
        )
        self.assertEqual(
            recommendation.assistant_advisory_draft["cited_summary"]["text"],
            "Reviewed case scope remains bounded to the cited evidence.",
        )

    def test_live_assistant_workflow_preserves_unresolved_feedback_loop_records(self) -> None:
        store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        service._assistant_provider_adapter = mock.Mock()
        service._assistant_provider_adapter.generate.side_effect = RuntimeError(
            "provider transport failed"
        )

        provider_adapter = AssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            request_timeout_seconds=5.0,
            max_attempts=1,
            transport=mock.Mock(),
        )
        service._assistant_provider_adapter.build_ai_trace_record.side_effect = (
            provider_adapter.build_ai_trace_record
        )

        snapshot = service.run_live_assistant_workflow(
            workflow_task="case_summary",
            record_family="case",
            record_id=promoted_case.case_id,
        )

        self.assertEqual(snapshot.status, "unresolved")

        ai_traces = store.list(AITraceRecord)
        self.assertEqual(len(ai_traces), 1)
        recommendations = store.list(RecommendationRecord)
        self.assertEqual(len(recommendations), 1)

        ai_trace = ai_traces[0]
        recommendation = recommendations[0]
        self.assertEqual(ai_trace.lifecycle_state, "under_review")
        self.assertEqual(recommendation.ai_trace_id, ai_trace.ai_trace_id)
        self.assertEqual(recommendation.lifecycle_state, "under_review")
        self.assertEqual(
            recommendation.assistant_advisory_draft["status"],
            "unresolved",
        )
        self.assertIn(
            "reviewed retry budget",
            recommendation.assistant_advisory_draft["unresolved_reasons"][0],
        )

    def test_live_assistant_workflow_persists_already_unresolved_advisory_feedback_loop(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        context_snapshot = service.inspect_assistant_context(
            "case",
            promoted_case.case_id,
        )
        expected_summary = (
            "Reviewed case summary remains unresolved until cited evidence is expanded."
        )
        unresolved_context = replace(
            context_snapshot,
            advisory_output={
                **dict(context_snapshot.advisory_output),
                "status": "unresolved",
                "cited_summary": {
                    "text": expected_summary,
                    "citations": (promoted_case.case_id,),
                },
                "uncertainty_flags": ("missing_supporting_citations",),
            },
        )
        expected_citations = _phase24_live_assistant_citations_from_context(
            unresolved_context
        )
        service._assistant_provider_adapter = mock.Mock()

        with mock.patch.object(
            service,
            "inspect_assistant_context",
            return_value=unresolved_context,
        ):
            snapshot = service.run_live_assistant_workflow(
                workflow_task="case_summary",
                record_family="case",
                record_id=promoted_case.case_id,
            )

        self.assertEqual(snapshot.status, "unresolved")
        self.assertEqual(snapshot.summary, expected_summary)
        service._assistant_provider_adapter.generate.assert_not_called()

        ai_traces = store.list(AITraceRecord)
        self.assertEqual(len(ai_traces), 1)
        ai_trace = ai_traces[0]
        self.assertEqual(ai_trace.lifecycle_state, "under_review")
        self.assertEqual(
            ai_trace.assistant_advisory_draft["status"],
            "unresolved",
        )
        self.assertEqual(
            ai_trace.assistant_advisory_draft["summary"],
            expected_summary,
        )

        recommendations = store.list(RecommendationRecord)
        self.assertEqual(len(recommendations), 1)
        recommendation = recommendations[0]
        self.assertEqual(recommendation.ai_trace_id, ai_trace.ai_trace_id)
        self.assertEqual(recommendation.lifecycle_state, "under_review")
        self.assertEqual(
            recommendation.assistant_advisory_draft["status"],
            "unresolved",
        )
        self.assertEqual(
            recommendation.assistant_advisory_draft["cited_summary"]["text"],
            expected_summary,
        )
        self.assertEqual(
            recommendation.assistant_advisory_draft["citations"],
            expected_citations,
        )
        self.assertEqual(
            recommendation.assistant_advisory_draft["unresolved_reasons"],
            ("required citations are missing",),
        )
