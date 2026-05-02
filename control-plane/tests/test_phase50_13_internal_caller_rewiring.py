from __future__ import annotations

import ast
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase5013InternalCallerRewiringTests(unittest.TestCase):
    def _path(self, relative_path: str) -> pathlib.Path:
        path = REPO_ROOT / relative_path
        if path.exists():
            return path
        canonical_relative_path = relative_path.replace(
            "control-plane/aegisops_control_plane/",
            "control-plane/aegisops/control_plane/",
            1,
        )
        return REPO_ROOT / canonical_relative_path

    def _service_facade_delegate_calls(
        self,
        relative_path: str,
        forbidden_methods: set[str],
    ) -> list[str]:
        source = self._path(relative_path).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative_path)
        calls: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            if not isinstance(function, ast.Attribute):
                continue
            value = function.value
            if (
                isinstance(value, ast.Attribute)
                and value.attr == "_service"
                and isinstance(value.value, ast.Name)
                and value.value.id == "self"
                and function.attr in forbidden_methods
            ):
                calls.append(f"{relative_path}:{node.lineno}:{function.attr}")
        return calls

    def test_internal_focus_modules_do_not_call_public_facade_delegates(self) -> None:
        forbidden_methods = {
            "inspect_assistant_context",
            "list_lifecycle_transitions",
            "render_recommendation_draft",
        }
        focused_modules = (
            "control-plane/aegisops_control_plane/assistant/assistant_context.py",
            "control-plane/aegisops_control_plane/actions/execution_coordinator_action_requests.py",
            "control-plane/aegisops_control_plane/assistant/live_assistant_workflow.py",
            "control-plane/aegisops_control_plane/operator_inspection.py",
        )

        calls = [
            call
            for relative_path in focused_modules
            for call in self._service_facade_delegate_calls(
                relative_path,
                forbidden_methods,
            )
        ]

        self.assertEqual(
            calls,
            [],
            "focused internal services must call owning collaborators or stores directly",
        )


if __name__ == "__main__":
    unittest.main()
