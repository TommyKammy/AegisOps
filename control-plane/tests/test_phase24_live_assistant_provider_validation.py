from __future__ import annotations

from copy import deepcopy
import pathlib
import sys
import time
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.assistant_provider import (  # type: ignore[attr-defined]
    AssistantProviderAdapter,
    AssistantProviderAttemptFailure,
    AssistantProviderFailure,
    AssistantProviderTimeout,
)


class AssistantProviderAdapterValidationTests(unittest.TestCase):
    def test_adapter_enforces_timeout_budget_for_non_cooperative_transport(self) -> None:
        def slow_transport(*, request: dict[str, object]) -> dict[str, object]:
            self.assertEqual(request["timeout_seconds"], 0.01)
            time.sleep(0.2)
            return {
                "provider_request_id": "provider-request-slow-001",
                "provider_response_id": "provider-response-slow-001",
                "provider_transcript_id": "provider-transcript-slow-001",
                "model_version": "model-version-2026-04-18",
                "output_text": "This response should arrive too late.",
            }

        adapter = AssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            request_timeout_seconds=0.01,
            max_attempts=1,
            transport=mock.Mock(send_request=slow_transport),
        )

        started_at = time.perf_counter()
        result = adapter.generate(
            workflow_family="first_live_assistant_summary_family",
            workflow_task="case_summary",
            transcript=[{"role": "user", "content": "Summarize case-001."}],
            reviewed_input_refs=("case-001",),
            metadata={"record_family": "case", "record_id": "case-001"},
        )
        elapsed = time.perf_counter() - started_at

        self.assertEqual(result.status, "timeout")
        self.assertIsNone(result.output_text)
        self.assertEqual(result.attempt_count, 1)
        self.assertEqual(result.operational_quality["availability"], "unavailable")
        self.assertEqual(result.operational_quality["posture"], "timeout")
        self.assertEqual(result.operational_quality["retry_policy"], "retry_exhausted")
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failures[0].failure_kind, "timeout")
        self.assertEqual(result.failures[0].detail, "AssistantProviderTimeout")
        self.assertIn(
            "attempt 1: timeout: AssistantProviderTimeout",
            result.failure_summary,
        )
        self.assertLess(elapsed, 0.15)

    def test_adapter_retries_bounded_timeout_failures_and_records_no_memory_provenance(
        self,
    ) -> None:
        transport = mock.Mock()
        transport.send_request.side_effect = [
            AssistantProviderTimeout("provider timed out"),
            {
                "provider_request_id": "provider-request-002",
                "provider_response_id": "provider-response-002",
                "provider_transcript_id": "provider-transcript-002",
                "model_version": "model-version-2026-04-17",
                "output_text": "Reviewed case summary.",
            },
        ]
        adapter = AssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            request_timeout_seconds=5.0,
            max_attempts=2,
            transport=transport,
        )

        result = adapter.generate(
            workflow_family="first_live_assistant_summary_family",
            workflow_task="case_summary",
            transcript=[
                {"role": "system", "content": "Summarize reviewed case state only."},
                {"role": "user", "content": "Summarize case-001."},
            ],
            reviewed_input_refs=("case-001", "evidence-001"),
            metadata={"record_family": "case", "record_id": "case-001"},
        )

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.operational_quality["availability"], "available")
        self.assertEqual(result.operational_quality["posture"], "degraded")
        self.assertEqual(result.operational_quality["retry_policy"], "retried")
        self.assertEqual(result.output_text, "Reviewed case summary.")
        self.assertEqual(result.attempt_count, 2)
        self.assertEqual(
            result.request_provenance["memory_policy"],
            "no_memory",
        )
        self.assertEqual(
            result.request_provenance["transcript_messages"],
            2,
        )
        self.assertEqual(
            result.response_provenance["provider_transcript_id"],
            "provider-transcript-002",
        )
        self.assertEqual(
            result.response_provenance["model_version"],
            "model-version-2026-04-17",
        )
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failures[0].failure_kind, "timeout")
        self.assertEqual(transport.send_request.call_count, 2)
        first_request = transport.send_request.call_args_list[0].kwargs["request"]
        self.assertEqual(first_request["memory_policy"], "no_memory")
        self.assertFalse(first_request["allow_provider_memory"])
        self.assertEqual(first_request["timeout_seconds"], 5.0)
        self.assertEqual(first_request["workflow_task"], "case_summary")

    def test_adapter_rebuilds_request_payload_for_each_attempt(self) -> None:
        recorded_requests: list[dict[str, object]] = []
        mutated_requests: list[dict[str, object]] = []

        def mutate_request_then_retry(*, request: dict[str, object]) -> dict[str, object]:
            recorded_requests.append(deepcopy(request))
            request["request_metadata"]["mutated"] = True
            request["transcript"][0]["content"] = "Mutated by transport."
            mutated_requests.append(deepcopy(request))
            if len(recorded_requests) == 1:
                raise AssistantProviderTimeout("provider timed out")
            return {
                "provider_request_id": "provider-request-004",
                "provider_response_id": "provider-response-004",
                "provider_transcript_id": "provider-transcript-004",
                "model_version": "model-version-2026-04-17",
                "output_text": "Reviewed case summary.",
            }

        adapter = AssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            request_timeout_seconds=5.0,
            max_attempts=2,
            transport=mock.Mock(send_request=mutate_request_then_retry),
        )

        result = adapter.generate(
            workflow_family="first_live_assistant_summary_family",
            workflow_task="case_summary",
            transcript=[{"role": "user", "content": "Summarize case-001."}],
            reviewed_input_refs=("case-001",),
            metadata={"record_family": "case", "record_id": "case-001"},
        )

        self.assertEqual(result.status, "ready")
        self.assertEqual(len(recorded_requests), 2)
        self.assertIn("mutated", mutated_requests[0]["request_metadata"])
        self.assertNotIn("mutated", recorded_requests[0]["request_metadata"])
        self.assertNotIn("mutated", recorded_requests[1]["request_metadata"])
        self.assertEqual(mutated_requests[0]["transcript"][0]["content"], "Mutated by transport.")
        self.assertEqual(recorded_requests[0]["transcript"][0]["content"], "Summarize case-001.")
        self.assertEqual(
            recorded_requests[1]["transcript"][0]["content"],
            "Summarize case-001.",
        )
        self.assertNotIn("mutated", result.request_provenance["request_metadata"])

    def test_adapter_returns_explicit_failure_without_fabricating_output(self) -> None:
        transport = mock.Mock()
        transport.send_request.side_effect = RuntimeError("malformed provider output")
        adapter = AssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            request_timeout_seconds=5.0,
            max_attempts=2,
            transport=transport,
        )

        result = adapter.generate(
            workflow_family="first_live_assistant_summary_family",
            workflow_task="case_summary",
            transcript=[{"role": "user", "content": "Summarize case-001."}],
            reviewed_input_refs=("case-001",),
            metadata={"record_family": "case", "record_id": "case-001"},
        )

        self.assertEqual(result.status, "failed")
        self.assertIsNone(result.output_text)
        self.assertEqual(result.attempt_count, 2)
        self.assertEqual(result.operational_quality["availability"], "unavailable")
        self.assertEqual(result.operational_quality["posture"], "unavailable")
        self.assertEqual(result.operational_quality["retry_policy"], "retry_exhausted")
        self.assertEqual(len(result.failures), 2)
        self.assertTrue(
            all(failure.failure_kind == "provider_error" for failure in result.failures)
        )
        self.assertEqual(
            tuple(failure.detail for failure in result.failures),
            ("RuntimeError", "RuntimeError"),
        )
        self.assertIn(
            "attempt 1: provider_error: RuntimeError",
            result.failure_summary,
        )
        self.assertNotIn("malformed provider output", result.failure_summary)

    def test_adapter_builds_ai_trace_with_request_response_and_failure_provenance(
        self,
    ) -> None:
        transport = mock.Mock()
        transport.send_request.return_value = {
            "provider_request_id": "provider-request-003",
            "provider_response_id": "provider-response-003",
            "provider_transcript_id": "provider-transcript-003",
            "model_version": "model-version-2026-04-17",
            "output_text": "Queue triage summary.",
        }
        adapter = AssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-queue-summary-v1",
            request_timeout_seconds=7.5,
            max_attempts=1,
            transport=transport,
        )

        result = adapter.generate(
            workflow_family="first_live_assistant_summary_family",
            workflow_task="queue_triage_summary",
            transcript=[{"role": "user", "content": "Summarize alert-001."}],
            reviewed_input_refs=("alert-001", "evidence-001"),
            metadata={"record_family": "alert", "record_id": "alert-001"},
        )

        ai_trace = adapter.build_ai_trace_record(
            ai_trace_id="ai-trace-provider-001",
            reviewer_identity="reviewer-001",
            generated_at=result.generated_at,
            result=result,
            subject_linkage={
                "alert_ids": ("alert-001",),
                "recommendation_ids": ("recommendation-001",),
            },
        )

        self.assertEqual(ai_trace.model_identity, "openai/gpt-5.4")
        self.assertEqual(ai_trace.prompt_version, "phase24-queue-summary-v1")
        self.assertEqual(
            ai_trace.material_input_refs,
            ("alert-001", "evidence-001"),
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_identity"],
            "openai",
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_request_provenance"]["memory_policy"],
            "no_memory",
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_response_provenance"][
                "provider_response_id"
            ],
            "provider-response-003",
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_operational_quality"]["posture"],
            "ready",
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_failures"],
            (),
        )

    def test_adapter_builds_ai_trace_with_timeout_quality_signal(self) -> None:
        adapter = AssistantProviderAdapter(
            provider_identity="openai",
            model_identity="gpt-5.4",
            prompt_version="phase24-case-summary-v1",
            request_timeout_seconds=5.0,
            max_attempts=1,
            transport=mock.Mock(
                send_request=mock.Mock(
                    side_effect=AssistantProviderTimeout("provider timed out")
                )
            ),
        )

        result = adapter.generate(
            workflow_family="first_live_assistant_summary_family",
            workflow_task="case_summary",
            transcript=[{"role": "user", "content": "Summarize case-001."}],
            reviewed_input_refs=("case-001",),
            metadata={"record_family": "case", "record_id": "case-001"},
        )
        ai_trace = adapter.build_ai_trace_record(
            ai_trace_id="ai-trace-provider-timeout-001",
            reviewer_identity="reviewer-001",
            generated_at=result.generated_at,
            result=result,
            subject_linkage={"case_ids": ("case-001",)},
        )

        self.assertEqual(result.status, "timeout")
        self.assertEqual(ai_trace.lifecycle_state, "under_review")
        self.assertEqual(
            ai_trace.subject_linkage["provider_operational_quality"],
            {
                "availability": "unavailable",
                "posture": "timeout",
                "retry_policy": "retry_exhausted",
                "terminal_failure_kind": "timeout",
            },
        )


if __name__ == "__main__":
    unittest.main()
