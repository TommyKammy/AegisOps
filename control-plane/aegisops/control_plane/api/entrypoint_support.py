from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import ipaddress
import json
from typing import Mapping

MAX_WAZUH_INGEST_BODY_BYTES = 1_048_576


class RequestTooLargeError(ValueError):
    """Raised when a reviewed request body exceeds the allowed size limit."""


def normalize_alert_id(value: str) -> str:
    return value.strip()


def normalize_case_id(value: str) -> str:
    return value.strip()


def normalize_record_family(value: str) -> str:
    return value.strip()


def normalize_record_id(value: str) -> str:
    return value.strip()


def normalize_optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("optional string fields must be JSON strings when provided")
    normalized = value.strip()
    return normalized or None


def require_json_string(payload: Mapping[str, object], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def require_json_string_sequence(
    payload: Mapping[str, object],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name, ())
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array of non-empty strings")
    normalized_values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must be a JSON array of non-empty strings")
        normalized_values.append(item.strip())
    return tuple(normalized_values)


def parse_datetime_arg(value: str, field_name: str) -> datetime:
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} must be a non-empty ISO 8601 datetime")
    try:
        parsed = datetime.fromisoformat(normalized_value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO 8601 datetime") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone offset")
    return parsed


def require_json_datetime(payload: Mapping[str, object], field_name: str) -> datetime:
    value = payload.get(field_name)
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty ISO 8601 datetime")
    return parse_datetime_arg(value, field_name)


def read_json_request_body(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except ValueError as exc:
        raise ValueError("Content-Length must be an integer") from exc
    if content_length <= 0:
        raise ValueError("request body is required")
    if content_length > MAX_WAZUH_INGEST_BODY_BYTES:
        raise RequestTooLargeError("request body exceeds the reviewed size limit")
    try:
        raw_payload = handler.rfile.read(content_length).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("request body must be valid UTF-8 JSON") from exc
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"request body must be valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")
    return payload


def read_json_file(path: str) -> dict[str, object]:
    normalized_path = path.strip()
    if not normalized_path:
        raise ValueError("input path must be a non-empty string")
    try:
        with open(normalized_path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        raise ValueError(f"input path must point to a readable JSON file: {normalized_path!r}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"input path must contain valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("input path must contain a JSON object")
    return payload


def peer_addr_is_loopback(peer_addr: str | None) -> bool:
    if peer_addr is None or peer_addr.strip() == "":
        return False
    try:
        return ipaddress.ip_address(peer_addr.strip()).is_loopback
    except ValueError:
        return False


def require_loopback_operator_request(handler: BaseHTTPRequestHandler) -> None:
    peer_addr = handler.client_address[0] if handler.client_address else None
    if peer_addr_is_loopback(peer_addr):
        return
    raise PermissionError(
        "operator write surface only accepts loopback callers until a reviewed operator auth boundary exists"
    )


def json_ready(value: object) -> object:
    if is_dataclass(value):
        raw = {field.name: getattr(value, field.name) for field in fields(value)}
    else:
        raw = value
    if isinstance(raw, Mapping):
        return {str(key): json_ready(item) for key, item in raw.items()}
    if isinstance(raw, dict):
        return {key: json_ready(item) for key, item in raw.items()}
    if isinstance(raw, tuple):
        return [json_ready(item) for item in raw]
    if isinstance(raw, list):
        return [json_ready(item) for item in raw]
    if hasattr(raw, "isoformat"):
        try:
            return raw.isoformat()
        except TypeError:
            return raw
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    return raw
