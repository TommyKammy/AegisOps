from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest


CONTROL_PLANE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CONTROL_PLANE_ROOT.parent
LAB_ROOT = CONTROL_PLANE_ROOT / "deployment" / "phase-67-integration-lab"
E2E_ROOT = LAB_ROOT / "e2e"
WAZUH_ROOT = LAB_ROOT / "wazuh"
SHUFFLE_ROOT = LAB_ROOT / "shuffle"


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
builder = _load_module(
    "phase67_4_evidence_builder",
    E2E_ROOT / "build_evidence.py",
)
swarm_labeler = _load_module(
    "phase67_4_swarm_service_labeler",
    E2E_ROOT / "update_swarm_service_labels.py",
)
SCHEMA = validator.load_json(E2E_ROOT / "evidence-manifest.schema.json")


class _FakeDockerEngine:
    def __init__(self, service: dict, after_update=None) -> None:
        self.service = deepcopy(service)
        self.after_update = after_update
        self.api_checked = False
        self.updated_spec: dict | None = None

    def assert_api_version_supported(self) -> None:
        self.api_checked = True

    def get_service(self, service_id: str) -> dict:
        if self.service["ID"] != service_id:
            raise AssertionError("unexpected service ID")
        return deepcopy(self.service)

    def update_service(
        self,
        service_id: str,
        version: int,
        spec: dict,
    ) -> None:
        if self.service["ID"] != service_id:
            raise AssertionError("unexpected service ID")
        if self.service["Version"]["Index"] != version:
            raise AssertionError("unexpected service version")
        self.updated_spec = deepcopy(spec)
        self.service["Spec"] = deepcopy(spec)
        self.service["Version"]["Index"] += 1
        if self.after_update is not None:
            self.after_update(self.service)


def _hybrid_network_worker_service() -> dict:
    return {
        "ID": "wo7au34eetl5tc0id1jzxxu9e",
        "Version": {"Index": 2342226},
        "Spec": {
            "Name": "shuffle-workers",
            "Labels": {"shuffle-existing": "retained"},
            "TaskTemplate": {
                "ContainerSpec": {
                    "Image": (
                        "ghcr.io/shuffle/shuffle-worker:2.2.1@sha256:"
                        + "9" * 64
                    )
                },
                "Networks": [{"Target": "shuffle-overlay"}],
            },
            "Networks": [
                {"Target": "shuffle-overlay"},
                {"Target": "ingress"},
            ],
            "EndpointSpec": {
                "Mode": "vip",
                "Ports": [
                    {
                        "Protocol": "tcp",
                        "TargetPort": 33333,
                        "PublishedPort": 33333,
                        "PublishMode": "ingress",
                    }
                ],
            },
        },
    }


def _manifest() -> dict[str, object]:
    trial_run_id = "phase67-e2e-20260801T100000Z-0123456789ab"
    snapshot: dict[str, object] = {
        "repository_revision": "a" * 40,
        "compose_sha256": "b" * 64,
        "evidence_schema_sha256": "c" * 64,
        "runtime_artifact_sha256": "d" * 64,
        "shuffle_api_workflow_id": "42c15ad7-ff1f-4d50-bf6c-a1b2c3d4e5f6",
        "shuffle_reviewed_workflow_sha256": "2" * 64,
        "shuffle_live_workflow_sha256": "4" * 64,
        "host_architecture": "arm64",
        "docker_context": "colima",
        "colima_profile": "default",
        "selected_profile": "full",
        "images": [
            {
                "service": "control-plane",
                "immutable_reference": "control-plane@sha256:" + "e" * 64,
            },
            *(
                {
                    "service": service,
                    "immutable_reference": immutable_reference,
                    **(
                        {"runtime_image_id": "sha256:" + "f" * 64}
                        if service in validator.CURRENT_RUNTIME_IMAGE_ID_SERVICES
                        else {}
                    ),
                }
                for service, immutable_reference in sorted(
                    validator.REVIEWED_IMMUTABLE_IMAGE_REFERENCES.items()
                )
            ),
        ],
    }
    snapshot_id = validator._snapshot_identifier(trial_run_id, snapshot)
    snapshot["snapshot_id"] = snapshot_id
    approval_confirmed_at = "2026-08-01T10:00:07.500000Z"
    evaluated_at = "2026-08-01T10:00:15Z"
    steps = [
        {
            "step": index,
            "name": name,
            "status": "passed",
            "snapshot_id": snapshot_id,
            "observed_at": f"2026-08-01T10:00:{index:02d}Z",
            "evidence_refs": list(builder.STEP_EVIDENCE_REFS[index - 1]),
        }
        for index, name in enumerate(validator.STEP_NAMES, start=1)
    ]
    return {
        "schema_version": validator.SCHEMA_VERSION,
        "captured_at": "2026-08-01T10:00:16Z",
        "source_mode": "real_services",
        "trial_run_id": trial_run_id,
        "snapshot": snapshot,
        "steps": steps,
        "identifiers": {
            "wazuh_manager_id": "wazuh.manager",
            "wazuh_agent_id": "000",
            "wazuh_rule_id": "5710",
            "native_wazuh_alert_id": "1754042400.123456",
            "aegisops_alert_id": "alert-a1b2c3d4",
            "finding_id": (
                "finding:wazuh:rule:5710:source:agent:000:"
                "alert:1754042400.123456"
            ),
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
            "approver_identity": "local-operator:reviewer",
            "authenticated_approver_identity": "local-operator:reviewer",
            "denied_action_execution_count": 0,
            "denied_dispatch_rejected": True,
            "approval_source": "interactive_local_operator_ceremony",
            "approval_method": "tty_challenge",
            "approval_challenge_sha256": "4" * 64,
            "approval_confirmed_at": approval_confirmed_at,
        },
        "idempotency": {
            "wazuh_first_disposition": "created",
            "wazuh_duplicate_disposition": "deduplicated",
            "wazuh_alert_identity_preserved": True,
            "wazuh_replay_observed_at": "2026-08-01T10:00:04.500000Z",
            "shuffle_execution_count": 1,
            "receipt_replay_reconciliation_id": "reconciliation-a1b2c3d4",
            "receipt_identity_preserved": True,
            "shuffle_receipt_replay_observed_at": (
                "2026-08-01T10:00:12Z"
            ),
        },
        "negative_cases": {
            key: {
                "observed_at": (
                    "2026-08-01T10:00:02.500000Z"
                    if key in {"invalid_credential", "proxy_bypass"}
                    else "2026-08-01T10:00:13Z"
                ),
                "status": "rejected" if key != "failed_execution" else "contained",
                "authority_before": 10,
                "authority_after": (
                    11
                    if key in {"failed_execution", "reconciliation_mismatch"}
                    else 10
                ),
                "measurement_source": (
                    "aegisops_authoritative_alert_count"
                    if key in {"invalid_credential", "proxy_bypass"}
                    else "aegisops_authoritative_record_count"
                ),
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
                "denied_action_request_id",
                "denied_approval_decision_id",
                "action_request_id",
                "approval_decision_id",
                "action_execution_id",
                "reconciliation_id",
                "wazuh_reconciliation_ids",
            ],
        },
        "report": {
            "report_id": "phase67-report-a1b2c3d4",
            "sha256": "2" * 64,
            "source_of_truth": "aegisops_authoritative_records",
            "redacted": True,
        },
        "evaluation": {
            "evaluated_at": evaluated_at,
            "verdict": "integration_trial_passed_with_owned_limitations",
            "ga_accepted": False,
            "sha256": "5" * 64,
        },
        "artifacts": {
            "retention": "local_mode_0600",
            "directory_name": (
                "phase67-e2e-20260801T100000Z-0123456789ab-artifacts"
            ),
            "files": [
                {
                    "name": name,
                    "sha256": (
                        "5" * 64
                        if name == "evaluation-record.json"
                        else "6" * 64
                    ),
                }
                for name in sorted(validator.ARTIFACT_NAMES)
            ],
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
                "limitation_id": "phase67-single-host",
                "owner": "AegisOps platform operations",
                "status": "accepted",
                "description": "One bounded non-production host was exercised.",
                "follow_up_issue": None,
            },
            {
                "limitation_id": "phase67-bounded-connectors",
                "owner": "AegisOps integration engineering",
                "status": "follow_up_required",
                "description": "One Wazuh rule and one Shuffle workflow were exercised.",
                "follow_up_issue": None,
            },
            {
                "limitation_id": "phase67-ga-gates-open",
                "owner": "AegisOps release owner",
                "status": "blocking",
                "description": "Production and GA gates remain open.",
                "follow_up_issue": None,
            },
        ],
    }


def _evaluation_record(manifest: dict[str, object]) -> dict[str, object]:
    snapshot = manifest["snapshot"]
    evaluation = manifest["evaluation"]
    limitations = manifest["limitations"]
    assert isinstance(snapshot, dict)
    assert isinstance(evaluation, dict)
    assert isinstance(limitations, list)
    return {
        "schema_version": builder.PREREQUISITE_EVALUATION_SCHEMA_VERSION,
        "trial_run_id": manifest["trial_run_id"],
        "snapshot_id": snapshot["snapshot_id"],
        "repository_revision": snapshot["repository_revision"],
        "evaluated_at": evaluation["evaluated_at"],
        "verdict": evaluation["verdict"],
        "ga_accepted": evaluation["ga_accepted"],
        "limitation_ids": [
            limitation["limitation_id"]
            for limitation in limitations
            if isinstance(limitation, dict)
        ],
    }


def _wazuh_manifest() -> dict[str, object]:
    return {
        "schema_version": "phase67-wazuh-intake-evidence-v1",
        "source_mode": "real_wazuh",
        "fixture_provenance": "live_capture_sanitized",
        "captured_at": "2026-07-29T00:00:00Z",
        "repository_revision": "a" * 40,
        "worktree_artifact_digest": "b" * 64,
        "runtime_artifact_digest": "b" * 64,
        "wazuh_manager_health": "healthy",
        "native_wazuh_alert_id": "phase67-native-alert",
        "native_wazuh_manager_id": "wazuh.manager",
        "native_wazuh_agent_id": "000",
        "native_wazuh_rule_id": "5710",
        "native_event_timestamp": "2026-07-29T00:00:00+00:00",
        "aegisops_alert_id": "alert-phase67",
        "negative_boundary": {
            "baseline_alert_count": 3,
            "after_alert_count": 3,
            "authoritative_alert_delta": 0,
        },
        "first_delivery": {
            "http_status": 202,
            "disposition": "created",
            "finding_id": (
                "finding:wazuh:rule:5710:source:agent:000:"
                "alert:phase67-native-alert"
            ),
            "reconciliation_id": "reconciliation-created",
        },
        "duplicate_delivery": {
            "http_status": 202,
            "disposition": "deduplicated",
            "finding_id": (
                "finding:wazuh:rule:5710:source:agent:000:"
                "alert:phase67-native-alert"
            ),
            "reconciliation_id": "reconciliation-deduplicated",
        },
        "analyst_queue": {
            "source_system": "wazuh",
            "case_id": None,
        },
        "case_promotion": "not_performed",
        "authority_boundary": "aegisops_admission_is_authoritative",
    }


def _compose_status_inventory(snapshot: dict[str, object]) -> list[dict[str, object]]:
    services = {
        image["service"]
        for image in snapshot["images"]
        if image["service"] not in builder.RUNTIME_ONLY_IMAGE_SERVICES
    }
    inventory: list[dict[str, object]] = []
    for service in sorted(services):
        if service in builder.COMPLETED_COMPOSE_SERVICES:
            inventory.append(
                {
                    "Service": service,
                    "State": "exited",
                    "Health": "",
                    "ExitCode": 0,
                }
            )
            continue
        inventory.append(
            {
                "Service": service,
                "State": "running",
                "Health": (
                    ""
                    if service in builder.COMPOSE_SERVICES_WITHOUT_HEALTHCHECKS
                    else "healthy"
                ),
                "ExitCode": 0,
            }
        )
    return inventory


class Phase674RealServiceE2ETests(unittest.TestCase):
    def test_valid_evidence_enforces_the_complete_real_identifier_chain(self) -> None:
        self.assertEqual(builder.STEP_NAMES, validator.STEP_NAMES)
        self.assertEqual(
            builder.REVIEWED_SHUFFLE_WORKFLOW_VERSION,
            validator.REVIEWED_SHUFFLE_WORKFLOW_VERSION,
        )
        self.assertEqual(
            builder.REVIEWED_SHUFFLE_WORKFLOW_VERSION,
            journey.REVIEWED_SHUFFLE_WORKFLOW_VERSION,
        )
        self.assertEqual(
            builder.NEGATIVE_PROBE_APPROVER_IDENTITY,
            journey.NEGATIVE_PROBE_APPROVER_IDENTITY,
        )
        self.assertEqual(
            builder.STEP_NAMES[-1],
            "record_prerequisite_evaluation",
        )
        self.assertEqual(builder.STEP_EVIDENCE_REFS, validator.STEP_EVIDENCE_REFS)
        self.assertEqual(
            builder.LIMITATION_STATUSES,
            validator.OWNED_LIMITATION_STATUSES,
        )
        self.assertEqual(builder.CURRENT_TRIAL_VERDICT, validator.PASSED_VERDICT)
        self.assertEqual(
            builder.PREREQUISITE_EVALUATION_SCHEMA_VERSION,
            validator.PREREQUISITE_EVALUATION_SCHEMA_VERSION,
        )
        validator.validate_manifest(_manifest(), SCHEMA)

    def test_published_file_validation_rehashes_the_complete_packet(self) -> None:
        manifest = _manifest()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts_directory = root / manifest["artifacts"]["directory_name"]
            artifacts_directory.mkdir()
            for index, item in enumerate(manifest["artifacts"]["files"]):
                if item["name"] == "evaluation-record.json":
                    payload = (
                        json.dumps(
                            _evaluation_record(manifest),
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                    ).encode()
                else:
                    payload = f"artifact-{index}-{item['name']}\n".encode()
                (artifacts_directory / item["name"]).write_bytes(payload)
                item["sha256"] = hashlib.sha256(payload).hexdigest()
                if item["name"] == "evaluation-record.json":
                    manifest["evaluation"]["sha256"] = item["sha256"]
            report_path = root / "report.json"
            report_payload = b'{"source_of_truth":"aegisops_authoritative_records"}\n'
            report_path.write_bytes(report_payload)
            manifest["report"]["sha256"] = hashlib.sha256(
                report_payload
            ).hexdigest()

            validator.validate_published_files(
                manifest,
                report_path,
                artifacts_directory,
            )
            original_loader = validator._load_validated_manifest
            try:
                validator._load_validated_manifest = lambda *_args: manifest
                self.assertEqual(
                    validator.main(
                        (
                            "--published",
                            str(root / "schema.json"),
                            str(root / "evidence.json"),
                            str(report_path),
                            str(artifacts_directory),
                        )
                    ),
                    0,
                )
            finally:
                validator._load_validated_manifest = original_loader

            first_artifact = artifacts_directory / manifest["artifacts"][
                "files"
            ][0]["name"]
            first_artifact.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(
                validator.EvidenceValidationError,
                "published artifact .* digest does not match",
            ):
                validator.validate_published_files(
                    manifest,
                    report_path,
                    artifacts_directory,
                )
            first_payload = (
                "artifact-0-" + manifest["artifacts"]["files"][0]["name"] + "\n"
            ).encode()
            first_artifact.write_bytes(first_payload)

            unexpected = artifacts_directory / "unlisted-secret.txt"
            unexpected.write_text("unlisted\n", encoding="utf-8")
            with self.assertRaisesRegex(
                validator.EvidenceValidationError,
                "file set does not match",
            ):
                validator.validate_published_files(
                    manifest,
                    report_path,
                    artifacts_directory,
                )
            unexpected.unlink()

            report_path.write_text("tampered report\n", encoding="utf-8")
            with self.assertRaisesRegex(
                validator.EvidenceValidationError,
                "published report digest does not match",
            ):
                validator.validate_published_files(
                    manifest,
                    report_path,
                    artifacts_directory,
                )

    def test_published_file_validation_rebinds_evaluation_record(self) -> None:
        manifest = _manifest()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts_directory = root / manifest["artifacts"]["directory_name"]
            artifacts_directory.mkdir()
            evaluation_item = None
            for index, item in enumerate(manifest["artifacts"]["files"]):
                if item["name"] == "evaluation-record.json":
                    evaluation_item = item
                    payload = (
                        json.dumps(
                            _evaluation_record(manifest),
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                    ).encode()
                else:
                    payload = f"artifact-{index}-{item['name']}\n".encode()
                (artifacts_directory / item["name"]).write_bytes(payload)
                item["sha256"] = hashlib.sha256(payload).hexdigest()
            assert evaluation_item is not None
            manifest["evaluation"]["sha256"] = evaluation_item["sha256"]
            report_path = root / "report.json"
            report_payload = b'{"source_of_truth":"aegisops_authoritative_records"}\n'
            report_path.write_bytes(report_payload)
            manifest["report"]["sha256"] = hashlib.sha256(
                report_payload
            ).hexdigest()

            validator.validate_published_files(
                manifest,
                report_path,
                artifacts_directory,
            )
            mismatches = {
                "schema_version": "phase67.4-prerequisite-evaluation-v0",
                "trial_run_id": "phase67-e2e-20260801T100001Z-0123456789ab",
                "snapshot_id": "sha256:" + "0" * 64,
                "repository_revision": "0" * 40,
                "evaluated_at": "2026-08-01T10:00:14Z",
                "verdict": "integration_trial_failed",
                "ga_accepted": True,
                "limitation_ids": ["phase67-single-host"],
            }
            evaluation_path = artifacts_directory / "evaluation-record.json"
            for field, replacement in mismatches.items():
                with self.subTest(field=field):
                    record = _evaluation_record(manifest)
                    record[field] = replacement
                    payload = (
                        json.dumps(
                            record,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                    ).encode()
                    evaluation_path.write_bytes(payload)
                    digest = hashlib.sha256(payload).hexdigest()
                    evaluation_item["sha256"] = digest
                    manifest["evaluation"]["sha256"] = digest
                    with self.assertRaisesRegex(
                        validator.EvidenceValidationError,
                        f"published evaluation record {field} does not match",
                    ):
                        validator.validate_published_files(
                            manifest,
                            report_path,
                            artifacts_directory,
                        )

    def test_schema_selects_exact_historical_and_current_profiles(
        self,
    ) -> None:
        images_schema = SCHEMA["properties"]["snapshot"]["properties"]["images"]
        self.assertNotIn("minItems", images_schema)
        self.assertNotIn("maxItems", images_schema)
        current_images = SCHEMA["$defs"]["current_image_inventory"][
            "properties"
        ]["snapshot"]["properties"]["images"]
        legacy_images = SCHEMA["$defs"]["legacy_blocked_image_inventory"][
            "properties"
        ]["snapshot"]["properties"]["images"]
        self.assertEqual(
            current_images["minItems"],
            len(validator.EXPECTED_FULL_PROFILE_IMAGE_SERVICES),
        )
        self.assertEqual(
            current_images["maxItems"],
            len(validator.EXPECTED_FULL_PROFILE_IMAGE_SERVICES),
        )
        self.assertEqual(
            SCHEMA["$defs"]["current_image_inventory"],
            validator._schema_image_inventory_profile(
                validator.EXPECTED_FULL_PROFILE_IMAGE_SERVICES,
                runtime_image_id_services=(
                    validator.CURRENT_RUNTIME_IMAGE_ID_SERVICES
                ),
            ),
        )
        self.assertEqual(
            len(_manifest()["snapshot"]["images"]),
            current_images["maxItems"],
        )
        historical = validator.load_json(E2E_ROOT / "sample-evidence.json")
        self.assertEqual(
            legacy_images["minItems"],
            len(historical["snapshot"]["images"]),
        )
        self.assertEqual(legacy_images["maxItems"], legacy_images["minItems"])
        self.assertEqual(
            SCHEMA["$defs"]["legacy_blocked_image_inventory"],
            validator._schema_image_inventory_profile(
                validator.LEGACY_BLOCKED_IMAGE_SERVICES,
            ),
        )
        legacy_identity = SCHEMA["$defs"]["legacy_blocked_identity"][
            "properties"
        ]
        self.assertEqual(
            legacy_identity["trial_run_id"]["const"],
            historical["trial_run_id"],
        )
        self.assertEqual(
            legacy_identity["snapshot"]["properties"]["snapshot_id"]["const"],
            historical["snapshot"]["snapshot_id"],
        )
        self.assertEqual(
            legacy_identity["snapshot"]["properties"]["repository_revision"][
                "const"
            ],
            historical["snapshot"]["repository_revision"],
        )
        self.assertEqual(
            set(
                SCHEMA["properties"]["snapshot"]["properties"][
                    "host_architecture"
                ]["enum"]
            ),
            validator.SUPPORTED_HOST_ARCHITECTURES,
        )
        self.assertEqual(
            SCHEMA["$defs"]["current_step_journey"],
            validator._schema_ordered_step_journey(
                validator.STEP_NAMES,
                evidence_refs=validator.STEP_EVIDENCE_REFS,
            ),
        )
        self.assertEqual(
            SCHEMA["$defs"]["legacy_blocked_step_journey"],
            validator._schema_ordered_step_journey(
                validator.LEGACY_BLOCKED_STEP_NAMES,
                evidence_refs=validator.LEGACY_BLOCKED_STEP_EVIDENCE_REFS,
            ),
        )
        current_steps = SCHEMA["$defs"]["current_step_journey"][
            "properties"
        ]["steps"]["prefixItems"]
        self.assertEqual(
            [item["properties"]["step"]["const"] for item in current_steps],
            list(range(1, len(validator.STEP_NAMES) + 1)),
        )
        self.assertEqual(
            [item["properties"]["name"]["const"] for item in current_steps],
            list(validator.STEP_NAMES),
        )

    def test_schema_and_validator_share_the_reviewed_verdict_and_uuid_contracts(
        self,
    ) -> None:
        verdict_schema = SCHEMA["properties"]["verdict"]
        self.assertEqual(set(verdict_schema["enum"]), validator.VERDICTS)
        passed_branches = [
            branch
            for branch in SCHEMA["allOf"]
            if branch.get("if", {})
            .get("properties", {})
            .get("verdict", {})
            .get("const")
            == validator.PASSED_VERDICT
        ]
        self.assertEqual(len(passed_branches), 1)
        self.assertEqual(
            passed_branches[0],
            validator._schema_passed_verdict_contract(),
        )
        self.assertEqual(
            passed_branches[0]["then"]["properties"]["steps"]["items"][
                "properties"
            ]["status"],
            {"const": "passed"},
        )
        self.assertEqual(
            passed_branches[0]["then"]["properties"]["identifiers"],
            validator._schema_passed_verdict_contract()["then"]["properties"][
                "identifiers"
            ],
        )
        execution_schema = SCHEMA["properties"]["identifiers"]["properties"][
            "shuffle_execution_id"
        ]
        self.assertEqual(
            execution_schema["pattern"],
            validator.CANONICAL_UUID_PATTERN,
        )
        self.assertEqual(
            SCHEMA["properties"]["identifiers"]["properties"]["wazuh_rule_id"][
                "enum"
            ],
            [validator.REVIEWED_WAZUH_RULE_ID, None],
        )
        passed_properties = passed_branches[0]["then"]["properties"]
        self.assertEqual(
            set(passed_properties["idempotency"]["required"]),
            {
                "wazuh_replay_observed_at",
                "shuffle_receipt_replay_observed_at",
            },
        )
        for case_name in validator.NEGATIVE_CASE_KEYS:
            with self.subTest(case_name=case_name):
                case_contract = passed_properties["negative_cases"][
                    "properties"
                ][case_name]
                self.assertEqual(case_contract["required"], ["observed_at"])
                self.assertIs(
                    case_contract["properties"]["authority_delta"],
                    False,
                )
        for identity in (
            "requester_identity",
            "approver_identity",
            "authenticated_approver_identity",
        ):
            with self.subTest(identity=identity):
                self.assertEqual(
                    passed_properties["human_control"]["properties"][identity][
                        "type"
                    ],
                    "string",
                )
        self.assertEqual(
            passed_properties["restart"]["properties"]["performed"],
            {"const": True},
        )
        self.assertEqual(
            passed_properties["restart"]["properties"]["records_persisted"],
            {"const": True},
        )
        self.assertEqual(
            set(
                passed_properties["restart"]["properties"][
                    "checked_identifiers"
                ]["items"]["enum"]
            ),
            set(validator.RESTART_CHECKED_IDENTIFIER_FIELDS),
        )
        self.assertEqual(
            passed_properties["evaluation"]["properties"]["ga_accepted"],
            {"const": False},
        )
        self.assertEqual(
            passed_properties["evaluation"]["required"],
            list(validator.EVALUATION_KEYS),
        )
        for duplicate_identity in (
            "trial_run_id",
            "snapshot_id",
            "repository_revision",
        ):
            with self.subTest(duplicate_identity=duplicate_identity):
                self.assertIs(
                    passed_properties["evaluation"]["properties"][
                        duplicate_identity
                    ],
                    False,
                )

        unsupported_verdict = _manifest()
        unsupported_verdict["verdict"] = (
            "integration_trial_passed_ga_not_accepted"
        )
        unsupported_verdict["evaluation"]["verdict"] = (
            "integration_trial_passed_ga_not_accepted"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "reviewed vocabulary",
        ):
            validator.validate_manifest(unsupported_verdict, SCHEMA)

        drifted_schema = deepcopy(SCHEMA)
        drifted_schema["properties"]["verdict"]["enum"].append(
            "integration_trial_passed_ga_not_accepted"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "schema verdict vocabulary drifted",
        ):
            validator.validate_manifest(_manifest(), drifted_schema)

        drifted_uuid_schema = deepcopy(SCHEMA)
        drifted_uuid_schema["properties"]["identifiers"]["properties"][
            "shuffle_execution_id"
        ]["pattern"] = ".+"
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "schema Shuffle execution ID contract drifted",
        ):
            validator.validate_manifest(_manifest(), drifted_uuid_schema)

        drifted_image_schema = deepcopy(SCHEMA)
        drifted_image_schema["$defs"]["current_image_inventory"]["properties"][
            "snapshot"
        ]["properties"]["images"]["minItems"] -= 1
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "schema current image inventory contract drifted",
        ):
            validator.validate_manifest(_manifest(), drifted_image_schema)

        drifted_legacy_identity = deepcopy(SCHEMA)
        drifted_legacy_identity["$defs"]["legacy_blocked_identity"][
            "required"
        ].append("schema_version")
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "schema historical packet identity drifted",
        ):
            validator.validate_manifest(_manifest(), drifted_legacy_identity)

        drifted_rule_schema = deepcopy(SCHEMA)
        drifted_rule_schema["properties"]["identifiers"]["properties"][
            "wazuh_rule_id"
        ]["enum"] = ["999999", None]
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "schema Wazuh rule ID contract drifted",
        ):
            validator.validate_manifest(_manifest(), drifted_rule_schema)

    def test_snapshot_accepts_every_preflight_host_architecture(self) -> None:
        manifest = _manifest()
        for architecture in ("arm64", "aarch64", "amd64", "x86_64"):
            with self.subTest(architecture=architecture):
                snapshot = deepcopy(manifest["snapshot"])
                snapshot["host_architecture"] = architecture
                snapshot["snapshot_id"] = validator._snapshot_identifier(
                    manifest["trial_run_id"],
                    snapshot,
                )
                validator._validate_snapshot(
                    snapshot,
                    trial_run_id=manifest["trial_run_id"],
                )
        unsupported = deepcopy(manifest["snapshot"])
        unsupported["host_architecture"] = "ppc64le"
        unsupported["snapshot_id"] = validator._snapshot_identifier(
            manifest["trial_run_id"],
            unsupported,
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "host_architecture is not supported",
        ):
            validator._validate_snapshot(
                unsupported,
                trial_run_id=manifest["trial_run_id"],
            )

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

    def test_validator_requires_the_reviewed_wazuh_rule(self) -> None:
        manifest = _manifest()
        manifest["identifiers"]["wazuh_rule_id"] = "999999"
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "outside the reviewed detection contract",
        ):
            validator.validate_manifest(manifest, SCHEMA)

    def test_validator_binds_the_wazuh_agent_to_the_finding(self) -> None:
        manifest = _manifest()
        manifest["identifiers"]["wazuh_agent_id"] = "999"
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "finding ID is not bound",
        ):
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

    def test_validator_rejects_non_chronological_step_observations(self) -> None:
        manifest = _manifest()
        manifest["steps"][7]["observed_at"] = manifest["steps"][6]["observed_at"]
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "strictly chronological",
        ):
            validator.validate_manifest(manifest, SCHEMA)

    def test_validator_binds_component_observations_to_actual_subtrials(
        self,
    ) -> None:
        mutations = {
            "Wazuh negatives after detection": (
                lambda manifest: manifest["negative_cases"][
                    "invalid_credential"
                ].__setitem__("observed_at", "2026-08-01T10:00:03.500000Z"),
                "precede native detection",
            ),
            "Wazuh replay after promotion": (
                lambda manifest: manifest["idempotency"].__setitem__(
                    "wazuh_replay_observed_at",
                    "2026-08-01T10:00:05.500000Z",
                ),
                "precede case promotion",
            ),
            "Shuffle replay differs from step": (
                lambda manifest: manifest["idempotency"].__setitem__(
                    "shuffle_receipt_replay_observed_at",
                    "2026-08-01T10:00:11.500000Z",
                ),
                "must match journey step 12",
            ),
            "Shuffle negative differs from step": (
                lambda manifest: manifest["negative_cases"][
                    "malformed_receipt"
                ].__setitem__("observed_at", "2026-08-01T10:00:12.500000Z"),
                "must match journey step 13",
            ),
        }
        for name, (mutate, message) in mutations.items():
            with self.subTest(name=name):
                manifest = _manifest()
                mutate(manifest)
                with self.assertRaisesRegex(
                    validator.EvidenceValidationError,
                    message,
                ):
                    validator.validate_manifest(manifest, SCHEMA)

    def test_validator_binds_approval_evaluation_and_capture_times(self) -> None:
        temporal_mutations = {
            "approval before denial proof": (
                lambda manifest: manifest["human_control"].__setitem__(
                    "approval_confirmed_at",
                    "2026-08-01T10:00:06Z",
                ),
                "approval confirmation must follow denial proof",
            ),
            "approval after dispatch": (
                lambda manifest: manifest["human_control"].__setitem__(
                    "approval_confirmed_at",
                    "2026-08-01T10:00:09Z",
                ),
                "approval confirmation must follow denial proof",
            ),
            "evaluation differs from step": (
                lambda manifest: manifest["evaluation"].__setitem__(
                    "evaluated_at",
                    "2026-08-01T10:00:14.500000Z",
                ),
                "evaluation time must match",
            ),
            "capture predates last step": (
                lambda manifest: manifest.__setitem__(
                    "captured_at",
                    "2026-08-01T10:00:14Z",
                ),
                "capture time must not precede",
            ),
        }
        for name, (mutate, message) in temporal_mutations.items():
            with self.subTest(name=name):
                manifest = _manifest()
                mutate(manifest)
                with self.assertRaisesRegex(
                    validator.EvidenceValidationError,
                    message,
                ):
                    validator.validate_manifest(manifest, SCHEMA)

    def test_validator_rejects_unreviewed_step_evidence_references(self) -> None:
        manifest = _manifest()
        manifest["steps"][7]["evidence_refs"] = ["fake"]
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "reviewed step contract",
        ):
            validator.validate_manifest(manifest, SCHEMA)

    def test_failed_verdict_requires_one_terminal_failure(self) -> None:
        manifest = _manifest()
        steps = manifest["steps"]
        steps[7]["status"] = "failed"
        steps[7]["blocker"] = {
            "owner": "AegisOps integration engineering",
            "reason": "Reviewed dispatch failed closed.",
        }
        for step in steps[8:]:
            step["status"] = "not_run"
            step["evidence_refs"] = ["not-run:upstream-failure"]
        validator._validate_steps(
            steps,
            manifest["snapshot"]["snapshot_id"],
            "integration_trial_failed",
        )

        unreviewed_not_run = deepcopy(steps)
        unreviewed_not_run[8]["evidence_refs"] = ["fake"]
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "must record a not-run reason",
        ):
            validator._validate_steps(
                unreviewed_not_run,
                manifest["snapshot"]["snapshot_id"],
                "integration_trial_failed",
            )

        later_pass = deepcopy(steps)
        later_pass[9]["status"] = "passed"
        later_pass[9]["evidence_refs"] = list(builder.STEP_EVIDENCE_REFS[9])
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "steps after a failure must be not_run",
        ):
            validator._validate_steps(
                later_pass,
                manifest["snapshot"]["snapshot_id"],
                "integration_trial_failed",
            )

        impossible = deepcopy(steps)
        impossible[9]["status"] = "failed"
        impossible[9]["evidence_refs"] = list(builder.STEP_EVIDENCE_REFS[9])
        impossible[9]["blocker"] = {
            "owner": "AegisOps integration engineering",
            "reason": "A later step cannot fail after an unexecuted prerequisite.",
        }
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "exactly one failed step",
        ):
            validator._validate_steps(
                impossible,
                manifest["snapshot"]["snapshot_id"],
                "integration_trial_failed",
            )

    def test_builder_loads_a_complete_chronological_observation_log(self) -> None:
        start = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        lines = [
            json.dumps(
                {
                    "step": index,
                    "name": name,
                    "observed_at": (start + timedelta(seconds=index))
                    .isoformat()
                    .replace("+00:00", "Z"),
                }
            )
            for index, name in enumerate(builder.STEP_NAMES, start=1)
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "step-observations.jsonl"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            observations = builder._load_step_observations(path)
        self.assertEqual(len(observations), 15)
        self.assertEqual(observations[-1]["name"], builder.STEP_NAMES[-1])

    def test_builder_rejects_duplicate_keys_in_retained_json_inputs(self) -> None:
        with TemporaryDirectory() as directory:
            retained_json = Path(directory) / "journey.json"
            retained_json.write_text(
                '{"trial_run_id":"first","trial_run_id":"second"}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                builder._read_json(retained_json)

            observations = Path(directory) / "step-observations.jsonl"
            observations.write_text(
                '{"step":1,"step":2,"name":"capture_immutable_snapshot",'
                '"observed_at":"2026-08-01T10:00:01Z"}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "not valid JSON"):
                builder._load_step_observations(observations)

    def test_builder_parses_the_structured_prerequisite_contract(self) -> None:
        evaluation_path = REPO_ROOT / "docs" / "phase-67-prerequisite-evaluation.md"
        document = evaluation_path.read_text(encoding="utf-8")
        parsed = builder._parse_prerequisite_evaluation(document)
        self.assertEqual(parsed["direct_verdict"], "integration_trial_blocked")
        self.assertEqual(
            parsed["next_complete_trial_verdict"],
            builder.CURRENT_TRIAL_VERDICT,
        )
        self.assertEqual(parsed["ga_acceptance"], "not_accepted")

        mutations = {
            "unknown direct verdict": document.replace(
                "Direct verdict: `integration_trial_blocked`",
                "Direct verdict: `integration_trial_unknown`",
            ),
            "wrong next verdict": document.replace(
                "Next complete-trial verdict: "
                "`integration_trial_passed_with_owned_limitations`",
                "Next complete-trial verdict: `integration_trial_blocked`",
            ),
            "GA overclaim": document.replace(
                "GA acceptance: `not_accepted`",
                "GA acceptance: `accepted`",
            ),
            "duplicate field": (
                document + "\nDirect verdict: `integration_trial_blocked`\n"
            ),
        }
        for name, mutated in mutations.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                builder._parse_prerequisite_evaluation(mutated)

    def test_builder_preserves_real_wazuh_subtrial_observation_times(self) -> None:
        output = "\n".join(
            (
                "step_observation.wazuh_negative_cases=2026-08-01T09:59:59Z",
                "step_observation.trigger_real_wazuh_detection=2026-08-01T10:00:01Z",
                "step_observation.admit_wazuh_alert=2026-08-01T10:00:02Z",
                "step_observation.replay_wazuh_delivery=2026-08-01T10:00:03Z",
            )
        )
        observations = builder._load_wazuh_observations(output)
        self.assertEqual(
            observations["wazuh_negative_cases"],
            "2026-08-01T09:59:59Z",
        )
        self.assertEqual(
            observations["replay_wazuh_delivery"],
            "2026-08-01T10:00:03Z",
        )
        with self.assertRaisesRegex(ValueError, "exactly one"):
            builder._load_wazuh_observations(
                output.replace(
                    "step_observation.replay_wazuh_delivery=2026-08-01T10:00:03Z",
                    "",
                )
            )

    def test_builder_binds_wazuh_command_output_to_the_manifest(self) -> None:
        wazuh = {
            "native_wazuh_alert_id": "wazuh-native-alert-a1b2c3d4",
            "aegisops_alert_id": "alert-a1b2c3d4",
            "first_delivery": {"disposition": "created"},
            "duplicate_delivery": {"disposition": "deduplicated"},
        }
        output = "\n".join(
            (
                "PASS invalid_bearer_secret=403",
                "PASS proxy_bypass=403",
                "PASS negative_authoritative_alert_delta=0",
                "PASS native_wazuh_alert_id=wazuh-native-alert-a1b2c3d4",
                "PASS first_disposition=created",
                "PASS duplicate_disposition=deduplicated",
                "PASS analyst_queue_alert_id=alert-a1b2c3d4",
            )
        )
        builder._validate_wazuh_output_contract(output, wazuh)

        mutations = {
            "native alert mismatch": output.replace(
                "wazuh-native-alert-a1b2c3d4",
                "wazuh-native-alert-from-another-trial",
            ),
            "AegisOps alert mismatch": output.replace(
                "PASS analyst_queue_alert_id=alert-a1b2c3d4",
                "PASS analyst_queue_alert_id=alert-from-another-trial",
            ),
            "disposition mismatch": output.replace(
                "PASS duplicate_disposition=deduplicated",
                "PASS duplicate_disposition=created",
            ),
            "duplicate claim": output
            + "\nPASS native_wazuh_alert_id=wazuh-native-alert-a1b2c3d4",
        }
        for name, mutated in mutations.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                builder._validate_wazuh_output_contract(mutated, wazuh)

    def test_builder_requires_the_journey_embedded_report_to_match(self) -> None:
        report = {
            "export_id": "phase67-report-a1b2c3d4",
            "records": {"alert": [{"alert_id": "alert-a1b2c3d4"}]},
        }
        builder._validate_embedded_report({"report": deepcopy(report)}, report)

        mismatched = deepcopy(report)
        mismatched["records"]["alert"][0]["alert_id"] = (
            "alert-from-another-trial"
        )
        with self.assertRaisesRegex(ValueError, "embedded report does not match"):
            builder._validate_embedded_report({"report": mismatched}, report)

    def test_builder_rejects_unredacted_report_values_recursively(self) -> None:
        redacted_report = {
            "records": {
                "action_request": [
                    {
                        "credential_reference": "<redacted-secret>",
                        "reviewed_context": {
                            "source_path": "<redacted-local-path>/capture.json"
                        },
                    }
                ]
            }
        }
        self.assertTrue(builder._validate_report_redaction(redacted_report))

        unsafe_reports = (
            {"records": {"credential": "live-credential"}},
            {"records": {"context": {"password": "plaintext"}}},
            {"records": {"context": "Bearer live-token"}},
            {
                "records": {
                    "source_path": str(
                        Path("/") / "Users" / "operator" / "private.json"
                    )
                }
            },
        )
        for unsafe_report in unsafe_reports:
            with self.subTest(report=unsafe_report), self.assertRaisesRegex(
                ValueError,
                "unredacted",
            ):
                builder._validate_report_redaction(unsafe_report)

    def test_builder_binds_trial_and_wazuh_provenance_to_snapshot(self) -> None:
        trial_run_id = "phase67-e2e-20260801T100000Z-0123456789ab"
        snapshot = {
            "trial_run_id": trial_run_id,
            "repository_revision": "a" * 40,
            "runtime_artifact_sha256": "b" * 64,
        }
        preparation = {"trial_run_id": trial_run_id}
        journey_record = {"trial_run_id": trial_run_id}
        wazuh = {
            "repository_revision": "a" * 40,
            "runtime_artifact_digest": "b" * 64,
        }
        builder._validate_snapshot_artifact_bindings(
            snapshot,
            preparation,
            wazuh,
            journey_record,
        )

        mutations = (
            ("preparation", "trial_run_id", "phase67-e2e-other"),
            ("journey", "trial_run_id", "phase67-e2e-other"),
            ("wazuh", "repository_revision", "c" * 40),
            ("wazuh", "runtime_artifact_digest", "d" * 64),
        )
        for source_name, field_name, field_value in mutations:
            sources = {
                "preparation": deepcopy(preparation),
                "journey": deepcopy(journey_record),
                "wazuh": deepcopy(wazuh),
            }
            sources[source_name][field_name] = field_value
            with self.subTest(
                source=source_name,
                field=field_name,
            ), self.assertRaisesRegex(ValueError, "does not match the snapshot"):
                builder._validate_snapshot_artifact_bindings(
                    snapshot,
                    sources["preparation"],
                    sources["wazuh"],
                    sources["journey"],
                )

    def test_builder_binds_all_source_backed_step_observation_times(self) -> None:
        observations = [
            {
                "step": index,
                "name": name,
                "observed_at": f"2026-08-01T10:00:{index:02d}Z",
            }
            for index, name in enumerate(builder.STEP_NAMES, start=1)
        ]

        def source_payloads() -> dict[str, dict[str, object]]:
            return {
                "preparation": {
                    "step_observations": {
                        builder.STEP_NAMES[index]: observations[index][
                            "observed_at"
                        ]
                        for index in range(4, 7)
                    }
                },
                "wazuh_observations": {
                    builder.STEP_NAMES[index]: observations[index][
                        "observed_at"
                    ]
                    for index in range(2, 4)
                }
                | {
                    "wazuh_negative_cases": (
                        "2026-08-01T10:00:02.500000Z"
                    ),
                    "replay_wazuh_delivery": (
                        "2026-08-01T10:00:04.500000Z"
                    ),
                },
                "journey": {
                    "approval_confirmed_at": "2026-08-01T10:00:07.500000Z",
                    "step_observations": {
                        builder.STEP_NAMES[index]: observations[index][
                            "observed_at"
                        ]
                        for index in range(7, 13)
                    }
                },
                "restart": {"observed_at": observations[13]["observed_at"]},
                "evaluation_record": {
                    "evaluated_at": observations[14]["observed_at"]
                },
            }

        component_times = builder._validate_step_observation_sources(
            observations,
            **source_payloads(),
        )
        self.assertEqual(
            component_times,
            {
                "wazuh_negative_cases": "2026-08-01T10:00:02.500000Z",
                "replay_wazuh_delivery": "2026-08-01T10:00:04.500000Z",
                "shuffle_receipt_replay": "2026-08-01T10:00:12Z",
                "shuffle_negative_cases": "2026-08-01T10:00:13Z",
            },
        )
        for step_index in range(2, len(builder.STEP_NAMES)):
            with self.subTest(step=step_index + 1):
                sources = source_payloads()
                step_name = builder.STEP_NAMES[step_index]
                if step_index < 4:
                    sources["wazuh_observations"][step_name] = (
                        "2026-08-01T11:00:00Z"
                    )
                elif step_index < 7:
                    sources["preparation"]["step_observations"][step_name] = (
                        "2026-08-01T11:00:00Z"
                    )
                elif step_index < 13:
                    sources["journey"]["step_observations"][step_name] = (
                        "2026-08-01T11:00:00Z"
                    )
                elif step_index == 13:
                    sources["restart"]["observed_at"] = (
                        "2026-08-01T11:00:00Z"
                    )
                else:
                    sources["evaluation_record"]["evaluated_at"] = (
                        "2026-08-01T11:00:00Z"
                    )
                with self.assertRaisesRegex(
                    ValueError,
                    "does not use the authoritative",
                ):
                    builder._validate_step_observation_sources(
                        observations,
                        **sources,
                    )

        for observation_name, invalid_time, message in (
            (
                "wazuh_negative_cases",
                "2026-08-01T10:00:03.500000Z",
                "Wazuh negative probes",
            ),
            (
                "replay_wazuh_delivery",
                "2026-08-01T10:00:05.500000Z",
                "Wazuh replay",
            ),
        ):
            with self.subTest(observation_name=observation_name):
                sources = source_payloads()
                sources["wazuh_observations"][observation_name] = invalid_time
                with self.assertRaisesRegex(ValueError, message):
                    builder._validate_step_observation_sources(
                        observations,
                        **sources,
                    )

        for approval_confirmed_at in (
            "2026-08-01T10:00:06Z",
            "2026-08-01T10:00:09Z",
        ):
            with self.subTest(approval_confirmed_at=approval_confirmed_at):
                sources = source_payloads()
                sources["journey"]["approval_confirmed_at"] = (
                    approval_confirmed_at
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "approval confirmation must follow denial proof",
                ):
                    builder._validate_step_observation_sources(
                        observations,
                        **sources,
                    )

    def test_negative_receipt_probes_rollback_authoritative_execution(self) -> None:
        record_types = (
            journey.ActionRequestRecord,
            journey.ApprovalDecisionRecord,
            journey.ActionExecutionRecord,
            journey.ReconciliationRecord,
        )
        baseline_execution = SimpleNamespace(
            action_execution_id="execution-real-1",
            lifecycle_state="succeeded",
            provenance={"normalized_receipt": {"status": "succeeded"}},
        )

        class FakeStore:
            def __init__(self) -> None:
                self.records = {record_type: [] for record_type in record_types}
                self.records[journey.ActionExecutionRecord] = [baseline_execution]

            def list(self, record_type: object) -> tuple[object, ...]:
                return tuple(self.records[record_type])

            @contextmanager
            def transaction(self):
                saved = deepcopy(self.records)
                try:
                    yield
                except Exception:
                    self.records = saved
                    raise

        class FakeService:
            def __init__(self) -> None:
                self._store = FakeStore()
                self.reason_override: str | None = None

            def get_record(self, record_type: object, record_id: str) -> object | None:
                for record in self._store.list(record_type):
                    if getattr(record, "action_execution_id", None) == record_id:
                        return record
                return None

            def reconcile_action_execution(self, **kwargs: object) -> object:
                observed = kwargs["observed_executions"][0]
                if "payload_hash" not in observed:
                    raise ValueError("missing payload_hash")
                self._store.records[journey.ReconciliationRecord].append(
                    SimpleNamespace(reconciliation_id="probe")
                )
                if observed["status"] == "failed":
                    self._store.records[journey.ActionExecutionRecord][0] = (
                        SimpleNamespace(
                            action_execution_id="execution-real-1",
                            lifecycle_state="failed",
                            provenance={"normalized_receipt": {"status": "failed"}},
                        )
                    )
                mismatch_summary = (
                    "downstream execution failed and requires operator review"
                    if observed["status"] == "failed"
                    else "approved binding mismatch between authoritative "
                    "action execution and observed downstream execution"
                )
                return SimpleNamespace(
                    ingest_disposition="mismatch",
                    lifecycle_state="mismatched",
                    mismatch_summary=self.reason_override or mismatch_summary,
                )

        service = FakeService()
        results = journey._run_receipt_negative_probes(
            service=service,
            action=SimpleNamespace(action_request_id="action-real-1"),
            execution=baseline_execution,
            receipt={
                "execution_run_id": "real-run-1",
                "status": "succeeded",
                "payload_hash": "a" * 64,
            },
            compared_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(results["failed_execution"]["authority_delta"], 1)
        self.assertEqual(
            service.get_record(
                journey.ActionExecutionRecord,
                "execution-real-1",
            ),
            baseline_execution,
        )

        service.reason_override = "unrelated binding mismatch"
        with self.assertRaisesRegex(
            RuntimeError,
            "reconciliation reason does not match",
        ):
            journey._run_receipt_negative_probes(
                service=service,
                action=SimpleNamespace(action_request_id="action-real-1"),
                execution=baseline_execution,
                receipt={
                    "execution_run_id": "real-run-1",
                    "status": "succeeded",
                    "payload_hash": "a" * 64,
                },
                compared_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
            )

    def test_validator_rejects_missing_action_image_and_stale_evaluation(self) -> None:
        missing_image = _manifest()
        missing_image["snapshot"]["images"] = [
            image
            for image in missing_image["snapshot"]["images"]
            if image["service"] != "shuffle-action-image"
        ]
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "dynamic Shuffle action image",
        ):
            validator.validate_manifest(missing_image, SCHEMA)

        incomplete_inventory = _manifest()
        incomplete_inventory["snapshot"]["images"] = [
            image
            for image in incomplete_inventory["snapshot"]["images"]
            if image["service"] == "shuffle-action-image"
        ]
        incomplete_inventory["snapshot"]["snapshot_id"] = (
            validator._snapshot_identifier(
                incomplete_inventory["trial_run_id"],
                incomplete_inventory["snapshot"],
            )
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "complete reviewed full-profile service inventory",
        ):
            validator.validate_manifest(incomplete_inventory, SCHEMA)

        unreviewed_action = _manifest()
        action_image = next(
            image
            for image in unreviewed_action["snapshot"]["images"]
            if image["service"] == "shuffle-action-image"
        )
        action_image["immutable_reference"] = "frikky/shuffle@sha256:" + "9" * 64
        unreviewed_action["snapshot"]["snapshot_id"] = (
            validator._snapshot_identifier(
                unreviewed_action["trial_run_id"],
                unreviewed_action["snapshot"],
            )
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "reviewed immutable reference",
        ):
            validator.validate_manifest(unreviewed_action, SCHEMA)

        for service in validator.CURRENT_RUNTIME_IMAGE_ID_SERVICES:
            missing_runtime_identity = _manifest()
            runtime_image = next(
                image
                for image in missing_runtime_identity["snapshot"]["images"]
                if image["service"] == service
            )
            runtime_image.pop("runtime_image_id")
            missing_runtime_identity["snapshot"]["snapshot_id"] = (
                validator._snapshot_identifier(
                    missing_runtime_identity["trial_run_id"],
                    missing_runtime_identity["snapshot"],
                )
            )
            with self.subTest(service=service), self.assertRaisesRegex(
                validator.EvidenceValidationError,
                "Shuffle action and worker runtime image IDs",
            ):
                validator.validate_manifest(missing_runtime_identity, SCHEMA)

        unreviewed_service = _manifest()
        postgres_image = next(
            image
            for image in unreviewed_service["snapshot"]["images"]
            if image["service"] == "postgres"
        )
        postgres_image["immutable_reference"] = "postgres:16.4@sha256:" + "8" * 64
        unreviewed_service["snapshot"]["snapshot_id"] = (
            validator._snapshot_identifier(
                unreviewed_service["trial_run_id"],
                unreviewed_service["snapshot"],
            )
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "reviewed immutable reference",
        ):
            validator.validate_manifest(unreviewed_service, SCHEMA)

        unexpected_service = _manifest()
        unexpected_service["snapshot"]["images"].append(
            {
                "service": "ambient-container",
                "immutable_reference": "ambient@sha256:" + "7" * 64,
            }
        )
        unexpected_service["snapshot"]["snapshot_id"] = (
            validator._snapshot_identifier(
                unexpected_service["trial_run_id"],
                unexpected_service["snapshot"],
            )
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "complete reviewed full-profile service inventory",
        ):
            validator.validate_manifest(unexpected_service, SCHEMA)

        duplicate_evaluation_identities = {
            "trial_run_id": "phase67-e2e-20260801T100001Z-0123456789ab",
            "snapshot_id": "phase67-snapshot-fedcba9876543210",
            "repository_revision": "9" * 40,
        }
        for field_name, field_value in duplicate_evaluation_identities.items():
            stale_evaluation = _manifest()
            stale_evaluation["evaluation"][field_name] = field_value
            with self.subTest(field_name=field_name), self.assertRaisesRegex(
                validator.EvidenceValidationError,
                r"\$\.evaluation has unexpected keys",
            ):
                validator.validate_manifest(stale_evaluation, SCHEMA)

        altered_snapshot = _manifest()
        altered_snapshot["snapshot"]["docker_context"] = "different-colima"
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "not bound to all snapshot inputs",
        ):
            validator.validate_manifest(altered_snapshot, SCHEMA)

    def test_snapshot_identifier_commits_to_every_environment_input(self) -> None:
        manifest = _manifest()
        trial_run_id = manifest["trial_run_id"]
        snapshot = manifest["snapshot"]
        baseline = validator._snapshot_identifier(trial_run_id, snapshot)
        mutations = {
            "repository_revision": "9" * 40,
            "compose_sha256": "8" * 64,
            "evidence_schema_sha256": "7" * 64,
            "runtime_artifact_sha256": "6" * 64,
            "shuffle_api_workflow_id": "52c15ad7-ff1f-4d50-bf6c-a1b2c3d4e5f6",
            "shuffle_reviewed_workflow_sha256": "0" * 64,
            "shuffle_live_workflow_sha256": "a" * 64,
            "host_architecture": "aarch64",
            "docker_context": "colima-review",
            "colima_profile": "review",
            "selected_profile": "full-review",
        }
        for field_name, value in mutations.items():
            with self.subTest(field_name=field_name):
                changed = deepcopy(snapshot)
                changed[field_name] = value
                self.assertNotEqual(
                    validator._snapshot_identifier(trial_run_id, changed),
                    baseline,
                )
        changed_image = deepcopy(snapshot)
        changed_image["images"][0]["immutable_reference"] = (
            "control-plane@sha256:" + "5" * 64
        )
        self.assertNotEqual(
            validator._snapshot_identifier(trial_run_id, changed_image),
            baseline,
        )

    def test_validator_binds_current_manifests_to_the_schema_file_digest(self) -> None:
        schema_path = E2E_ROOT / "evidence-manifest.schema.json"
        loaded_schema, schema_sha256 = validator.load_json_with_sha256(schema_path)
        self.assertEqual(loaded_schema, SCHEMA)
        manifest = _manifest()
        manifest["snapshot"]["evidence_schema_sha256"] = schema_sha256
        snapshot_id = validator._snapshot_identifier(
            manifest["trial_run_id"],
            manifest["snapshot"],
        )
        manifest["snapshot"]["snapshot_id"] = snapshot_id
        for step in manifest["steps"]:
            step["snapshot_id"] = snapshot_id
        validator.validate_manifest(
            manifest,
            SCHEMA,
            schema_sha256=schema_sha256,
        )

        tampered = deepcopy(manifest)
        tampered["snapshot"]["evidence_schema_sha256"] = "0" * 64
        tampered_snapshot_id = validator._snapshot_identifier(
            tampered["trial_run_id"],
            tampered["snapshot"],
        )
        tampered["snapshot"]["snapshot_id"] = tampered_snapshot_id
        for step in tampered["steps"]:
            step["snapshot_id"] = tampered_snapshot_id
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "does not match the validator schema",
        ):
            validator.validate_manifest(
                tampered,
                SCHEMA,
                schema_sha256=schema_sha256,
            )

        legacy = validator.load_json(E2E_ROOT / "sample-evidence.json")
        validator.validate_manifest(
            legacy,
            SCHEMA,
            schema_sha256=schema_sha256,
        )
        legacy["snapshot"]["evidence_schema_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "does not match the validator schema",
        ):
            validator.validate_manifest(
                legacy,
                SCHEMA,
                schema_sha256=schema_sha256,
            )

    def test_status_evidence_requires_one_complete_image_identity(self) -> None:
        snapshot = _manifest()["snapshot"]

        def status_text(
            inventory: list[dict[str, object]],
            *,
            control_plane_image_id: str = "sha256:" + "e" * 64,
        ) -> str:
            return (
                "repository_commit="
                + "a" * 40
                + "\nrepository_runtime_state=clean\n"
                + "repository_runtime_artifact_sha256="
                + "d" * 64
                + "\ncontrol_plane_container_image_id="
                + control_plane_image_id
                + "\ncompose_ps_json="
                + json.dumps(inventory, separators=(",", ":"))
                + "\n"
            )

        inventory = _compose_status_inventory(snapshot)
        with TemporaryDirectory() as temporary_directory:
            status_path = Path(temporary_directory) / "status.txt"
            status_path.write_text(
                status_text(inventory),
                encoding="utf-8",
            )
            builder._validate_status_snapshot(status_path, snapshot)
            status_path.write_text(
                status_text(
                    inventory,
                    control_plane_image_id="sha256:" + "f" * 64,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "different control-plane image"):
                builder._validate_status_snapshot(status_path, snapshot)

            unhealthy = deepcopy(inventory)
            next(
                row for row in unhealthy if row["Service"] == "wazuh-manager"
            )["Health"] = "unhealthy"
            status_path.write_text(status_text(unhealthy), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "wazuh-manager is not healthy"):
                builder._validate_status_snapshot(status_path, snapshot)

            incomplete = [
                row for row in inventory if row["Service"] != "shuffle-backend"
            ]
            status_path.write_text(status_text(incomplete), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inventory does not match"):
                builder._validate_status_snapshot(status_path, snapshot)

            for invalid_exit_code in (1, False, "0"):
                failed_bootstrap = deepcopy(inventory)
                next(
                    row
                    for row in failed_bootstrap
                    if row["Service"] == "wazuh-security-bootstrap"
                )["ExitCode"] = invalid_exit_code
                status_path.write_text(
                    status_text(failed_bootstrap),
                    encoding="utf-8",
                )
                with self.subTest(
                    invalid_exit_code=invalid_exit_code
                ), self.assertRaisesRegex(ValueError, "completed successfully"):
                    builder._validate_status_snapshot(status_path, snapshot)

    def test_builder_binds_retained_images_to_the_snapshot_inventory(self) -> None:
        snapshot = _manifest()["snapshot"]
        images = deepcopy(snapshot["images"])
        builder._validate_snapshot_images(images, snapshot)

        images[0]["immutable_reference"] = "changed@sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "does not match"):
            builder._validate_snapshot_images(images, snapshot)
        with self.assertRaisesRegex(ValueError, "images.json must be an array"):
            builder._validate_snapshot_images({}, snapshot)

    def test_builder_revalidates_the_retained_wazuh_manifest(self) -> None:
        self.assertEqual(
            builder.WAZUH_SCHEMA_PATH,
            WAZUH_ROOT / "evidence-manifest.schema.json",
        )
        self.assertEqual(
            builder.WAZUH_VALIDATOR_PATH,
            WAZUH_ROOT / "validate_evidence_manifest.py",
        )
        manifest = _wazuh_manifest()
        builder._validate_wazuh_manifest_contract(
            manifest,
            schema_path=WAZUH_ROOT / "evidence-manifest.schema.json",
            validator_path=WAZUH_ROOT / "validate_evidence_manifest.py",
        )

        manifest["wazuh_manager_health"] = "unhealthy"
        with self.assertRaisesRegex(ValueError, "retained Wazuh manifest is invalid"):
            builder._validate_wazuh_manifest_contract(
                manifest,
                schema_path=WAZUH_ROOT / "evidence-manifest.schema.json",
                validator_path=WAZUH_ROOT / "validate_evidence_manifest.py",
            )

    def test_builder_binds_the_wazuh_agent_to_both_delivery_findings(
        self,
    ) -> None:
        wazuh = _wazuh_manifest()
        finding_id = wazuh["first_delivery"]["finding_id"]
        builder._validate_wazuh_finding_identity(wazuh, finding_id)

        for source in ("agent", "first delivery", "journey"):
            with self.subTest(source=source):
                tampered = deepcopy(wazuh)
                journey_finding_id = finding_id
                if source == "agent":
                    tampered["native_wazuh_agent_id"] = "999"
                elif source == "first delivery":
                    tampered["first_delivery"]["finding_id"] = (
                        "finding:wazuh:rule:5710:source:agent:999:"
                        "alert:phase67-native-alert"
                    )
                else:
                    journey_finding_id = (
                        "finding:wazuh:rule:5710:source:agent:999:"
                        "alert:phase67-native-alert"
                    )
                with self.assertRaisesRegex(ValueError, "not bound"):
                    builder._validate_wazuh_finding_identity(
                        tampered,
                        journey_finding_id,
                    )

    def test_builder_revalidates_both_retained_shuffle_workflows(self) -> None:
        self.assertEqual(
            builder.WORKFLOW_VALIDATOR_PATH,
            SHUFFLE_ROOT / "validate_preserved_workflow.py",
        )
        workflow_id = _manifest()["snapshot"]["shuffle_api_workflow_id"]
        reviewed = builder._read_json(
            SHUFFLE_ROOT / "harmless-local-log-workflow.json"
        )
        observed = deepcopy(reviewed)
        observed["id"] = workflow_id
        validator_path = SHUFFLE_ROOT / "validate_preserved_workflow.py"

        for label in ("snapshot", "pre-dispatch"):
            with self.subTest(label=label):
                builder._validate_preserved_workflow_contract(
                    reviewed,
                    observed,
                    workflow_id,
                    validator_path=validator_path,
                    label=label,
                )

        drifted = deepcopy(observed)
        drifted["actions"][0]["name"] = "send_email"
        with self.assertRaisesRegex(ValueError, "violates the reviewed workflow"):
            builder._validate_preserved_workflow_contract(
                reviewed,
                drifted,
                workflow_id,
                validator_path=validator_path,
                label="pre-dispatch",
            )

    def test_builder_binds_snapshot_provenance_to_runner_inputs(self) -> None:
        with TemporaryDirectory() as directory:
            compose_config = Path(directory) / "compose-config.yml"
            compose_config.write_text(
                "services:\n  control-plane: {}\n",
                encoding="utf-8",
            )
            compose_sha256 = hashlib.sha256(compose_config.read_bytes()).hexdigest()
            compose_digest_record = Path(directory) / "compose-config.sha256"
            compose_digest_record.write_text(
                f"{compose_sha256}  compose-config.yml\n",
                encoding="utf-8",
            )
            snapshot = {
                "repository_revision": "a" * 40,
                "compose_sha256": compose_sha256,
            }
            builder._validate_snapshot_provenance(
                snapshot,
                expected_repository_revision="a" * 40,
                expected_compose_sha256=compose_sha256,
                compose_config=compose_config,
                compose_digest_record=compose_digest_record,
            )

            changed_revision = deepcopy(snapshot)
            changed_revision["repository_revision"] = "b" * 40
            with self.assertRaisesRegex(ValueError, "does not match the checkout"):
                builder._validate_snapshot_provenance(
                    changed_revision,
                    expected_repository_revision="a" * 40,
                    expected_compose_sha256=compose_sha256,
                    compose_config=compose_config,
                    compose_digest_record=compose_digest_record,
                )

            changed_compose = deepcopy(snapshot)
            changed_compose["compose_sha256"] = "c" * 64
            with self.assertRaisesRegex(ValueError, "does not match the trial render"):
                builder._validate_snapshot_provenance(
                    changed_compose,
                    expected_repository_revision="a" * 40,
                    expected_compose_sha256=compose_sha256,
                    compose_config=compose_config,
                    compose_digest_record=compose_digest_record,
                )

            compose_config.write_text("services: {}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "captured Compose render"):
                builder._validate_snapshot_provenance(
                    snapshot,
                    expected_repository_revision="a" * 40,
                    expected_compose_sha256=compose_sha256,
                    compose_config=compose_config,
                    compose_digest_record=compose_digest_record,
                )

            compose_config.write_text(
                "services:\n  control-plane: {}\n",
                encoding="utf-8",
            )
            compose_digest_record.write_text(
                "c" * 64 + "  compose-config.yml\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Compose digest record"):
                builder._validate_snapshot_provenance(
                    snapshot,
                    expected_repository_revision="a" * 40,
                    expected_compose_sha256=compose_sha256,
                    compose_config=compose_config,
                    compose_digest_record=compose_digest_record,
                )

    def test_restart_verifies_every_wazuh_reconciliation_record(self) -> None:
        identifiers = _manifest()["identifiers"]
        payload = {
            field_name: identifiers[field_name]
            for field_name in journey.RESTART_RECORD_TYPES
        }
        payload["wazuh_reconciliation_ids"] = [
            "reconciliation-wazuh-admission",
            "reconciliation-wazuh-duplicate",
        ]
        retained_ids = {
            str(payload[field_name])
            for field_name in journey.RESTART_RECORD_TYPES
        } | set(payload["wazuh_reconciliation_ids"])

        class FakeService:
            def __init__(self, record_ids: set[str]) -> None:
                self.record_ids = record_ids

            def get_record(self, _record_type: object, record_id: str) -> object:
                return object() if record_id in self.record_ids else None

        checked, wazuh_ids = journey._verify_restart_records(
            FakeService(retained_ids),
            payload,
        )
        self.assertIn("wazuh_reconciliation_ids", checked)
        self.assertEqual(wazuh_ids, tuple(payload["wazuh_reconciliation_ids"]))

        missing_duplicate = retained_ids - {"reconciliation-wazuh-duplicate"}
        with self.assertRaisesRegex(
            RuntimeError,
            "restart lost wazuh_reconciliation_id=reconciliation-wazuh-duplicate",
        ):
            journey._verify_restart_records(FakeService(missing_duplicate), payload)

    def test_restart_compares_authoritative_record_contents_with_the_report(
        self,
    ) -> None:
        records = {
            record_type.record_family: [
                {
                    record_type.identifier_field: (
                        f"{record_type.record_family}-retained"
                    ),
                    "lifecycle_state": "retained",
                }
            ]
            for record_type in journey.REPORT_RECORD_TYPES
        }
        report = {"records": deepcopy(records)}
        service = SimpleNamespace(_store=object())
        original_export = journey.export_audit_retention_baseline

        def exported_records(**kwargs: object) -> dict[str, object]:
            expected_scope = {
                record_type.record_family: frozenset(
                    {f"{record_type.record_family}-retained"}
                )
                for record_type in journey.REPORT_RECORD_TYPES
            }
            self.assertEqual(kwargs["record_ids_by_family"], expected_scope)
            return {"records": deepcopy(records)}

        try:
            journey.export_audit_retention_baseline = exported_records
            journey._verify_restart_report_contents(service, report)

            changed_records = deepcopy(records)
            changed_records["action_request"][0]["lifecycle_state"] = (
                "changed-after-restart"
            )
            journey.export_audit_retention_baseline = lambda **_kwargs: {
                "records": changed_records
            }
            with self.assertRaisesRegex(
                RuntimeError,
                "changed authoritative record contents",
            ):
                journey._verify_restart_report_contents(service, report)
        finally:
            journey.export_audit_retention_baseline = original_export

    def test_validator_requires_the_exact_reviewed_restart_identifier_set(self) -> None:
        extra = _manifest()
        extra["restart"]["checked_identifiers"].append("unreviewed_id")
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "exactly the reviewed authoritative identifiers",
        ):
            validator.validate_manifest(extra, SCHEMA)

        non_string = _manifest()
        non_string["restart"]["checked_identifiers"][0] = None
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            r"checked_identifiers\[0\] must be a non-empty string",
        ):
            validator.validate_manifest(non_string, SCHEMA)

    def test_builder_binds_every_wazuh_reconciliation_scope(self) -> None:
        reconciliation_ids = [
            "reconciliation-wazuh-admission",
            "reconciliation-wazuh-duplicate",
        ]
        wazuh = {
            "first_delivery": {"reconciliation_id": reconciliation_ids[0]},
            "duplicate_delivery": {"reconciliation_id": reconciliation_ids[1]},
        }
        sources = [
            {"wazuh_reconciliation_ids": list(reconciliation_ids)}
            for _ in range(3)
        ]
        builder._validate_wazuh_reconciliation_scope(wazuh, *sources)

        for source_index, source_name in enumerate(
            ("preparation", "journey", "restart")
        ):
            tampered_sources = deepcopy(sources)
            tampered_sources[source_index]["wazuh_reconciliation_ids"] = [
                reconciliation_ids[0]
            ]
            with self.subTest(source=source_name), self.assertRaisesRegex(
                ValueError,
                f"{source_name} Wazuh reconciliation scope does not match",
            ):
                builder._validate_wazuh_reconciliation_scope(
                    wazuh,
                    *tampered_sources,
                )

        duplicate = deepcopy(wazuh)
        duplicate["duplicate_delivery"]["reconciliation_id"] = (
            reconciliation_ids[0]
        )
        with self.assertRaisesRegex(ValueError, "must have distinct"):
            builder._validate_wazuh_reconciliation_scope(duplicate, *sources)

    def test_builder_binds_preparation_to_the_complete_journey_request(self) -> None:
        trial_run_id = "phase67-e2e-20260801T100000Z-0123456789ab"
        action_request_id = "action-a1b2c3d4"
        payload_hash = "a" * 64
        preparation = {
            "trial_run_id": trial_run_id,
            "alert_id": "alert-a1b2c3d4",
            "finding_id": "finding-a1b2c3d4",
            "case_id": "case-a1b2c3d4",
            "denied_action_request_id": "action-denied-a1b2c3d4",
            "denied_approval_decision_id": "approval-denied-a1b2c3d4",
            "denied_dispatch": {
                "binding_reviewed": True,
                "dispatch_rejected": True,
                "execution_count": 0,
                "action_request_id": "action-denied-a1b2c3d4",
                "approval_decision_id": "approval-denied-a1b2c3d4",
                "idempotency_key": "denied-phase67-idempotency-a1b2c3d4",
                "payload_hash": "c" * 64,
                "target_scope": {"identity_id": "local-test-sink"},
                "requester_identity": "phase67-lab-requester",
                "action_request_lifecycle_state": "rejected",
                "approval_decision_lifecycle_state": "rejected",
                "approver_identities": [journey.NEGATIVE_PROBE_APPROVER_IDENTITY],
            },
            "action_request_id": action_request_id,
            "idempotency_key": "phase67-idempotency-a1b2c3d4",
            "payload_hash": payload_hash,
            "target_scope": {"identity_id": "local-test-sink"},
            "requester_identity": "phase67-lab-requester",
            "approval_challenge_sha256": builder._approval_challenge_sha256(
                trial_run_id=trial_run_id,
                action_request_id=action_request_id,
                payload_hash=payload_hash,
            ),
        }
        journey_request = deepcopy(preparation)
        builder._validate_preparation_journey_binding(
            preparation,
            journey_request,
        )

        for field_name in builder.PREPARATION_JOURNEY_BINDINGS:
            tampered = deepcopy(journey_request)
            tampered[field_name] = (
                {"identity_id": "another-target"}
                if field_name == "target_scope"
                else f"different-{field_name}"
            )
            with self.subTest(field_name=field_name), self.assertRaisesRegex(
                ValueError,
                f"preparation {field_name} does not match the journey",
            ):
                builder._validate_preparation_journey_binding(
                    preparation,
                    tampered,
                )

        jointly_tampered = deepcopy(preparation)
        jointly_tampered["approval_challenge_sha256"] = "b" * 64
        with self.assertRaisesRegex(
            ValueError,
            "approval challenge digest does not match the deterministic",
        ):
            builder._validate_preparation_journey_binding(
                jointly_tampered,
                deepcopy(jointly_tampered),
            )

        challenge_input_mutations = {
            "trial_run_id": "phase67-e2e-20260801T100000Z-othertrial",
            "action_request_id": "action-from-another-trial",
            "payload_hash": "d" * 64,
        }
        for field_name, field_value in challenge_input_mutations.items():
            tampered_preparation = deepcopy(preparation)
            tampered_journey = deepcopy(preparation)
            tampered_preparation[field_name] = field_value
            tampered_journey[field_name] = field_value
            with self.subTest(
                challenge_input=field_name
            ), self.assertRaisesRegex(
                ValueError,
                "approval challenge digest does not match the deterministic",
            ):
                builder._validate_preparation_journey_binding(
                    tampered_preparation,
                    tampered_journey,
                )

    def test_live_workflow_digest_is_canonical_and_content_bound(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            workflow_path = Path(temporary_directory) / "workflow.json"
            workflow_path.write_text('{"b":2,"a":1}\n', encoding="utf-8")
            baseline = builder._canonical_json_sha256(workflow_path)
            workflow_path.write_text(
                '{\n  "a": 1,\n  "b": 2\n}\n',
                encoding="utf-8",
            )
            self.assertEqual(builder._canonical_json_sha256(workflow_path), baseline)
            workflow_path.write_text('{"a":1,"b":3}\n', encoding="utf-8")
            self.assertNotEqual(
                builder._canonical_json_sha256(workflow_path),
                baseline,
            )

    def test_validator_rejects_unmeasured_negative_and_missing_artifact(self) -> None:
        contradictory = _manifest()
        contradictory["negative_cases"]["failed_execution"][
            "authority_delta"
        ] = 0
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "has unexpected keys: authority_delta",
        ):
            validator.validate_manifest(contradictory, SCHEMA)

        self.assertEqual(
            builder._validated_authority_counts(
                {
                    "authority_before": 1,
                    "authority_after": 2,
                    "authority_delta": 1,
                },
                path="probe",
            ),
            (1, 2),
        )
        with self.assertRaisesRegex(
            ValueError,
            "authority_delta is not derived from its counts",
        ):
            builder._validated_authority_counts(
                {
                    "authority_before": 1,
                    "authority_after": 2,
                    "authority_delta": 0,
                },
                path="probe",
            )

        incomplete = _manifest()
        incomplete["artifacts"]["files"].pop()
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "raw artifact inventory is incomplete",
        ):
            validator.validate_manifest(incomplete, SCHEMA)

        mismatched_evaluation = _manifest()
        evaluation_artifact = next(
            artifact
            for artifact in mismatched_evaluation["artifacts"]["files"]
            if artifact["name"] == "evaluation-record.json"
        )
        evaluation_artifact["sha256"] = "7" * 64
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "evaluation digest does not match",
        ):
            validator.validate_manifest(mismatched_evaluation, SCHEMA)

    def test_validator_binds_dispatch_to_distinct_reviewed_records(self) -> None:
        mutations = {
            "reused action request": (
                "denied_action_request_id",
                "action_request_id",
                "action request IDs must remain distinct",
            ),
            "reused approval decision": (
                "denied_approval_decision_id",
                "approval_decision_id",
                "decision IDs must remain distinct",
            ),
        }
        for name, (denied_key, approved_key, diagnostic) in mutations.items():
            manifest = _manifest()
            manifest["identifiers"][denied_key] = manifest["identifiers"][
                approved_key
            ]
            with self.subTest(name=name), self.assertRaisesRegex(
                validator.EvidenceValidationError,
                diagnostic,
            ):
                validator.validate_manifest(manifest, SCHEMA)

        wrong_workflow = _manifest()
        wrong_workflow["identifiers"]["shuffle_workflow_id"] = (
            "52c15ad7-ff1f-4d50-bf6c-a1b2c3d4e5f6"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "workflow ID is not bound to the snapshot",
        ):
            validator.validate_manifest(wrong_workflow, SCHEMA)

        wrong_version = _manifest()
        wrong_version["identifiers"]["shuffle_workflow_version"] = (
            "notify_identity_owner-v2-unreviewed"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "workflow version is not the reviewed version",
        ):
            validator.validate_manifest(wrong_version, SCHEMA)

        invalid_execution_id = _manifest()
        invalid_execution_id["identifiers"]["shuffle_execution_id"] = (
            "not-a-real-run"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "canonical UUID form",
        ):
            validator.validate_manifest(invalid_execution_id, SCHEMA)

    def test_validator_rejects_inferred_human_control_or_receipt_success(self) -> None:
        missing_requester = _manifest()
        missing_requester["human_control"]["requester_identity"] = None
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "requires a requester and challenge digest",
        ):
            validator.validate_manifest(missing_requester, SCHEMA)

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

        stale_denial = _manifest()
        blocked_step_index = 5
        for index in range(blocked_step_index, len(stale_denial["steps"])):
            step = stale_denial["steps"][index]
            if index == blocked_step_index:
                step["status"] = "blocked"
                step["evidence_refs"] = [
                    builder.STEP_EVIDENCE_REFS[index][0]
                ]
                step["blocker"] = {
                    "owner": "AegisOps integration engineering",
                    "reason": "Reviewed request creation did not complete.",
                }
            else:
                step["status"] = "not_run"
                step["evidence_refs"] = ["not-run:prerequisite-blocked"]
        stale_denial["verdict"] = "integration_trial_blocked"
        for identifier, producing_step in validator.IDENTIFIER_PRODUCING_STEPS.items():
            if validator.STEP_NAMES.index(producing_step) >= blocked_step_index:
                stale_denial["identifiers"][identifier] = None
        stale_denial["human_control"]["requester_identity"] = None
        stale_denial["human_control"]["approval_challenge_sha256"] = None
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "cannot claim denial proof",
        ):
            validator.validate_manifest(stale_denial, SCHEMA)

        unattended = _manifest()
        unattended["human_control"]["approval_source"] = (
            "aegisops_approval_decision_record"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "interactive ceremony",
        ):
            validator.validate_manifest(unattended, SCHEMA)

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

    def test_validator_enforces_complete_non_destructive_cleanup_states(
        self,
    ) -> None:
        cleanup_schema = SCHEMA["properties"]["cleanup"]
        self.assertEqual(len(cleanup_schema["oneOf"]), 2)

        invalid_states = (
            {
                "mode": "destructive",
                "containers_stopped": True,
                "data_preserved": True,
            },
            {
                "mode": "non_destructive",
                "containers_stopped": False,
                "data_preserved": True,
            },
            {
                "mode": None,
                "containers_stopped": True,
                "data_preserved": None,
            },
        )
        for cleanup in invalid_states:
            manifest = _manifest()
            manifest["cleanup"] = cleanup
            with self.subTest(cleanup=cleanup), self.assertRaisesRegex(
                validator.EvidenceValidationError,
                "cleanup must be either unobserved or completed",
            ):
                validator.validate_manifest(manifest, SCHEMA)

        missing_passed_cleanup = _manifest()
        missing_passed_cleanup["cleanup"] = {
            "mode": None,
            "containers_stopped": None,
            "data_preserved": None,
        }
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "cleanup must stop services",
        ):
            validator.validate_manifest(missing_passed_cleanup, SCHEMA)

    def test_validator_binds_owned_limitations_to_the_trial_verdict(self) -> None:
        for mutation, message in (
            (
                lambda manifest: manifest["limitations"].pop(1),
                "must retain phase67-bounded-connectors",
            ),
            (
                lambda manifest: manifest["limitations"][2].update(
                    status="accepted"
                ),
                "must retain phase67-ga-gates-open with status blocking",
            ),
            (
                lambda manifest: manifest["limitations"].append(
                    {
                        "limitation_id": "unreviewed-extra",
                        "owner": "Nobody",
                        "status": "accepted",
                        "description": "This does not qualify the trial.",
                        "follow_up_issue": None,
                    }
                ),
                "must match the reviewed owned limitations",
            ),
        ):
            with self.subTest(message=message):
                manifest = _manifest()
                mutation(manifest)
                with self.assertRaisesRegex(
                    validator.EvidenceValidationError,
                    message,
                ):
                    validator.validate_manifest(manifest, SCHEMA)

        historical = validator.load_json(E2E_ROOT / "sample-evidence.json")
        self.assertEqual(
            validator._manifest_sha256(historical),
            validator.LEGACY_BLOCKED_MANIFEST_SHA256,
        )
        self.assertTrue(validator._is_legacy_blocked_manifest(historical))
        historical["limitations"][0]["limitation_id"] = "unrelated-blocker"
        self.assertFalse(validator._is_legacy_blocked_manifest(historical))
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "complete reviewed full-profile service inventory",
        ):
            validator.validate_manifest(historical, SCHEMA)

    def test_legacy_exception_cannot_be_reused_by_a_fabricated_passed_trial(self) -> None:
        fabricated = validator.load_json(E2E_ROOT / "sample-evidence.json")
        fabricated["verdict"] = "integration_trial_passed_with_owned_limitations"
        fabricated["steps"][7]["status"] = "passed"
        fabricated["steps"][7].pop("blocker")
        self.assertFalse(validator._is_legacy_blocked_manifest(fabricated))
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "complete reviewed full-profile service inventory",
        ):
            validator.validate_manifest(fabricated, SCHEMA)

    def test_builder_rejects_report_records_outside_the_trial_chain(self) -> None:
        identifiers = _manifest()["identifiers"]
        target_scope = {"identity_id": "local-test-sink"}
        approved_payload_hash = "a" * 64
        denied_payload_hash = "b" * 64
        expected_receipt_id = identifiers["expected_receipt_id"]
        approved_payload = {
            "action_type": "notify_identity_owner",
            "shuffle_delegation_binding": {
                "expected_execution_receipt_id": expected_receipt_id,
            },
        }
        requester_identity = "phase67-lab-requester"
        approver_identity = "phase67-lab-independent-approver"
        journey_record = {
            "alert_id": identifiers["aegisops_alert_id"],
            "finding_id": identifiers["finding_id"],
            "case_id": identifiers["case_id"],
            "requester_identity": requester_identity,
            "approver_identity": approver_identity,
            "denied_action_request_id": identifiers["denied_action_request_id"],
            "denied_approval_decision_id": identifiers[
                "denied_approval_decision_id"
            ],
            "denied_dispatch": {
                "binding_reviewed": True,
                "dispatch_rejected": True,
                "execution_count": 0,
                "action_request_id": identifiers["denied_action_request_id"],
                "approval_decision_id": identifiers[
                    "denied_approval_decision_id"
                ],
                "idempotency_key": "denied-phase67-idempotency-a1b2c3d4",
                "payload_hash": denied_payload_hash,
                "target_scope": target_scope,
                "requester_identity": requester_identity,
                "action_request_lifecycle_state": "rejected",
                "approval_decision_lifecycle_state": "rejected",
                "approver_identities": [
                    builder.NEGATIVE_PROBE_APPROVER_IDENTITY
                ],
            },
            "action_request_id": identifiers["action_request_id"],
            "approval_decision_id": identifiers["approval_decision_id"],
            "delegation_id": identifiers["delegation_id"],
            "execution_id": identifiers["shuffle_execution_id"],
            "action_execution_id": identifiers["action_execution_id"],
            "idempotency_key": "phase67-idempotency-a1b2c3d4",
            "payload_hash": approved_payload_hash,
            "target_scope": target_scope,
            "expected_receipt_id": expected_receipt_id,
            "reconciliation_id": identifiers["reconciliation_id"],
            "wazuh_reconciliation_ids": [
                "phase67-admission-reconciliation",
                "phase67-duplicate-reconciliation",
            ],
        }
        wazuh = {
            "native_wazuh_alert_id": "wazuh-native-alert-a1b2c3d4",
            "aegisops_alert_id": identifiers["aegisops_alert_id"],
            "first_delivery": {
                "disposition": "created",
                "finding_id": identifiers["finding_id"],
                "reconciliation_id": "phase67-admission-reconciliation",
            },
            "duplicate_delivery": {
                "disposition": "deduplicated",
                "finding_id": identifiers["finding_id"],
                "reconciliation_id": "phase67-duplicate-reconciliation",
            },
        }
        report = {
            "records": {
                "alert": [
                    {
                        "alert_id": identifiers["aegisops_alert_id"],
                        "finding_id": identifiers["finding_id"],
                        "case_id": identifiers["case_id"],
                        "authority_role": "authoritative_control_plane_record",
                    }
                ],
                "case": [
                    {
                        "case_id": identifiers["case_id"],
                        "alert_id": identifiers["aegisops_alert_id"],
                        "finding_id": identifiers["finding_id"],
                        "authority_role": "authoritative_control_plane_record",
                    }
                ],
                "action_request": [
                    {
                        "action_request_id": identifiers[
                            "denied_action_request_id"
                        ],
                        "approval_decision_id": identifiers[
                            "denied_approval_decision_id"
                        ],
                        "case_id": identifiers["case_id"],
                        "alert_id": identifiers["aegisops_alert_id"],
                        "finding_id": identifiers["finding_id"],
                        "idempotency_key": "denied-phase67-idempotency-a1b2c3d4",
                        "target_scope": target_scope,
                        "payload_hash": denied_payload_hash,
                        "lifecycle_state": "rejected",
                        "requester_identity": requester_identity,
                        "authority_role": "authoritative_control_plane_record",
                    },
                    {
                        "action_request_id": identifiers["action_request_id"],
                        "approval_decision_id": identifiers[
                            "approval_decision_id"
                        ],
                        "case_id": identifiers["case_id"],
                        "alert_id": identifiers["aegisops_alert_id"],
                        "finding_id": identifiers["finding_id"],
                        "idempotency_key": "phase67-idempotency-a1b2c3d4",
                        "target_scope": target_scope,
                        "payload_hash": approved_payload_hash,
                        "requested_payload": deepcopy(approved_payload),
                        "lifecycle_state": "approved",
                        "requester_identity": requester_identity,
                        "authority_role": "authoritative_control_plane_record",
                    },
                ],
                "approval_decision": [
                    {
                        "approval_decision_id": identifiers[
                            "denied_approval_decision_id"
                        ],
                        "action_request_id": identifiers[
                            "denied_action_request_id"
                        ],
                        "approver_identities": [
                            builder.NEGATIVE_PROBE_APPROVER_IDENTITY
                        ],
                        "target_snapshot": target_scope,
                        "payload_hash": denied_payload_hash,
                        "lifecycle_state": "rejected",
                        "authority_role": "authoritative_control_plane_record",
                    },
                    {
                        "approval_decision_id": identifiers[
                            "approval_decision_id"
                        ],
                        "action_request_id": identifiers["action_request_id"],
                        "approver_identities": [approver_identity],
                        "target_snapshot": target_scope,
                        "payload_hash": approved_payload_hash,
                        "lifecycle_state": "approved",
                        "authority_role": "authoritative_control_plane_record",
                    },
                ],
                "action_execution": [
                    {
                        "action_execution_id": identifiers[
                            "action_execution_id"
                        ],
                        "action_request_id": identifiers["action_request_id"],
                        "approval_decision_id": identifiers[
                            "approval_decision_id"
                        ],
                        "delegation_id": identifiers["delegation_id"],
                        "execution_run_id": identifiers["shuffle_execution_id"],
                        "idempotency_key": "phase67-idempotency-a1b2c3d4",
                        "payload_hash": "a" * 64,
                        "approved_payload": deepcopy(approved_payload),
                        "target_scope": {"identity_id": "local-test-sink"},
                        "execution_surface_type": "automation_substrate",
                        "execution_surface_id": "shuffle",
                        "lifecycle_state": "succeeded",
                        "authority_role": "authoritative_control_plane_record",
                    }
                ],
                "reconciliation": [
                    {
                        "reconciliation_id": "phase67-admission-reconciliation",
                        "alert_id": identifiers["aegisops_alert_id"],
                        "finding_id": identifiers["finding_id"],
                        "execution_run_id": None,
                        "linked_execution_run_ids": [],
                        "ingest_disposition": "created",
                        "lifecycle_state": "matched",
                        "mismatch_summary": (
                            "created upstream analytic signal into alert lifecycle"
                        ),
                        "subject_linkage": {
                            "alert_ids": [identifiers["aegisops_alert_id"]],
                            "finding_ids": [identifiers["finding_id"]],
                        },
                        "authority_role": "authoritative_control_plane_record",
                    },
                    {
                        "reconciliation_id": "phase67-duplicate-reconciliation",
                        "alert_id": identifiers["aegisops_alert_id"],
                        "finding_id": identifiers["finding_id"],
                        "execution_run_id": None,
                        "linked_execution_run_ids": [],
                        "ingest_disposition": "deduplicated",
                        "lifecycle_state": "matched",
                        "mismatch_summary": (
                            "deduplicated upstream analytic signal into alert "
                            "lifecycle"
                        ),
                        "subject_linkage": {
                            "alert_ids": [identifiers["aegisops_alert_id"]],
                            "finding_ids": [identifiers["finding_id"]],
                        },
                        "authority_role": "authoritative_control_plane_record",
                    },
                    {
                        "reconciliation_id": identifiers["reconciliation_id"],
                        "alert_id": identifiers["aegisops_alert_id"],
                        "finding_id": identifiers["finding_id"],
                        "execution_run_id": identifiers["shuffle_execution_id"],
                        "linked_execution_run_ids": [
                            identifiers["shuffle_execution_id"]
                        ],
                        "ingest_disposition": "matched",
                        "lifecycle_state": "matched",
                        "mismatch_summary": (
                            "matched approved action request to reviewed "
                            "execution run"
                        ),
                        "subject_linkage": {
                            "action_request_ids": [
                                identifiers["action_request_id"]
                            ],
                            "approval_decision_ids": [
                                identifiers["approval_decision_id"]
                            ],
                            "action_execution_ids": [
                                identifiers["action_execution_id"]
                            ],
                            "delegation_ids": [identifiers["delegation_id"]],
                            "alert_ids": [identifiers["aegisops_alert_id"]],
                            "case_ids": [identifiers["case_id"]],
                            "finding_ids": [identifiers["finding_id"]],
                            "execution_surface_types": [
                                "automation_substrate"
                            ],
                            "execution_surface_ids": ["shuffle"],
                        },
                        "authority_role": "authoritative_control_plane_record",
                    },
                ],
            }
        }
        builder._validate_trial_report_scope(report, journey_record, wazuh)

        tampered_journey_receipt = deepcopy(journey_record)
        tampered_journey_receipt["expected_receipt_id"] = (
            "phase67-receipt-from-another-trial"
        )
        with self.assertRaisesRegex(
            ValueError,
            "approved action request is not bound to the journey: "
            "expected_execution_receipt_id",
        ):
            builder._validate_trial_report_scope(
                report,
                tampered_journey_receipt,
                wazuh,
            )

        tampered_request_receipt = deepcopy(report)
        tampered_request_receipt["records"]["action_request"][1][
            "requested_payload"
        ]["shuffle_delegation_binding"]["expected_execution_receipt_id"] = (
            "phase67-receipt-from-another-trial"
        )
        with self.assertRaisesRegex(
            ValueError,
            "approved action request is not bound to the journey: "
            "expected_execution_receipt_id",
        ):
            builder._validate_trial_report_scope(
                tampered_request_receipt,
                journey_record,
                wazuh,
            )

        tampered_execution_receipt = deepcopy(report)
        tampered_execution_receipt["records"]["action_execution"][0][
            "approved_payload"
        ]["shuffle_delegation_binding"]["expected_execution_receipt_id"] = (
            "phase67-receipt-from-another-trial"
        )
        with self.assertRaisesRegex(
            ValueError,
            "action execution is not bound to the journey: "
            "expected_execution_receipt_id",
        ):
            builder._validate_trial_report_scope(
                tampered_execution_receipt,
                journey_record,
                wazuh,
            )

        binding_mutations = {
            "execution_run_id": "2f90e91d-e217-42da-bd83-a1b2c3d4e5f7",
            "delegation_id": "delegation-from-another-trial",
            "approval_decision_id": "approval-from-another-trial",
            "action_request_id": "action-from-another-trial",
            "idempotency_key": "idempotency-from-another-trial",
            "payload_hash": "b" * 64,
            "target_scope": {"identity_id": "another-target"},
            "execution_surface_id": "unreviewed-automation",
            "lifecycle_state": "failed",
        }
        for field_name, field_value in binding_mutations.items():
            tampered = deepcopy(report)
            tampered["records"]["action_execution"][0][field_name] = field_value
            with self.subTest(field_name=field_name), self.assertRaisesRegex(
                ValueError,
                "report action execution is not bound to the journey",
            ):
                builder._validate_trial_report_scope(
                    tampered,
                    journey_record,
                    wazuh,
                )

        relationship_mutations = (
            ("alert", 0, "finding_id", "finding-from-another-trial"),
            ("case", 0, "alert_id", "alert-from-another-trial"),
            (
                "action_request",
                0,
                "payload_hash",
                "c" * 64,
            ),
            (
                "action_request",
                1,
                "requester_identity",
                "requester-from-another-trial",
            ),
            (
                "approval_decision",
                0,
                "target_snapshot",
                {"identity_id": "another-target"},
            ),
            (
                "approval_decision",
                1,
                "approver_identities",
                ["approver-from-another-trial"],
            ),
        )
        for family, index, field_name, field_value in relationship_mutations:
            tampered = deepcopy(report)
            tampered["records"][family][index][field_name] = field_value
            with self.subTest(
                family=family,
                field_name=field_name,
            ), self.assertRaisesRegex(ValueError, "is not bound to the journey"):
                builder._validate_trial_report_scope(
                    tampered,
                    journey_record,
                    wazuh,
                )

        non_authoritative = deepcopy(report)
        non_authoritative["records"]["approval_decision"][0][
            "authority_role"
        ] = "subordinate_evidence"
        with self.assertRaisesRegex(ValueError, "is not authoritative"):
            builder._validate_trial_report_scope(
                non_authoritative,
                journey_record,
                wazuh,
            )

        altered_denial = deepcopy(journey_record)
        altered_denial["denied_dispatch"]["requester_identity"] = (
            "requester-from-another-trial"
        )
        with self.assertRaisesRegex(ValueError, "denied dispatch is not bound"):
            builder._validate_trial_report_scope(report, altered_denial, wazuh)

        wazuh_reconciliation_mutations = (
            (0, "ingest_disposition", "mismatch"),
            (0, "lifecycle_state", "stale"),
            (0, "mismatch_summary", "unrelated summary"),
            (1, "execution_run_id", identifiers["shuffle_execution_id"]),
            (1, "linked_execution_run_ids", [identifiers["shuffle_execution_id"]]),
        )
        for index, field_name, field_value in wazuh_reconciliation_mutations:
            tampered = deepcopy(report)
            tampered["records"]["reconciliation"][index][field_name] = field_value
            delivery_name = (
                "first_delivery" if index == 0 else "duplicate_delivery"
            )
            with self.subTest(
                delivery=delivery_name,
                field_name=field_name,
            ), self.assertRaisesRegex(
                ValueError,
                f"report {delivery_name} reconciliation is not bound",
            ):
                builder._validate_trial_report_scope(
                    tampered,
                    journey_record,
                    wazuh,
                )

        for index, linkage_name in ((0, "alert_ids"), (1, "finding_ids")):
            tampered = deepcopy(report)
            tampered["records"]["reconciliation"][index]["subject_linkage"][
                linkage_name
            ] = ["record-from-another-trial"]
            delivery_name = (
                "first_delivery" if index == 0 else "duplicate_delivery"
            )
            with self.subTest(
                delivery=delivery_name,
                linkage=linkage_name,
            ), self.assertRaisesRegex(
                ValueError,
                f"report {delivery_name} reconciliation is not bound",
            ):
                builder._validate_trial_report_scope(
                    tampered,
                    journey_record,
                    wazuh,
                )

        unbound_action_reconciliation = deepcopy(report)
        action_reconciliation = unbound_action_reconciliation["records"][
            "reconciliation"
        ][2]
        action_reconciliation["execution_run_id"] = None
        action_reconciliation["linked_execution_run_ids"] = []
        with self.assertRaisesRegex(
            ValueError,
            "action reconciliation is not bound",
        ):
            builder._validate_trial_report_scope(
                unbound_action_reconciliation,
                journey_record,
                wazuh,
            )

        reconciliation_mutations = (
            ("ingest_disposition", "mismatch"),
            ("lifecycle_state", "mismatched"),
            ("mismatch_summary", "unrelated mismatch"),
        )
        for field_name, field_value in reconciliation_mutations:
            tampered = deepcopy(report)
            tampered["records"]["reconciliation"][2][field_name] = field_value
            with self.subTest(
                reconciliation_field=field_name
            ), self.assertRaisesRegex(
                ValueError,
                "action reconciliation is not bound",
            ):
                builder._validate_trial_report_scope(
                    tampered,
                    journey_record,
                    wazuh,
                )

        wrong_subject = deepcopy(report)
        wrong_subject["records"]["reconciliation"][2]["subject_linkage"][
            "action_request_ids"
        ] = ["action-from-another-trial"]
        with self.assertRaisesRegex(
            ValueError,
            "action reconciliation is not bound",
        ):
            builder._validate_trial_report_scope(
                wrong_subject,
                journey_record,
                wazuh,
            )

        previous_trial = deepcopy(report)
        previous_trial["records"]["action_request"].append(
            {
                "action_request_id": "phase67-action-from-previous-trial",
                "authority_role": "authoritative_control_plane_record",
            }
        )
        with self.assertRaisesRegex(ValueError, "is not scoped to this trial"):
            builder._validate_trial_report_scope(
                previous_trial,
                journey_record,
                wazuh,
            )

        unrelated_reconciliation = deepcopy(report)
        unrelated_reconciliation["records"]["reconciliation"].append(
            {
                "reconciliation_id": "phase67-unexpected-linked-reconciliation",
                "alert_id": identifiers["aegisops_alert_id"],
                "finding_id": identifiers["finding_id"],
                "execution_run_id": identifiers["shuffle_execution_id"],
                "linked_execution_run_ids": [],
                "authority_role": "authoritative_control_plane_record",
            }
        )
        with self.assertRaisesRegex(ValueError, "record outside this trial"):
            builder._validate_trial_report_scope(
                unrelated_reconciliation,
                journey_record,
                wazuh,
            )

    def test_journey_report_scope_excludes_preserved_prior_trial_records(self) -> None:
        current_reconciliation = SimpleNamespace(
            reconciliation_id="reconciliation-current",
            alert_id="alert-current",
            finding_id="finding-current",
            execution_run_id="execution-current",
            linked_execution_run_ids=("execution-current",),
        )
        identifiers = {
            "case_id": "case-current",
            "denied_action_request_id": "denied-action-current",
            "action_request_id": "action-current",
            "denied_approval_decision_id": "denied-approval-current",
            "approval_decision_id": "approval-current",
        }
        scope = journey._trial_report_record_ids(
            preparation={
                "alert_id": "alert-current",
                "finding_id": "finding-current",
                "wazuh_reconciliation_ids": ["reconciliation-admission"],
            },
            identifiers=identifiers,
            execution=SimpleNamespace(
                action_execution_id="action-execution-current",
                execution_run_id="execution-current",
            ),
            reconciliation=current_reconciliation,
        )
        self.assertEqual(
            scope["reconciliation"],
            frozenset(
                {"reconciliation-current", "reconciliation-admission"}
            ),
        )
        self.assertNotIn("reconciliation-previous", scope["reconciliation"])

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
            case.update(
                observed_at=None,
                status=None,
                authority_before=None,
                authority_after=None,
                measurement_source=None,
                evidence_ref=None,
            )
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
        manifest["evaluation"] = {
            "evaluated_at": None,
            "verdict": None,
            "ga_accepted": None,
            "sha256": None,
        }
        manifest["artifacts"] = {
            "retention": None,
            "directory_name": None,
            "files": [],
        }
        manifest["cleanup"] = {
            "mode": None,
            "containers_stopped": None,
            "data_preserved": None,
        }
        manifest["limitations"].append(
            {
                "limitation_id": "phase67-blocked-trigger-real-wazuh-detection",
                "owner": "AegisOps integration engineering",
                "status": "blocking",
                "description": "Reviewed service bootstrap did not complete.",
                "follow_up_issue": None,
            }
        )
        for index, step in enumerate(manifest["steps"]):
            if index < 2:
                continue
            step["status"] = "blocked" if index == 2 else "not_run"
            if index == 2:
                step["blocker"] = {
                    "owner": "AegisOps integration engineering",
                    "reason": "Reviewed service bootstrap did not complete.",
                }
            else:
                step["evidence_refs"] = ["not-run:upstream-blocker"]
        validator.validate_manifest(manifest, SCHEMA)

        for key, producing_step in validator.NEGATIVE_CASE_PRODUCING_STEPS.items():
            with self.subTest(key=key, producing_step=producing_step):
                unobserved_probe = deepcopy(manifest)
                unobserved_probe["negative_cases"][key] = {
                    "observed_at": None,
                    "status": "contained",
                    "authority_before": 1,
                    "authority_after": 1,
                    "measurement_source": (
                        "aegisops_authoritative_alert_count"
                        if key in {"invalid_credential", "proxy_bypass"}
                        else "aegisops_authoritative_record_count"
                    ),
                    "evidence_ref": "unobserved:negative-probe",
                }
                with self.assertRaisesRegex(
                    validator.EvidenceValidationError,
                    f"must be null when {producing_step} did not pass",
                ):
                    validator.validate_manifest(unobserved_probe, SCHEMA)

        claimed_evaluation = deepcopy(manifest)
        claimed_evaluation["evaluation"] = deepcopy(_manifest()["evaluation"])
        claimed_evaluation["evaluation"]["verdict"] = (
            "integration_trial_blocked"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "non-passed evaluation step cannot claim",
        ):
            validator.validate_manifest(claimed_evaluation, SCHEMA)

        unrelated_blocker = deepcopy(manifest)
        unrelated_blocker["limitations"][-1]["limitation_id"] = (
            "phase67-blocked-unrelated-step"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "must match its terminal step",
        ):
            validator.validate_manifest(unrelated_blocker, SCHEMA)

        mixed_snapshot = deepcopy(manifest)
        mixed_snapshot["snapshot"]["docker_context"] = "different-colima"
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "not bound to all snapshot inputs",
        ):
            validator.validate_manifest(mixed_snapshot, SCHEMA)

        non_chronological = deepcopy(manifest)
        non_chronological["steps"][1]["observed_at"] = (
            non_chronological["steps"][0]["observed_at"]
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "strictly chronological",
        ):
            validator.validate_manifest(non_chronological, SCHEMA)

        unobserved_identifier = deepcopy(manifest)
        unobserved_identifier["identifiers"]["native_wazuh_alert_id"] = (
            "1754042400.123456"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "must be null",
        ):
            validator.validate_manifest(unobserved_identifier, SCHEMA)

        manifest["steps"][3]["status"] = "passed"
        manifest["steps"][3]["evidence_refs"] = list(
            builder.STEP_EVIDENCE_REFS[3]
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "steps after a blocker",
        ):
            validator.validate_manifest(manifest, SCHEMA)

    def test_approval_blocked_sample_rejects_downstream_identifiers(self) -> None:
        sample = validator.load_json(E2E_ROOT / "sample-evidence.json")
        validator.validate_manifest(sample, SCHEMA)
        downstream_identifiers = {
            "shuffle_execution_id": "e89b4567-12d3-4a56-8266-426614174000",
            "action_execution_id": "action-execution-a1b2c3d4",
            "reconciliation_id": "reconciliation-a1b2c3d4",
            "report_id": "report-a1b2c3d4",
        }
        for key, value in downstream_identifiers.items():
            with self.subTest(key=key):
                tampered = deepcopy(sample)
                tampered["identifiers"][key] = value
                self.assertFalse(validator._is_legacy_blocked_manifest(tampered))
                with self.assertRaisesRegex(
                    validator.EvidenceValidationError,
                    "complete reviewed full-profile service inventory",
                ):
                    validator.validate_manifest(tampered, SCHEMA)

    def test_approval_blocked_sample_rejects_unobserved_receipt_probes(self) -> None:
        sample = validator.load_json(E2E_ROOT / "sample-evidence.json")
        for key in (
            "failed_execution",
            "malformed_receipt",
            "reconciliation_mismatch",
        ):
            with self.subTest(key=key):
                tampered = deepcopy(sample)
                tampered["negative_cases"][key] = {
                    "status": "contained",
                    "authority_before": 1,
                    "authority_after": 1,
                    "authority_delta": 0,
                    "measurement_source": "aegisops_authoritative_record_count",
                    "evidence_ref": "journey:negative-probe",
                }
                self.assertFalse(validator._is_legacy_blocked_manifest(tampered))
                with self.assertRaisesRegex(
                    validator.EvidenceValidationError,
                    "complete reviewed full-profile service inventory",
                ):
                    validator.validate_manifest(tampered, SCHEMA)

    def test_runner_uses_bound_approval_challenges_and_deterministic_record_ids(self) -> None:
        challenge_inputs = {
            "trial_id": "phase67-e2e-20260801T100000Z-0123456789ab",
            "action_request_id": "action-a1b2c3d4",
            "payload_hash": "a" * 64,
        }
        challenge = journey._approval_challenge(**challenge_inputs)
        challenge_sha256 = journey._approval_challenge_sha256(
            **challenge_inputs
        )
        self.assertEqual(
            challenge_sha256,
            hashlib.sha256(challenge.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            challenge_sha256,
            builder._approval_challenge_sha256(
                trial_run_id=challenge_inputs["trial_id"],
                action_request_id=challenge_inputs["action_request_id"],
                payload_hash=challenge_inputs["payload_hash"],
            ),
        )
        challenge_input_mutations = {
            "trial_id": "phase67-e2e-20260801T100000Z-othertrial",
            "action_request_id": "action-from-another-trial",
            "payload_hash": "b" * 64,
        }
        for field_name, field_value in challenge_input_mutations.items():
            changed_inputs = dict(challenge_inputs)
            changed_inputs[field_name] = field_value
            with self.subTest(challenge_input=field_name):
                self.assertNotEqual(
                    challenge,
                    journey._approval_challenge(**changed_inputs),
                )
                self.assertNotEqual(
                    challenge_sha256,
                    journey._approval_challenge_sha256(**changed_inputs),
                )
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

    def test_runner_action_requests_pass_the_authoritative_policy_evaluator(self) -> None:
        from aegisops.control_plane.actions.action_policy import (
            ACTION_POLICY_ALLOWED_VALUES,
            evaluate_action_policy_record,
        )

        service = SimpleNamespace(
            persist_record=lambda record, *, transitioned_at: record
        )
        action_request = journey._persist_action_request(
            service,
            action_request_id="action-a1b2c3d4",
            case=SimpleNamespace(
                case_id="case-a1b2c3d4",
                alert_id="alert-a1b2c3d4",
                finding_id="finding-a1b2c3d4",
            ),
            idempotency_key="phase67-action-a1b2c3d4",
            target_scope={"identity_id": "local-test-sink"},
            payload={"action_type": "notify_identity_owner"},
            payload_hash="a" * 64,
            requested_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
        )
        evaluated = evaluate_action_policy_record(action_request)
        self.assertEqual(
            set(action_request.policy_basis),
            set(ACTION_POLICY_ALLOWED_VALUES),
        )
        self.assertEqual(
            evaluated.policy_evaluation["approval_requirement"],
            "human_required",
        )
        self.assertEqual(evaluated.policy_evaluation["routing_target"], "approval")
        self.assertEqual(
            evaluated.policy_evaluation["execution_surface_id"],
            "shuffle",
        )

    def test_denied_action_is_revalidated_from_authoritative_records(self) -> None:
        identifiers = {
            "denied_action_request_id": "denied-action-a1b2c3d4",
            "denied_approval_decision_id": "denied-decision-a1b2c3d4",
        }

        def service_for(
            *,
            action_state: str = "rejected",
            decision_state: str = "rejected",
            execution_count: int = 0,
        ) -> SimpleNamespace:
            action = SimpleNamespace(
                action_request_id=identifiers["denied_action_request_id"],
                lifecycle_state=action_state,
                approval_decision_id=identifiers[
                    "denied_approval_decision_id"
                ],
                idempotency_key="denied-phase67-idempotency-a1b2c3d4",
                payload_hash="b" * 64,
                target_scope={"identity_id": "local-test-sink"},
                requester_identity="phase67-lab-requester",
                requested_payload={
                    "shuffle_delegation_binding": {
                        "workflow_id": "notify_identity_owner"
                    }
                },
            )
            decision = SimpleNamespace(
                approval_decision_id=identifiers[
                    "denied_approval_decision_id"
                ],
                action_request_id=identifiers["denied_action_request_id"],
                lifecycle_state=decision_state,
                approver_identities=(journey.NEGATIVE_PROBE_APPROVER_IDENTITY,),
            )
            records = {
                identifiers["denied_action_request_id"]: action,
                identifiers["denied_approval_decision_id"]: decision,
            }
            executions = [
                SimpleNamespace(
                    action_request_id=identifiers["denied_action_request_id"]
                )
                for _ in range(execution_count)
            ]
            return SimpleNamespace(
                get_record=lambda _record_type, record_id: records.get(record_id),
                _store=SimpleNamespace(list=lambda _record_type: executions),
            )

        self.assertEqual(
            journey._authoritative_denied_action_state(
                service_for(),
                identifiers,
            ),
            {
                "binding_reviewed": True,
                "dispatch_rejected": True,
                "execution_count": 0,
                "action_request_id": identifiers["denied_action_request_id"],
                "approval_decision_id": identifiers[
                    "denied_approval_decision_id"
                ],
                "idempotency_key": "denied-phase67-idempotency-a1b2c3d4",
                "payload_hash": "b" * 64,
                "target_scope": {"identity_id": "local-test-sink"},
                "requester_identity": "phase67-lab-requester",
                "action_request_lifecycle_state": "rejected",
                "approval_decision_lifecycle_state": "rejected",
                "approver_identities": [
                    journey.NEGATIVE_PROBE_APPROVER_IDENTITY
                ],
            },
        )
        for kwargs in (
            {"action_state": "approved"},
            {"decision_state": "granted"},
            {"execution_count": 1},
        ):
            with self.subTest(**kwargs), self.assertRaisesRegex(
                RuntimeError,
                "authoritative denied action state changed",
            ):
                journey._authoritative_denied_action_state(
                    service_for(**kwargs),
                    identifiers,
                )

    def test_swarm_label_claim_preserves_hybrid_network_spec(self) -> None:
        service = _hybrid_network_worker_service()
        api = _FakeDockerEngine(service)
        labels = {
            "com.aegisops.lab.phase": "67.4",
            "com.aegisops.lab.component": "shuffle-worker-image",
            "com.aegisops.lab.trial-run-id": "phase67-e2e-test",
        }

        result = swarm_labeler.claim_service_labels(
            api,
            service_id=service["ID"],
            expected_version=service["Version"]["Index"],
            expected_name=service["Spec"]["Name"],
            expected_image=service["Spec"]["TaskTemplate"]["ContainerSpec"][
                "Image"
            ],
            labels=labels,
        )

        self.assertTrue(api.api_checked)
        self.assertIsNotNone(api.updated_spec)
        assert api.updated_spec is not None
        self.assertEqual(
            api.updated_spec["TaskTemplate"]["Networks"],
            service["Spec"]["TaskTemplate"]["Networks"],
        )
        self.assertEqual(
            api.updated_spec["Networks"],
            service["Spec"]["Networks"],
        )
        expected_spec = deepcopy(service["Spec"])
        expected_spec["Labels"].update(labels)
        self.assertEqual(api.updated_spec, expected_spec)
        self.assertEqual(result["version_before"], 2342226)
        self.assertEqual(result["version_after"], 2342227)

    def test_swarm_label_claim_rejects_stale_or_preowned_service(self) -> None:
        service = _hybrid_network_worker_service()
        arguments = {
            "service_id": service["ID"],
            "expected_name": service["Spec"]["Name"],
            "expected_image": service["Spec"]["TaskTemplate"]["ContainerSpec"][
                "Image"
            ],
            "labels": {"com.aegisops.lab.phase": "67.4"},
        }
        with self.assertRaisesRegex(
            swarm_labeler.SwarmLabelUpdateError,
            "changed before ownership",
        ):
            swarm_labeler.claim_service_labels(
                _FakeDockerEngine(service),
                expected_version=service["Version"]["Index"] - 1,
                **arguments,
            )

        service["Spec"]["Labels"]["com.aegisops.lab.phase"] = "unknown"
        with self.assertRaisesRegex(
            swarm_labeler.SwarmLabelUpdateError,
            "already carries ownership labels",
        ):
            swarm_labeler.claim_service_labels(
                _FakeDockerEngine(service),
                expected_version=service["Version"]["Index"],
                **arguments,
            )

    def test_swarm_label_claim_rejects_nonlabel_daemon_mutation(self) -> None:
        service = _hybrid_network_worker_service()

        def mutate_network(updated_service: dict) -> None:
            updated_service["Spec"]["TaskTemplate"]["Networks"].append(
                {"Target": "unexpected-overlay"}
            )

        with self.assertRaisesRegex(
            swarm_labeler.SwarmLabelUpdateError,
            "changed outside ownership labels",
        ):
            swarm_labeler.claim_service_labels(
                _FakeDockerEngine(service, after_update=mutate_network),
                service_id=service["ID"],
                expected_version=service["Version"]["Index"],
                expected_name=service["Spec"]["Name"],
                expected_image=service["Spec"]["TaskTemplate"][
                    "ContainerSpec"
                ]["Image"],
                labels={"com.aegisops.lab.phase": "67.4"},
            )

    def test_swarm_labeler_uses_the_v140_engine_update_endpoint(self) -> None:
        requests: list[tuple[str, str, object, dict[str, str]]] = []
        response_payloads = [
            {"ApiVersion": "1.51", "MinAPIVersion": "1.24"},
            {"ID": "wo7au34eetl5tc0id1jzxxu9e"},
            {"Warnings": None},
            {"Warnings": ["unexpected daemon warning"]},
        ]

        class FakeConnection:
            def __init__(self, _socket_path: Path, _timeout: float) -> None:
                pass

            def request(
                self,
                method: str,
                path: str,
                body=None,
                headers=None,
            ) -> None:
                requests.append((method, path, body, headers or {}))

            def getresponse(self):
                payload = json.dumps(response_payloads.pop(0)).encode("utf-8")
                return SimpleNamespace(
                    status=200,
                    reason="OK",
                    read=lambda _limit: payload,
                )

            def close(self) -> None:
                pass

        original_connection = swarm_labeler.UnixSocketHTTPConnection
        swarm_labeler.UnixSocketHTTPConnection = FakeConnection
        try:
            api = swarm_labeler.DockerEngineAPI(Path("/unused/docker.sock"))
            api.assert_api_version_supported()
            self.assertEqual(
                api.get_service("wo7au34eetl5tc0id1jzxxu9e"),
                {"ID": "wo7au34eetl5tc0id1jzxxu9e"},
            )
            spec = {"Name": "shuffle-workers", "Labels": {"owner": "trial"}}
            api.update_service("wo7au34eetl5tc0id1jzxxu9e", 42, spec)
            with self.assertRaisesRegex(
                swarm_labeler.SwarmLabelUpdateError,
                "returned warnings",
            ):
                api.update_service("wo7au34eetl5tc0id1jzxxu9e", 43, spec)
        finally:
            swarm_labeler.UnixSocketHTTPConnection = original_connection

        self.assertEqual(requests[0][0:2], ("GET", "/version"))
        self.assertEqual(
            requests[1][0:2],
            (
                "GET",
                "/v1.40/services/wo7au34eetl5tc0id1jzxxu9e",
            ),
        )
        self.assertEqual(
            requests[2][0:2],
            (
                "POST",
                "/v1.40/services/wo7au34eetl5tc0id1jzxxu9e/update?version=42",
            ),
        )
        self.assertEqual(json.loads(requests[2][2]), spec)
        self.assertEqual(
            requests[2][3],
            {"Content-Type": "application/json"},
        )

    def test_swarm_labeler_rejects_non_unix_docker_context(self) -> None:
        context = {
            "Name": "remote-context",
            "Endpoints": {"docker": {"Host": "tcp://docker.example:2376"}},
        }
        original_run = swarm_labeler.subprocess.run
        swarm_labeler.subprocess.run = lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps([context]),
            stderr="",
        )
        try:
            with self.assertRaisesRegex(
                swarm_labeler.SwarmLabelUpdateError,
                "local Unix-socket Docker context",
            ):
                swarm_labeler.resolve_docker_socket("remote-context")
        finally:
            swarm_labeler.subprocess.run = original_run

    def test_operator_runner_binds_full_scope_restart_and_cleanup(self) -> None:
        runner = (LAB_ROOT / "run-e2e-trial.sh").read_text(encoding="utf-8")
        compose = (LAB_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        reviewed_image_env = {
            key: value
            for key, value in (
                line.split("=", 1)
                for line in (LAB_ROOT / "shuffle" / "reviewed-app-image.env")
                .read_text(encoding="utf-8")
                .splitlines()
                if line
            )
        }
        services_section = compose.partition("services:\n")[2].partition(
            "\nnetworks:\n"
        )[0]
        compose_services = set(
            re.findall(r"^  ([a-z0-9-]+):$", services_section, re.MULTILINE)
        )
        self.assertEqual(
            compose_services | {"shuffle-action-image", "shuffle-worker-image"},
            validator.EXPECTED_FULL_PROFILE_IMAGE_SERVICES,
        )
        for service, immutable_reference in (
            validator.REVIEWED_IMMUTABLE_IMAGE_REFERENCES.items()
        ):
            if service == "shuffle-action-image":
                continue
            self.assertIn(immutable_reference, compose)
        self.assertEqual(
            validator.REVIEWED_IMMUTABLE_IMAGE_REFERENCES[
                "shuffle-action-image"
            ],
            reviewed_image_env["AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_REPOSITORY"]
            + "@"
            + reviewed_image_env["AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST"],
        )
        self.assertIn('"${LAB_DIR}/up.sh" full', runner)
        wrapper_start = runner.index("run_reviewed_lab_command()")
        wrapper_end = runner.index("run_reviewed_journey()", wrapper_start)
        reviewed_lab_wrapper = runner[wrapper_start:wrapper_end]
        self.assertRegex(
            reviewed_lab_wrapper,
            r'assert_repository_snapshot\s+"\$@"',
        )
        reviewed_lab_calls = (
            'run_reviewed_lab_command "${LAB_DIR}/pin-shuffle-app-image.sh"',
            "run_reviewed_lab_command ensure_reviewed_shuffle_action_service",
            'run_reviewed_lab_command "${LAB_DIR}/status.sh" full --write-evidence',
            'run_reviewed_lab_command "${LAB_DIR}/test-wazuh-intake.sh"',
            "run_reviewed_lab_command remove_reviewed_shuffle_action_service",
            "run_reviewed_lab_command remove_reviewed_shuffle_worker_service",
            'run_reviewed_lab_command "${LAB_DIR}/down.sh"',
            'run_reviewed_lab_command "${LAB_DIR}/cleanup.sh"',
        )
        for reviewed_call in reviewed_lab_calls:
            with self.subTest(reviewed_call=reviewed_call):
                self.assertIn(reviewed_call, runner)
        self.assertEqual(
            runner.count('run_reviewed_lab_startup "${LAB_DIR}/up.sh" full'),
            2,
        )
        startup_wrapper_start = runner.index("run_reviewed_lab_startup()")
        startup_wrapper_end = runner.index(
            '[[ -f "${evaluation}" ]]',
            startup_wrapper_start,
        )
        startup_wrapper = runner[startup_wrapper_start:startup_wrapper_end]
        self.assertLess(
            startup_wrapper.index("assert_repository_snapshot"),
            startup_wrapper.index("assert_compose_snapshot"),
        )
        self.assertIn("AEGISOPS_LAB_TRIAL_SCOPE=full", runner)
        self.assertIn("compose_scope full ps -aq", runner)
        self.assertIn("docker_lab inspect ${container_ids}", runner)
        self.assertIn('python3 "${validator}" --runtime-images', runner)
        self.assertIn('docker_context="${AEGISOPS_LAB_DOCKER_CONTEXT}"', runner)
        self.assertIn('colima_profile="${AEGISOPS_LAB_COLIMA_PROFILE}"', runner)
        self.assertIn('[[ -t 0 && -t 1 ]]', runner)
        self.assertIn('approval_method="macos_operator_dialog"', runner)
        self.assertIn('display dialog promptText', runner)
        self.assertIn('"APPROVE ${approval_challenge}"', runner)
        self.assertIn(
            'record_step 15 "record_prerequisite_evaluation"',
            runner,
        )
        self.assertNotIn(
            'record_step 15 "publish_prerequisite_evaluation"',
            runner,
        )
        self.assertIn('prepare \\', runner)
        self.assertIn('--approver-identity "${approver_identity}"', runner)
        self.assertIn('"shuffle-action-image"', runner)
        self.assertIn('"shuffle-worker-image"', runner)
        self.assertIn("capture_reviewed_shuffle_action_image()", runner)
        self.assertIn("capture_reviewed_shuffle_worker_image()", runner)
        self.assertIn("ensure_reviewed_shuffle_action_service()", runner)
        self.assertIn("assert_reviewed_shuffle_action_service()", runner)
        self.assertIn('--name "${shuffle_action_service}"', runner)
        self.assertIn('"${shuffle_tools_immutable_ref}"', runner)
        service_create = runner.index("docker_lab service create")
        service_create_end = runner.index(
            '"${shuffle_tools_immutable_ref}"',
            service_create,
        )
        service_create_block = runner[service_create:service_create_end + 40]
        self.assertIn('"${shuffle_tools_immutable_ref}"', service_create_block)
        self.assertNotIn('"${shuffle_tools_image}"', service_create_block)
        self.assertIn("--quiet", service_create_block)
        self.assertIn(
            'com.aegisops.lab.trial-run-id=${trial_run_id}',
            service_create_block,
        )
        self.assertIn(
            'shuffle_action_service_id="$(docker_lab service create',
            runner,
        )
        self.assertIn(".Image == $image_id", runner)
        self.assertIn(
            "postdispatch_shuffle_action_image=",
            runner,
        )
        self.assertIn('runtime_image_id: $runtime_image_id', runner)
        self.assertIn('SHUFFLE_WORKER_IMAGE=', runner)
        self.assertIn(
            'docker_lab service inspect "${shuffle_worker_service}"',
            runner,
        )
        self.assertIn("docker_lab service ps \\", runner)
        self.assertIn('.Status.State == "running"', runner)
        self.assertIn(".Status.ContainerStatus.ContainerID", runner)
        self.assertIn('.State.Running == true', runner)
        self.assertIn('docker_lab logs \\', runner)
        self.assertIn(
            'capture_reviewed_shuffle_worker_image "${shuffle_execution_id}"',
            runner,
        )
        self.assertIn(
            "Shuffle worker container logs do not contain the reviewed execution ID",
            runner,
        )
        self.assertIn(
            '[[ "${postdispatch_shuffle_worker_image}" == "${shuffle_worker_image}" ]]',
            runner,
        )
        self.assertIn("configured_shuffle_worker_immutable_ref()", runner)
        self.assertIn("assert_shuffle_action_service_absent()", runner)
        self.assertIn("assert_shuffle_worker_service_absent()", runner)
        self.assertIn("claim_reviewed_shuffle_worker_service()", runner)
        self.assertIn("shuffle_worker_service_is_trial_owned()", runner)
        self.assertIn(
            "shuffle_worker_service_matches_attempted_claim()",
            runner,
        )
        self.assertIn(
            "com.aegisops.lab.trial-run-id=${trial_run_id}",
            runner,
        )
        action_preflight = runner.index(
            "run_reviewed_lab_command assert_shuffle_action_service_absent"
        )
        worker_preflight = runner.index(
            "run_reviewed_lab_command assert_shuffle_worker_service_absent"
        )
        first_startup = runner.index(
            'run_reviewed_lab_startup "${LAB_DIR}/up.sh" full'
        )
        self.assertLess(action_preflight, worker_preflight)
        self.assertLess(worker_preflight, first_startup)
        first_worker_capture = runner.index(
            "capture_reviewed_shuffle_worker_image >/dev/null",
            first_startup,
        )
        self.assertLess(
            first_worker_capture,
            runner.index(
                'retain_status_evidence "${startup_output}"',
                first_startup,
            ),
        )
        self.assertLess(
            first_worker_capture,
            runner.index(
                "run_reviewed_lab_command ensure_reviewed_shuffle_action_service",
                first_startup,
            ),
        )
        capture_start = runner.index("capture_reviewed_shuffle_worker_image()")
        capture_end = runner.index("cleanup_on_exit()", capture_start)
        worker_capture = runner[capture_start:capture_end]
        self.assertLess(
            worker_capture.index("claim_reviewed_shuffle_worker_service"),
            worker_capture.index('service_image="$('),
        )
        claim_start = runner.index("claim_reviewed_shuffle_worker_service()")
        claim_end = runner.index(
            "remove_reviewed_shuffle_worker_service()",
            claim_start,
        )
        worker_claim = runner[claim_start:claim_end]
        self.assertLess(
            worker_claim.index(
                '[[ "${service_image}" != "${shuffle_worker_immutable_ref}" ]]'
            ),
            worker_claim.index('python3 "${swarm_service_labeler}"'),
        )
        self.assertIn(
            '--expected-version "${service_version}"',
            worker_claim,
        )
        self.assertIn(
            '--docker-context "${AEGISOPS_LAB_DOCKER_CONTEXT}"',
            worker_claim,
        )
        self.assertNotIn("docker_lab service update", worker_claim)
        self.assertIn(
            "shuffle_worker_service_matches_attempted_claim",
            worker_claim,
        )
        self.assertLess(
            worker_claim.index('shuffle_worker_service_id="${service_id}"'),
            worker_claim.index('owned_metadata="$('),
        )
        self.assertIn("remove_reviewed_shuffle_worker_service()", runner)
        remove_action_start = runner.index(
            "remove_reviewed_shuffle_action_service()"
        )
        remove_action_end = runner.index(
            "configured_shuffle_worker_immutable_ref()",
            remove_action_start,
        )
        remove_action = runner[remove_action_start:remove_action_end]
        self.assertLess(
            remove_action.index('[[ "${shuffle_action_owned}" == true ]]'),
            remove_action.index(
                'docker_lab service inspect "${owned_service_id}"'
            ),
        )
        self.assertLess(
            remove_action.index(
                'com.aegisops.lab.trial-run-id"] == $trial_run_id'
            ),
            remove_action.index('docker_lab service rm "${owned_service_id}"'),
        )
        self.assertLess(
            remove_action.index(
                ".Spec.TaskTemplate.ContainerSpec.Image == $image"
            ),
            remove_action.index('docker_lab service rm "${owned_service_id}"'),
        )
        self.assertIn(
            'label=com.docker.swarm.service.id=${owned_service_id}',
            remove_action,
        )
        remove_start = runner.index("remove_reviewed_shuffle_worker_service()")
        remove_end = runner.index(
            '[[ -f "${evaluation}" ]]',
            remove_start,
        )
        remove_worker = runner[remove_start:remove_end]
        self.assertLess(
            remove_worker.index("shuffle_worker_service_is_trial_owned"),
            remove_worker.index('docker_lab service rm "${shuffle_worker_service_id}"'),
        )
        self.assertLess(
            remove_worker.index(
                '[[ "${shuffle_worker_preflight_absent}" != true ]]'
            ),
            remove_worker.index("claim_reviewed_shuffle_worker_service"),
        )
        self.assertLess(
            remove_worker.index('shuffle_worker_immutable_ref="${expected_image}"'),
            remove_worker.index("claim_reviewed_shuffle_worker_service"),
        )
        self.assertIn(
            "refusing to claim an unverified Shuffle worker service during cleanup",
            remove_worker,
        )
        self.assertIn(
            '[[ "${service_image}" != "${expected_image}" ]]',
            runner,
        )
        self.assertIn(
            'docker_lab service rm "${shuffle_worker_service_id}"',
            runner,
        )
        self.assertIn(
            'label=com.docker.swarm.service.name=${shuffle_worker_service}',
            runner,
        )
        exit_cleanup_start = runner.index("cleanup_on_exit()")
        exit_cleanup_end = runner.index("trap cleanup_on_exit EXIT")
        exit_cleanup = runner[exit_cleanup_start:exit_cleanup_end]
        self.assertLess(
            exit_cleanup.index("remove_reviewed_shuffle_worker_service"),
            exit_cleanup.index('"${LAB_DIR}/cleanup.sh"'),
        )
        normal_worker_cleanup = runner.rindex(
            "run_reviewed_lab_command remove_reviewed_shuffle_worker_service"
        )
        normal_compose_cleanup = runner.rindex(
            'run_reviewed_lab_command "${LAB_DIR}/cleanup.sh"'
        )
        self.assertLess(normal_worker_cleanup, normal_compose_cleanup)
        self.assertIn('final_artifacts=', runner)
        self.assertLess(
            runner.index('mv "${report_output}" "${final_report}"'),
            runner.index('mv "${final_artifacts}/evidence.json" "${final_evidence}"'),
        )
        self.assertLess(
            runner.index('mv "${staging_dir}" "${final_artifacts}"'),
            runner.index('mv "${final_artifacts}/evidence.json" "${final_evidence}"'),
        )
        self.assertIn('publication_manifest_published=false', runner)
        self.assertIn('publication_manifest_moved=false', runner)
        self.assertIn('no passing manifest was published', runner)
        self.assertIn('startup_status_output=', runner)
        self.assertIn('initial_status_output=', runner)
        self.assertIn('restart_status_output=', runner)
        self.assertIn('workflow_snapshot_output=', runner)
        self.assertIn('workflow_predispatch_output=', runner)
        self.assertIn('compose_render_output=', runner)
        self.assertIn('compose_digest_output=', runner)
        self.assertIn(
            'capture_reviewed_compose_config >"${compose_render_output}"',
            runner,
        )
        self.assertIn('--compose-config "${compose_render_output}"', runner)
        self.assertIn(
            '--compose-digest-record "${compose_digest_output}"',
            runner,
        )
        self.assertIn(
            '--expected-repository-revision "${repository_revision}"',
            runner,
        )
        self.assertIn(
            '--expected-compose-sha256 "${compose_render_sha256}"',
            runner,
        )
        self.assertNotIn("--wazuh-schema", runner)
        self.assertNotIn("--wazuh-validator", runner)
        self.assertNotIn("--workflow-validator", runner)
        self.assertGreaterEqual(
            runner.count('rm -f "${compose_render_output}"'),
            2,
        )
        self.assertIn(
            'capture_reviewed_shuffle_workflow "${workflow_snapshot_output}"',
            runner,
        )
        self.assertIn(
            'capture_reviewed_shuffle_workflow "${workflow_predispatch_output}"',
            runner,
        )
        self.assertIn(
            'live Shuffle workflow changed after the trial snapshot',
            runner,
        )
        dispatch = runner.index("run_reviewed_journey \\\n  execute")
        predispatch_image_check = runner.rindex(
            'predispatch_shuffle_action_image="$(capture_reviewed_shuffle_action_image)"',
            0,
            dispatch,
        )
        self.assertLess(predispatch_image_check, dispatch)
        guarded_runner_start = runner.index("run_reviewed_journey()")
        guarded_runner_end = runner.index(
            '[[ -f "${evaluation}" ]]',
            guarded_runner_start,
        )
        guarded_runner = runner[guarded_runner_start:guarded_runner_end]
        self.assertLess(
            guarded_runner.index("assert_repository_snapshot"),
            guarded_runner.index("compose_scope full exec -T"),
        )
        self.assertEqual(
            runner.count(
                "python3 /opt/aegisops/phase67-e2e/run_real_journey.py"
            ),
            1,
        )
        self.assertEqual(runner.count("run_reviewed_journey"), 4)
        self.assertIn('retain_status_evidence "${startup_output}"', runner)
        self.assertIn('--startup-status "${startup_status_output}"', runner)
        snapshot_completed = runner.index('>"${snapshot_output}"')
        action_service_ready = runner.index(
            "run_reviewed_lab_command ensure_reviewed_shuffle_action_service"
        )
        worker_image_captured = runner.index(
            "capture_reviewed_shuffle_worker_image >/dev/null"
        )
        runtime_images_validated = runner.index(
            'python3 "${validator}" --runtime-images'
        )
        journey_prepared = runner.index(
            "run_reviewed_journey \\\n  prepare"
        )
        step_one_recorded = runner.index('record_step 1 "capture_immutable_snapshot"')
        initial_status_retained = runner.index(
            '"${initial_status_output}"\nrecord_step 2'
        )
        self.assertLess(runtime_images_validated, journey_prepared)
        self.assertLess(action_service_ready, snapshot_completed)
        self.assertLess(worker_image_captured, snapshot_completed)
        self.assertLess(snapshot_completed, step_one_recorded)
        self.assertLess(step_one_recorded, initial_status_retained)
        self.assertIn(
            'record_step 2 "record_lab_health_after_snapshot"',
            runner,
        )
        self.assertNotIn(
            'record_step 2 "start_lab_and_record_health"',
            runner,
        )
        self.assertNotIn("docker inspect ${container_ids}", runner)
        self.assertNotIn("docker context show", runner)
        self.assertNotIn('colima_profile="${COLIMA_PROFILE:-default}"', runner)
        self.assertNotIn('rm -rf "${staging_dir}"', runner)
        self.assertIn("verify-restart", runner)
        self.assertIn(
            "--slurpfile report \"${report_output}\"",
            runner,
        )
        self.assertIn("report: $report[0]", runner)
        self.assertIn('"${LAB_DIR}/cleanup.sh"', runner)
        cleanup = runner.index('"${LAB_DIR}/cleanup.sh"')
        final_snapshot_check = runner.index("assert_repository_snapshot", cleanup)
        evidence_build = runner.index('python3 "${builder}"', final_snapshot_check)
        final_compose_check = runner.index(
            "assert_compose_snapshot",
            final_snapshot_check,
        )
        self.assertLess(cleanup, final_snapshot_check)
        self.assertLess(final_snapshot_check, final_compose_check)
        self.assertLess(final_compose_check, evidence_build)
        self.assertLess(final_snapshot_check, evidence_build)
        post_build_snapshot_check = runner.index(
            "assert_repository_snapshot",
            evidence_build,
        )
        evidence_validation = runner.index(
            'python3 "${validator}"',
            post_build_snapshot_check,
        )
        post_validation_snapshot_check = runner.index(
            "assert_repository_snapshot",
            evidence_validation,
        )
        self.assertLess(evidence_build, post_build_snapshot_check)
        self.assertLess(post_build_snapshot_check, evidence_validation)
        self.assertLess(evidence_validation, post_validation_snapshot_check)
        final_manifest_move = runner.index(
            'mv "${final_artifacts}/evidence.json" "${final_evidence}"'
        )
        final_manifest_validation = runner.index(
            "--published",
            final_manifest_move,
        )
        self.assertLess(final_manifest_move, final_manifest_validation)
        publication_complete = runner.index(
            "publication_manifest_published=true",
            final_manifest_validation,
        )
        validation_block = runner[
            final_manifest_validation:publication_complete
        ]
        self.assertIn('"${final_report}"', validation_block)
        self.assertIn('"${final_artifacts}"', validation_block)
        self.assertLess(
            final_manifest_validation,
            publication_complete,
        )
        self.assertIn("status --porcelain=v1 --untracked-files=all", runner)
        self.assertNotIn("destroy-data.sh", runner)
        real_journey = (E2E_ROOT / "run_real_journey.py").read_text(
            encoding="utf-8"
        )
        self.assertGreaterEqual(
            real_journey.count('"idempotency_key": action.idempotency_key'),
            2,
        )
        self.assertGreaterEqual(
            real_journey.count('"payload_hash": action.payload_hash'),
            2,
        )
        self.assertIn('"target_scope": dict(action.target_scope)', real_journey)
        self.assertIn('lifecycle_state="rejected"', real_journey)
        self.assertNotIn('lifecycle_state="denied"', real_journey)
        self.assertNotIn("class _StaticTransport", real_journey)
        self.assertIn("service.reconcile_action_execution(", real_journey)
        self.assertIn("record_ids_by_family=_trial_report_record_ids(", real_journey)
        self.assertIn("delegated_at = datetime.now(timezone.utc)", real_journey)
        self.assertIn("delegated_at=delegated_at", real_journey)
        self.assertNotIn(
            "delegated_at=decided_at + timedelta(seconds=1)",
            real_journey,
        )
        self.assertNotIn(
            "datetime.now(timezone.utc) - timedelta(seconds=5)",
            real_journey,
        )
        denied_revalidation = real_journey.index(
            "denied = _authoritative_denied_action_state(service, identifiers)"
        )
        delegated = real_journey.index(
            "execution = service.delegate_approved_action_to_shuffle(",
            denied_revalidation,
        )
        self.assertLess(denied_revalidation, delegated)
        real_shuffle_adapter = (
            CONTROL_PLANE_ROOT
            / "aegisops"
            / "control_plane"
            / "adapters"
            / "shuffle_real.py"
        ).read_text(encoding="utf-8")
        revalidation = real_shuffle_adapter.index(
            "self._revalidate_reviewed_workflow()"
        )
        dispatch = real_shuffle_adapter.index(
            'method="POST",',
            revalidation,
        )
        self.assertLess(revalidation, dispatch)
        compose = (LAB_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("./e2e:/opt/aegisops/phase67-e2e:ro", compose)


if __name__ == "__main__":
    unittest.main()
