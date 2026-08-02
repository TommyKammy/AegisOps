from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
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
builder = _load_module(
    "phase67_4_evidence_builder",
    E2E_ROOT / "build_evidence.py",
)
SCHEMA = validator.load_json(E2E_ROOT / "evidence-manifest.schema.json")


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
            {
                "service": "wazuh-manager",
                "immutable_reference": "wazuh/wazuh-manager@sha256:" + "f" * 64,
            },
            {
                "service": "shuffle-backend",
                "immutable_reference": "frikky/shuffle-backend@sha256:" + "1" * 64,
            },
            {
                "service": "shuffle-action-image",
                "immutable_reference": "ghcr.io/aegisops/shuffle-tools@sha256:"
                + "3" * 64,
            },
        ],
    }
    snapshot_id = validator._snapshot_identifier(trial_run_id, snapshot)
    snapshot["snapshot_id"] = snapshot_id
    observed_at = "2026-08-01T10:00:00Z"
    steps = [
        {
            "step": index,
            "name": name,
            "status": "passed",
            "snapshot_id": snapshot_id,
            "observed_at": f"2026-08-01T10:00:{index:02d}Z",
            "evidence_refs": [f"evidence:step-{index}"],
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
            "approver_identity": "local-operator:reviewer",
            "authenticated_approver_identity": "local-operator:reviewer",
            "denied_action_execution_count": 0,
            "denied_dispatch_rejected": True,
            "approval_source": "interactive_local_operator_ceremony",
            "approval_method": "tty_challenge",
            "approval_challenge_sha256": "4" * 64,
            "approval_confirmed_at": observed_at,
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
                "authority_before": 10,
                "authority_after": (
                    11
                    if key in {"failed_execution", "reconciliation_mismatch"}
                    else 10
                ),
                "authority_delta": (
                    1
                    if key in {"failed_execution", "reconciliation_mismatch"}
                    else 0
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
        "evaluation": {
            "trial_run_id": "phase67-e2e-20260801T100000Z-0123456789ab",
            "snapshot_id": snapshot_id,
            "repository_revision": "a" * 40,
            "evaluated_at": observed_at,
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
                {"name": name, "sha256": "6" * 64}
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

    def test_validator_rejects_non_chronological_step_observations(self) -> None:
        manifest = _manifest()
        manifest["steps"][7]["observed_at"] = manifest["steps"][6]["observed_at"]
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "strictly chronological",
        ):
            validator.validate_manifest(manifest, SCHEMA)

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
                return SimpleNamespace(ingest_disposition="mismatch")

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

        stale_evaluation = _manifest()
        stale_evaluation["evaluation"]["trial_run_id"] = (
            "phase67-e2e-20260801T100001Z-0123456789ab"
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "evaluation is not bound to this trial",
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

    def test_status_evidence_requires_one_complete_image_identity(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            status_path = Path(temporary_directory) / "status.txt"
            status_path.write_text(
                "control_plane_container_image_id=sha256:" + "a" * 64 + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                builder._status_value(
                    status_path,
                    "control_plane_container_image_id",
                ),
                "sha256:" + "a" * 64,
            )
            status_path.write_text(
                "control_plane_container_image_id=sha256:" + "a" * 64 + "\n"
                "control_plane_container_image_id=sha256:" + "b" * 64 + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "exactly one"):
                builder._status_value(
                    status_path,
                    "control_plane_container_image_id",
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
        unmeasured = _manifest()
        unmeasured["negative_cases"]["failed_execution"]["authority_delta"] = 0
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "authority delta is not measured",
        ):
            validator.validate_manifest(unmeasured, SCHEMA)

        incomplete = _manifest()
        incomplete["artifacts"]["files"].pop()
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "raw artifact inventory is incomplete",
        ):
            validator.validate_manifest(incomplete, SCHEMA)

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
                status=None,
                authority_before=None,
                authority_after=None,
                authority_delta=None,
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
            "trial_run_id": None,
            "snapshot_id": None,
            "repository_revision": None,
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
                with self.assertRaisesRegex(
                    validator.EvidenceValidationError,
                    "must be null",
                ):
                    validator.validate_manifest(tampered, SCHEMA)

    def test_runner_uses_bound_approval_challenges_and_deterministic_record_ids(self) -> None:
        challenge = journey._approval_challenge(
            trial_id="phase67-e2e-20260801T100000Z-0123456789ab",
            action_request_id="action-a1b2c3d4",
            payload_hash="a" * 64,
        )
        changed = journey._approval_challenge(
            trial_id="phase67-e2e-20260801T100000Z-0123456789ab",
            action_request_id="action-a1b2c3d4",
            payload_hash="b" * 64,
        )
        self.assertNotEqual(challenge, changed)
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

    def test_operator_runner_binds_full_scope_restart_and_cleanup(self) -> None:
        runner = (LAB_ROOT / "run-e2e-trial.sh").read_text(encoding="utf-8")
        self.assertIn('"${LAB_DIR}/up.sh" full', runner)
        self.assertIn("AEGISOPS_LAB_TRIAL_SCOPE=full", runner)
        self.assertIn("docker_lab inspect ${container_ids}", runner)
        self.assertIn('docker_context="${AEGISOPS_LAB_DOCKER_CONTEXT}"', runner)
        self.assertIn('colima_profile="${AEGISOPS_LAB_COLIMA_PROFILE}"', runner)
        self.assertIn('[[ -t 0 && -t 1 ]]', runner)
        self.assertIn('approval_method="macos_operator_dialog"', runner)
        self.assertIn('display dialog promptText', runner)
        self.assertIn('"APPROVE ${approval_challenge}"', runner)
        self.assertIn('prepare \\', runner)
        self.assertIn('--approver-identity "${approver_identity}"', runner)
        self.assertIn('"shuffle-action-image"', runner)
        self.assertIn('final_artifacts=', runner)
        self.assertIn('startup_status_output=', runner)
        self.assertIn('initial_status_output=', runner)
        self.assertIn('restart_status_output=', runner)
        self.assertIn('workflow_snapshot_output=', runner)
        self.assertIn('workflow_predispatch_output=', runner)
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
        self.assertIn('retain_status_evidence "${startup_output}"', runner)
        self.assertIn('--startup-status "${startup_status_output}"', runner)
        snapshot_completed = runner.index('>"${snapshot_output}"')
        step_one_recorded = runner.index('record_step 1 "capture_immutable_snapshot"')
        initial_status_retained = runner.index(
            '"${initial_status_output}"\nrecord_step 2'
        )
        self.assertLess(snapshot_completed, step_one_recorded)
        self.assertLess(step_one_recorded, initial_status_retained)
        self.assertNotIn("docker inspect ${container_ids}", runner)
        self.assertNotIn("docker context show", runner)
        self.assertNotIn('colima_profile="${COLIMA_PROFILE:-default}"', runner)
        self.assertNotIn('rm -rf "${staging_dir}"', runner)
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
        self.assertNotIn("class _StaticTransport", real_journey)
        self.assertIn("service.reconcile_action_execution(", real_journey)
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
