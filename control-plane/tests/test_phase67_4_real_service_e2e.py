from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
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
            *(
                {
                    "service": service,
                    "immutable_reference": immutable_reference,
                    **(
                        {"runtime_image_id": "sha256:" + "f" * 64}
                        if service == "shuffle-action-image"
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
    observed_at = "2026-08-01T10:00:00Z"
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
            builder.STEP_NAMES[-1],
            "record_prerequisite_evaluation",
        )
        self.assertEqual(builder.STEP_EVIDENCE_REFS, validator.STEP_EVIDENCE_REFS)
        self.assertEqual(
            builder.LIMITATION_STATUSES,
            validator.OWNED_LIMITATION_STATUSES,
        )
        validator.validate_manifest(_manifest(), SCHEMA)

    def test_schema_allows_the_complete_runtime_image_inventory(self) -> None:
        images_schema = SCHEMA["properties"]["snapshot"]["properties"]["images"]
        self.assertEqual(
            images_schema["maxItems"],
            len(validator.EXPECTED_FULL_PROFILE_IMAGE_SERVICES),
        )
        self.assertEqual(
            len(_manifest()["snapshot"]["images"]),
            images_schema["maxItems"],
        )
        self.assertEqual(
            set(
                SCHEMA["properties"]["snapshot"]["properties"][
                    "host_architecture"
                ]["enum"]
            ),
            validator.SUPPORTED_HOST_ARCHITECTURES,
        )

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
                },
                "journey": {
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

        builder._validate_step_observation_sources(
            observations,
            **source_payloads(),
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

        missing_runtime_identity = _manifest()
        action_image = next(
            image
            for image in missing_runtime_identity["snapshot"]["images"]
            if image["service"] == "shuffle-action-image"
        )
        action_image.pop("runtime_image_id")
        missing_runtime_identity["snapshot"]["snapshot_id"] = (
            validator._snapshot_identifier(
                missing_runtime_identity["trial_run_id"],
                missing_runtime_identity["snapshot"],
            )
        )
        with self.assertRaisesRegex(
            validator.EvidenceValidationError,
            "observed Shuffle action runtime image ID",
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
        manifest["evaluation"]["snapshot_id"] = snapshot_id
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
        tampered["evaluation"]["snapshot_id"] = tampered_snapshot_id
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
        with TemporaryDirectory() as temporary_directory:
            status_path = Path(temporary_directory) / "status.txt"
            status_path.write_text(
                "repository_commit=" + "a" * 40 + "\n"
                "repository_runtime_state=clean\n"
                "repository_runtime_artifact_sha256=" + "d" * 64 + "\n"
                "control_plane_container_image_id=sha256:" + "e" * 64 + "\n",
                encoding="utf-8",
            )
            builder._validate_status_snapshot(status_path, snapshot)
            status_path.write_text(
                "repository_commit=" + "a" * 40 + "\n"
                "repository_runtime_state=clean\n"
                "repository_runtime_artifact_sha256=" + "d" * 64 + "\n"
                "control_plane_container_image_id=sha256:" + "f" * 64 + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "different control-plane image"):
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

    def test_builder_binds_restart_to_exact_wazuh_reconciliation_scope(self) -> None:
        journey_scope = {
            "wazuh_reconciliation_ids": [
                "reconciliation-wazuh-admission",
                "reconciliation-wazuh-duplicate",
            ]
        }
        builder._validate_restart_wazuh_scope(
            {"wazuh_reconciliation_ids": list(journey_scope["wazuh_reconciliation_ids"])},
            journey_scope,
        )
        with self.assertRaisesRegex(ValueError, "does not match the journey"):
            builder._validate_restart_wazuh_scope(
                {"wazuh_reconciliation_ids": ["reconciliation-wazuh-admission"]},
                journey_scope,
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
        journey_record = {
            "alert_id": identifiers["aegisops_alert_id"],
            "finding_id": identifiers["finding_id"],
            "case_id": identifiers["case_id"],
            "denied_action_request_id": identifiers["denied_action_request_id"],
            "denied_approval_decision_id": identifiers[
                "denied_approval_decision_id"
            ],
            "action_request_id": identifiers["action_request_id"],
            "approval_decision_id": identifiers["approval_decision_id"],
            "execution_id": identifiers["shuffle_execution_id"],
            "action_execution_id": identifiers["action_execution_id"],
            "reconciliation_id": identifiers["reconciliation_id"],
            "wazuh_reconciliation_ids": [
                "phase67-admission-reconciliation"
            ],
        }
        report = {
            "records": {
                "alert": [{"alert_id": identifiers["aegisops_alert_id"]}],
                "case": [{"case_id": identifiers["case_id"]}],
                "action_request": [
                    {
                        "action_request_id": identifiers[
                            "denied_action_request_id"
                        ]
                    },
                    {"action_request_id": identifiers["action_request_id"]},
                ],
                "approval_decision": [
                    {
                        "approval_decision_id": identifiers[
                            "denied_approval_decision_id"
                        ]
                    },
                    {
                        "approval_decision_id": identifiers[
                            "approval_decision_id"
                        ]
                    },
                ],
                "action_execution": [
                    {
                        "action_execution_id": identifiers[
                            "action_execution_id"
                        ]
                    }
                ],
                "reconciliation": [
                    {
                        "reconciliation_id": "phase67-admission-reconciliation",
                        "alert_id": identifiers["aegisops_alert_id"],
                        "finding_id": identifiers["finding_id"],
                        "execution_run_id": None,
                        "linked_execution_run_ids": [],
                    },
                    {
                        "reconciliation_id": identifiers["reconciliation_id"],
                        "alert_id": identifiers["aegisops_alert_id"],
                        "finding_id": identifiers["finding_id"],
                        "execution_run_id": identifiers["shuffle_execution_id"],
                        "linked_execution_run_ids": [
                            identifiers["shuffle_execution_id"]
                        ],
                    },
                ],
            }
        }
        builder._validate_trial_report_scope(report, journey_record)

        previous_trial = deepcopy(report)
        previous_trial["records"]["action_request"].append(
            {"action_request_id": "phase67-action-from-previous-trial"}
        )
        with self.assertRaisesRegex(ValueError, "is not scoped to this trial"):
            builder._validate_trial_report_scope(previous_trial, journey_record)

        unrelated_reconciliation = deepcopy(report)
        unrelated_reconciliation["records"]["reconciliation"].append(
            {
                "reconciliation_id": "phase67-unexpected-linked-reconciliation",
                "alert_id": identifiers["aegisops_alert_id"],
                "finding_id": identifiers["finding_id"],
                "execution_run_id": identifiers["shuffle_execution_id"],
                "linked_execution_run_ids": [],
            }
        )
        with self.assertRaisesRegex(ValueError, "is not scoped to this trial"):
            builder._validate_trial_report_scope(
                unrelated_reconciliation,
                journey_record,
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
            'run_reviewed_lab_command "${LAB_DIR}/up.sh" full',
            'run_reviewed_lab_command "${LAB_DIR}/status.sh" full --write-evidence',
            'run_reviewed_lab_command "${LAB_DIR}/test-wazuh-intake.sh"',
            'run_reviewed_lab_command "${LAB_DIR}/down.sh"',
            'run_reviewed_lab_command "${LAB_DIR}/cleanup.sh"',
        )
        for reviewed_call in reviewed_lab_calls:
            with self.subTest(reviewed_call=reviewed_call):
                self.assertIn(reviewed_call, runner)
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
        self.assertIn('runtime_image_id: $runtime_image_id', runner)
        self.assertIn('SHUFFLE_WORKER_IMAGE=', runner)
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
        self.assertIn('no passing manifest was published', runner)
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
        cleanup = runner.index('"${LAB_DIR}/cleanup.sh"')
        final_snapshot_check = runner.index("assert_repository_snapshot", cleanup)
        evidence_build = runner.index('python3 "${builder}"', final_snapshot_check)
        self.assertLess(cleanup, final_snapshot_check)
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
        self.assertIn("status --porcelain=v1 --untracked-files=all", runner)
        self.assertNotIn("destroy-data.sh", runner)
        real_journey = (E2E_ROOT / "run_real_journey.py").read_text(
            encoding="utf-8"
        )
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
