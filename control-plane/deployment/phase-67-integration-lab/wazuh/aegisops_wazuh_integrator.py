from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import ssl
import sys
from typing import Callable, Mapping
from urllib import request
from urllib.parse import urlsplit


MAX_ALERT_BYTES = 256 * 1024
DEFAULT_TIMEOUT_SECONDS = 10
SOURCE_FAMILY = "wazuh_detection"
PRODUCT_PROFILE = "phase-67-single-node"
REVIEWED_BY = "phase-67.2-live-wazuh-mapping-v1"
SECRET_CUSTODY_REFERENCE = (
    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE"
)
PROXY_ROUTE = "phase67-proxy:/intake/wazuh -> control-plane:/intake/wazuh"


class IntegrationError(RuntimeError):
    pass


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise IntegrationError(f"{field_name} must be a JSON object")
    return value


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IntegrationError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_timestamp(value: object) -> str:
    timestamp = _require_string(value, "timestamp")
    normalized = timestamp
    if timestamp.endswith("Z"):
        normalized = timestamp[:-1] + "+00:00"
    elif (
        len(timestamp) >= 5
        and timestamp[-5] in {"+", "-"}
        and timestamp[-4:].isdigit()
    ):
        # Wazuh 4.x emits RFC 3339 timestamps with a basic +HHMM offset.
        normalized = f"{timestamp[:-2]}:{timestamp[-2:]}"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise IntegrationError("timestamp must be ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise IntegrationError("timestamp must include a timezone")
    return timestamp


def load_native_alert(path: Path) -> Mapping[str, object]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise IntegrationError(f"cannot inspect Wazuh alert file: {exc}") from exc
    if size <= 0:
        raise IntegrationError("Wazuh alert file is empty")
    if size > MAX_ALERT_BYTES:
        raise IntegrationError(
            f"Wazuh alert file exceeds the {MAX_ALERT_BYTES}-byte intake limit"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntegrationError(f"Wazuh alert file is not valid UTF-8 JSON: {exc}") from exc
    return _require_mapping(payload, "alert")


def load_secret(path: Path) -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as exc:
        raise IntegrationError(f"cannot read the mounted intake secret: {exc}") from exc
    if not value or any(character.isspace() for character in value):
        raise IntegrationError("mounted intake secret must be one non-empty token")
    if len(value) > 512:
        raise IntegrationError("mounted intake secret exceeds the reviewed size limit")
    return value


def map_native_alert(
    native_alert: Mapping[str, object],
    *,
    allowed_rule_id: str,
) -> dict[str, object]:
    native_id = _require_string(native_alert.get("id"), "id")
    timestamp = _require_timestamp(native_alert.get("timestamp"))
    rule = _require_mapping(native_alert.get("rule"), "rule")
    rule_id = _require_string(rule.get("id"), "rule.id")
    if rule_id != allowed_rule_id:
        raise IntegrationError(
            f"rule.id {rule_id!r} is outside the reviewed {allowed_rule_id!r} filter"
        )
    rule_level = rule.get("level")
    if not isinstance(rule_level, int) or isinstance(rule_level, bool):
        raise IntegrationError("rule.level must be an integer")
    _require_string(rule.get("description"), "rule.description")

    manager = _require_mapping(native_alert.get("manager"), "manager")
    manager_name = _require_string(manager.get("name"), "manager.name")
    existing_data = native_alert.get("data")
    if existing_data is not None and not isinstance(existing_data, Mapping):
        raise IntegrationError("data must be a JSON object when present")

    mapped = deepcopy(dict(native_alert))
    mapped_data = deepcopy(dict(existing_data or {}))
    mapped_data.update(
        {
            "source_family": SOURCE_FAMILY,
            "source_system": "wazuh",
            "source_component": "wazuh-manager",
            "source_id": manager_name,
            "event_id": native_id,
            "event_timestamp": timestamp,
            "wazuh_manager_id": manager_name,
            "wazuh_rule_id": rule_id,
            "wazuh_rule_level": str(rule_level),
            "ingest_channel": "reviewed_proxy",
            "admission_channel": "live_wazuh_webhook",
            "secret_custody_reference": SECRET_CUSTODY_REFERENCE,
            "proxy_route": PROXY_ROUTE,
            "reviewed_by": REVIEWED_BY,
            "product_profile": PRODUCT_PROFILE,
            "mapping_version": "phase67-wazuh-v1",
        }
    )
    mapped["data"] = mapped_data
    return mapped


def validate_https_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise IntegrationError("Wazuh intake hook_url must be an absolute HTTPS URL")
    if parsed.username or parsed.password or parsed.fragment:
        raise IntegrationError("Wazuh intake hook_url must not contain credentials or a fragment")
    if parsed.path != "/intake/wazuh" or parsed.query:
        raise IntegrationError("Wazuh intake hook_url must target exactly /intake/wazuh")
    return value


def post_mapped_alert(
    *,
    hook_url: str,
    shared_secret: str,
    ca_file: Path,
    mapped_alert: Mapping[str, object],
    timeout_seconds: int,
    urlopen: Callable[..., object] = request.urlopen,
) -> tuple[int, Mapping[str, object]]:
    validate_https_url(hook_url)
    if timeout_seconds < 1 or timeout_seconds > 60:
        raise IntegrationError("HTTP timeout must be between 1 and 60 seconds")
    try:
        context = ssl.create_default_context(cafile=str(ca_file))
    except (OSError, ssl.SSLError) as exc:
        raise IntegrationError(f"cannot load the reviewed proxy CA file: {exc}") from exc
    encoded = json.dumps(
        mapped_alert,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(encoded) > MAX_ALERT_BYTES:
        raise IntegrationError(
            f"mapped alert exceeds the {MAX_ALERT_BYTES}-byte intake limit"
        )
    http_request = request.Request(
        hook_url,
        data=encoded,
        headers={
            "Authorization": f"Bearer {shared_secret}",
            "Content-Type": "application/json",
            "User-Agent": "aegisops-phase67-wazuh-integrator/1",
        },
        method="POST",
    )
    try:
        with urlopen(
            http_request,
            context=context,
            timeout=timeout_seconds,
        ) as response:
            status = int(response.status)
            response_body = response.read(MAX_ALERT_BYTES + 1)
    except Exception as exc:
        raise IntegrationError(f"AegisOps intake request failed: {exc}") from exc
    if len(response_body) > MAX_ALERT_BYTES:
        raise IntegrationError("AegisOps intake response exceeds the reviewed size limit")
    try:
        response_payload = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntegrationError("AegisOps intake response is not valid UTF-8 JSON") from exc
    response_mapping = _require_mapping(response_payload, "intake response")
    if status != 202:
        raise IntegrationError(f"AegisOps intake returned unexpected HTTP {status}")
    return status, response_mapping


def build_receipt(
    *,
    native_alert_id: str,
    status: int,
    response_payload: Mapping[str, object],
) -> dict[str, object]:
    alert = _require_mapping(response_payload.get("alert"), "intake response alert")
    reconciliation = _require_mapping(
        response_payload.get("reconciliation"),
        "intake response reconciliation",
    )
    return {
        "schema_version": "phase67-wazuh-receipt-v1",
        "source_mode": "real_wazuh",
        "native_wazuh_alert_id": native_alert_id,
        "http_status": status,
        "disposition": _require_string(
            response_payload.get("disposition"),
            "intake response disposition",
        ),
        "aegisops_alert_id": _require_string(
            alert.get("alert_id"),
            "intake response alert.alert_id",
        ),
        "finding_id": _require_string(
            response_payload.get("finding_id"),
            "intake response finding_id",
        ),
        "reconciliation_id": _require_string(
            reconciliation.get("reconciliation_id"),
            "intake response reconciliation.reconciliation_id",
        ),
    }


def append_receipt(path: Path, receipt: Mapping[str, object]) -> None:
    path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    encoded = (
        json.dumps(receipt, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o640)
        try:
            os.fchmod(descriptor, 0o640)
            os.write(descriptor, encoded)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise IntegrationError(f"cannot append the sanitized intake receipt: {exc}") from exc


def run(argv: list[str], environ: Mapping[str, str]) -> dict[str, object]:
    if len(argv) < 4:
        raise IntegrationError(
            "Wazuh Integrator must supply alert_file, api_key, and hook_url arguments"
        )
    if argv[2] != "file-bound":
        raise IntegrationError(
            "ossec.conf api_key must be the non-secret file-bound custody marker"
        )

    alert_file = Path(argv[1])
    hook_url = validate_https_url(argv[3])
    expected_hook_url = _require_string(
        environ.get("AEGISOPS_WAZUH_INGEST_URL"),
        "AEGISOPS_WAZUH_INGEST_URL",
    )
    if hook_url != expected_hook_url:
        raise IntegrationError("Integrator hook_url does not match the reviewed runtime URL")
    secret_file = Path(
        _require_string(
            environ.get("AEGISOPS_WAZUH_INGEST_SHARED_SECRET_FILE"),
            "AEGISOPS_WAZUH_INGEST_SHARED_SECRET_FILE",
        )
    )
    ca_file = Path(
        _require_string(
            environ.get("AEGISOPS_WAZUH_INGEST_CA_FILE"),
            "AEGISOPS_WAZUH_INGEST_CA_FILE",
        )
    )
    allowed_rule_id = _require_string(
        environ.get("AEGISOPS_WAZUH_ALLOWED_RULE_ID"),
        "AEGISOPS_WAZUH_ALLOWED_RULE_ID",
    )
    receipt_file = Path(
        _require_string(
            environ.get("AEGISOPS_WAZUH_RECEIPT_FILE"),
            "AEGISOPS_WAZUH_RECEIPT_FILE",
        )
    )
    try:
        timeout_seconds = int(
            environ.get(
                "AEGISOPS_WAZUH_HTTP_TIMEOUT_SECONDS",
                str(DEFAULT_TIMEOUT_SECONDS),
            )
        )
    except ValueError as exc:
        raise IntegrationError("AEGISOPS_WAZUH_HTTP_TIMEOUT_SECONDS must be an integer") from exc

    native_alert = load_native_alert(alert_file)
    mapped_alert = map_native_alert(
        native_alert,
        allowed_rule_id=allowed_rule_id,
    )
    status, response_payload = post_mapped_alert(
        hook_url=hook_url,
        shared_secret=load_secret(secret_file),
        ca_file=ca_file,
        mapped_alert=mapped_alert,
        timeout_seconds=timeout_seconds,
    )
    receipt = build_receipt(
        native_alert_id=_require_string(native_alert.get("id"), "id"),
        status=status,
        response_payload=response_payload,
    )
    append_receipt(receipt_file, receipt)
    return receipt


def main() -> int:
    try:
        receipt = run(sys.argv, os.environ)
    except IntegrationError as exc:
        print(f"custom-aegisops: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "schema_version": receipt["schema_version"],
                "native_wazuh_alert_id": receipt["native_wazuh_alert_id"],
                "http_status": receipt["http_status"],
                "disposition": receipt["disposition"],
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
