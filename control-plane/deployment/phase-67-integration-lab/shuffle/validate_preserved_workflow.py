from __future__ import annotations
# ruff: noqa: E402

import json
import pathlib
import sys
from typing import NoReturn
from uuid import UUID

CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.adapters.shuffle_workflow_contract import (
    validate_reviewed_workflow,
)


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def main() -> int:
    if len(sys.argv) != 3:
        fail(
            "usage: validate_preserved_workflow.py "
            "<reviewed-template> <runtime-workflow-id>"
        )
    template_path = pathlib.Path(sys.argv[1])
    workflow_id = str(UUID(sys.argv[2]))
    expected = json.loads(template_path.read_text(encoding="utf-8"))
    observed = json.load(sys.stdin)
    if not isinstance(expected, dict) or not isinstance(observed, dict):
        fail("workflow definitions must be JSON objects")

    validate_reviewed_workflow(expected, observed, workflow_id)
    print("PASS: preserved Shuffle workflow matches reviewed execution semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
