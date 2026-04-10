#!/usr/bin/env python3

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from typing import Sequence, TextIO
from urllib.parse import parse_qs, urlsplit

from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    build_runtime_service,
)


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

            self._write_json(
                HTTPStatus.NOT_FOUND,
                {
                    "error": "not_found",
                    "path": request_path,
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
        else:
            raise AssertionError(f"Unhandled command: {command}")

    print(json.dumps(payload, indent=2, sort_keys=True), file=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
