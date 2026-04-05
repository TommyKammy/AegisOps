#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence, TextIO

from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    build_runtime_service,
    build_runtime_snapshot,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render read-only control-plane runtime, record, and reconciliation "
            "inspection views."
        )
    )
    subparsers = parser.add_subparsers(dest="command")

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
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    service: AegisOpsControlPlaneService | None = None,
) -> int:
    parser = _build_parser()
    parsed = parser.parse_args(list(argv) if argv is not None else None)
    command = parsed.command or "runtime"
    stdout = stdout or sys.stdout

    if command == "runtime":
        payload = build_runtime_snapshot().to_dict()
    else:
        using_runtime_service = service is None
        service = service or build_runtime_service()
        if using_runtime_service and service.describe_runtime().persistence_mode == "in_memory":
            parser.error(
                "read-only inspection commands require a persisted control-plane store; "
                "current runtime uses persistence_mode='in_memory'"
            )
        if command == "inspect-records":
            try:
                payload = service.inspect_records(parsed.family).to_dict()
            except ValueError as exc:
                parser.error(str(exc))
        elif command == "inspect-reconciliation-status":
            payload = service.inspect_reconciliation_status().to_dict()
        else:
            raise AssertionError(f"Unhandled command: {command}")

    print(json.dumps(payload, indent=2, sort_keys=True), file=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
