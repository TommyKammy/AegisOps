from __future__ import annotations

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _cli_inspection_support import *  # noqa: F403
from _cli_inspection_support import _approved_payload_binding_hash, _load_wazuh_fixture


class CliInspectionUsageErrorTests(ControlPlaneCliInspectionTestBase):
    def test_cli_rejects_case_scoped_out_of_scope_advisory_reads_as_usage_errors(
        self,
    ) -> None:
        service, recommendation, ai_trace = self._build_out_of_scope_case_advisory_review_records(
            fixture_name="github-audit-alert.json"
        )
        expected_message = (
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice"
        )

        for command, record_family, record_id in (
            (
                "inspect-advisory-output",
                "recommendation",
                recommendation.recommendation_id,
            ),
            (
                "inspect-advisory-output",
                "ai_trace",
                ai_trace.ai_trace_id,
            ),
            (
                "render-recommendation-draft",
                "recommendation",
                recommendation.recommendation_id,
            ),
            (
                "render-recommendation-draft",
                "ai_trace",
                ai_trace.ai_trace_id,
            ),
        ):
            stderr = io.StringIO()
            with self.subTest(
                command=command,
                record_family=record_family,
            ), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc_info:
                    main.main(
                        [
                            command,
                            "--family",
                            record_family,
                            "--record-id",
                            record_id,
                        ],
                        service=service,
                    )

            self.assertEqual(exc_info.exception.code, 2)
            self.assertIn(expected_message, stderr.getvalue())

    def test_cli_rejects_case_family_out_of_scope_advisory_reads_as_usage_errors(
        self,
    ) -> None:
        service, promoted_case = self._build_phase19_out_of_scope_case(
            fixture_name="github-audit-alert.json"
        )
        expected_message = (
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice"
        )

        for command in (
            "inspect-assistant-context",
            "inspect-advisory-output",
            "render-recommendation-draft",
        ):
            stderr = io.StringIO()
            with self.subTest(command=command), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc_info:
                    main.main(
                        [
                            command,
                            "--family",
                            "case",
                            "--record-id",
                            promoted_case.case_id,
                        ],
                        service=service,
                    )

            self.assertEqual(exc_info.exception.code, 2)
            self.assertIn(expected_message, stderr.getvalue())

    def test_cli_rejects_case_scoped_advisory_reads_without_linked_case_as_usage_errors(
        self,
    ) -> None:
        service, recommendation, ai_trace = (
            self._build_case_scoped_advisory_records_without_case_lineage()
        )
        expected_message = (
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice"
        )

        for command, record_family, record_id in (
            (
                "inspect-advisory-output",
                "recommendation",
                recommendation.recommendation_id,
            ),
            (
                "inspect-advisory-output",
                "ai_trace",
                ai_trace.ai_trace_id,
            ),
            (
                "render-recommendation-draft",
                "recommendation",
                recommendation.recommendation_id,
            ),
            (
                "render-recommendation-draft",
                "ai_trace",
                ai_trace.ai_trace_id,
            ),
        ):
            stderr = io.StringIO()
            with self.subTest(
                command=command,
                record_family=record_family,
            ), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc_info:
                    main.main(
                        [
                            command,
                            "--family",
                            record_family,
                            "--record-id",
                            record_id,
                        ],
                        service=service,
                    )

            self.assertEqual(exc_info.exception.code, 2)
            self.assertIn(expected_message, stderr.getvalue())

    def test_cli_renders_recommendation_draft_with_source_review_outcome(self) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-draft-cli-outcome-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="accepted",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "render-recommendation-draft",
                "--family",
                "recommendation",
                "--record-id",
                recommendation.recommendation_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["record_family"], "recommendation")
        self.assertEqual(payload["record_id"], recommendation.recommendation_id)
        self.assertEqual(
            payload["recommendation_draft"]["source_output_kind"],
            "recommendation_draft",
        )
        self.assertEqual(
            payload["recommendation_draft"]["review_lifecycle_state"],
            "accepted",
        )
        self.assertIn(
            "has been accepted and is anchored",
            payload["recommendation_draft"]["cited_summary"]["text"],
        )
        self.assertNotIn(
            "remains under review",
            payload["recommendation_draft"]["cited_summary"]["text"],
        )
        self.assertIn(
            evidence_id,
            payload["recommendation_draft"]["citations"],
        )

    def test_cli_renders_identity_rich_analyst_queue_view_with_reviewed_context(
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
                _load_wazuh_fixture("microsoft-365-audit-alert.json")
            ),
        )
        service.promote_alert_to_case(admitted.alert.alert_id)

        stdout = io.StringIO()
        main.main(["inspect-analyst-queue"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["total_records"], 1)
        self.assertEqual(
            payload["records"][0]["reviewed_context"]["source"]["source_family"],
            "microsoft_365_audit",
        )
        self.assertEqual(
            payload["records"][0]["reviewed_context"]["identity"]["actor"]["identity_id"],
            "alex@contoso.com",
        )

    def test_cli_rejects_unknown_record_family_as_usage_error(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exc_info:
                main.main(
                    ["inspect-records", "--family", "unknown-family"],
                    service=service,
                )

        self.assertEqual(exc_info.exception.code, 2)
        self.assertIn("Unsupported control-plane record family", stderr.getvalue())

    def test_cli_rejects_blank_alert_detail_identifier_as_usage_error(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exc_info:
                main.main(
                    ["inspect-alert-detail", "--alert-id", "   "],
                    service=service,
                )

        self.assertEqual(exc_info.exception.code, 2)
        self.assertIn("alert_id must be a non-empty string", stderr.getvalue())

    def test_cli_renders_inspection_views_against_empty_postgresql_store(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        records_stdout = io.StringIO()
        status_stdout = io.StringIO()

        main.main(
            ["inspect-records", "--family", "alert"],
            stdout=records_stdout,
            service=service,
        )
        main.main(
            ["inspect-reconciliation-status"],
            stdout=status_stdout,
            service=service,
        )

        records_payload = json.loads(records_stdout.getvalue())
        status_payload = json.loads(status_stdout.getvalue())

        self.assertTrue(records_payload["read_only"])
        self.assertEqual(records_payload["record_family"], "alert")
        self.assertEqual(records_payload["total_records"], 0)
        self.assertEqual(records_payload["records"], [])

        self.assertTrue(status_payload["read_only"])
        self.assertEqual(status_payload["total_records"], 0)
        self.assertIsNone(status_payload["latest_compared_at"])
        self.assertEqual(status_payload["by_lifecycle_state"], {})
        self.assertEqual(status_payload["by_ingest_disposition"], {})
        self.assertEqual(status_payload["records"], [])


if __name__ == "__main__":
    unittest.main()
