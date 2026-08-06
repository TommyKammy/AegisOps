#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime
import hashlib
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
PASSED_VERDICT = "integration_trial_passed_with_owned_limitations"
VERDICTS = {
    PASSED_VERDICT,
    "integration_trial_blocked",
    "integration_trial_failed",
}
OWNED_LIMITATION_STATUSES = {
    "phase67-single-host": "accepted",
    "phase67-bounded-connectors": "follow_up_required",
    "phase67-ga-gates-open": "blocking",
}
SUPPORTED_HOST_ARCHITECTURES = frozenset(
    {"arm64", "aarch64", "amd64", "x86_64"}
)
LEGACY_APPROVAL_BLOCKER_STATUSES = {
    "phase67-independent-human-approval-required": "blocking",
}
REVIEWED_SHUFFLE_WORKFLOW_VERSION = (
    "notify_identity_owner-v1-reviewed-2026-05-03"
)
REVIEWED_WAZUH_RULE_ID = "5710"
STEP_NAMES = (
    "capture_immutable_snapshot",
    "record_lab_health_after_snapshot",
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
    "record_prerequisite_evaluation",
)
LEGACY_BLOCKED_STEP_NAMES = (
    STEP_NAMES[0],
    "start_lab_and_record_health",
    *STEP_NAMES[2:-1],
    "publish_prerequisite_evaluation",
)
STEP_EVIDENCE_REFS = (
    (
        "snapshot",
        "artifact:compose-config.sha256",
        "artifact:workflow-snapshot.json",
    ),
    ("artifact:initial-status.txt",),
    (
        "wazuh-manifest:native_wazuh_alert_id",
        "artifact:wazuh-output.txt",
    ),
    (
        "wazuh-manifest:aegisops_alert_id",
        "artifact:wazuh-output.txt",
    ),
    ("journey:case_id",),
    ("journey:action_request_id",),
    ("journey:denied_dispatch",),
    (
        "journey:approval_challenge_sha256",
        "artifact:workflow-pre-dispatch.json",
        "journey:execution_id",
    ),
    ("journey:expected_receipt_id",),
    ("journey:reconciliation_id",),
    ("report:sha256",),
    ("journey:replay_reconciliation_id",),
    ("journey:measured_negative_probes",),
    ("restart:checked_identifiers", "artifact:restart-status.txt"),
    ("evaluation-record:sha256",),
)
RESTART_REQUIRED_IDENTIFIER_FIELDS = (
    "aegisops_alert_id",
    "case_id",
    "denied_action_request_id",
    "denied_approval_decision_id",
    "action_request_id",
    "approval_decision_id",
    "action_execution_id",
    "reconciliation_id",
)
RESTART_CHECKED_IDENTIFIER_FIELDS = (
    *RESTART_REQUIRED_IDENTIFIER_FIELDS,
    "wazuh_reconciliation_ids",
)
# The committed approval-blocked packet predates retained status/workflow captures.
# Keep its concrete references reviewable without treating them as the current contract.
LEGACY_BLOCKED_STEP_EVIDENCE_REFS = (
    ("snapshot",),
    ("lab-status:full",),
    ("wazuh-manifest:native_wazuh_alert_id",),
    ("wazuh-manifest:aegisops_alert_id",),
    ("preparation:case_id",),
    ("preparation:action_request_id",),
    ("preparation:denied_dispatch",),
    ("preparation:approval_challenge_sha256",),
    ("not-run:approval-blocked",),
    ("not-run:approval-blocked",),
    ("not-run:approval-blocked",),
    ("wazuh-manifest:duplicate_delivery",),
    ("wazuh-command:negative-boundaries",),
    ("not-run:approval-blocked",),
    ("evaluation-record:sha256",),
)
LEGACY_BLOCKED_TRIAL = (
    "phase67-e2e-20260801T135206Z-26c533b6ca31",
    "2473b66f5702a38f1d4630c990509bf812a6af7a",
)
LEGACY_BLOCKED_SNAPSHOT_ID = "phase67-snapshot-0661c0413ecdd062"
LEGACY_BLOCKED_IMAGE_COUNT = 11
LEGACY_BLOCKED_MANIFEST_SHA256 = (
    "69024ef973dc820ef797bb6b5dfad66ff322a9f11673951f6a53ff0a168d09e8"
)
REVIEWED_IMMUTABLE_IMAGE_REFERENCES = {
    "postgres": (
        "postgres:16.4@sha256:"
        "e62fbf9d3e2b49816a32c400ed2dba83e3b361e6833e624024309c35d334b412"
    ),
    "proxy": (
        "nginx:1.27.0@sha256:"
        "98f8ec75657d21b924fe4f69b6b9bff2f6550ea48838af479d8894a852000e40"
    ),
    "wazuh-indexer": (
        "wazuh/wazuh-indexer:4.14.6@sha256:"
        "27261711c6479e2e503171918aae9a23b3fc4dcfc2d28d204e75985c1e0fb4c5"
    ),
    "wazuh-security-bootstrap": (
        "wazuh/wazuh-indexer:4.14.6@sha256:"
        "27261711c6479e2e503171918aae9a23b3fc4dcfc2d28d204e75985c1e0fb4c5"
    ),
    "wazuh-manager": (
        "wazuh/wazuh-manager:4.14.6@sha256:"
        "4683ddc88474c79ae6171d9132adbd45fda86bdfb22ad0d8ddee167654c9e841"
    ),
    "wazuh-dashboard": (
        "wazuh/wazuh-dashboard:4.14.6@sha256:"
        "16aa978eaa6355fe3965e310ef8eaaed4df6f701dcf5885ebd0783fcd5ee6f16"
    ),
    "shuffle-opensearch": (
        "opensearchproject/opensearch:3.2.0@sha256:"
        "23297b8d8545e129dd58c254ed08d786dc552410ba772983ad2af31048d2f04b"
    ),
    "shuffle-backend": (
        "ghcr.io/shuffle/shuffle-backend:2.2.1@sha256:"
        "0cc1775e48b7d94b7f16d0be713aa274ced52be24ad521beaaf58c67023fd2e5"
    ),
    "shuffle-orborus": (
        "ghcr.io/shuffle/shuffle-orborus:2.2.1@sha256:"
        "3519810b3ca4fe568acefdf15ce6f2deba0ae6f0ff6b84412354d59d663dff31"
    ),
    "shuffle-frontend": (
        "ghcr.io/shuffle/shuffle-frontend:2.2.1@sha256:"
        "0561dd421382f70d15cada11a324b40762f0930522fcc1b51edcce9c87cc0f00"
    ),
    "shuffle-action-image": (
        "frikky/shuffle@sha256:"
        "fd5391cb0af02e92be194a8c4fe67a4221d5fb26f279eaa3f00676b201bf6cb8"
    ),
    "shuffle-worker-image": (
        "ghcr.io/shuffle/shuffle-worker:2.2.1@sha256:"
        "9541c1fef2bc8511727610b565adbd0f7c817c53afee2dd9fef6aad8a971ffb1"
    ),
}
EXPECTED_FULL_PROFILE_IMAGE_SERVICES = frozenset(
    {"control-plane", *REVIEWED_IMMUTABLE_IMAGE_REFERENCES}
)
LEGACY_BLOCKED_IMAGE_SERVICES = (
    EXPECTED_FULL_PROFILE_IMAGE_SERVICES
    - {"wazuh-security-bootstrap", "shuffle-worker-image"}
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
IDENTIFIER_PRODUCING_STEPS = {
    "wazuh_manager_id": "trigger_real_wazuh_detection",
    "wazuh_agent_id": "trigger_real_wazuh_detection",
    "wazuh_rule_id": "trigger_real_wazuh_detection",
    "native_wazuh_alert_id": "trigger_real_wazuh_detection",
    "aegisops_alert_id": "admit_wazuh_alert",
    "finding_id": "admit_wazuh_alert",
    "case_id": "promote_alert_to_case",
    "action_request_id": "create_reviewed_action_request",
    "denied_action_request_id": "prove_denied_action_non_dispatch",
    "denied_approval_decision_id": "prove_denied_action_non_dispatch",
    "approval_decision_id": "approve_and_dispatch_real_shuffle_action",
    "delegation_id": "approve_and_dispatch_real_shuffle_action",
    "shuffle_workflow_id": "approve_and_dispatch_real_shuffle_action",
    "shuffle_workflow_version": "approve_and_dispatch_real_shuffle_action",
    "shuffle_execution_id": "approve_and_dispatch_real_shuffle_action",
    "expected_receipt_id": "approve_and_dispatch_real_shuffle_action",
    "action_execution_id": "approve_and_dispatch_real_shuffle_action",
    "reconciliation_id": "reconcile_from_aegisops_records",
    "report_id": "export_redacted_aegisops_report",
}
NEGATIVE_CASE_KEYS = (
    "invalid_credential",
    "proxy_bypass",
    "failed_execution",
    "malformed_receipt",
    "reconciliation_mismatch",
)
NEGATIVE_CASE_PRODUCING_STEPS = {
    "invalid_credential": "trigger_real_wazuh_detection",
    "proxy_bypass": "trigger_real_wazuh_detection",
    "failed_execution": "run_negative_cases",
    "malformed_receipt": "run_negative_cases",
    "reconciliation_mismatch": "run_negative_cases",
}
ARTIFACT_NAMES = {
    "compose-config.sha256",
    "preparation.json",
    "wazuh-manifest.json",
    "wazuh-output.txt",
    "journey.json",
    "restart.json",
    "snapshot.json",
    "images.json",
    "evaluation-record.json",
    "step-observations.jsonl",
    "startup-status.txt",
    "initial-status.txt",
    "restart-status.txt",
    "workflow-snapshot.json",
    "workflow-pre-dispatch.json",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
TRIAL_ID = re.compile(r"^phase67-e2e-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}$")
SNAPSHOT_ID = re.compile(r"^phase67-snapshot-[0-9a-f]{16}$")
IMMUTABLE_IMAGE = re.compile(r"^.+@sha256:[0-9a-f]{64}$")
RUNTIME_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
WORKFLOW_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
CANONICAL_UUID_PATTERN = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
CANONICAL_UUID = re.compile(CANONICAL_UUID_PATTERN)
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


def _read_json_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise EvidenceValidationError(f"cannot read {path}: {exc}") from exc


def _parse_json_bytes(payload: bytes, path: Path) -> object:
    try:
        return json.loads(
            payload,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceValidationError(f"cannot read {path}: {exc}") from exc


def load_json(path: Path) -> object:
    return _parse_json_bytes(_read_json_bytes(path), path)


def load_json_with_sha256(path: Path) -> tuple[object, str]:
    payload = _read_json_bytes(path)
    return _parse_json_bytes(payload, path), hashlib.sha256(payload).hexdigest()


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


def require_datetime(value: object, path: str) -> str:
    text = require_string(value, path)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EvidenceValidationError(f"{path} must be RFC3339 date-time") from exc
    require(parsed.tzinfo is not None, f"{path} must include a timezone")
    return text


def _datetime_value(value: object, path: str) -> datetime:
    text = require_datetime(value, path)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    return datetime.fromisoformat(normalized)


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


def _schema_image_inventory_profile(item_count: int) -> dict[str, object]:
    return {
        "type": "object",
        "required": ["snapshot"],
        "properties": {
            "snapshot": {
                "type": "object",
                "required": ["images"],
                "properties": {
                    "images": {
                        "type": "array",
                        "minItems": item_count,
                        "maxItems": item_count,
                    }
                },
            }
        },
    }


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
    verdict_schema = require_mapping(
        properties.get("verdict"),
        "$schema.properties.verdict",
    )
    verdict_enum = verdict_schema.get("enum")
    require(
        isinstance(verdict_enum, list) and set(verdict_enum) == VERDICTS,
        "schema verdict vocabulary drifted",
    )
    identifiers = require_mapping(
        properties.get("identifiers"),
        "$schema.properties.identifiers",
    )
    identifier_properties = require_mapping(
        identifiers.get("properties"),
        "$schema.properties.identifiers.properties",
    )
    shuffle_execution_id = require_mapping(
        identifier_properties.get("shuffle_execution_id"),
        "$schema.properties.identifiers.properties.shuffle_execution_id",
    )
    require(
        shuffle_execution_id.get("pattern") == CANONICAL_UUID_PATTERN,
        "schema Shuffle execution ID contract drifted",
    )
    wazuh_rule_id = require_mapping(
        identifier_properties.get("wazuh_rule_id"),
        "$schema.properties.identifiers.properties.wazuh_rule_id",
    )
    require(
        wazuh_rule_id.get("enum") == [REVIEWED_WAZUH_RULE_ID, None],
        "schema Wazuh rule ID contract drifted",
    )
    snapshot = require_mapping(properties.get("snapshot"), "$schema.properties.snapshot")
    snapshot_properties = require_mapping(
        snapshot.get("properties"),
        "$schema.properties.snapshot.properties",
    )
    images = require_mapping(
        snapshot_properties.get("images"),
        "$schema.properties.snapshot.properties.images",
    )
    host_architecture = require_mapping(
        snapshot_properties.get("host_architecture"),
        "$schema.properties.snapshot.properties.host_architecture",
    )
    host_architecture_enum = host_architecture.get("enum")
    require(
        isinstance(host_architecture_enum, list)
        and set(host_architecture_enum) == SUPPORTED_HOST_ARCHITECTURES,
        "schema host architecture contract drifted",
    )
    require(
        "minItems" not in images and "maxItems" not in images,
        "schema base image inventory must defer to reviewed profiles",
    )
    definitions = require_mapping(root.get("$defs"), "$schema.$defs")
    expected_legacy_identity = {
        "type": "object",
        "required": ["trial_run_id", "snapshot", "verdict"],
        "properties": {
            "trial_run_id": {"const": LEGACY_BLOCKED_TRIAL[0]},
            "snapshot": {
                "type": "object",
                "required": ["snapshot_id", "repository_revision"],
                "properties": {
                    "snapshot_id": {"const": LEGACY_BLOCKED_SNAPSHOT_ID},
                    "repository_revision": {"const": LEGACY_BLOCKED_TRIAL[1]},
                },
            },
            "verdict": {"const": "integration_trial_blocked"},
        },
    }
    require(
        definitions.get("legacy_blocked_identity") == expected_legacy_identity,
        "schema historical packet identity drifted",
    )
    require(
        root.get("allOf")
        == [
            {
                "if": {"$ref": "#/$defs/legacy_blocked_identity"},
                "then": {"$ref": "#/$defs/legacy_blocked_image_inventory"},
                "else": {"$ref": "#/$defs/current_image_inventory"},
            }
        ],
        "schema image inventory profile selection drifted",
    )
    require(
        definitions.get("legacy_blocked_image_inventory")
        == _schema_image_inventory_profile(LEGACY_BLOCKED_IMAGE_COUNT),
        "schema historical image inventory contract drifted",
    )
    require(
        definitions.get("current_image_inventory")
        == _schema_image_inventory_profile(
            len(EXPECTED_FULL_PROFILE_IMAGE_SERVICES)
        ),
        "schema current image inventory contract drifted",
    )


def _snapshot_identifier(
    trial_run_id: str,
    snapshot: Mapping[str, object],
) -> str:
    payload = {
        "trial_run_id": trial_run_id,
        **{
            key: value
            for key, value in snapshot.items()
            if key != "snapshot_id"
        },
    }
    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return "phase67-snapshot-" + hashlib.sha256(encoded).hexdigest()[:16]


def _manifest_sha256(value: Mapping[str, object]) -> str:
    encoded = json.dumps(
        value,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _is_legacy_blocked_manifest(value: Mapping[str, object]) -> bool:
    snapshot = value.get("snapshot")
    return (
        _manifest_sha256(value) == LEGACY_BLOCKED_MANIFEST_SHA256
        and value.get("verdict") == "integration_trial_blocked"
        and value.get("trial_run_id") == LEGACY_BLOCKED_TRIAL[0]
        and isinstance(snapshot, Mapping)
        and snapshot.get("snapshot_id") == LEGACY_BLOCKED_SNAPSHOT_ID
        and snapshot.get("repository_revision") == LEGACY_BLOCKED_TRIAL[1]
    )


def _validate_runtime_images(
    value: object,
    *,
    allow_legacy_blocked_inventory: bool = False,
) -> None:
    require(isinstance(value, list) and value, "$.snapshot.images must be non-empty")
    services: set[str] = set()
    image_references: dict[str, str] = {}
    runtime_image_ids: dict[str, str] = {}
    for index, item in enumerate(value):
        image = require_mapping(item, f"$.snapshot.images[{index}]")
        require_exact_keys(
            image,
            required=("service", "immutable_reference"),
            optional=("runtime_image_id",),
            path=f"$.snapshot.images[{index}]",
        )
        service = require_string(image["service"], f"$.snapshot.images[{index}].service")
        require(service not in services, "$.snapshot.images contains duplicate services")
        services.add(service)
        reference = require_string(image["immutable_reference"], f"$.snapshot.images[{index}].immutable_reference")
        require(IMMUTABLE_IMAGE.fullmatch(reference) is not None, f"$.snapshot.images[{index}] is not digest-pinned")
        image_references[service] = reference
        runtime_image_id = image.get("runtime_image_id")
        if runtime_image_id is not None:
            runtime_image_id = require_string(
                runtime_image_id,
                f"$.snapshot.images[{index}].runtime_image_id",
            )
            require(
                RUNTIME_IMAGE_ID.fullmatch(runtime_image_id) is not None,
                f"$.snapshot.images[{index}].runtime_image_id is not an image ID",
            )
            runtime_image_ids[service] = runtime_image_id
    require(
        "shuffle-action-image" in services,
        "$.snapshot.images omits the dynamic Shuffle action image",
    )
    expected_services = (
        LEGACY_BLOCKED_IMAGE_SERVICES
        if allow_legacy_blocked_inventory
        else EXPECTED_FULL_PROFILE_IMAGE_SERVICES
    )
    require(
        services == expected_services,
        "$.snapshot.images must contain the complete reviewed full-profile service inventory",
    )
    if not allow_legacy_blocked_inventory:
        require(
            "shuffle-action-image" in runtime_image_ids,
            "$.snapshot.images must retain the observed Shuffle action runtime image ID",
        )
    require(
        re.fullmatch(
            r"control-plane@sha256:[0-9a-f]{64}",
            image_references["control-plane"],
        )
        is not None,
        "$.snapshot.images control-plane entry must use its captured image ID",
    )
    for service, reviewed_reference in REVIEWED_IMMUTABLE_IMAGE_REFERENCES.items():
        if service not in expected_services:
            continue
        require(
            image_references[service] == reviewed_reference,
            f"$.snapshot.images.{service} does not use the reviewed immutable reference",
        )


def _validate_snapshot(
    value: object,
    *,
    trial_run_id: str,
    allow_legacy_blocked_inventory: bool = False,
    expected_schema_sha256: str | None = None,
) -> Mapping[str, object]:
    snapshot = require_mapping(value, "$.snapshot")
    require_exact_keys(
        snapshot,
        required=(
            "snapshot_id",
            "repository_revision",
            "compose_sha256",
            "evidence_schema_sha256",
            "runtime_artifact_sha256",
            "shuffle_api_workflow_id",
            "shuffle_reviewed_workflow_sha256",
            "shuffle_live_workflow_sha256",
            "host_architecture",
            "docker_context",
            "colima_profile",
            "selected_profile",
            "images",
        ),
        path="$.snapshot",
    )
    require(SNAPSHOT_ID.fullmatch(require_string(snapshot["snapshot_id"], "$.snapshot.snapshot_id")) is not None, "$.snapshot.snapshot_id is invalid")
    repository_revision = require_string(
        snapshot["repository_revision"],
        "$.snapshot.repository_revision",
    )
    require(
        REVISION.fullmatch(repository_revision) is not None,
        "$.snapshot.repository_revision must be a full commit SHA",
    )
    for key in (
        "compose_sha256",
        "evidence_schema_sha256",
        "runtime_artifact_sha256",
        "shuffle_reviewed_workflow_sha256",
        "shuffle_live_workflow_sha256",
    ):
        require(SHA256.fullmatch(require_string(snapshot[key], f"$.snapshot.{key}")) is not None, f"$.snapshot.{key} must be SHA-256")
    if expected_schema_sha256 is not None and not allow_legacy_blocked_inventory:
        require(
            snapshot["evidence_schema_sha256"] == expected_schema_sha256,
            "$.snapshot.evidence_schema_sha256 does not match the validator schema",
        )
    require(
        WORKFLOW_UUID.fullmatch(
            require_string(
                snapshot["shuffle_api_workflow_id"],
                "$.snapshot.shuffle_api_workflow_id",
            )
        )
        is not None,
        "$.snapshot.shuffle_api_workflow_id must be a UUID",
    )
    require(
        snapshot["host_architecture"] in SUPPORTED_HOST_ARCHITECTURES,
        "$.snapshot.host_architecture is not supported",
    )
    require_string(snapshot["docker_context"], "$.snapshot.docker_context")
    require_string(snapshot["colima_profile"], "$.snapshot.colima_profile")
    require(snapshot["selected_profile"] == "full", "$.snapshot.selected_profile must be full")
    _validate_runtime_images(
        snapshot["images"],
        allow_legacy_blocked_inventory=allow_legacy_blocked_inventory,
    )
    require(
        snapshot["snapshot_id"] == _snapshot_identifier(trial_run_id, snapshot),
        "$.snapshot.snapshot_id is not bound to all snapshot inputs",
    )
    return snapshot


def _validate_steps(
    value: object,
    snapshot_id: str,
    verdict: str,
    *,
    allow_legacy_blocked_refs: bool = False,
) -> tuple[tuple[str, ...], tuple[datetime, ...]]:
    require(isinstance(value, list) and len(value) == len(STEP_NAMES), "$.steps must contain exactly 15 steps")
    statuses: list[str] = []
    observed_times: list[datetime] = []
    reviewed_step_names = (
        LEGACY_BLOCKED_STEP_NAMES if allow_legacy_blocked_refs else STEP_NAMES
    )
    for index, expected_name in enumerate(reviewed_step_names):
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
        observed_at = _datetime_value(
            item["observed_at"],
            f"$.steps[{index}].observed_at",
        )
        observed_times.append(observed_at)
        refs = item["evidence_refs"]
        require(isinstance(refs, list) and refs, f"$.steps[{index}].evidence_refs must be non-empty")
        for ref_index, evidence_ref in enumerate(refs):
            require_string(evidence_ref, f"$.steps[{index}].evidence_refs[{ref_index}]")
        refs_tuple = tuple(refs)
        if allow_legacy_blocked_refs:
            require(
                refs_tuple == LEGACY_BLOCKED_STEP_EVIDENCE_REFS[index],
                f"$.steps[{index}].evidence_refs do not match the historical trial contract",
            )
        elif status == "passed":
            require(
                refs_tuple == STEP_EVIDENCE_REFS[index],
                f"$.steps[{index}].evidence_refs do not match the reviewed step contract",
            )
        elif status in {"blocked", "failed"}:
            require(
                set(refs).issubset(STEP_EVIDENCE_REFS[index]),
                f"$.steps[{index}].evidence_refs are outside the reviewed step contract",
            )
        else:
            require(
                len(refs) == 1 and refs[0].startswith("not-run:"),
                f"$.steps[{index}].evidence_refs must record a not-run reason",
            )
        blocker = item.get("blocker")
        if status in {"blocked", "failed"}:
            blocker_mapping = require_mapping(blocker, f"$.steps[{index}].blocker")
            require_exact_keys(blocker_mapping, required=("owner", "reason"), path=f"$.steps[{index}].blocker")
            require_string(blocker_mapping["owner"], f"$.steps[{index}].blocker.owner")
            require_string(blocker_mapping["reason"], f"$.steps[{index}].blocker.reason")
        else:
            require(blocker is None, f"$.steps[{index}].blocker is only allowed for failed or blocked steps")
    completed_times = [
        observed_at
        for status, observed_at in zip(statuses, observed_times)
        if status != "not_run"
    ]
    require(
        all(
            current > previous
            for previous, current in zip(completed_times, completed_times[1:])
        ),
        "completed step observations must be strictly chronological",
    )
    if verdict == PASSED_VERDICT:
        require(all(status == "passed" for status in statuses), "a passed verdict requires all journey steps to pass")
    elif verdict == "integration_trial_blocked":
        require(statuses.count("blocked") == 1, "a blocked verdict requires exactly one blocked step")
        blocked_index = statuses.index("blocked")
        require(all(status == "passed" for status in statuses[:blocked_index]), "steps before a blocker must pass")
        require(all(status == "not_run" for status in statuses[blocked_index + 1 :]), "steps after a blocker must be not_run")
    elif verdict == "integration_trial_failed":
        require(statuses.count("failed") == 1, "a failed verdict requires exactly one failed step")
        failed_index = statuses.index("failed")
        require(all(status == "passed" for status in statuses[:failed_index]), "steps before a failure must pass")
        require(all(status == "not_run" for status in statuses[failed_index + 1 :]), "steps after a failure must be not_run")
    return tuple(statuses), tuple(observed_times)


def validate_manifest(
    manifest: object,
    schema: object,
    *,
    schema_sha256: str | None = None,
) -> None:
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
    captured_at = _datetime_value(root["captured_at"], "$.captured_at")
    require(root["source_mode"] == "real_services", "$.source_mode must be real_services")
    allow_legacy_blocked_packet = _is_legacy_blocked_manifest(root)
    trial_run_id = require_string(root["trial_run_id"], "$.trial_run_id")
    require(TRIAL_ID.fullmatch(trial_run_id) is not None, "$.trial_run_id is invalid")
    verdict = require_string(root["verdict"], "$.verdict")
    require(verdict in VERDICTS, "$.verdict is not in the reviewed vocabulary")
    snapshot = _validate_snapshot(
        root["snapshot"],
        trial_run_id=trial_run_id,
        allow_legacy_blocked_inventory=allow_legacy_blocked_packet,
        expected_schema_sha256=schema_sha256,
    )
    snapshot_id = require_string(snapshot["snapshot_id"], "$.snapshot.snapshot_id")
    step_statuses, step_observed_times = _validate_steps(
        root["steps"],
        snapshot_id,
        verdict,
        allow_legacy_blocked_refs=allow_legacy_blocked_packet,
    )
    completed_step_times = tuple(
        observed_at
        for status, observed_at in zip(step_statuses, step_observed_times)
        if status != "not_run"
    )
    require(
        completed_step_times and captured_at >= completed_step_times[-1],
        "manifest capture time must not precede the last completed step",
    )

    identifiers = require_mapping(root["identifiers"], "$.identifiers")
    require_exact_keys(identifiers, required=IDENTIFIER_KEYS, path="$.identifiers")
    normalized_ids = {
        key: require_nullable_string(identifiers[key], f"$.identifiers.{key}")
        for key in IDENTIFIER_KEYS
    }
    require(
        set(IDENTIFIER_PRODUCING_STEPS) == set(IDENTIFIER_KEYS),
        "identifier-producing step contract is incomplete",
    )
    for key, producing_step in IDENTIFIER_PRODUCING_STEPS.items():
        step_status = step_statuses[STEP_NAMES.index(producing_step)]
        if step_status == "passed":
            require(
                normalized_ids[key] is not None,
                f"$.identifiers.{key} is required after {producing_step} passed",
            )
        else:
            require(
                normalized_ids[key] is None,
                f"$.identifiers.{key} must be null when {producing_step} did not pass",
            )
    for key, value in normalized_ids.items():
        if value is not None:
            require(PLACEHOLDER.search(value) is None, f"$.identifiers.{key} looks synthetic or placeholder-derived")
    wazuh_rule_id = normalized_ids["wazuh_rule_id"]
    if wazuh_rule_id is not None:
        require(
            wazuh_rule_id == REVIEWED_WAZUH_RULE_ID,
            "Wazuh rule ID is outside the reviewed detection contract",
        )
    execution_id = normalized_ids["shuffle_execution_id"]
    if execution_id is not None:
        require(not execution_id.startswith("shuffle-run-"), "synthetic Shuffle execution ID cannot be live evidence")
        require(
            CANONICAL_UUID.fullmatch(execution_id) is not None,
            "Shuffle execution ID must use canonical UUID form",
        )
    if normalized_ids["native_wazuh_alert_id"] and normalized_ids["aegisops_alert_id"]:
        require(normalized_ids["native_wazuh_alert_id"] != normalized_ids["aegisops_alert_id"], "native Wazuh and AegisOps alert IDs must remain distinct")
    denied_action_request_id = normalized_ids["denied_action_request_id"]
    approved_action_request_id = normalized_ids["action_request_id"]
    if denied_action_request_id is not None and approved_action_request_id is not None:
        require(
            denied_action_request_id != approved_action_request_id,
            "denied and approved action request IDs must remain distinct",
        )
    denied_approval_decision_id = normalized_ids["denied_approval_decision_id"]
    approved_approval_decision_id = normalized_ids["approval_decision_id"]
    if (
        denied_approval_decision_id is not None
        and approved_approval_decision_id is not None
    ):
        require(
            denied_approval_decision_id != approved_approval_decision_id,
            "denied and approved decision IDs must remain distinct",
        )
    workflow_id = normalized_ids["shuffle_workflow_id"]
    workflow_version = normalized_ids["shuffle_workflow_version"]
    if workflow_id is not None:
        require(
            workflow_id == snapshot["shuffle_api_workflow_id"],
            "Shuffle workflow ID is not bound to the snapshot",
        )
        require(
            workflow_version == REVIEWED_SHUFFLE_WORKFLOW_VERSION,
            "Shuffle workflow version is not the reviewed version",
        )

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
    if step_statuses[5] == "passed":
        require(
            requester is not None
            and approval_challenge_sha256 is not None
            and SHA256.fullmatch(approval_challenge_sha256) is not None,
            "a reviewed action request requires a requester and challenge digest",
        )
    else:
        require(
            requester is None and approval_challenge_sha256 is None,
            "a non-passed action-request step cannot claim request control proof",
        )
    if step_statuses[6] == "passed":
        require(denied_count == 0 and denied_rejected is True, "denied action must produce no dispatch")
    else:
        require(
            denied_count is None and denied_rejected is None,
            "a non-passed denial step cannot claim denial proof",
        )
    if step_statuses[7] == "passed":
        require(
            requester is not None
            and approver is not None
            and authenticated_approver is not None,
            "an approved dispatch requires requester and approver identities",
        )
        require(requester != approver, "requester and approver must be distinct")
        require(approver == authenticated_approver, "approver must match the authenticated local operator")
        require(approval_source == "interactive_local_operator_ceremony", "approval must come from the interactive ceremony")
        require(approval_method in {"macos_operator_dialog", "tty_challenge"}, "approval method is not independently interactive")
        approval_time = _datetime_value(
            approval_confirmed_at,
            "$.human_control.approval_confirmed_at",
        )
        require(
            step_observed_times[6] < approval_time <= step_observed_times[7],
            "approval confirmation must follow denial proof and precede "
            "the dispatch observation",
        )
    else:
        require(
            all(
                value is None
                for value in (
                    approver,
                    authenticated_approver,
                    approval_source,
                    approval_method,
                    approval_confirmed_at,
                )
            ),
            "a non-passed approval step cannot claim an approver or approval event",
        )

    idempotency = require_mapping(root["idempotency"], "$.idempotency")
    require_exact_keys(idempotency, required=("wazuh_first_disposition", "wazuh_duplicate_disposition", "wazuh_alert_identity_preserved", "shuffle_execution_count", "receipt_replay_reconciliation_id", "receipt_identity_preserved"), path="$.idempotency")
    first_disposition = require_nullable_string(idempotency["wazuh_first_disposition"], "$.idempotency.wazuh_first_disposition")
    duplicate_disposition = require_nullable_string(idempotency["wazuh_duplicate_disposition"], "$.idempotency.wazuh_duplicate_disposition")
    wazuh_preserved = require_nullable_boolean(idempotency["wazuh_alert_identity_preserved"], "$.idempotency.wazuh_alert_identity_preserved")
    execution_count = require_nullable_integer(idempotency["shuffle_execution_count"], "$.idempotency.shuffle_execution_count")
    replay_id = require_nullable_string(idempotency["receipt_replay_reconciliation_id"], "$.idempotency.receipt_replay_reconciliation_id")
    receipt_preserved = require_nullable_boolean(idempotency["receipt_identity_preserved"], "$.idempotency.receipt_identity_preserved")
    if step_statuses[3] == "passed":
        require(first_disposition == "created" and duplicate_disposition == "deduplicated" and wazuh_preserved is True, "Wazuh replay must preserve one admitted alert")
    else:
        require(
            first_disposition is None
            and duplicate_disposition is None
            and wazuh_preserved is None,
            "a non-passed Wazuh admission step cannot claim replay success",
        )
    if step_statuses[11] == "passed":
        require(execution_count == 1 and receipt_preserved is True, "Shuffle replay must preserve one execution and receipt")
        require(replay_id == normalized_ids["reconciliation_id"], "receipt replay must reuse the reconciliation ID")
    else:
        require(
            execution_count is None and replay_id is None and receipt_preserved is None,
            "a non-passed receipt replay step cannot claim Shuffle replay success",
        )

    negative_cases = require_mapping(root["negative_cases"], "$.negative_cases")
    require_exact_keys(negative_cases, required=NEGATIVE_CASE_KEYS, path="$.negative_cases")
    require(
        set(NEGATIVE_CASE_PRODUCING_STEPS) == set(NEGATIVE_CASE_KEYS),
        "negative-case producing step contract is incomplete",
    )
    for key in NEGATIVE_CASE_KEYS:
        case = require_mapping(negative_cases[key], f"$.negative_cases.{key}")
        require_exact_keys(case, required=("status", "authority_before", "authority_after", "authority_delta", "measurement_source", "evidence_ref"), path=f"$.negative_cases.{key}")
        status = require_nullable_string(case["status"], f"$.negative_cases.{key}.status")
        before = require_nullable_integer(case["authority_before"], f"$.negative_cases.{key}.authority_before")
        after = require_nullable_integer(case["authority_after"], f"$.negative_cases.{key}.authority_after")
        delta = require_nullable_integer(case["authority_delta"], f"$.negative_cases.{key}.authority_delta")
        measurement_source = require_nullable_string(case["measurement_source"], f"$.negative_cases.{key}.measurement_source")
        evidence_ref = require_nullable_string(case["evidence_ref"], f"$.negative_cases.{key}.evidence_ref")
        producing_step = NEGATIVE_CASE_PRODUCING_STEPS[key]
        producing_step_status = step_statuses[STEP_NAMES.index(producing_step)]
        if producing_step_status != "passed":
            require(
                all(
                    value is None
                    for value in (
                        status,
                        before,
                        after,
                        delta,
                        measurement_source,
                        evidence_ref,
                    )
                ),
                f"$.negative_cases.{key} must be null when {producing_step} did not pass",
            )
            continue
        if status is not None:
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
        else:
            raise EvidenceValidationError(
                f"$.negative_cases.{key} is missing after {producing_step} passed"
            )

    restart = require_mapping(root["restart"], "$.restart")
    require_exact_keys(restart, required=("performed", "records_persisted", "checked_identifiers"), path="$.restart")
    restart_performed = require_nullable_boolean(restart["performed"], "$.restart.performed")
    records_persisted = require_nullable_boolean(restart["records_persisted"], "$.restart.records_persisted")
    checked = restart["checked_identifiers"]
    require(isinstance(checked, list), "$.restart.checked_identifiers must be an array")
    normalized_checked = tuple(
        require_string(value, f"$.restart.checked_identifiers[{index}]")
        for index, value in enumerate(checked)
    )
    if step_statuses[13] == "passed":
        require(restart_performed is True and records_persisted is True, "passed trial requires restart persistence proof")
        require(
            len(normalized_checked) == len(set(normalized_checked)),
            "restart proof cannot contain duplicate identifiers",
        )
        require(
            set(normalized_checked) == set(RESTART_CHECKED_IDENTIFIER_FIELDS),
            "restart proof must contain exactly the reviewed authoritative identifiers",
        )
    else:
        require(restart_performed is None and records_persisted is None and checked == [], "a non-passed restart step cannot claim persistence proof")

    report = require_mapping(root["report"], "$.report")
    require_exact_keys(report, required=("report_id", "sha256", "source_of_truth", "redacted"), path="$.report")
    report_id = require_nullable_string(report["report_id"], "$.report.report_id")
    report_sha = require_nullable_string(report["sha256"], "$.report.sha256")
    report_source = require_nullable_string(report["source_of_truth"], "$.report.source_of_truth")
    report_redacted = require_nullable_boolean(report["redacted"], "$.report.redacted")
    if step_statuses[10] == "passed":
        require(report_id == normalized_ids["report_id"], "report ID is not bound to journey identifiers")
        require(report_sha is not None and SHA256.fullmatch(report_sha) is not None, "report digest must be SHA-256")
        require(report_source == "aegisops_authoritative_records" and report_redacted is True, "report must be redacted and AegisOps-derived")
    else:
        require(
            report_id is None
            and report_sha is None
            and report_source is None
            and report_redacted is None,
            "a non-passed report step cannot claim a report export",
        )

    evaluation = require_mapping(root["evaluation"], "$.evaluation")
    require_exact_keys(evaluation, required=("trial_run_id", "snapshot_id", "repository_revision", "evaluated_at", "verdict", "ga_accepted", "sha256"), path="$.evaluation")
    evaluation_trial = require_nullable_string(evaluation["trial_run_id"], "$.evaluation.trial_run_id")
    evaluation_snapshot = require_nullable_string(evaluation["snapshot_id"], "$.evaluation.snapshot_id")
    evaluation_revision = require_nullable_string(evaluation["repository_revision"], "$.evaluation.repository_revision")
    evaluation_verdict = require_nullable_string(evaluation["verdict"], "$.evaluation.verdict")
    evaluation_ga = require_nullable_boolean(evaluation["ga_accepted"], "$.evaluation.ga_accepted")
    evaluation_sha = require_nullable_string(evaluation["sha256"], "$.evaluation.sha256")
    evaluation_present = any(
        value is not None
        for value in (
            evaluation_trial,
            evaluation_snapshot,
            evaluation_revision,
            evaluation["evaluated_at"],
            evaluation_verdict,
            evaluation_ga,
            evaluation_sha,
        )
    )
    if step_statuses[14] == "passed" or allow_legacy_blocked_packet:
        require(
            evaluation_present,
            "a passed evaluation step requires a bound evaluation record",
        )
        require(evaluation_trial == root["trial_run_id"], "evaluation is not bound to this trial")
        require(evaluation_snapshot == snapshot_id, "evaluation is not bound to this snapshot")
        require(evaluation_revision == snapshot["repository_revision"], "evaluation is not bound to this repository revision")
        evaluation_time = _datetime_value(
            evaluation["evaluated_at"],
            "$.evaluation.evaluated_at",
        )
        require(
            evaluation_time == step_observed_times[14],
            "evaluation time must match the evaluation step observation",
        )
        require(evaluation_verdict == verdict, "evaluation verdict does not match the manifest")
        require(evaluation_ga is False, "Phase 67 evidence cannot accept GA")
        require(evaluation_sha is not None and SHA256.fullmatch(evaluation_sha) is not None, "evaluation record digest must be SHA-256")
    else:
        require(
            not evaluation_present,
            "a non-passed evaluation step cannot claim a published evaluation",
        )

    artifacts = require_mapping(root["artifacts"], "$.artifacts")
    require_exact_keys(artifacts, required=("retention", "directory_name", "files"), path="$.artifacts")
    retention = require_nullable_string(artifacts["retention"], "$.artifacts.retention")
    directory_name = require_nullable_string(artifacts["directory_name"], "$.artifacts.directory_name")
    files = artifacts["files"]
    require(isinstance(files, list), "$.artifacts.files must be an array")
    artifact_names: set[str] = set()
    artifact_digests: dict[str, str] = {}
    for index, item in enumerate(files):
        artifact = require_mapping(item, f"$.artifacts.files[{index}]")
        require_exact_keys(artifact, required=("name", "sha256"), path=f"$.artifacts.files[{index}]")
        name = require_string(artifact["name"], f"$.artifacts.files[{index}].name")
        require(name not in artifact_names, "$.artifacts.files contains duplicate names")
        artifact_names.add(name)
        digest = require_string(artifact["sha256"], f"$.artifacts.files[{index}].sha256")
        require(SHA256.fullmatch(digest) is not None, f"$.artifacts.files[{index}].sha256 must be SHA-256")
        artifact_digests[name] = digest
    if evaluation_present:
        require(
            artifact_digests.get("evaluation-record.json") == evaluation_sha,
            "evaluation digest does not match evaluation-record.json artifact",
        )
    if verdict == PASSED_VERDICT:
        require(retention == "local_mode_0600", "passed trial raw artifacts must be retained in local 0600 mode")
        require(directory_name == f"{root['trial_run_id']}-artifacts", "artifact directory is not bound to this trial")
        require(artifact_names == ARTIFACT_NAMES, "raw artifact inventory is incomplete")

    cleanup = require_mapping(root["cleanup"], "$.cleanup")
    require_exact_keys(cleanup, required=("mode", "containers_stopped", "data_preserved"), path="$.cleanup")
    cleanup_mode = require_nullable_string(cleanup["mode"], "$.cleanup.mode")
    containers_stopped = require_nullable_boolean(cleanup["containers_stopped"], "$.cleanup.containers_stopped")
    data_preserved = require_nullable_boolean(cleanup["data_preserved"], "$.cleanup.data_preserved")
    cleanup_state = (cleanup_mode, containers_stopped, data_preserved)
    require(
        cleanup_state
        in {
            (None, None, None),
            ("non_destructive", True, True),
        },
        "cleanup must be either unobserved or completed non-destructively",
    )
    if verdict == PASSED_VERDICT:
        require(
            cleanup_state == ("non_destructive", True, True),
            "cleanup must stop services without deleting evidence or volumes",
        )

    require(root["authority_posture"] == "aegisops_records_remain_authoritative", "$.authority_posture is invalid")
    limitations = root["limitations"]
    require(isinstance(limitations, list) and limitations, "$.limitations must be non-empty")
    limitation_statuses: dict[str, str] = {}
    for index, item in enumerate(limitations):
        limitation = require_mapping(item, f"$.limitations[{index}]")
        require_exact_keys(limitation, required=("limitation_id", "owner", "status", "description"), optional=("follow_up_issue",), path=f"$.limitations[{index}]")
        limitation_id = require_string(limitation["limitation_id"], f"$.limitations[{index}].limitation_id")
        require(limitation_id not in limitation_statuses, "duplicate limitation_id")
        require_string(limitation["owner"], f"$.limitations[{index}].owner")
        limitation_status = require_string(
            limitation["status"],
            f"$.limitations[{index}].status",
        )
        require(
            limitation_status in {"accepted", "follow_up_required", "blocking"},
            f"$.limitations[{index}].status is invalid",
        )
        limitation_statuses[limitation_id] = limitation_status
        require_string(limitation["description"], f"$.limitations[{index}].description")
        follow_up = limitation.get("follow_up_issue")
        require(follow_up is None or (isinstance(follow_up, str) and re.fullmatch(r"#[0-9]+", follow_up) is not None), f"$.limitations[{index}].follow_up_issue must be an issue reference or null")
    if allow_legacy_blocked_packet:
        require(
            limitation_statuses == LEGACY_APPROVAL_BLOCKER_STATUSES,
            "historical approval-blocked limitation contract is incomplete",
        )
    else:
        for limitation_id, expected_status in OWNED_LIMITATION_STATUSES.items():
            require(
                limitation_statuses.get(limitation_id) == expected_status,
                f"$.limitations must retain {limitation_id} with status {expected_status}",
            )
        if verdict == PASSED_VERDICT:
            require(
                limitation_statuses == OWNED_LIMITATION_STATUSES,
                "passed trial limitation set must match the reviewed owned limitations",
            )
        else:
            terminal_status = (
                "blocked"
                if verdict == "integration_trial_blocked"
                else "failed"
            )
            terminal_step = STEP_NAMES[step_statuses.index(terminal_status)]
            terminal_limitation_id = (
                f"phase67-{terminal_status}-{terminal_step.replace('_', '-')}"
            )
            expected_statuses = {
                **OWNED_LIMITATION_STATUSES,
                terminal_limitation_id: "blocking",
            }
            require(
                limitation_statuses == expected_statuses,
                "blocked or failed trial limitation set must match its terminal step",
            )
    _scan_secret_values(root)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 2:
        print(
            "usage: validate_evidence_manifest.py SCHEMA MANIFEST\n"
            "       validate_evidence_manifest.py --runtime-images IMAGES",
            file=sys.stderr,
        )
        return 2
    try:
        if arguments[0] == "--runtime-images":
            _validate_runtime_images(load_json(Path(arguments[1])))
        else:
            schema_path = Path(arguments[0])
            schema, schema_sha256 = load_json_with_sha256(schema_path)
            manifest = load_json(Path(arguments[1]))
            validate_manifest(
                manifest,
                schema,
                schema_sha256=schema_sha256,
            )
    except EvidenceValidationError as exc:
        print(f"Phase 67.4 evidence validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
