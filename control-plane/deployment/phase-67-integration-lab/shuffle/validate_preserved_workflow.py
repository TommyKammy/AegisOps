from __future__ import annotations

import json
import pathlib
import sys
from typing import NoReturn
from uuid import UUID


_ROOT_SERVER_METADATA_FIELDS = frozenset(
    {
        "backup_config",
        "blogpost",
        "categories",
        "comments",
        "contact_info",
        "created",
        "due_date",
        "edited",
        "execution_org",
        "form_control",
        "input_questions",
        "last_runtime",
        "org_id",
        "owner",
        "previously_saved",
        "published_id",
        "revision_id",
        "updated_by",
        "usecase_ids",
        "validated",
        "validation",
        "video",
    }
)
_ROOT_SERVER_DEFAULTS = {
    "auth_groups": None,
    "background_processing": False,
    "childorg_workflow_ids": None,
    "configuration": {
        "exit_on_error": False,
        "skip_notifications": False,
        "start_from_top": False,
    },
    "default_return_value": "",
    "example_argument": "",
    "execution_environment": "",
    "generated": False,
    "hidden": False,
    "parentorg_workflow": "",
    "public": False,
    "sharing": "private",
    "status": "test",
    "suborg_distribution": [],
    "visual_branches": None,
    "workflow_as_code": False,
    "workflow_type": "",
}
_ACTION_SERVER_DEFAULTS = {
    "authentication_id": "",
    "category": "",
    "category_label": None,
    "description": "",
    "execution_delay": 0,
    "execution_variable": {
        "description": "",
        "id": "",
        "name": "",
        "value": "",
    },
    "generated": False,
    "isStartNode": True,
    "parent_controlled": False,
    "public": True,
    "reference_url": "",
    "run_magic_input": False,
    "run_magic_output": False,
    "sharing": True,
    "source_execution": "",
    "source_workflow": "",
    "sub_action": False,
    "suggestion": False,
}
_PARAMETER_SERVER_DEFAULTS = {
    "action_field": "",
    "configuration": False,
    "custom_value": False,
    "description": "",
    "error": "",
    "example": "",
    "hidden": False,
    "id": "",
    "multiline": False,
    "multiselect": False,
    "options": None,
    "required": False,
    "schema": {"type": ""},
    "skip_multicheck": False,
    "tags": None,
    "unique_toggled": False,
    "value_replace": None,
}


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def json_equal(left: object, right: object) -> bool:
    try:
        return json.dumps(
            left,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ) == json.dumps(
            right,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError):
        return False


def strip_server_fields(
    value: dict[str, object],
    *,
    metadata_fields: frozenset[str],
    default_fields: dict[str, object],
    path: str,
) -> None:
    for field_name in metadata_fields:
        value.pop(field_name, None)
    for field_name, expected_default in default_fields.items():
        if field_name not in value:
            continue
        if not json_equal(value[field_name], expected_default):
            fail(f"{path}.{field_name}: Shuffle server default changed")
        value.pop(field_name)


def normalize_server_fields(
    expected: dict[str, object],
    observed: dict[str, object],
) -> None:
    strip_server_fields(
        observed,
        metadata_fields=_ROOT_SERVER_METADATA_FIELDS,
        default_fields=_ROOT_SERVER_DEFAULTS,
        path="$",
    )
    expected_actions = expected.get("actions")
    observed_actions = observed.get("actions")
    if not isinstance(expected_actions, list) or not isinstance(observed_actions, list):
        return
    for expected_action, observed_action in zip(expected_actions, observed_actions):
        if not isinstance(expected_action, dict) or not isinstance(observed_action, dict):
            continue
        # Shuffle rewrites canvas coordinates while preserving execution semantics.
        expected_action.pop("position", None)
        observed_action.pop("position", None)
        strip_server_fields(
            observed_action,
            metadata_fields=frozenset(),
            default_fields=_ACTION_SERVER_DEFAULTS,
            path="$.actions[]",
        )
        expected_parameters = expected_action.get("parameters")
        observed_parameters = observed_action.get("parameters")
        if not isinstance(expected_parameters, list) or not isinstance(
            observed_parameters,
            list,
        ):
            continue
        for observed_parameter in observed_parameters:
            if isinstance(observed_parameter, dict):
                strip_server_fields(
                    observed_parameter,
                    metadata_fields=frozenset(),
                    default_fields=_PARAMETER_SERVER_DEFAULTS,
                    path="$.actions[].parameters[]",
                )


def require_reviewed_definition(
    expected: object,
    observed: object,
    path: str,
) -> None:
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            fail(f"{path}: expected an object")
        unexpected = sorted(set(observed) - set(expected))
        if unexpected:
            fail(f"{path}: unreviewed properties {unexpected!r}")
        for key, expected_value in expected.items():
            if key not in observed:
                if expected_value in ([], {}):
                    continue
                fail(f"{path}: missing reviewed field {key!r}")
            require_reviewed_definition(
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
            require_reviewed_definition(
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
    normalize_server_fields(expected, observed)
    require_reviewed_definition(expected, observed, "$")
    print("PASS: preserved Shuffle workflow matches reviewed execution semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
