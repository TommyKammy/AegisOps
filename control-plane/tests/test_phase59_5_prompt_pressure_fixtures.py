from __future__ import annotations

import json
import pathlib
import sys
import unittest


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parents[0]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.assistant.assistant_context import (
    _advisory_text_claims_authority_or_scope_expansion,
)
from aegisops.control_plane.assistant.live_assistant_workflow import (
    phase24_live_assistant_prompt_injection_flags,
    phase24_live_assistant_unresolved_reasons,
)


FIXTURE_PATH = (
    TESTS_ROOT
    / "fixtures"
    / "phase59"
    / "prompt-pressure-negative-fixtures.json"
)


class Phase595PromptPressureFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_cases_have_explicit_reviewable_failure_reasons(self) -> None:
        self.assertEqual(
            self.fixture["fixture_family"],
            "phase59_prompt_pressure_negative",
        )

        for fixture_case in self.fixture["cases"]:
            with self.subTest(case_id=fixture_case["case_id"]):
                flags = self._flags_for_fixture_case(fixture_case)

                self.assertEqual(
                    tuple(flags),
                    tuple(fixture_case["expected_flags"]),
                )
                self.assertTrue(
                    phase24_live_assistant_unresolved_reasons(tuple(flags)),
                    msg=(
                        f"{fixture_case['case_id']} must produce an explicit "
                        "operator-reviewable unresolved reason"
                    ),
                )

    def test_prompt_pressure_fixtures_do_not_use_workstation_paths_or_secrets(
        self,
    ) -> None:
        serialized = FIXTURE_PATH.read_text(encoding="utf-8")
        mac_home = "/" + "/".join(("Users", ""))
        unix_home = "/" + "/".join(("home", ""))
        windows_home = "C:" + "\\".join(("", "Users", ""))

        self.assertNotIn(mac_home, serialized)
        self.assertNotIn(unix_home, serialized)
        self.assertNotIn(windows_home, serialized)
        self.assertNotIn("sk-", serialized)
        self.assertNotIn("token=", serialized.lower())

    @staticmethod
    def _flags_for_fixture_case(fixture_case: dict[str, object]) -> tuple[str, ...]:
        prompt_text = fixture_case["prompt_text"]
        surface = fixture_case["surface"]
        if surface == "live_assistant_output":
            return phase24_live_assistant_prompt_injection_flags(prompt_text)
        if surface == "advisory_text":
            return _advisory_text_claims_authority_or_scope_expansion(prompt_text)
        raise AssertionError(f"unknown fixture surface: {surface!r}")


if __name__ == "__main__":
    unittest.main()
