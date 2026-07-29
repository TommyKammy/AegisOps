from __future__ import annotations

from datetime import datetime
import json
import pathlib
import re
import sys
from uuid import UUID


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _json_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    return left == right


def _matches_type(value: object, expected_type: str) -> bool:
    return {
        "array": lambda: isinstance(value, list),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "object": lambda: isinstance(value, dict),
        "string": lambda: isinstance(value, str),
    }.get(expected_type, lambda: False)()


def _schema_accepts(value: object, schema: object, path: str) -> bool:
    try:
        _validate_schema(value, schema, path)
    except ValueError:
        return False
    return True


def _validate_schema(value: object, schema: object, path: str) -> None:
    require(isinstance(schema, dict), f"{path}: schema node must be an object")
    expected_type = schema.get("type")
    if expected_type is not None:
        require(
            isinstance(expected_type, str)
            and _matches_type(value, expected_type),
            f"{path}: expected {expected_type}",
        )
    if "const" in schema:
        require(
            _json_equal(value, schema["const"]),
            f"{path}: value does not match const",
        )
    if isinstance(value, str):
        min_length = schema.get("minLength")
        if min_length is not None:
            require(
                isinstance(min_length, int) and len(value) >= min_length,
                f"{path}: string is too short",
            )
        pattern = schema.get("pattern")
        if pattern is not None:
            require(
                isinstance(pattern, str) and re.search(pattern, value) is not None,
                f"{path}: string does not match pattern",
            )
        value_format = schema.get("format")
        if value_format == "uuid":
            try:
                UUID(value)
            except ValueError as exc:
                raise ValueError(f"{path}: invalid UUID") from exc
        elif value_format == "date-time":
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"{path}: invalid date-time") from exc
            require(parsed.tzinfo is not None, f"{path}: date-time must include timezone")
        elif value_format is not None:
            raise ValueError(f"{path}: unsupported schema format {value_format!r}")
    if isinstance(value, dict):
        required = schema.get("required", [])
        require(isinstance(required, list), f"{path}: required must be an array")
        for field_name in required:
            require(
                isinstance(field_name, str) and field_name in value,
                f"{path}: missing required property {field_name!r}",
            )
        properties = schema.get("properties", {})
        require(isinstance(properties, dict), f"{path}: properties must be an object")
        if schema.get("additionalProperties") is False:
            unexpected = sorted(set(value) - set(properties))
            require(
                not unexpected,
                f"{path}: unexpected properties {unexpected!r}",
            )
        for field_name, field_schema in properties.items():
            if field_name in value:
                _validate_schema(
                    value[field_name],
                    field_schema,
                    f"{path}.{field_name}",
                )
    if isinstance(value, list):
        min_items = schema.get("minItems")
        if min_items is not None:
            require(
                isinstance(min_items, int) and len(value) >= min_items,
                f"{path}: array has too few items",
            )
        if schema.get("uniqueItems") is True:
            encoded_items = [
                json.dumps(item, separators=(",", ":"), sort_keys=True)
                for item in value
            ]
            require(
                len(encoded_items) == len(set(encoded_items)),
                f"{path}: array items are not unique",
            )
        if "contains" in schema:
            require(
                any(
                    _schema_accepts(item, schema["contains"], f"{path}[{index}]")
                    for index, item in enumerate(value)
                ),
                f"{path}: array does not contain a required item",
            )
    if "not" in schema:
        require(
            not _schema_accepts(value, schema["not"], path),
            f"{path}: value matches a forbidden schema",
        )


def main() -> int:
    require(len(sys.argv) == 2, "usage: validate_evidence_manifest.py <manifest>")
    path = pathlib.Path(sys.argv[1])
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "manifest must be a JSON object")
    schema_path = pathlib.Path(__file__).with_name("evidence-manifest.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    _validate_schema(payload, schema, "$")
    require(
        payload.get("schema_version") == "phase67.3-real-shuffle-trial-v1",
        "unexpected schema_version",
    )
    require(payload.get("source_mode") == "real_shuffle", "source_mode is not real")
    workflow_id = payload.get("workflow_api_id")
    require(isinstance(workflow_id, str), "workflow_api_id is missing")
    UUID(workflow_id)
    execution_id = payload.get("execution_id")
    receipt_id = payload.get("expected_execution_receipt_id")
    require(
        isinstance(execution_id, str)
        and execution_id
        and not execution_id.startswith("shuffle-run-"),
        "execution_id is synthetic or missing",
    )
    UUID(execution_id)
    require(
        isinstance(payload.get("idempotency_key"), str)
        and payload["idempotency_key"],
        "idempotency_key is missing",
    )
    idempotency_execution_count = payload.get("idempotency_execution_count")
    require(
        isinstance(idempotency_execution_count, int)
        and not isinstance(idempotency_execution_count, bool)
        and idempotency_execution_count == 1,
        "idempotency key did not resolve to integer one execution",
    )
    requested_scope = payload.get("requested_scope")
    require(
        isinstance(requested_scope, dict)
        and requested_scope.get("record_family") == "phase67_lab_trial"
        and requested_scope.get("recipient_identity") == "local-test-sink",
        "requested_scope is invalid",
    )
    require(
        isinstance(receipt_id, str)
        and receipt_id
        and not receipt_id.startswith("shuffle-receipt-"),
        "receipt id is synthetic or missing",
    )
    for digest_field in ("payload_hash", "normalized_receipt_sha256"):
        require(
            isinstance(payload.get(digest_field), str)
            and re.fullmatch(r"[0-9a-f]{64}", payload[digest_field]) is not None,
            f"{digest_field} is invalid",
        )
    require(
        payload.get("reconciliation_id")
        == payload.get("replay_reconciliation_id"),
        "receipt replay was not idempotent",
    )
    require(
        payload.get("execution_lifecycle_state") == "succeeded",
        "execution lifecycle is not succeeded",
    )
    require(
        payload.get("reconciliation_disposition") == "matched",
        "reconciliation disposition is not matched",
    )
    require(
        payload.get("authority_posture")
        == "aegisops_reconciliation_remains_authoritative",
        "Shuffle state was promoted beyond its authority boundary",
    )
    require(
        "isolated_non-production_lab" in payload.get("limitations", []),
        "non-production limitation is missing",
    )
    print("PASS: Phase 67.3 real Shuffle evidence is structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
