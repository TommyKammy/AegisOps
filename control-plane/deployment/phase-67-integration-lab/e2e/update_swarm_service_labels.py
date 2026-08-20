#!/usr/bin/env python3

from __future__ import annotations

import argparse
from copy import deepcopy
import http.client
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
from typing import Any, Mapping
from urllib.parse import quote, urlencode


API_VERSION = "1.40"
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
SERVICE_ID_PATTERN = re.compile(r"^[a-z0-9]{12,64}$")
IMMUTABLE_IMAGE_PATTERN = re.compile(
    r"^[^\s@]+@sha256:[0-9a-f]{64}$"
)
CONTEXT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class SwarmLabelUpdateError(RuntimeError):
    pass


class UnixSocketHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: Path, timeout: float) -> None:
        super().__init__("localhost", timeout=timeout)
        self.socket_path = socket_path

    def connect(self) -> None:
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(self.timeout)
        connection.connect(os.fspath(self.socket_path))
        self.sock = connection


class DockerEngineAPI:
    def __init__(self, socket_path: Path, timeout: float = 30.0) -> None:
        self.socket_path = socket_path
        self.timeout = timeout

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Any:
        body = None
        headers: dict[str, str] = {}
        if payload is not None:
            body = json.dumps(
                payload,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8")
            headers["Content-Type"] = "application/json"

        connection = UnixSocketHTTPConnection(self.socket_path, self.timeout)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            response_body = response.read(MAX_RESPONSE_BYTES + 1)
        except (OSError, TimeoutError, http.client.HTTPException) as exc:
            raise SwarmLabelUpdateError(
                f"Docker Engine {method} {path} failed: {exc}"
            ) from exc
        finally:
            connection.close()

        if len(response_body) > MAX_RESPONSE_BYTES:
            raise SwarmLabelUpdateError(
                f"Docker Engine {method} {path} exceeded the response limit"
            )
        decoded: Any = None
        if response_body:
            try:
                decoded = json.loads(response_body)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise SwarmLabelUpdateError(
                    f"Docker Engine {method} {path} returned invalid JSON"
                ) from exc
        if not 200 <= response.status < 300:
            message = (
                decoded.get("message")
                if isinstance(decoded, dict)
                else response_body.decode("utf-8", errors="replace")
            )
            raise SwarmLabelUpdateError(
                f"Docker Engine {method} {path} returned HTTP "
                f"{response.status}: {message or response.reason}"
            )
        return decoded

    def assert_api_version_supported(self) -> None:
        version = _require_mapping(self._request_json("GET", "/version"), "version")
        daemon_max = _parse_api_version(version.get("ApiVersion"), "ApiVersion")
        daemon_min = _parse_api_version(
            version.get("MinAPIVersion"),
            "MinAPIVersion",
        )
        required = _parse_api_version(API_VERSION, "required API version")
        if not daemon_min <= required <= daemon_max:
            raise SwarmLabelUpdateError(
                f"Docker Engine API v{API_VERSION} is outside daemon range "
                f"{daemon_min[0]}.{daemon_min[1]}-"
                f"{daemon_max[0]}.{daemon_max[1]}"
            )

    def get_service(self, service_id: str) -> Mapping[str, Any]:
        path = f"/v{API_VERSION}/services/{quote(service_id, safe='')}"
        return _require_mapping(self._request_json("GET", path), "service")

    def update_service(
        self,
        service_id: str,
        version: int,
        spec: Mapping[str, Any],
    ) -> None:
        query = urlencode({"version": version})
        path = (
            f"/v{API_VERSION}/services/{quote(service_id, safe='')}/update?"
            f"{query}"
        )
        result = self._request_json("POST", path, spec)
        if result is None:
            return
        response = _require_mapping(result, "service update response")
        warnings = response.get("Warnings")
        if warnings not in (None, []):
            raise SwarmLabelUpdateError(
                f"Docker Engine service update returned warnings: {warnings}"
            )


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise SwarmLabelUpdateError(f"Docker Engine {field} must be an object")
    return value


def _parse_api_version(value: Any, field: str) -> tuple[int, int]:
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+", value):
        raise SwarmLabelUpdateError(f"Docker Engine {field} is invalid")
    major, minor = value.split(".", 1)
    return int(major), int(minor)


def _service_state(
    service: Mapping[str, Any],
    *,
    expected_id: str,
    expected_name: str,
    expected_image: str,
) -> tuple[int, dict[str, Any], dict[str, str]]:
    if service.get("ID") != expected_id:
        raise SwarmLabelUpdateError("Shuffle service ID changed")
    version = _require_mapping(service.get("Version"), "service Version").get(
        "Index"
    )
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise SwarmLabelUpdateError("Shuffle service version is invalid")
    spec = deepcopy(dict(_require_mapping(service.get("Spec"), "service Spec")))
    if spec.get("Name") != expected_name:
        raise SwarmLabelUpdateError("Shuffle service name changed")
    task_template = _require_mapping(
        spec.get("TaskTemplate"),
        "service TaskTemplate",
    )
    container_spec = _require_mapping(
        task_template.get("ContainerSpec"),
        "service ContainerSpec",
    )
    if container_spec.get("Image") != expected_image:
        raise SwarmLabelUpdateError(
            "Shuffle service image does not match the expected reference"
        )
    raw_labels = spec.get("Labels", {})
    if not isinstance(raw_labels, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in raw_labels.items()
    ):
        raise SwarmLabelUpdateError("Shuffle service labels are invalid")
    return version, spec, dict(raw_labels)


def claim_service_labels(
    api: DockerEngineAPI,
    *,
    service_id: str,
    expected_version: int,
    expected_name: str,
    expected_image: str,
    labels: Mapping[str, str],
) -> Mapping[str, Any]:
    if not labels or not all(
        isinstance(key, str)
        and bool(key)
        and isinstance(value, str)
        and not any(ord(character) < 32 for character in key + value)
        for key, value in labels.items()
    ):
        raise SwarmLabelUpdateError("ownership labels are invalid")
    api.assert_api_version_supported()
    before = api.get_service(service_id)
    version, before_spec, before_labels = _service_state(
        before,
        expected_id=service_id,
        expected_name=expected_name,
        expected_image=expected_image,
    )
    if version != expected_version:
        raise SwarmLabelUpdateError(
            "Shuffle service changed before ownership could be claimed"
        )
    conflicting_keys = sorted(set(before_labels).intersection(labels))
    if conflicting_keys:
        raise SwarmLabelUpdateError(
            "Shuffle service already carries ownership labels: "
            + ", ".join(conflicting_keys)
        )

    expected_labels = {**before_labels, **labels}
    updated_spec = deepcopy(before_spec)
    updated_spec["Labels"] = expected_labels
    before_nonlabel_spec = deepcopy(before_spec)
    before_nonlabel_spec.pop("Labels", None)
    updated_nonlabel_spec = deepcopy(updated_spec)
    updated_nonlabel_spec.pop("Labels", None)
    if updated_nonlabel_spec != before_nonlabel_spec:
        raise SwarmLabelUpdateError(
            "ownership update attempted to change the service specification"
        )

    api.update_service(service_id, version, updated_spec)
    after = api.get_service(service_id)
    after_version, after_spec, after_labels = _service_state(
        after,
        expected_id=service_id,
        expected_name=expected_name,
        expected_image=expected_image,
    )
    if after_version <= version:
        raise SwarmLabelUpdateError(
            "Shuffle service version did not advance after ownership update"
        )
    if after_labels != expected_labels:
        raise SwarmLabelUpdateError(
            "Shuffle service did not retain the exact ownership labels"
        )
    after_nonlabel_spec = deepcopy(after_spec)
    after_nonlabel_spec.pop("Labels", None)
    if after_nonlabel_spec != before_nonlabel_spec:
        raise SwarmLabelUpdateError(
            "Shuffle service changed outside ownership labels"
        )
    return {
        "service_id": service_id,
        "version_before": version,
        "version_after": after_version,
        "labels": expected_labels,
    }


def resolve_docker_socket(context: str) -> Path:
    if not CONTEXT_NAME_PATTERN.fullmatch(context):
        raise SwarmLabelUpdateError("Docker context name is invalid")
    try:
        completed = subprocess.run(
            ["docker", "context", "inspect", context],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SwarmLabelUpdateError(
            f"cannot inspect Docker context {context}: {exc}"
        ) from exc
    if completed.returncode != 0:
        diagnostic = completed.stderr.strip() or completed.stdout.strip()
        raise SwarmLabelUpdateError(
            f"cannot inspect Docker context {context}: {diagnostic}"
        )
    try:
        contexts = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SwarmLabelUpdateError(
            f"Docker context {context} returned invalid JSON"
        ) from exc
    if not isinstance(contexts, list) or len(contexts) != 1:
        raise SwarmLabelUpdateError(
            f"Docker context {context} did not resolve uniquely"
        )
    metadata = _require_mapping(contexts[0], "context metadata")
    if metadata.get("Name") != context:
        raise SwarmLabelUpdateError("Docker context identity changed")
    endpoints = _require_mapping(metadata.get("Endpoints"), "context Endpoints")
    docker_endpoint = _require_mapping(
        endpoints.get("docker"),
        "context Docker endpoint",
    )
    host = docker_endpoint.get("Host")
    if not isinstance(host, str) or not host.startswith("unix:///"):
        raise SwarmLabelUpdateError(
            "Phase 67.4 requires a local Unix-socket Docker context"
        )
    socket_path = Path(host.removeprefix("unix://")).resolve(strict=True)
    if not socket_path.is_absolute() or not stat.S_ISSOCK(socket_path.stat().st_mode):
        raise SwarmLabelUpdateError(
            f"Docker context endpoint is not a Unix socket: {socket_path}"
        )
    return socket_path


def _parse_label(raw: str) -> tuple[str, str]:
    key, separator, value = raw.partition("=")
    if not separator or not key or any(ord(character) < 32 for character in raw):
        raise argparse.ArgumentTypeError("labels must use non-empty key=value form")
    return key, value


def _positive_timeout(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be numeric") from exc
    if not 0 < value <= 120:
        raise argparse.ArgumentTypeError("timeout must be between 0 and 120 seconds")
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Claim a Shuffle-created service without migrating its legacy "
            "Swarm network specification. Callers that admit an observed "
            "tag-only image reference must independently verify the running "
            "task's runtime image ID before and after this helper runs."
        )
    )
    parser.add_argument("--docker-context", required=True)
    parser.add_argument("--service-id", required=True)
    parser.add_argument("--expected-version", required=True, type=int)
    parser.add_argument("--expected-name", required=True)
    parser.add_argument("--expected-image", required=True)
    parser.add_argument(
        "--allow-observed-image-reference-after-runtime-id-verification",
        action="store_true",
        help=(
            "admit the exact observed service image string when the caller "
            "has already verified the running task image ID against a "
            "reviewed digest and will verify it again after the update"
        ),
    )
    parser.add_argument(
        "--label",
        action="append",
        required=True,
        type=_parse_label,
        metavar="KEY=VALUE",
    )
    parser.add_argument("--timeout", type=_positive_timeout, default=30.0)
    args = parser.parse_args(argv)
    if not SERVICE_ID_PATTERN.fullmatch(args.service_id):
        parser.error("--service-id is not a Swarm service ID")
    if args.expected_version < 1:
        parser.error("--expected-version must be positive")
    if (
        not args.allow_observed_image_reference_after_runtime_id_verification
        and not IMMUTABLE_IMAGE_PATTERN.fullmatch(args.expected_image)
    ):
        parser.error("--expected-image must be a digest-pinned image reference")
    if (
        args.allow_observed_image_reference_after_runtime_id_verification
        and (
            not isinstance(args.expected_image, str)
            or not args.expected_image
            or any(character.isspace() for character in args.expected_image)
        )
    ):
        parser.error("--expected-image must be an observed image reference")
    label_keys = [key for key, _ in args.label]
    if len(label_keys) != len(set(label_keys)):
        parser.error("--label keys must be unique")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        socket_path = resolve_docker_socket(args.docker_context)
        result = claim_service_labels(
            DockerEngineAPI(socket_path, timeout=args.timeout),
            service_id=args.service_id,
            expected_version=args.expected_version,
            expected_name=args.expected_name,
            expected_image=args.expected_image,
            labels=dict(args.label),
        )
    except (OSError, ValueError, SwarmLabelUpdateError) as exc:
        print(f"Swarm ownership update failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
