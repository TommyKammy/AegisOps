#!/usr/bin/env python3

from __future__ import annotations

from http.server import ThreadingHTTPServer
import json
import sys
from typing import Sequence, TextIO

from aegisops.control_plane.api import cli, http_surface
from aegisops.control_plane.api.entrypoint_support import (
    MAX_WAZUH_INGEST_BODY_BYTES,
    read_json_file as _read_json_file,
    require_loopback_operator_request as _require_loopback_operator_request,
)
from aegisops.control_plane.service import (
    AegisOpsControlPlaneService,
    build_runtime_service,
)


def run_control_plane_service(
    service: AegisOpsControlPlaneService,
    *,
    stderr: TextIO | None = None,
) -> int:
    return http_surface.run_control_plane_service(
        service,
        stderr=stderr,
        server_class=ThreadingHTTPServer,
        require_loopback_operator_request_fn=_require_loopback_operator_request,
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    service: AegisOpsControlPlaneService | None = None,
) -> int:
    parser = cli.build_parser()
    parsed = parser.parse_args(list(argv) if argv is not None else None)
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    service = service or build_runtime_service()

    if (parsed.command or "runtime") == "serve":
        return run_control_plane_service(service, stderr=stderr)

    payload = cli.run_command(
        parsed,
        service=service,
        parser=parser,
        read_json_file_fn=_read_json_file,
    )
    print(json.dumps(payload, indent=2, sort_keys=True), file=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
