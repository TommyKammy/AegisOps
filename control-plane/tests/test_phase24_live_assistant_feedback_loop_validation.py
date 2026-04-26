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
    def test_live_assistant_workflow_clones_configured_adapter_when_only_prompt_version_changes(
        self,
    ) -> None:
        store, service, alert, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_alert_without_case()
        )

        class StatefulAssistantProviderAdapter(AssistantProviderAdapter):
            def __init__(self, *, stateful_marker: str, **kwargs: object) -> None:
                super().__init__(**kwargs)
                self.stateful_marker = stateful_marker

            def build_ai_trace_record(self, **kwargs: object) -> AITraceRecord:
                ai_trace = super().build_ai_trace_record(**kwargs)
                subject_linkage = dict(ai_trace.subject_linkage)
                subject_linkage["adapter_marker"] = self.stateful_marker
                return replace(ai_trace, subject_linkage=subject_linkage)

        service._assistant_provider_adapter = StatefulAssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            request_timeout_seconds=5.0,
            max_attempts=1,
            transport=mock.Mock(
                send_request=mock.Mock(
                    return_value={
                        "provider_request_id": "provider-request-clone-001",
                        "provider_response_id": "provider-response-clone-001",
                        "provider_transcript_id": "provider-transcript-clone-001",
                        "model_version": "model-version-2026-04-20",
                        "output_text": (
                            "Reviewed queue alert scope remains bounded to the cited evidence."
                        ),
                    }
                )
            ),
            stateful_marker="preserved-subclass-state",
        )

        snapshot = service.run_live_assistant_workflow(
            workflow_task="queue_triage_summary",
            record_family="alert",
            record_id=alert.alert_id,
        )

        self.assertEqual(snapshot.status, "ready")
        ai_traces = store.list(AITraceRecord)
        self.assertEqual(len(ai_traces), 1)
        self.assertEqual(
            ai_traces[0].prompt_version,
            "phase24-queue-summary-v1",
        )
        self.assertEqual(
            ai_traces[0].subject_linkage["adapter_marker"],
            "preserved-subclass-state",
        )
        self.assertEqual(
            service._assistant_provider_adapter._prompt_version,
            "phase24-case-summary-v1",
        )
        self.assertIn(alert.alert_id, ai_traces[0].material_input_refs)
        self.assertIn(evidence_id, ai_traces[0].material_input_refs)

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
        self.assertEqual(
            ai_trace.subject_linkage["recommendation_ids"],
            (recommendation.recommendation_id,),
        )
        self.assertEqual(
            ai_trace.assistant_advisory_draft["subject_linkage"]["recommendation_ids"],
            (recommendation.recommendation_id,),
        )
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
        self.assertEqual(ai_trace.subject_linkage["provider_status"], "failed")
        self.assertEqual(
            ai_trace.subject_linkage["provider_operational_quality"],
            {
                "availability": "unavailable",
                "posture": "unavailable",
                "retry_policy": "retry_exhausted",
                "terminal_failure_kind": "provider_error",
            },
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_failure_summary"],
            "attempt 1: provider_error: RuntimeError",
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_failures"],
            (
                {
                    "attempt_number": 1,
                    "failure_kind": "provider_error",
                    "detail": "RuntimeError",
                },
            ),
        )
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

    def test_live_assistant_workflow_sanitizes_provider_exception_trace_detail(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        service._assistant_provider_adapter = mock.Mock()
        service._assistant_provider_adapter.generate.side_effect = RuntimeError(
            "POST https://provider.example/v1/chat?api_key=secret-token "
            "Authorization: Bearer secret-token"
        )

        snapshot = service.run_live_assistant_workflow(
            workflow_task="case_summary",
            record_family="case",
            record_id=promoted_case.case_id,
        )

        self.assertEqual(snapshot.status, "unresolved")
        ai_traces = store.list(AITraceRecord)
        self.assertEqual(len(ai_traces), 1)
        provider_failures = ai_traces[0].subject_linkage["provider_failures"]
        failure_summary = ai_traces[0].subject_linkage["provider_failure_summary"]

        self.assertEqual(
            provider_failures,
            (
                {
                    "attempt_number": 1,
                    "failure_kind": "provider_error",
                    "detail": "RuntimeError",
                },
            ),
        )
        self.assertEqual(failure_summary, "attempt 1: provider_error: RuntimeError")
        self.assertNotIn("https://provider.example", failure_summary)
        self.assertNotIn("secret-token", failure_summary)
        self.assertNotIn("Bearer", failure_summary)

    def test_live_assistant_workflow_preserves_raised_timeout_provider_posture(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        service._assistant_provider_adapter = mock.Mock()
        service._assistant_provider_adapter.generate.side_effect = TimeoutError(
            "provider call to https://provider.example/v1 timed out "
            "with token=secret-token"
        )

        snapshot = service.run_live_assistant_workflow(
            workflow_task="case_summary",
            record_family="case",
            record_id=promoted_case.case_id,
        )

        self.assertEqual(snapshot.status, "unresolved")
        ai_traces = store.list(AITraceRecord)
        self.assertEqual(len(ai_traces), 1)
        ai_trace = ai_traces[0]
        readiness = service.inspect_readiness_diagnostics()
        assistant_extension = readiness.metrics["optional_extensions"]["extensions"][
            "assistant"
        ]

        self.assertEqual(ai_trace.subject_linkage["provider_status"], "timeout")
        self.assertEqual(
            ai_trace.subject_linkage["provider_operational_quality"],
            {
                "availability": "unavailable",
                "posture": "timeout",
                "retry_policy": "retry_exhausted",
                "terminal_failure_kind": "timeout",
            },
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_failure_summary"],
            "attempt 1: timeout: TimeoutError",
        )
        self.assertEqual(assistant_extension["reason"], "assistant_provider_timeout")
        self.assertEqual(assistant_extension["provider_status"], "timeout")

    def test_live_assistant_provider_failure_stays_visible_on_recommendation_advisory_inspection(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        service._assistant_provider_adapter = mock.Mock()
        service._assistant_provider_adapter.generate.side_effect = RuntimeError(
            "provider transport failed"
        )

        snapshot = service.run_live_assistant_workflow(
            workflow_task="case_summary",
            record_family="case",
            record_id=promoted_case.case_id,
        )

        self.assertEqual(snapshot.status, "unresolved")
        recommendations = store.list(RecommendationRecord)
        self.assertEqual(len(recommendations), 1)

        advisory_snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendations[0].recommendation_id,
        )

        self.assertEqual(advisory_snapshot.advisory_output["status"], "unresolved")
        self.assertIn(
            "provider_generation_failed",
            advisory_snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertTrue(
            any(
                "bounded live assistant did not return a trusted summary"
                in question["text"]
                for question in advisory_snapshot.advisory_output["unresolved_questions"]
            )
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

    def test_live_assistant_workflow_uses_task_specific_adapter_for_unresolved_queue_triage_feedback_loop(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        alert_id = promoted_case.alert_id
        context_snapshot = service.inspect_assistant_context("alert", alert_id)
        unresolved_context = replace(
            context_snapshot,
            linked_alert_ids=(),
            advisory_output={
                **dict(context_snapshot.advisory_output),
                "status": "unresolved",
                "cited_summary": {
                    "text": "Reviewed queue triage remains unresolved pending cited alert context.",
                    "citations": (alert_id,),
                },
                "uncertainty_flags": ("missing_supporting_citations",),
            },
        )
        service._assistant_provider_adapter = AssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            request_timeout_seconds=5.0,
            max_attempts=1,
            transport=mock.Mock(),
        )

        with mock.patch.object(
            service,
            "inspect_assistant_context",
            return_value=unresolved_context,
        ):
            snapshot = service.run_live_assistant_workflow(
                workflow_task="queue_triage_summary",
                record_family="alert",
                record_id=alert_id,
            )

        self.assertEqual(snapshot.status, "unresolved")

        ai_traces = store.list(AITraceRecord)
        self.assertEqual(len(ai_traces), 1)
        self.assertEqual(ai_traces[0].prompt_version, "phase24-queue-summary-v1")

        recommendations = store.list(RecommendationRecord)
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].alert_id, alert_id)
        self.assertEqual(
            recommendations[0].assistant_advisory_draft["source_record_id"],
            alert_id,
        )

    def test_live_assistant_workflow_canonicalizes_provider_trace_linkage_and_case_binding(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        context_snapshot = service.inspect_assistant_context(
            "case",
            promoted_case.case_id,
        )
        linked_context = replace(
            context_snapshot,
            linked_case_ids=(),
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
                "provider_response_id": "provider-response-feedback-loop-002",
                "provider_transcript_id": "provider-transcript-feedback-loop-002",
                "model_version": "model-version-2026-04-18",
            },
            failures=(),
            failure_summary=None,
        )
        service._assistant_provider_adapter.build_ai_trace_record.return_value = (
            AITraceRecord(
                ai_trace_id="ai-trace-provider-stale-001",
                subject_linkage={
                    "source_record_family": "case",
                    "source_record_id": "case-stale-001",
                    "alert_ids": ("alert-stale-001",),
                    "case_ids": ("case-stale-001",),
                    "evidence_ids": (),
                    "recommendation_ids": (),
                    "reconciliation_ids": (),
                    "output_contract": {
                        "workflow_family": "stale-family",
                        "workflow_task": "stale-task",
                        "status": "ready",
                    },
                    "provider_identity": "openai",
                    "provider_response_provenance": {
                        "provider_response_id": "provider-response-feedback-loop-002",
                    },
                },
                model_identity="openai/gpt-5.4",
                prompt_version="phase24-case-summary-v1",
                generated_at=reviewed_at,
                material_input_refs=("stale-ref-001",),
                reviewer_identity="system://bounded-live-assistant",
                lifecycle_state="ready",
                assistant_advisory_draft={
                    "provider_record_family": "ai_trace",
                    "provider_request_id": "provider-request-feedback-loop-002",
                    "subject_linkage": {
                        "source_record_family": "case",
                        "source_record_id": "case-stale-001",
                    },
                    "reviewed_input_refs": ("stale-ref-001",),
                },
            )
        )

        with mock.patch.object(
            service,
            "inspect_assistant_context",
            return_value=linked_context,
        ):
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
            ai_trace.subject_linkage["source_record_id"],
            promoted_case.case_id,
        )
        self.assertEqual(
            ai_trace.subject_linkage["output_contract"]["workflow_task"],
            "case_summary",
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_identity"],
            "openai",
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_response_provenance"][
                "provider_response_id"
            ],
            "provider-response-feedback-loop-002",
        )
        self.assertNotIn("stale-ref-001", ai_trace.material_input_refs)
        self.assertEqual(
            ai_trace.assistant_advisory_draft["subject_linkage"]["source_record_id"],
            promoted_case.case_id,
        )
        self.assertEqual(
            ai_trace.assistant_advisory_draft["subject_linkage"]["provider_identity"],
            "openai",
        )
        self.assertEqual(
            ai_trace.assistant_advisory_draft["provider_record_family"],
            "ai_trace",
        )
        self.assertEqual(
            ai_trace.assistant_advisory_draft["provider_request_id"],
            "provider-request-feedback-loop-002",
        )
        self.assertEqual(
            ai_trace.assistant_advisory_draft["reviewed_input_refs"],
            ai_trace.material_input_refs,
        )

        recommendations = store.list(RecommendationRecord)
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].case_id, promoted_case.case_id)
