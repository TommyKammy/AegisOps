from __future__ import annotations

import io
import json
import pathlib
import sys
from types import SimpleNamespace
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parent
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from aegisops.control_plane.api.http_runtime_surface import runtime_read_response
from aegisops.control_plane.runtime.doctor_contract import build_doctor_snapshot

from _cli_inspection_support import *  # noqa: F403


class Phase581DoctorContractTests(ControlPlaneCliInspectionTestBase):
    def test_doctor_cli_renders_bounded_non_mutating_contract(self) -> None:
        _store, service, _case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        before_counts = {
            family: len(service.inspect_records(family).records)
            for family in (
                "alert",
                "case",
                "evidence",
                "action_request",
                "action_execution",
                "reconciliation",
            )
        }
        stdout = io.StringIO()

        main.main(["doctor"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertFalse(payload["mutates_authoritative_records"])
        self.assertEqual(payload["authority_boundary"], "explanatory_subordinate")
        self.assertEqual(
            payload["posture_semantics"],
            ["available", "degraded", "unavailable", "not_applicable"],
        )
        required_families = {
            "control_plane",
            "wazuh",
            "shuffle",
            "database",
            "proxy",
            "stale_source",
            "ai_enablement",
            "evidence_availability",
            "workflow_template",
            "execution_receipt",
        }
        self.assertEqual(set(payload["states"]), required_families)
        self.assertEqual(payload["states"]["control_plane"]["posture"], "available")
        self.assertEqual(payload["states"]["wazuh"]["posture"], "available")
        self.assertEqual(payload["states"]["shuffle"]["posture"], "not_applicable")
        self.assertEqual(payload["states"]["execution_receipt"]["posture"], "not_applicable")
        self.assertEqual(payload["summary"]["overall_posture"], "available")
        self.assertIn("automatic_repair", payload["negative_authority"])
        self.assertIn("release_truth", payload["negative_authority"])
        self.assertIn("workflow_truth", payload["negative_authority"])
        after_counts = {
            family: len(service.inspect_records(family).records)
            for family in before_counts
        }
        self.assertEqual(after_counts, before_counts)

    def test_doctor_http_runtime_surface_exposes_same_read_only_contract(self) -> None:
        _store, service, _case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )

        status, payload = runtime_read_response(
            service=service,
            request_path="/diagnostics/doctor",
        )

        self.assertEqual(status.value, 200)
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["contract"], "phase58_1_aegisops_doctor")
        self.assertFalse(payload["mutates_authoritative_records"])

    def test_doctor_contract_reports_degraded_source_and_ai_without_authority(self) -> None:
        payload = self._build_doctor_payload(
            config_overrides={"ai_enablement_posture": "degraded"},
            metrics_overrides={
                "source_health": {
                    "tracked_sources": 1,
                    "overall_state": "degraded",
                    "sources": {
                        "wazuh": {
                            "state": "degraded",
                            "reason": "source_health_signal_stale",
                        }
                    },
                }
            },
        )

        self.assertEqual(payload["summary"]["overall_posture"], "degraded")
        self.assertEqual(payload["states"]["stale_source"]["posture"], "degraded")
        self.assertEqual(payload["states"]["ai_enablement"]["posture"], "degraded")
        self.assertFalse(payload["states"]["stale_source"]["authoritative"])
        self.assertIn("stale_source", self._recommended_families(payload))
        self.assertIn("ai_enablement", self._recommended_families(payload))

    def test_doctor_contract_fails_closed_for_missing_or_malformed_signals(self) -> None:
        payload = build_doctor_snapshot(
            config=self._doctor_config(),
            readiness_payload={"read_only": True, "status": "optimistic"},
        ).to_dict()

        self.assertEqual(payload["summary"]["overall_posture"], "unavailable")
        self.assertEqual(payload["states"]["control_plane"]["posture"], "unavailable")
        self.assertEqual(payload["states"]["database"]["posture"], "unavailable")
        self.assertIn("control_plane", self._recommended_families(payload))
        self.assertIn("database", self._recommended_families(payload))

    def test_doctor_contract_blocks_missing_execution_receipt_success_inference(self) -> None:
        payload = self._build_doctor_payload(
            metrics_overrides={
                "action_executions": {
                    "total": 1,
                    "dispatching": 0,
                    "queued": 0,
                    "running": 1,
                    "terminal": 0,
                },
                "reconciliations": {
                    "total": 0,
                    "pending": 0,
                    "mismatched": 0,
                    "stale": 0,
                    "by_ingest_disposition": {},
                },
            },
        )

        self.assertEqual(payload["summary"]["overall_posture"], "unavailable")
        self.assertEqual(payload["states"]["execution_receipt"]["posture"], "unavailable")
        self.assertEqual(
            payload["states"]["execution_receipt"]["reason"],
            "missing_execution_receipt_signal",
        )
        self.assertIn("execution_receipt", self._recommended_families(payload))

    def test_doctor_contract_rejects_missing_wazuh_prerequisite_as_unavailable(self) -> None:
        payload = self._build_doctor_payload(
            config_overrides={"wazuh_ingest_shared_secret": ""}
        )

        self.assertEqual(payload["summary"]["overall_posture"], "unavailable")
        self.assertEqual(payload["states"]["wazuh"]["posture"], "unavailable")
        self.assertEqual(
            payload["states"]["wazuh"]["reason"],
            "missing_wazuh_ingest_secret_or_proxy_secret",
        )

    @staticmethod
    def _doctor_config(**overrides: object) -> SimpleNamespace:
        values = {
            "host": "127.0.0.1",
            "postgres_dsn": "postgresql://control-plane.local/aegisops",
            "opensearch_url": "https://opensearch.local",
            "n8n_base_url": "<set-me>",
            "shuffle_base_url": "<set-me>",
            "wazuh_ingest_shared_secret": "reviewed-shared-secret",  # noqa: S106 - fixture
            "wazuh_ingest_reverse_proxy_secret": "reviewed-proxy-secret",  # noqa: S106 - fixture
            "protected_surface_reverse_proxy_secret": "",
            "ai_enablement_posture": "enabled",
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def _build_doctor_payload(
        self,
        *,
        config_overrides: dict[str, object] | None = None,
        metrics_overrides: dict[str, object] | None = None,
    ) -> dict[str, object]:
        metrics = {
            "alerts": {"total": 1},
            "cases": {"total": 1, "open": 1},
            "action_requests": {
                "total": 0,
                "pending_approval": 0,
                "approved": 0,
                "executing": 0,
                "unresolved": 0,
            },
            "action_executions": {
                "total": 0,
                "dispatching": 0,
                "queued": 0,
                "running": 0,
                "terminal": 0,
            },
            "reconciliations": {
                "total": 0,
                "pending": 0,
                "mismatched": 0,
                "stale": 0,
                "by_ingest_disposition": {},
            },
            "source_health": {
                "tracked_sources": 1,
                "overall_state": "healthy",
                "sources": {"wazuh": {"state": "healthy"}},
            },
        }
        if metrics_overrides:
            metrics.update(metrics_overrides)
        return build_doctor_snapshot(
            config=self._doctor_config(**(config_overrides or {})),
            readiness_payload={
                "read_only": True,
                "status": "ready",
                "metrics": metrics,
            },
        ).to_dict()

    @staticmethod
    def _recommended_families(payload: dict[str, object]) -> set[str]:
        return {
            str(entry["state_family"])
            for entry in payload["recommended_next_steps"]
        }


if __name__ == "__main__":
    unittest.main()
