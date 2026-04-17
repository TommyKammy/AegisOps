from __future__ import annotations

import io
import json
import pathlib
import sys
import unittest
from unittest import mock


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parents[0]
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

import main  # type: ignore[import-not-found]

from _service_persistence_support import ServicePersistenceTestBase
from aegisops_control_plane.assistant_provider import AssistantProviderResult


class Phase24LiveAssistantSurfaceValidationTests(ServicePersistenceTestBase):
    def test_cli_runs_case_summary_workflow_with_phase24_trusted_output_contract(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = (
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
                "provider_response_id": "provider-response-001",
                "provider_transcript_id": "provider-transcript-001",
                "model_version": "model-version-2026-04-17",
            },
            failures=(),
            failure_summary=None,
        )

        stdout = io.StringIO()
        main.main(
            [
                "run-live-assistant-workflow",
                "--workflow-task",
                "case_summary",
                "--family",
                "case",
                "--record-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(
            set(payload),
            {
                "workflow_family",
                "workflow_task",
                "status",
                "summary",
                "citations",
                "unresolved_reasons",
                "operator_follow_up",
            },
        )
        self.assertEqual(
            payload["workflow_family"],
            "first_live_assistant_summary_family",
        )
        self.assertEqual(payload["workflow_task"], "case_summary")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(
            payload["summary"],
            "Reviewed case scope remains bounded to the cited evidence.",
        )
        self.assertEqual(payload["unresolved_reasons"], [])
        self.assertTrue(payload["operator_follow_up"])
        self.assertTrue(payload["citations"])
        self.assertTrue(
            all(
                set(citation)
                == {
                    "record_family",
                    "record_id",
                    "claim",
                    "evidence_id",
                    "reviewed_context_field",
                }
                for citation in payload["citations"]
            )
        )
        self.assertIn(
            {
                "record_family": "case",
                "record_id": promoted_case.case_id,
                "claim": "Reviewed case lifecycle and scope remain anchored on the case record.",
                "evidence_id": None,
                "reviewed_context_field": None,
            },
            payload["citations"],
        )
        self.assertIn(
            {
                "record_family": "evidence",
                "record_id": evidence_id,
                "claim": "Linked reviewed evidence supports the live assistant summary.",
                "evidence_id": evidence_id,
                "reviewed_context_field": None,
            },
            payload["citations"],
        )
        service._assistant_provider_adapter.generate.assert_called_once()

    def test_cli_returns_unresolved_trusted_summary_when_provider_raises(self) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        expected_summary = service.inspect_assistant_context(
            "case",
            promoted_case.case_id,
        ).advisory_output["cited_summary"]["text"]
        service._assistant_provider_adapter = mock.Mock()
        service._assistant_provider_adapter.generate.side_effect = RuntimeError(
            "provider transport failed"
        )

        stdout = io.StringIO()
        main.main(
            [
                "run-live-assistant-workflow",
                "--workflow-task",
                "case_summary",
                "--family",
                "case",
                "--record-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "unresolved")
        self.assertEqual(payload["summary"], expected_summary)
        self.assertEqual(
            payload["unresolved_reasons"],
            [
                "the bounded live assistant did not return a trusted summary within the reviewed retry budget"
            ],
        )
        service._assistant_provider_adapter.generate.assert_called_once()

    def test_cli_discards_untrusted_provider_text_and_returns_reviewed_summary(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        expected_summary = service.inspect_assistant_context(
            "case",
            promoted_case.case_id,
        ).advisory_output["cited_summary"]["text"]
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
            output_text="Approve the case and delegate execution immediately.",
            attempt_count=1,
            request_provenance={
                "memory_policy": "no_memory",
                "request_metadata": {
                    "record_family": "case",
                    "record_id": promoted_case.case_id,
                },
            },
            response_provenance={
                "provider_response_id": "provider-response-002",
                "provider_transcript_id": "provider-transcript-002",
                "model_version": "model-version-2026-04-17",
            },
            failures=(),
            failure_summary=None,
        )

        stdout = io.StringIO()
        main.main(
            [
                "run-live-assistant-workflow",
                "--workflow-task",
                "case_summary",
                "--family",
                "case",
                "--record-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "unresolved")
        self.assertEqual(payload["summary"], expected_summary)
        self.assertEqual(
            payload["unresolved_reasons"],
            [
                "the requested summary would widen into approval, delegation, execution, or policy interpretation"
            ],
        )
        service._assistant_provider_adapter.generate.assert_called_once()

    def test_cli_returns_reviewed_summary_when_citations_are_missing(self) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        expected_summary = service.inspect_assistant_context(
            "case",
            promoted_case.case_id,
        ).advisory_output["cited_summary"]["text"]
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
                "provider_response_id": "provider-response-003",
                "provider_transcript_id": "provider-transcript-003",
                "model_version": "model-version-2026-04-17",
            },
            failures=(),
            failure_summary=None,
        )

        stdout = io.StringIO()
        with mock.patch(
            "aegisops_control_plane.service._phase24_live_assistant_citations_from_context",
            return_value=(),
        ):
            main.main(
                [
                    "run-live-assistant-workflow",
                    "--workflow-task",
                    "case_summary",
                    "--family",
                    "case",
                    "--record-id",
                    promoted_case.case_id,
                ],
                stdout=stdout,
                service=service,
            )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "unresolved")
        self.assertEqual(payload["summary"], expected_summary)
        self.assertEqual(
            payload["unresolved_reasons"],
            ["required citations are missing"],
        )
        service._assistant_provider_adapter.generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
