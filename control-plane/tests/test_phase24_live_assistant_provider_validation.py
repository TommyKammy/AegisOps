from __future__ import annotations

import pathlib
import sys
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
        self.assertEqual(len(result.failures), 2)
        self.assertTrue(all(failure.failure_kind == "provider_error" for failure in result.failures))
        self.assertIn("malformed provider output", result.failure_summary)

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
            ai_trace.subject_linkage["provider_response_provenance"]["provider_response_id"],
            "provider-response-003",
        )
        self.assertEqual(
            ai_trace.subject_linkage["provider_failures"],
            (),
        )


if __name__ == "__main__":
    unittest.main()
