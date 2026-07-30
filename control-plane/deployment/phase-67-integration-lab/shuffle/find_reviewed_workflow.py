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

NOT_FOUND_EXIT_CODE = 3


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def _has_reviewed_identity(
    expected: dict[str, object],
    observed: dict[str, object],
) -> bool:
    if observed.get("name") == expected.get("name"):
        return True
    expected_variables = expected.get("workflow_variables")
    observed_variables = observed.get("workflow_variables")
    if not isinstance(expected_variables, list) or not isinstance(
        observed_variables,
        list,
    ):
        return False
    expected_identity = {
        variable.get("name"): variable.get("value")
        for variable in expected_variables
        if isinstance(variable, dict)
    }
    observed_identity = {
        variable.get("name"): variable.get("value")
        for variable in observed_variables
        if isinstance(variable, dict)
    }
    return bool(expected_identity) and all(
        observed_identity.get(name) == value
        for name, value in expected_identity.items()
    )


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: find_reviewed_workflow.py <reviewed-template>")
    template_path = pathlib.Path(sys.argv[1])
    expected = json.loads(template_path.read_text(encoding="utf-8"))
    observed_workflows = json.load(sys.stdin)
    if not isinstance(expected, dict) or not isinstance(observed_workflows, list):
        fail("workflow discovery payload has an unexpected shape")

    candidates = [
        workflow
        for workflow in observed_workflows
        if isinstance(workflow, dict)
        and _has_reviewed_identity(expected, workflow)
    ]
    if not candidates:
        return NOT_FOUND_EXIT_CODE

    matches: list[str] = []
    for candidate in candidates:
        workflow_id = candidate.get("id")
        if not isinstance(workflow_id, str):
            fail("reviewed workflow candidate is missing its runtime id")
        workflow_id = str(UUID(workflow_id))
        validate_reviewed_workflow(expected, candidate, workflow_id)
        matches.append(workflow_id)
    if len(matches) != 1:
        fail("reviewed workflow identity must resolve to exactly one workflow")
    print(matches[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
