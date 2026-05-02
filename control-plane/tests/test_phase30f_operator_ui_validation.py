from __future__ import annotations

from datetime import datetime, timezone
import pathlib
import sys
import unittest


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.models import AITraceRecord
from aegisops.control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store
from support.operator_ui_sources import read_operator_routes_test_bundle


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30FOperatorUiValidationTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase30f_validation_doc_locks_taxonomy_and_subordinate_status_semantics(
        self,
    ) -> None:
        text = self._read("docs/phase-30f-optional-extension-visibility-validation.md")

        for term in (
            "# Phase 30F Optional-Extension Visibility Validation",
            "Validation status: PASS",
            "disabled-by-default posture remains distinct from unavailable posture",
            "enabled posture still fails closed unless backend-owned availability is explicit",
            "optional-extension visibility remains subordinate context rather than authoritative lifecycle truth",
            "mainline expectation messaging remains explicit when optional paths are absent",
            "control-plane/tests/test_phase30f_operator_ui_validation.py",
            "apps/operator-ui/src/app/optionalExtensionVisibility.test.tsx",
            "apps/operator-ui/src/app/OperatorRoutes.test.tsx",
            "python3 -m unittest control-plane.tests.test_phase30f_operator_ui_validation",
            "npm --prefix apps/operator-ui test -- --run src/app/optionalExtensionVisibility.test.tsx src/app/OperatorRoutes.test.tsx",
            "npm --prefix apps/operator-ui run build",
        ):
            self.assertIn(term, text)

    def test_phase30f_readiness_defaults_keep_optional_extension_status_subordinate(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        readiness = service.inspect_readiness_diagnostics()
        optional_extensions = readiness.metrics["optional_extensions"]["extensions"]

        self.assertEqual(
            optional_extensions["assistant"]["enablement"],
            "enabled",
        )
        self.assertEqual(
            optional_extensions["assistant"]["authority_mode"],
            "advisory_only",
        )

        for extension_name, authority_mode in (
            ("endpoint_evidence", "augmenting_evidence"),
            ("network_evidence", "augmenting_evidence"),
            ("ml_shadow", "shadow_only"),
        ):
            with self.subTest(extension=extension_name):
                self.assertEqual(
                    optional_extensions[extension_name]["enablement"],
                    "disabled_by_default",
                )
                self.assertEqual(
                    optional_extensions[extension_name]["mainline_dependency"],
                    "non_blocking",
                )
                self.assertEqual(
                    optional_extensions[extension_name]["authority_mode"],
                    authority_mode,
                )

    def test_phase30f_readiness_exposes_assistant_provider_timeout_posture(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-timeout-001",
                subject_linkage={
                    "provider_identity": "openai",
                    "provider_status": "timeout",
                    "provider_failure_summary": "attempt 1: timeout: provider timed out",
                    "provider_failures": (
                        {
                            "attempt_number": 1,
                            "failure_kind": "timeout",
                            "detail": "provider timed out",
                        },
                    ),
                    "provider_operational_quality": {
                        "availability": "unavailable",
                        "posture": "timeout",
                        "retry_policy": "retry_exhausted",
                        "terminal_failure_kind": "timeout",
                    },
                },
                model_identity="openai/gpt-5.4",
                prompt_version="phase24-case-summary-v1",
                generated_at=datetime(2026, 4, 26, 9, 0, tzinfo=timezone.utc),
                material_input_refs=("case-001",),
                reviewer_identity="system://bounded-live-assistant",
                lifecycle_state="under_review",
            )
        )

        readiness = service.inspect_readiness_diagnostics()
        assistant = readiness.metrics["optional_extensions"]["extensions"]["assistant"]

        self.assertEqual(readiness.metrics["optional_extensions"]["overall_state"], "degraded")
        self.assertEqual(assistant["availability"], "unavailable")
        self.assertEqual(assistant["readiness"], "degraded")
        self.assertEqual(assistant["reason"], "assistant_provider_timeout")
        self.assertEqual(assistant["provider_status"], "timeout")
        self.assertEqual(assistant["retry_policy"], "retry_exhausted")
        self.assertIn("attempt 1: timeout", assistant["failure_summary"])

    def test_phase30f_readiness_exposes_unresolved_assistant_citation_posture(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-citation-001",
                subject_linkage={
                    "provider_identity": "openai",
                    "provider_status": "ready",
                    "provider_operational_quality": {
                        "availability": "available",
                        "posture": "ready",
                        "retry_policy": "not_needed",
                        "terminal_failure_kind": None,
                    },
                },
                model_identity="openai/gpt-5.4",
                prompt_version="phase24-case-summary-v1",
                generated_at=datetime(2026, 4, 26, 9, 5, tzinfo=timezone.utc),
                material_input_refs=("case-001",),
                reviewer_identity="system://bounded-live-assistant",
                lifecycle_state="under_review",
                assistant_advisory_draft={
                    "status": "unresolved",
                    "unresolved_reasons": ("Required Citations Are Missing",),
                },
            )
        )

        readiness = service.inspect_readiness_diagnostics()
        assistant = readiness.metrics["optional_extensions"]["extensions"]["assistant"]

        self.assertEqual(assistant["availability"], "available")
        self.assertEqual(assistant["readiness"], "degraded")
        self.assertEqual(assistant["reason"], "assistant_citation_failure")
        self.assertEqual(
            assistant["unresolved_reasons"],
            ("Required Citations Are Missing",),
        )

    def test_phase30f_frontend_tests_lock_taxonomy_and_non_authority_rendering(
        self,
    ) -> None:
        mapper_tests = self._read(
            "apps/operator-ui/src/app/optionalExtensionVisibility.test.tsx"
        )
        route_tests = read_operator_routes_test_bundle(REPO_ROOT)

        for term in (
            "keeps disabled-by-default posture distinct from unavailable",
            "fails closed when enablement says enabled but availability is missing",
            "keeps degraded posture primary over other optional signals",
        ):
            self.assertIn(term, mapper_tests)

        for term in (
            "keeps disabled-by-default endpoint and network evidence posture visible",
            "fails closed when optional enablement is present without backend availability",
            "Optional extension visibility",
            "Optional evidence posture",
            "Disabled By Default",
            "Optional-path posture stays subordinate to authoritative workflow pages and reviewed runtime truth.",
            "Missing optional paths do not imply a control-plane failure when the mainline reviewed workflow remains healthy.",
        ):
            self.assertIn(term, route_tests)


if __name__ == "__main__":
    unittest.main()
