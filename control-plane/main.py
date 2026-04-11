#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from typing import Mapping, Sequence, TextIO
from urllib.parse import parse_qs, urlsplit

from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    build_runtime_service,
)

MAX_WAZUH_INGEST_BODY_BYTES = 1_048_576


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the reviewed control-plane runtime service or render read-only "
            "runtime, record, and reconciliation inspection views."
        )
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "serve",
        help="Run the reviewed long-running control-plane runtime service.",
    )
    subparsers.add_parser("runtime", help="Render the current runtime snapshot.")

    inspect_records = subparsers.add_parser(
        "inspect-records",
        help="Render a read-only view of one control-plane record family.",
    )
    inspect_records.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to inspect.",
    )

    subparsers.add_parser(
        "inspect-reconciliation-status",
        help="Render a read-only reconciliation status summary.",
    )
    subparsers.add_parser(
        "inspect-analyst-queue",
        help="Render the business-hours analyst review queue view.",
    )
    inspect_alert_detail = subparsers.add_parser(
        "inspect-alert-detail",
        help="Render the reviewed Wazuh-backed alert detail view for one alert.",
    )
    inspect_alert_detail.add_argument(
        "--alert-id",
        required=True,
        help="Control-plane alert identifier to inspect.",
    )
    inspect_assistant_context = subparsers.add_parser(
        "inspect-assistant-context",
        help="Render a read-only analyst-assistant context view for one record.",
    )
    inspect_assistant_context.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to inspect for assistant context.",
    )
    inspect_assistant_context.add_argument(
        "--record-id",
        required=True,
        help="Control-plane record identifier to inspect for assistant context.",
    )
    inspect_advisory_output = subparsers.add_parser(
        "inspect-advisory-output",
        help="Render the cited advisory-output contract for one reviewed record.",
    )
    inspect_advisory_output.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to inspect for advisory output.",
    )
    inspect_advisory_output.add_argument(
        "--record-id",
        required=True,
        help="Control-plane record identifier to inspect for advisory output.",
    )
    render_recommendation_draft = subparsers.add_parser(
        "render-recommendation-draft",
        help="Render cited recommendation-draft output for one reviewed record.",
    )
    render_recommendation_draft.add_argument(
        "--family",
        required=True,
        help="Control-plane record family to render for recommendation drafting.",
    )
    render_recommendation_draft.add_argument(
        "--record-id",
        required=True,
        help="Control-plane record identifier to render for recommendation drafting.",
    )
    return parser


def run_control_plane_service(
    service: AegisOpsControlPlaneService,
    *,
    stderr: TextIO | None = None,
) -> int:
    service.validate_wazuh_ingest_runtime()
    runtime_snapshot = service.describe_runtime().to_dict()
    stderr = stderr or sys.stderr

    class _RequestHandler(BaseHTTPRequestHandler):
        server_version = "AegisOpsControlPlane/1.0"

        def do_GET(self) -> None:  # noqa: N802
            request_target = urlsplit(self.path)
            request_path = request_target.path

            if request_path == "/healthz":
                self._write_json(
                    HTTPStatus.OK,
                    {
                        "service_name": runtime_snapshot["service_name"],
                        "status": "ok",
                    },
                )
                return

            if request_path == "/readyz":
                self._write_json(
                    HTTPStatus.OK,
                    {
                        "service_name": runtime_snapshot["service_name"],
                        "status": "ready",
                        "persistence_mode": runtime_snapshot["persistence_mode"],
                    },
                )
                return

            if request_path == "/runtime":
                self._write_json(HTTPStatus.OK, service.describe_runtime().to_dict())
                return

            if request_path == "/inspect-records":
                family = parse_qs(request_target.query).get("family", [""])[0]
                if not family:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": "family query parameter is required",
                        },
                    )
                    return

                try:
                    payload = service.inspect_records(family).to_dict()
                except ValueError as exc:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, payload)
                return

            if request_path == "/inspect-reconciliation-status":
                self._write_json(
                    HTTPStatus.OK,
                    service.inspect_reconciliation_status().to_dict(),
                )
                return

            if request_path == "/inspect-analyst-queue":
                self._write_json(HTTPStatus.OK, service.inspect_analyst_queue().to_dict())
                return

            if request_path == "/inspect-alert-detail":
                alert_id = parse_qs(request_target.query).get("alert_id", [""])[0]
                if not alert_id:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": "invalid_request",
                            "message": "alert_id query parameter is required",
                        },
                    )
                    return
                try:
                    payload = service.inspect_alert_detail(alert_id).to_dict()
                except LookupError as exc:
                    self._write_json(
                        HTTPStatus.NOT_FOUND,
                        {
                            "error": "not_found",
                            "message": str(exc),
                        },
                    )
                    return
                self._write_json(HTTPStatus.OK, payload)
                return

            self._write_json(
                HTTPStatus.NOT_FOUND,
                {
                    "error": "not_found",
                    "path": request_path,
                },
            )

        def do_POST(self) -> None:  # noqa: N802
            request_target = urlsplit(self.path)
            request_path = request_target.path

            if request_path != "/intake/wazuh":
                self._write_json(
                    HTTPStatus.NOT_FOUND,
                    {
                        "error": "not_found",
                        "path": request_path,
                    },
                )
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "invalid_request",
                        "message": "Content-Length must be an integer",
                    },
                )
                return
            if content_length <= 0:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "invalid_request",
                        "message": "request body is required",
                    },
                )
                return
            if content_length > MAX_WAZUH_INGEST_BODY_BYTES:
                self._write_json(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    {
                        "error": "request_too_large",
                        "message": "request body exceeds the reviewed Wazuh ingest size limit",
                    },
                )
                return

            try:
                raw_payload = self.rfile.read(content_length).decode("utf-8")
            except UnicodeDecodeError:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "invalid_request",
                        "message": "request body must be valid UTF-8 JSON",
                    },
                )
                return

            try:
                alert = json.loads(raw_payload)
            except json.JSONDecodeError as exc:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "invalid_request",
                        "message": f"request body must be valid JSON: {exc.msg}",
                    },
                )
                return

            try:
                ingest_result = service.ingest_wazuh_alert(
                    raw_alert=alert,
                    authorization_header=self.headers.get("Authorization"),
                    forwarded_proto=self.headers.get("X-Forwarded-Proto"),
                    reverse_proxy_secret_header=self.headers.get(
                        "X-AegisOps-Proxy-Secret"
                    ),
                    peer_addr=self.client_address[0] if self.client_address else None,
                )
            except PermissionError as exc:
                self._write_json(
                    HTTPStatus.FORBIDDEN,
                    {
                        "error": "forbidden",
                        "message": str(exc),
                    },
                )
                return
            except ValueError as exc:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "invalid_request",
                        "message": str(exc),
                    },
                )
                return

            self._write_json(
                HTTPStatus.ACCEPTED,
                {
                    "disposition": ingest_result.disposition,
                    "finding_id": ingest_result.alert.finding_id,
                    "alert": _json_ready(ingest_result.alert),
                    "reconciliation": _json_ready(ingest_result.reconciliation),
                },
            )

        def log_message(self, format: str, *args: object) -> None:
            print(
                "%s - - [%s] %s"
                % (
                    self.address_string(),
                    self.log_date_time_string(),
                    format % args,
                ),
                file=stderr,
            )

        def _write_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
            body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(
        (str(runtime_snapshot["bind_host"]), int(runtime_snapshot["bind_port"])),
        _RequestHandler,
    )

    try:
        server.serve_forever()
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


def _json_ready(value: object) -> object:
    if is_dataclass(value):
        raw = {
            field.name: getattr(value, field.name)
            for field in fields(value)
        }
    else:
        raw = value
    if isinstance(raw, Mapping):
        return {str(key): _json_ready(item) for key, item in raw.items()}
    if isinstance(raw, dict):
        return {key: _json_ready(item) for key, item in raw.items()}
    if isinstance(raw, tuple):
        return [_json_ready(item) for item in raw]
    if isinstance(raw, list):
        return [_json_ready(item) for item in raw]
    if hasattr(raw, "isoformat"):
        try:
            return raw.isoformat()
        except TypeError:
            return raw
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    return raw


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    service: AegisOpsControlPlaneService | None = None,
) -> int:
    parser = _build_parser()
    parsed = parser.parse_args(list(argv) if argv is not None else None)
    command = parsed.command or "runtime"
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    service = service or build_runtime_service()

    if command == "serve":
        return run_control_plane_service(service, stderr=stderr)
    if command == "runtime":
        payload = service.describe_runtime().to_dict()
    else:
        if command == "inspect-records":
            try:
                payload = service.inspect_records(parsed.family).to_dict()
            except ValueError as exc:
                parser.error(str(exc))
        elif command == "inspect-assistant-context":
            try:
                payload = service.inspect_assistant_context(
                    parsed.family,
                    parsed.record_id,
                ).to_dict()
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "inspect-advisory-output":
            try:
                payload = service.inspect_advisory_output(
                    parsed.family,
                    parsed.record_id,
                ).to_dict()
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "render-recommendation-draft":
            try:
                payload = service.render_recommendation_draft(
                    parsed.family,
                    parsed.record_id,
                ).to_dict()
            except (LookupError, ValueError) as exc:
                parser.error(str(exc))
        elif command == "inspect-reconciliation-status":
            payload = service.inspect_reconciliation_status().to_dict()
        elif command == "inspect-analyst-queue":
            payload = service.inspect_analyst_queue().to_dict()
        elif command == "inspect-alert-detail":
            try:
                payload = service.inspect_alert_detail(parsed.alert_id).to_dict()
            except LookupError as exc:
                parser.error(str(exc))
        else:
            raise AssertionError(f"Unhandled command: {command}")

    print(json.dumps(payload, indent=2, sort_keys=True), file=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
