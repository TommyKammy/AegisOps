#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


SCHEMA_VERSION = "phase67.4-real-service-e2e-evidence-v2"
SCHEMA_ID = (
    "https://aegisops.local/schemas/"
    "phase67-4-real-service-e2e-evidence-v2.json"
)
VERDICTS = {
    "integration_trial_passed_ga_not_accepted",
    "integration_trial_passed_with_owned_limitations",
    "integration_trial_blocked",
    "integration_trial_failed",
}
STEP_NAMES = (
    "capture_immutable_snapshot",
    "start_lab_and_record_health",
    "trigger_real_wazuh_detection",
    "admit_wazuh_alert",
    "promote_alert_to_case",
    "create_reviewed_action_request",
    "prove_denied_action_non_dispatch",
    "approve_and_dispatch_real_shuffle_action",
    "capture_authenticated_shuffle_receipt",
    "reconcile_from_aegisops_records",
    "export_redacted_aegisops_report",
    "replay_deliveries_for_idempotency",
    "run_negative_cases",
    "restart_and_verify_persistence",
    "publish_prerequisite_evaluation",
)
IDENTIFIER_KEYS = (
    "wazuh_manager_id",
    "wazuh_agent_id",
    "wazuh_rule_id",
    "native_wazuh_alert_id",
    "aegisops_alert_id",
    "finding_id",
    "case_id",
    "denied_action_request_id",
    "denied_approval_decision_id",
    "action_request_id",
    "approval_decision_id",
    "delegation_id",
    "shuffle_workflow_id",
    "shuffle_workflow_version",
    "shuffle_execution_id",
    "expected_receipt_id",
    "action_execution_id",
    "reconciliation_id",
    "report_id",
)
NEGATIVE_CASE_KEYS = (
    "invalid_credential",
    "proxy_bypass",
    "failed_execution",
    "malformed_receipt",
    "reconciliation_mismatch",
)
ARTIFACT_NAMES = {
    "preparation.json",
    "wazuh-manifest.json",
    "wazuh-output.txt",
    "journey.json",
    "restart.json",
    "snapshot.json",
    "images.json",
    "evaluation-record.json",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
TRIAL_ID = re.compile(r"^phase67-e2e-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}$")
SNAPSHOT_ID = re.compile(r"^phase67-snapshot-[0-9a-f]{16}$")
IMMUTABLE_IMAGE = re.compile(r"^.+@sha256:[0-9a-f]{64}$")
PLACEHOLDER = re.compile(
    r"(?:^|[-_.])(example|fixture|placeholder|synthetic|todo|tbd|unknown|"
    r"changeme|replace-me)(?:$|[-_.])",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+\S+", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@", re.IGNORECASE),
    re.compile(r"(?:^|[?&])(token|password|secret|api[_-]?key)=", re.IGNORECASE),
    re.compile(r"/(?:Users|home)/[^/\s]+/"),
    re.compile(
        r"(?:refs/(?:heads|remotes)/|origin/(?:main|master)(?:$|[/\s]))",
        re.IGNORECASE,
    ),
)


class EvidenceValidationError(ValueError):
    pass


def _reject_non_json_constant(value: str) -> object:
    raise EvidenceValidationError(f"non-JSON numeric constant {value!r}")


def _reject_duplicate_keys(
    pairs: Sequence[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceValidationError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_json(path: Path) -> object:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceValidationError(f"cannot read {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceValidationError(message)


def require_mapping(value: object, path: str) -> Mapping[str, object]:
    require(isinstance(value, Mapping), f"{path} must be an object")
    return value  # type: ignore[return-value]


def require_exact_keys(
    value: Mapping[str, object],
    *,
    required: Sequence[str],
    optional: Sequence[str] = (),
    path: str,
) -> None:
    required_keys = set(required)
    allowed_keys = required_keys | set(optional)
    missing = sorted(required_keys - set(value))
    unexpected = sorted(set(value) - allowed_keys)
    require(not missing, f"{path} is missing keys: {', '.join(missing)}")
    require(
        not unexpected,
        f"{path} has unexpected keys: {', '.join(unexpected)}",
    )


def require_string(value: object, path: str) -> str:
    require(isinstance(value, str) and value.strip() != "", f"{path} must be a non-empty string")
    return value.strip()  # type: ignore[union-attr]


def require_nullable_string(value: object, path: str) -> str | None:
    if value is None:
        return None
    return require_string(value, path)


def require_integer(value: object, path: str) -> int:
    require(
        isinstance(value, int) and not isinstance(value, bool),
        f"{path} must be an integer",
    )
    return value  # type: ignore[return-value]


def require_nullable_integer(value: object, path: str) -> int | None:
    if value is None:
        return None
    return require_integer(value, path)


def require_nullable_boolean(value: object, path: str) -> bool | None:
    require(value is None or isinstance(value, bool), f"{path} must be a boolean or null")
    return value  # type: ignore[return-value]


def require_boolean(value: object, path: str) -> bool:
    require(isinstance(value, bool), f"{path} must be a boolean")
    return value  # type: ignore[return-value]


def require_datetime(value: object, path: str) -> str:
    text = require_string(value, path)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EvidenceValidationError(f"{path} must be RFC3339 date-time") from exc
    require(parsed.tzinfo is not None, f"{path} must include a timezone")
    return text


def _scan_secret_values(value: object, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _scan_secret_values(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _scan_secret_values(item, f"{path}[{index}]")
        return
    if not isinstance(value, str):
        return
    for pattern in SECRET_VALUE_PATTERNS:
        require(
            pattern.search(value) is None,
            f"{path} contains a secret value or private host path",
        )


def _validate_schema_contract(schema: object) -> None:
    root = require_mapping(schema, "$schema")
    require(
        root.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
        "schema must declare JSON Schema Draft 2020-12",
    )
    require(root.get("$id") == SCHEMA_ID, "schema $id is not the reviewed identifier")
    properties = require_mapping(root.get("properties"), "$schema.properties")
    version = require_mapping(
        properties.get("schema_version"),
        "$schema.properties.schema_version",
    )
    require(version.get("const") == SCHEMA_VERSION, "schema version contract drifted")
    required = root.get("required")
    require(isinstance(required, list), "schema required list is missing")
    require(set(required) == set(properties), "schema top-level required fields drifted")
    require(root.get("additionalProperties") is False, "schema must reject extra fields")


def _validate_snapshot(value: object) -> Mapping[str, object]:
    snapshot = require_mapping(value, "$.snapshot")
    require_exact_keys(
        snapshot,
        required=(
            "snapshot_id",
            "repository_revision",
            "compose_sha256",
            "evidence_schema_sha256",
            "runtime_artifact_sha256",
            "host_architecture",
            "docker_context",
            "colima_profile",
            "selected_profile",
            "images",
        ),
        path="$.snapshot",
    )
    require(SNAPSHOT_ID.fullmatch(require_string(snapshot["snapshot_id"], "$.snapshot.snapshot_id")) is not None, "$.snapshot.snapshot_id is invalid")
    require(REVISION.fullmatch(require_string(snapshot["repository_revision"], "$.snapshot.repository_revision")) is not None, "$.snapshot.repository_revision must be a full commit SHA")
    for key in ("compose_sha256", "evidence_schema_sha256", "runtime_artifact_sha256"):
        require(SHA256.fullmatch(require_string(snapshot[key], f"$.snapshot.{key}")) is not None, f"$.snapshot.{key} must be SHA-256")
    require(snapshot["host_architecture"] in ("arm64", "aarch64"), "$.snapshot.host_architecture must be ARM64")
    require_string(snapshot["docker_context"], "$.snapshot.docker_context")
    require_string(snapshot["colima_profile"], "$.snapshot.colima_profile")
    require(snapshot["selected_profile"] == "full", "$.snapshot.selected_profile must be full")
    images = snapshot["images"]
    require(isinstance(images, list) and images, "$.snapshot.images must be non-empty")
    services: set[str] = set()
    for index, item in enumerate(images):
        image = require_mapping(item, f"$.snapshot.images[{index}]")
        require_exact_keys(image, required=("service", "immutable_reference"), path=f"$.snapshot.images[{index}]")
        service = require_string(image["service"], f"$.snapshot.images[{index}].service")
        require(service not in services, "$.snapshot.images contains duplicate services")
        services.add(service)
        reference = require_string(image["immutable_reference"], f"$.snapshot.images[{index}].immutable_reference")
        require(IMMUTABLE_IMAGE.fullmatch(reference) is not None, f"$.snapshot.images[{index}] is not digest-pinned")
    require(
        "shuffle-action-image" in services,
        "$.snapshot.images omits the dynamic Shuffle action image",
    )
    return snapshot


def _validate_steps(value: object, snapshot_id: str, verdict: str) -> None:
    require(isinstance(value, list) and len(value) == len(STEP_NAMES), "$.steps must contain exactly 15 steps")
    statuses: list[str] = []
    for index, expected_name in enumerate(STEP_NAMES):
        item = require_mapping(value[index], f"$.steps[{index}]")
        require_exact_keys(
            item,
            required=("step", "name", "status", "snapshot_id", "observed_at", "evidence_refs"),
            optional=("blocker",),
            path=f"$.steps[{index}]",
        )
        require(require_integer(item["step"], f"$.steps[{index}].step") == index + 1, "$.steps must be ordered 1 through 15")
        require(item["name"] == expected_name, f"$.steps[{index}].name is not the reviewed journey step")
        status = require_string(item["status"], f"$.steps[{index}].status")
        require(status in {"passed", "failed", "blocked", "not_run"}, f"$.steps[{index}].status is invalid")
        statuses.append(status)
        require(item["snapshot_id"] == snapshot_id, f"$.steps[{index}] uses a mixed snapshot")
        require_datetime(item["observed_at"], f"$.steps[{index}].observed_at")
        refs = item["evidence_refs"]
        require(isinstance(refs, list) and refs, f"$.steps[{index}].evidence_refs must be non-empty")
        for ref_index, evidence_ref in enumerate(refs):
            require_string(evidence_ref, f"$.steps[{index}].evidence_refs[{ref_index}]")
        blocker = item.get("blocker")
        if status in {"blocked", "failed"}:
            blocker_mapping = require_mapping(blocker, f"$.steps[{index}].blocker")
            require_exact_keys(blocker_mapping, required=("owner", "reason"), path=f"$.steps[{index}].blocker")
            require_string(blocker_mapping["owner"], f"$.steps[{index}].blocker.owner")
            require_string(blocker_mapping["reason"], f"$.steps[{index}].blocker.reason")
        else:
            require(blocker is None, f"$.steps[{index}].blocker is only allowed for failed or blocked steps")
    if verdict.startswith("integration_trial_passed"):
        require(all(status == "passed" for status in statuses), "a passed verdict requires all journey steps to pass")
    elif verdict == "integration_trial_blocked":
        require(statuses.count("blocked") == 1, "a blocked verdict requires exactly one blocked step")
        blocked_index = statuses.index("blocked")
        require(all(status == "passed" for status in statuses[:blocked_index]), "steps before a blocker must pass")
        require(all(status == "not_run" for status in statuses[blocked_index + 1 :]), "steps after a blocker must be not_run")
    elif verdict == "integration_trial_failed":
        require(statuses.count("failed") >= 1, "a failed verdict requires a failed step")


def validate_manifest(manifest: object, schema: object) -> None:
    _validate_schema_contract(schema)
    root = require_mapping(manifest, "$")
    required = (
        "schema_version",
        "captured_at",
        "source_mode",
        "trial_run_id",
        "snapshot",
        "steps",
        "identifiers",
        "human_control",
        "idempotency",
        "negative_cases",
        "restart",
        "report",
        "evaluation",
        "artifacts",
        "cleanup",
        "authority_posture",
        "verdict",
        "limitations",
    )
    require_exact_keys(root, required=required, path="$")
    require(root["schema_version"] == SCHEMA_VERSION, "$.schema_version is invalid")
    require_datetime(root["captured_at"], "$.captured_at")
    require(root["source_mode"] == "real_services", "$.source_mode must be real_services")
    require(TRIAL_ID.fullmatch(require_string(root["trial_run_id"], "$.trial_run_id")) is not None, "$.trial_run_id is invalid")
    verdict = require_string(root["verdict"], "$.verdict")
    require(verdict in VERDICTS, "$.verdict is not in the reviewed vocabulary")
    snapshot = _validate_snapshot(root["snapshot"])
    snapshot_id = require_string(snapshot["snapshot_id"], "$.snapshot.snapshot_id")
    _validate_steps(root["steps"], snapshot_id, verdict)

    identifiers = require_mapping(root["identifiers"], "$.identifiers")
    require_exact_keys(identifiers, required=IDENTIFIER_KEYS, path="$.identifiers")
    normalized_ids = {
        key: require_nullable_string(identifiers[key], f"$.identifiers.{key}")
        for key in IDENTIFIER_KEYS
    }
    if verdict.startswith("integration_trial_passed"):
        require(all(normalized_ids.values()), "a passed verdict requires every real journey identifier")
    for key, value in normalized_ids.items():
        if value is not None:
            require(PLACEHOLDER.search(value) is None, f"$.identifiers.{key} looks synthetic or placeholder-derived")
    execution_id = normalized_ids["shuffle_execution_id"]
    if execution_id is not None:
        require(not execution_id.startswith("shuffle-run-"), "synthetic Shuffle execution ID cannot be live evidence")
    if normalized_ids["native_wazuh_alert_id"] and normalized_ids["aegisops_alert_id"]:
        require(normalized_ids["native_wazuh_alert_id"] != normalized_ids["aegisops_alert_id"], "native Wazuh and AegisOps alert IDs must remain distinct")

    human = require_mapping(root["human_control"], "$.human_control")
    require_exact_keys(human, required=("requester_identity", "approver_identity", "authenticated_approver_identity", "denied_action_execution_count", "denied_dispatch_rejected", "approval_source", "approval_method", "approval_challenge_sha256", "approval_confirmed_at"), path="$.human_control")
    requester = require_nullable_string(human["requester_identity"], "$.human_control.requester_identity")
    approver = require_nullable_string(human["approver_identity"], "$.human_control.approver_identity")
    authenticated_approver = require_nullable_string(human["authenticated_approver_identity"], "$.human_control.authenticated_approver_identity")
    denied_count = require_nullable_integer(human["denied_action_execution_count"], "$.human_control.denied_action_execution_count")
    denied_rejected = require_nullable_boolean(human["denied_dispatch_rejected"], "$.human_control.denied_dispatch_rejected")
    approval_source = require_nullable_string(human["approval_source"], "$.human_control.approval_source")
    approval_method = require_nullable_string(human["approval_method"], "$.human_control.approval_method")
    approval_challenge_sha256 = require_nullable_string(human["approval_challenge_sha256"], "$.human_control.approval_challenge_sha256")
    approval_confirmed_at = human["approval_confirmed_at"]
    if verdict.startswith("integration_trial_passed"):
        require(requester != approver, "requester and approver must be distinct")
        require(approver == authenticated_approver, "approver must match the authenticated local operator")
        require(denied_count == 0 and denied_rejected is True, "denied action must produce no dispatch")
        require(approval_source == "interactive_local_operator_ceremony", "approval must come from the interactive ceremony")
        require(approval_method in {"macos_operator_dialog", "tty_challenge"}, "approval method is not independently interactive")
        require(approval_challenge_sha256 is not None and SHA256.fullmatch(approval_challenge_sha256) is not None, "approval challenge digest must be SHA-256")
        require_datetime(approval_confirmed_at, "$.human_control.approval_confirmed_at")
    else:
        require(approval_confirmed_at is None or isinstance(approval_confirmed_at, str), "$.human_control.approval_confirmed_at must be a date-time or null")

    idempotency = require_mapping(root["idempotency"], "$.idempotency")
    require_exact_keys(idempotency, required=("wazuh_first_disposition", "wazuh_duplicate_disposition", "wazuh_alert_identity_preserved", "shuffle_execution_count", "receipt_replay_reconciliation_id", "receipt_identity_preserved"), path="$.idempotency")
    first_disposition = require_nullable_string(idempotency["wazuh_first_disposition"], "$.idempotency.wazuh_first_disposition")
    duplicate_disposition = require_nullable_string(idempotency["wazuh_duplicate_disposition"], "$.idempotency.wazuh_duplicate_disposition")
    wazuh_preserved = require_nullable_boolean(idempotency["wazuh_alert_identity_preserved"], "$.idempotency.wazuh_alert_identity_preserved")
    execution_count = require_nullable_integer(idempotency["shuffle_execution_count"], "$.idempotency.shuffle_execution_count")
    replay_id = require_nullable_string(idempotency["receipt_replay_reconciliation_id"], "$.idempotency.receipt_replay_reconciliation_id")
    receipt_preserved = require_nullable_boolean(idempotency["receipt_identity_preserved"], "$.idempotency.receipt_identity_preserved")
    if verdict.startswith("integration_trial_passed"):
        require(first_disposition == "created" and duplicate_disposition == "deduplicated" and wazuh_preserved is True, "Wazuh replay must preserve one admitted alert")
        require(execution_count == 1 and receipt_preserved is True, "Shuffle replay must preserve one execution and receipt")
        require(replay_id == normalized_ids["reconciliation_id"], "receipt replay must reuse the reconciliation ID")

    negative_cases = require_mapping(root["negative_cases"], "$.negative_cases")
    require_exact_keys(negative_cases, required=NEGATIVE_CASE_KEYS, path="$.negative_cases")
    for key in NEGATIVE_CASE_KEYS:
        case = require_mapping(negative_cases[key], f"$.negative_cases.{key}")
        require_exact_keys(case, required=("status", "authority_before", "authority_after", "authority_delta", "measurement_source", "evidence_ref"), path=f"$.negative_cases.{key}")
        status = require_nullable_string(case["status"], f"$.negative_cases.{key}.status")
        before = require_nullable_integer(case["authority_before"], f"$.negative_cases.{key}.authority_before")
        after = require_nullable_integer(case["authority_after"], f"$.negative_cases.{key}.authority_after")
        delta = require_nullable_integer(case["authority_delta"], f"$.negative_cases.{key}.authority_delta")
        measurement_source = require_nullable_string(case["measurement_source"], f"$.negative_cases.{key}.measurement_source")
        evidence_ref = require_nullable_string(case["evidence_ref"], f"$.negative_cases.{key}.evidence_ref")
        if verdict.startswith("integration_trial_passed"):
            require(status in {"rejected", "contained"}, f"$.negative_cases.{key} did not reject or contain the probe")
            require(before is not None and before >= 0 and after is not None and after >= 0, f"$.negative_cases.{key} lacks authoritative before/after counts")
            require(delta == after - before, f"$.negative_cases.{key} authority delta is not measured")
            expected_source = (
                "aegisops_authoritative_alert_count"
                if key in {"invalid_credential", "proxy_bypass"}
                else "aegisops_authoritative_record_count"
            )
            require(measurement_source == expected_source, f"$.negative_cases.{key} did not use the real AegisOps measurement source")
            if key in {"invalid_credential", "proxy_bypass", "malformed_receipt"}:
                require(delta == 0, f"$.negative_cases.{key} unexpectedly persisted authoritative state")
            require(evidence_ref is not None, f"$.negative_cases.{key} lacks evidence")

    restart = require_mapping(root["restart"], "$.restart")
    require_exact_keys(restart, required=("performed", "records_persisted", "checked_identifiers"), path="$.restart")
    restart_performed = require_nullable_boolean(restart["performed"], "$.restart.performed")
    records_persisted = require_nullable_boolean(restart["records_persisted"], "$.restart.records_persisted")
    checked = restart["checked_identifiers"]
    require(isinstance(checked, list), "$.restart.checked_identifiers must be an array")
    if verdict.startswith("integration_trial_passed"):
        require(restart_performed is True and records_persisted is True, "passed trial requires restart persistence proof")
        require(set(checked) >= {"aegisops_alert_id", "case_id", "action_request_id", "action_execution_id", "reconciliation_id"}, "restart proof omits authoritative identifiers")

    report = require_mapping(root["report"], "$.report")
    require_exact_keys(report, required=("report_id", "sha256", "source_of_truth", "redacted"), path="$.report")
    report_id = require_nullable_string(report["report_id"], "$.report.report_id")
    report_sha = require_nullable_string(report["sha256"], "$.report.sha256")
    report_source = require_nullable_string(report["source_of_truth"], "$.report.source_of_truth")
    report_redacted = require_nullable_boolean(report["redacted"], "$.report.redacted")
    if verdict.startswith("integration_trial_passed"):
        require(report_id == normalized_ids["report_id"], "report ID is not bound to journey identifiers")
        require(report_sha is not None and SHA256.fullmatch(report_sha) is not None, "report digest must be SHA-256")
        require(report_source == "aegisops_authoritative_records" and report_redacted is True, "report must be redacted and AegisOps-derived")

    evaluation = require_mapping(root["evaluation"], "$.evaluation")
    require_exact_keys(evaluation, required=("trial_run_id", "snapshot_id", "repository_revision", "evaluated_at", "verdict", "ga_accepted", "sha256"), path="$.evaluation")
    evaluation_trial = require_nullable_string(evaluation["trial_run_id"], "$.evaluation.trial_run_id")
    evaluation_snapshot = require_nullable_string(evaluation["snapshot_id"], "$.evaluation.snapshot_id")
    evaluation_revision = require_nullable_string(evaluation["repository_revision"], "$.evaluation.repository_revision")
    evaluation_verdict = require_nullable_string(evaluation["verdict"], "$.evaluation.verdict")
    evaluation_ga = require_nullable_boolean(evaluation["ga_accepted"], "$.evaluation.ga_accepted")
    evaluation_sha = require_nullable_string(evaluation["sha256"], "$.evaluation.sha256")
    if verdict.startswith("integration_trial_passed"):
        require(evaluation_trial == root["trial_run_id"], "evaluation is not bound to this trial")
        require(evaluation_snapshot == snapshot_id, "evaluation is not bound to this snapshot")
        require(evaluation_revision == snapshot["repository_revision"], "evaluation is not bound to this repository revision")
        require_datetime(evaluation["evaluated_at"], "$.evaluation.evaluated_at")
        require(evaluation_verdict == verdict, "evaluation verdict does not match the manifest")
        require(evaluation_ga is False, "Phase 67 evidence cannot accept GA")
        require(evaluation_sha is not None and SHA256.fullmatch(evaluation_sha) is not None, "evaluation record digest must be SHA-256")

    artifacts = require_mapping(root["artifacts"], "$.artifacts")
    require_exact_keys(artifacts, required=("retention", "directory_name", "files"), path="$.artifacts")
    retention = require_nullable_string(artifacts["retention"], "$.artifacts.retention")
    directory_name = require_nullable_string(artifacts["directory_name"], "$.artifacts.directory_name")
    files = artifacts["files"]
    require(isinstance(files, list), "$.artifacts.files must be an array")
    artifact_names: set[str] = set()
    for index, item in enumerate(files):
        artifact = require_mapping(item, f"$.artifacts.files[{index}]")
        require_exact_keys(artifact, required=("name", "sha256"), path=f"$.artifacts.files[{index}]")
        name = require_string(artifact["name"], f"$.artifacts.files[{index}].name")
        require(name not in artifact_names, "$.artifacts.files contains duplicate names")
        artifact_names.add(name)
        digest = require_string(artifact["sha256"], f"$.artifacts.files[{index}].sha256")
        require(SHA256.fullmatch(digest) is not None, f"$.artifacts.files[{index}].sha256 must be SHA-256")
    if verdict.startswith("integration_trial_passed"):
        require(retention == "local_mode_0600", "passed trial raw artifacts must be retained in local 0600 mode")
        require(directory_name == f"{root['trial_run_id']}-artifacts", "artifact directory is not bound to this trial")
        require(artifact_names == ARTIFACT_NAMES, "raw artifact inventory is incomplete")

    cleanup = require_mapping(root["cleanup"], "$.cleanup")
    require_exact_keys(cleanup, required=("mode", "containers_stopped", "data_preserved"), path="$.cleanup")
    cleanup_mode = require_nullable_string(cleanup["mode"], "$.cleanup.mode")
    containers_stopped = require_nullable_boolean(cleanup["containers_stopped"], "$.cleanup.containers_stopped")
    data_preserved = require_nullable_boolean(cleanup["data_preserved"], "$.cleanup.data_preserved")
    if verdict.startswith("integration_trial_passed"):
        require(cleanup_mode == "non_destructive" and containers_stopped is True and data_preserved is True, "cleanup must stop services without deleting evidence or volumes")

    require(root["authority_posture"] == "aegisops_records_remain_authoritative", "$.authority_posture is invalid")
    limitations = root["limitations"]
    require(isinstance(limitations, list) and limitations, "$.limitations must be non-empty")
    seen_limitations: set[str] = set()
    for index, item in enumerate(limitations):
        limitation = require_mapping(item, f"$.limitations[{index}]")
        require_exact_keys(limitation, required=("limitation_id", "owner", "status", "description"), optional=("follow_up_issue",), path=f"$.limitations[{index}]")
        limitation_id = require_string(limitation["limitation_id"], f"$.limitations[{index}].limitation_id")
        require(limitation_id not in seen_limitations, "duplicate limitation_id")
        seen_limitations.add(limitation_id)
        require_string(limitation["owner"], f"$.limitations[{index}].owner")
        require(limitation["status"] in {"accepted", "follow_up_required", "blocking"}, f"$.limitations[{index}].status is invalid")
        require_string(limitation["description"], f"$.limitations[{index}].description")
        follow_up = limitation.get("follow_up_issue")
        require(follow_up is None or (isinstance(follow_up, str) and re.fullmatch(r"#[0-9]+", follow_up) is not None), f"$.limitations[{index}].follow_up_issue must be an issue reference or null")
    _scan_secret_values(root)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 2:
        print("usage: validate_evidence_manifest.py SCHEMA MANIFEST", file=sys.stderr)
        return 2
    try:
        schema = load_json(Path(arguments[0]))
        manifest = load_json(Path(arguments[1]))
        validate_manifest(manifest, schema)
    except EvidenceValidationError as exc:
        print(f"Phase 67.4 evidence validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
