#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
SUPPORTED_KEYWORDS = frozenset(
    {
        "$defs",
        "$id",
        "$ref",
        "$schema",
        "additionalProperties",
        "const",
        "enum",
        "format",
        "minLength",
        "minimum",
        "pattern",
        "properties",
        "required",
        "title",
        "type",
    }
)
SUPPORTED_TYPES = frozenset(
    {"array", "boolean", "integer", "null", "number", "object", "string"}
)


class EvidenceSchemaError(ValueError):
    pass


def _reject_non_json_constant(value: str) -> object:
    raise EvidenceSchemaError(f"non-JSON numeric constant {value!r}")


def _reject_duplicate_keys(
    pairs: Sequence[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceSchemaError(f"duplicate JSON key {key!r}")
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
        raise EvidenceSchemaError(f"cannot read {path}: {exc}") from exc


def _require_schema_mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise EvidenceSchemaError(f"{path} must be a schema object")
    return value


def _check_schema_tree(schema: Mapping[str, object], path: str = "$") -> None:
    unsupported = sorted(set(schema) - SUPPORTED_KEYWORDS)
    if unsupported:
        raise EvidenceSchemaError(
            f"{path} uses unsupported schema keywords: {', '.join(unsupported)}"
        )

    declared_type = schema.get("type")
    if declared_type is not None and declared_type not in SUPPORTED_TYPES:
        raise EvidenceSchemaError(f"{path}.type is unsupported")

    required = schema.get("required")
    if required is not None and (
        not isinstance(required, list)
        or any(not isinstance(item, str) for item in required)
        or len(set(required)) != len(required)
    ):
        raise EvidenceSchemaError(f"{path}.required must contain unique strings")

    additional = schema.get("additionalProperties")
    if additional is not None and not isinstance(additional, bool):
        raise EvidenceSchemaError(
            f"{path}.additionalProperties must be a boolean"
        )

    pattern = schema.get("pattern")
    if pattern is not None:
        if not isinstance(pattern, str):
            raise EvidenceSchemaError(f"{path}.pattern must be a string")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise EvidenceSchemaError(f"{path}.pattern is invalid: {exc}") from exc

    min_length = schema.get("minLength")
    if (
        min_length is not None
        and (
            not isinstance(min_length, int)
            or isinstance(min_length, bool)
            or min_length < 0
        )
    ):
        raise EvidenceSchemaError(
            f"{path}.minLength must be a non-negative integer"
        )

    minimum = schema.get("minimum")
    if minimum is not None and (
        not isinstance(minimum, (int, float)) or isinstance(minimum, bool)
    ):
        raise EvidenceSchemaError(f"{path}.minimum must be numeric")

    enum = schema.get("enum")
    if enum is not None and not isinstance(enum, list):
        raise EvidenceSchemaError(f"{path}.enum must be an array")

    format_name = schema.get("format")
    if format_name is not None and format_name != "date-time":
        raise EvidenceSchemaError(f"{path}.format is unsupported")

    reference = schema.get("$ref")
    if reference is not None and (
        not isinstance(reference, str) or not reference.startswith("#/")
    ):
        raise EvidenceSchemaError(f"{path} only supports local JSON Pointer refs")

    for container_name in ("properties", "$defs"):
        container = schema.get(container_name)
        if container is None:
            continue
        if not isinstance(container, Mapping):
            raise EvidenceSchemaError(f"{path}.{container_name} must be an object")
        for name, child in container.items():
            child_schema = _require_schema_mapping(
                child,
                f"{path}.{container_name}.{name}",
            )
            _check_schema_tree(child_schema, f"{path}.{container_name}.{name}")


def _resolve_local_ref(
    root_schema: Mapping[str, object],
    reference: str,
) -> Mapping[str, object]:
    current: object = root_schema
    for encoded_token in reference[2:].split("/"):
        token = encoded_token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, Mapping) or token not in current:
            raise EvidenceSchemaError(f"unresolvable schema ref {reference!r}")
        current = current[token]
    return _require_schema_mapping(current, reference)


def _json_equal(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    return left == right


def _matches_type(instance: object, expected: str) -> bool:
    if expected == "null":
        return instance is None
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(
            instance,
            bool,
        )
    if expected == "string":
        return isinstance(instance, str)
    if expected == "object":
        return isinstance(instance, Mapping)
    if expected == "array":
        return isinstance(instance, list)
    raise EvidenceSchemaError(f"unsupported schema type {expected!r}")


def _validate_date_time(value: str, path: str) -> None:
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EvidenceSchemaError(f"{path} must be a date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EvidenceSchemaError(f"{path} must include a timezone")


def _validate_instance(
    instance: object,
    schema: Mapping[str, object],
    root_schema: Mapping[str, object],
    path: str,
) -> None:
    reference = schema.get("$ref")
    if isinstance(reference, str):
        _validate_instance(
            instance,
            _resolve_local_ref(root_schema, reference),
            root_schema,
            path,
        )

    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _matches_type(instance, expected_type):
        raise EvidenceSchemaError(f"{path} must have type {expected_type}")

    if "const" in schema and not _json_equal(instance, schema["const"]):
        raise EvidenceSchemaError(f"{path} does not match its schema const")

    enum = schema.get("enum")
    if isinstance(enum, list) and not any(
        _json_equal(instance, candidate) for candidate in enum
    ):
        raise EvidenceSchemaError(f"{path} is not in its schema enum")

    if isinstance(instance, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(instance) < min_length:
            raise EvidenceSchemaError(f"{path} is shorter than minLength")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, instance) is None:
            raise EvidenceSchemaError(f"{path} does not match its schema pattern")
        if schema.get("format") == "date-time":
            _validate_date_time(instance, path)

    minimum = schema.get("minimum")
    if (
        isinstance(instance, (int, float))
        and not isinstance(instance, bool)
        and isinstance(minimum, (int, float))
        and instance < minimum
    ):
        raise EvidenceSchemaError(f"{path} is below its schema minimum")

    if not isinstance(instance, Mapping):
        return

    required = schema.get("required")
    if isinstance(required, list):
        missing = [name for name in required if name not in instance]
        if missing:
            raise EvidenceSchemaError(
                f"{path} is missing required properties: {', '.join(missing)}"
            )

    properties = schema.get("properties")
    property_schemas = properties if isinstance(properties, Mapping) else {}
    if schema.get("additionalProperties") is False:
        extras = sorted(set(instance) - set(property_schemas))
        if extras:
            raise EvidenceSchemaError(
                f"{path} has additional properties: {', '.join(extras)}"
            )
    for name, value in instance.items():
        child = property_schemas.get(name)
        if child is None:
            continue
        _validate_instance(
            value,
            _require_schema_mapping(child, f"{path}.{name}"),
            root_schema,
            f"{path}.{name}",
        )


def validate_evidence_manifest(
    instance: object,
    schema: object,
) -> None:
    root_schema = _require_schema_mapping(schema, "$")
    if root_schema.get("$schema") != DRAFT_2020_12:
        raise EvidenceSchemaError(
            "evidence schema must declare JSON Schema Draft 2020-12"
        )
    _check_schema_tree(root_schema)
    _validate_instance(instance, root_schema, root_schema, "$")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 2:
        print(
            "usage: validate_evidence_manifest.py SCHEMA MANIFEST",
            file=sys.stderr,
        )
        return 2
    try:
        schema = load_json(Path(arguments[0]))
        instance = load_json(Path(arguments[1]))
        validate_evidence_manifest(instance, schema)
    except EvidenceSchemaError as exc:
        print(f"evidence schema validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
