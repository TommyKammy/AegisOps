#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence, TextIO

from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    build_runtime_service,
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

    service = service or build_runtime_service()

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
