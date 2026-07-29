from __future__ import annotations

import json
import pathlib
import sys
from typing import NoReturn
from uuid import UUID


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def require_reviewed_subset(
    expected: object,
    observed: object,
    path: str,
) -> None:
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            fail(f"{path}: expected an object")
        for key, expected_value in expected.items():
            if key not in observed:
                if expected_value in ([], {}):
                    continue
                fail(f"{path}: missing reviewed field {key!r}")
            require_reviewed_subset(
                expected_value,
                observed[key],
                f"{path}.{key}",
            )
        return
    if isinstance(expected, list):
        if not isinstance(observed, list) or len(observed) != len(expected):
            fail(f"{path}: reviewed array length changed")
        for index, (expected_value, observed_value) in enumerate(
            zip(expected, observed)
        ):
            require_reviewed_subset(
                expected_value,
                observed_value,
                f"{path}[{index}]",
            )
        return
    if type(expected) is not type(observed) or expected != observed:
        fail(f"{path}: reviewed value changed")


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

    expected["id"] = workflow_id
    for action in expected.get("actions", []):
        if isinstance(action, dict):
            # Shuffle rewrites canvas coordinates while preserving execution semantics.
            action.pop("position", None)
    require_reviewed_subset(expected, observed, "$")
    print("PASS: preserved Shuffle workflow matches reviewed execution semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
