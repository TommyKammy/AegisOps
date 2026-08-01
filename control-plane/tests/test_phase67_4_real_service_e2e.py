from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


CONTROL_PLANE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CONTROL_PLANE_ROOT.parent
LAB_ROOT = CONTROL_PLANE_ROOT / "deployment" / "phase-67-integration-lab"
E2E_ROOT = LAB_ROOT / "e2e"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validator = _load_module(
    "phase67_4_evidence_validator",
    E2E_ROOT / "validate_evidence_manifest.py",
)
journey = _load_module(
    "phase67_4_real_journey",
    E2E_ROOT / "run_real_journey.py",
)
SCHEMA = validator.load_json(E2E_ROOT / "evidence-manifest.schema.json")


def _manifest() -> dict[str, object]:
    snapshot_id = "phase67-snapshot-0123456789abcdef"
    observed_at = "2026-08-01T10:00:00Z"
    steps = [
        {
            "step": index,
            "name": name,
            "status": "passed",
            "snapshot_id": snapshot_id,
            "observed_at": observed_at,
            "evidence_refs": [f"evidence:step-{index}"],
        }
        for index, name in enumerate(validator.STEP_NAMES, start=1)
    ]
    return {
        "schema_version": validator.SCHEMA_VERSION,
        "captured_at": observed_at,
        "source_mode": "real_services",
        "trial_run_id": "phase67-e2e-20260801T100000Z-0123456789ab",
        "snapshot": {
            "snapshot_id": snapshot_id,
            "repository_revision": "a" * 40,
            "compose_sha256": "b" * 64,
            "evidence_schema_sha256": "c" * 64,
            "runtime_artifact_sha256": "d" * 64,
            "host_architecture": "arm64",
            "docker_context": "colima",
            "colima_profile": "default",
            "selected_profile": "full",
            "images": [
                {
                    "service": "control-plane",
                    "immutable_reference": "control-plane@sha256:" + "e" * 64,
                },
                {
                    "service": "wazuh-manager",
                    "immutable_reference": "wazuh/wazuh-manager@sha256:"
                    + "f" * 64,
                },
                {
                    "service": "shuffle-backend",
                    "immutable_reference": "frikky/shuffle-backend@sha256:"
                    + "1" * 64,
                },
            ],
        },
        "steps": steps,
        "identifiers": {
            "wazuh_manager_id": "wazuh.manager",
            "wazuh_agent_id": "000",
            "wazuh_rule_id": "5710",
            "native_wazuh_alert_id": "1754042400.123456",
            "aegisops_alert_id": "alert-a1b2c3d4",
            "finding_id": "finding-a1b2c3d4",
            "case_id": "case-a1b2c3d4",
            "denied_action_request_id": "action-denied-a1b2c3d4",
            "denied_approval_decision_id": "approval-denied-a1b2c3d4",
            "action_request_id": "action-a1b2c3d4",
            "approval_decision_id": "approval-a1b2c3d4",
            "delegation_id": "delegation-a1b2c3d4",
            "shuffle_workflow_id": "42c15ad7-ff1f-4d50-bf6c-a1b2c3d4e5f6",
            "shuffle_workflow_version": (
                "notify_identity_owner-v1-reviewed-2026-05-03"
            ),
            "shuffle_execution_id": "2f90e91d-e217-42da-bd83-a1b2c3d4e5f6",
            "expected_receipt_id": "phase67-receipt-a1b2c3d4",
            "action_execution_id": "action-execution-a1b2c3d4",
            "reconciliation_id": "reconciliation-a1b2c3d4",
            "report_id": "phase67-report-a1b2c3d4",
        },
        "human_control": {
            "requester_identity": "phase67-lab-requester",
            "approver_identity": "phase67-lab-approver",
            "denied_action_execution_count": 0,
            "denied_dispatch_rejected": True,
            "approval_source": "aegisops_approval_decision_record",
        },
        "idempotency": {
            "wazuh_first_disposition": "created",
            "wazuh_duplicate_disposition": "deduplicated",
            "wazuh_alert_identity_preserved": True,
            "shuffle_execution_count": 1,
            "receipt_replay_reconciliation_id": "reconciliation-a1b2c3d4",
            "receipt_identity_preserved": True,
        },
        "negative_cases": {
            key: {
                "status": "rejected" if key != "failed_execution" else "contained",
                "authority_delta": 0,
                "evidence_ref": f"negative:{key}",
            }
            for key in validator.NEGATIVE_CASE_KEYS
        },
        "restart": {
            "performed": True,
            "records_persisted": True,
            "checked_identifiers": [
                "aegisops_alert_id",
                "case_id",
                "action_request_id",
                "action_execution_id",
                "reconciliation_id",
            ],
        },
        "report": {
            "report_id": "phase67-report-a1b2c3d4",
            "sha256": "2" * 64,
            "source_of_truth": "aegisops_authoritative_records",
            "redacted": True,
        },
        "cleanup": {
            "mode": "non_destructive",
            "containers_stopped": True,
            "data_preserved": True,
        },
        "authority_posture": "aegisops_records_remain_authoritative",
        "verdict": "integration_trial_passed_with_owned_limitations",
        "limitations": [
            {
                "limitation_id": "single-host",
                "owner": "AegisOps platform operations",
                "status": "accepted",
                "description": "One bounded non-production host was exercised.",
                "follow_up_issue": None,
            }
        ],
    }


class Phase674RealServiceE2ETests(unittest.TestCase):
    def test_valid_evidence_enforces_the_complete_real_identifier_chain(self) -> None:
        validator.validate_manifest(_manifest(), SCHEMA)

    def test_validator_rejects_placeholder_and_synthetic_live_ids(self) -> None:
        for field_name, value in (
            ("native_wazuh_alert_id", "fixture-alert-1"),
            ("shuffle_execution_id", "shuffle-run-123"),
            ("case_id", "case-placeholder-1"),
        ):
            with self.subTest(field_name=field_name):
                manifest = _manifest()
                manifest["identifiers"][field_name] = value
                with self.assertRaises(validator.EvidenceValidationError):
                    validator.validate_manifest(manifest, SCHEMA)

    def test_validator_rejects_mixed_snapshots_and_missing_steps(self) -> None:
        mixed = _manifest()
        mixed["steps"][8]["snapshot_id"] = "phase67-snapshot-fedcba9876543210"
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "mixed snapshot",
        ):
            validator.validate_manifest(mixed, SCHEMA)

        missing = _manifest()
        missing["steps"].pop()
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "exactly 15 steps",
        ):
            validator.validate_manifest(missing, SCHEMA)

    def test_validator_rejects_inferred_human_control_or_receipt_success(self) -> None:
        same_actor = _manifest()
        same_actor["human_control"]["approver_identity"] = same_actor[
            "human_control"
        ]["requester_identity"]
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "requester and approver",
        ):
            validator.validate_manifest(same_actor, SCHEMA)

        denied_dispatch = _manifest()
        denied_dispatch["human_control"]["denied_action_execution_count"] = 1
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "denied action",
        ):
            validator.validate_manifest(denied_dispatch, SCHEMA)

        replay = _manifest()
        replay["idempotency"]["receipt_replay_reconciliation_id"] = (
            "reconciliation-second"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "reuse the reconciliation ID",
        ):
            validator.validate_manifest(replay, SCHEMA)

    def test_validator_rejects_secret_values_and_private_host_paths(self) -> None:
        for description in (
            "Bearer secret-value",
            "Read the capture under /Users/alice/private/evidence.json",  # publishable-path-hygiene: allowlist -- adversarial fixture
            "https://operator:password@shuffle.local/api",
        ):
            with self.subTest(description=description):
                manifest = _manifest()
                manifest["limitations"][0]["description"] = description
                with self.assertRaisesRegex(
                    validator.EvidenceValidationError,
                    "secret value or private host path",
                ):
                    validator.validate_manifest(manifest, SCHEMA)

    def test_blocked_verdict_requires_one_owned_blocker_and_no_later_steps(self) -> None:
        manifest = _manifest()
        manifest["verdict"] = "integration_trial_blocked"
        for key in validator.IDENTIFIER_KEYS:
            manifest["identifiers"][key] = None
        for key in manifest["human_control"]:
            manifest["human_control"][key] = None
        for key in manifest["idempotency"]:
            manifest["idempotency"][key] = None
        for case in manifest["negative_cases"].values():
            case.update(status=None, authority_delta=None, evidence_ref=None)
        manifest["restart"] = {
            "performed": None,
            "records_persisted": None,
            "checked_identifiers": [],
        }
        manifest["report"] = {
            "report_id": None,
            "sha256": None,
            "source_of_truth": None,
            "redacted": None,
        }
        manifest["cleanup"] = {
            "mode": None,
            "containers_stopped": None,
            "data_preserved": None,
        }
        manifest["limitations"][0]["status"] = "blocking"
        for index, step in enumerate(manifest["steps"]):
            if index < 2:
                continue
            step["status"] = "blocked" if index == 2 else "not_run"
            if index == 2:
                step["blocker"] = {
                    "owner": "AegisOps integration engineering",
                    "reason": "Reviewed service bootstrap did not complete.",
                }
        validator.validate_manifest(manifest, SCHEMA)

        manifest["steps"][3]["status"] = "passed"
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "steps after a blocker",
        ):
            validator.validate_manifest(manifest, SCHEMA)

    def test_runner_uses_distinct_actors_and_deterministic_record_ids(self) -> None:
        self.assertNotEqual(journey.REQUESTER_IDENTITY, journey.APPROVER_IDENTITY)
        first = journey._identifiers_for_trial(
            "phase67-e2e-20260801T100000Z-0123456789ab"
        )
        second = journey._identifiers_for_trial(
            "phase67-e2e-20260801T100000Z-0123456789ab"
        )
        self.assertEqual(first, second)
        self.assertNotEqual(
            first["denied_action_request_id"],
            first["action_request_id"],
        )

    def test_operator_runner_binds_full_scope_restart_and_cleanup(self) -> None:
        runner = (LAB_ROOT / "run-e2e-trial.sh").read_text(encoding="utf-8")
        self.assertIn('"${LAB_DIR}/up.sh" full', runner)
        self.assertIn("AEGISOPS_LAB_TRIAL_SCOPE=full", runner)
        self.assertIn("docker_lab inspect ${container_ids}", runner)
        self.assertIn('docker_context="${AEGISOPS_LAB_DOCKER_CONTEXT}"', runner)
        self.assertNotIn("docker inspect ${container_ids}", runner)
        self.assertNotIn("docker context show", runner)
        self.assertIn("verify-restart", runner)
        self.assertIn(
            ".journey | .aegisops_alert_id = .alert_id",
            runner,
        )
        self.assertIn('"${LAB_DIR}/cleanup.sh"', runner)
        self.assertNotIn("destroy-data.sh", runner)
        real_journey = (E2E_ROOT / "run_real_journey.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('lifecycle_state="rejected"', real_journey)
        self.assertNotIn('lifecycle_state="denied"', real_journey)
        compose = (LAB_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("./e2e:/opt/aegisops/phase67-e2e:ro", compose)


if __name__ == "__main__":
    unittest.main()
