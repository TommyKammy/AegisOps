from __future__ import annotations

import json
import pathlib
import sys
import unittest


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parents[0]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.assistant.live_assistant_workflow import (
    phase24_live_assistant_unresolved_reasons,
)


FIXTURE_PATH = (
    TESTS_ROOT
    / "fixtures"
    / "phase59"
    / "stale-conflicting-evidence-ai-fixtures.json"
)


class Phase596StaleConflictingEvidenceFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_cases_force_uncertainty_and_review_needed_posture(self) -> None:
        self.assertEqual(
            self.fixture["fixture_family"],
            "phase59_stale_conflicting_evidence_ai",
        )

        expected_cases = {
            "phase59-stale-evidence-current-truth",
            "phase59-conflicting-evidence-truth-selection",
            "phase59-missing-citation-hidden",
            "phase59-outdated-source-health",
            "phase59-mismatched-record-family",
        }
        actual_cases = {fixture_case["case_id"] for fixture_case in self.fixture["cases"]}
        self.assertEqual(actual_cases, expected_cases)

        for fixture_case in self.fixture["cases"]:
            with self.subTest(case_id=fixture_case["case_id"]):
                flags = tuple(fixture_case["expected_uncertainty_flags"])
                unresolved_reasons = phase24_live_assistant_unresolved_reasons(flags)

                self.assertEqual(fixture_case["expected_status"], "unresolved")
                self.assertEqual(fixture_case["expected_operator_posture"], "review_needed")
                self.assertTrue(
                    unresolved_reasons,
                    msg=(
                        f"{fixture_case['case_id']} must expose an explicit "
                        "operator-reviewable unresolved reason"
                    ),
                )
                self.assertIn(
                    tuple(fixture_case["expected_unresolved_reason_contains"])[0],
                    " ".join(unresolved_reasons),
                )
                self.assertIn("draft_review_note", fixture_case["allowed_ai_actions"])
                self.assertIn("identify_evidence_gap", fixture_case["allowed_ai_actions"])
                self.assertIn(
                    "choose_authoritative_truth",
                    fixture_case["disallowed_ai_actions"],
                )
                self.assertIn(
                    "create_source_truth",
                    fixture_case["disallowed_ai_actions"],
                )

    def test_fixture_inputs_are_cited_or_explicitly_missing_citation(self) -> None:
        for fixture_case in self.fixture["cases"]:
            with self.subTest(case_id=fixture_case["case_id"]):
                evidence_items = fixture_case["evidence_inputs"]
                self.assertTrue(evidence_items)
                missing_citation_expected = "missing_supporting_citations" in tuple(
                    fixture_case["expected_uncertainty_flags"]
                )
                missing_citation_seen = False
                for item in evidence_items:
                    citation = item.get("citation")
                    if citation is None:
                        missing_citation_seen = True
                    else:
                        self.assertEqual(citation["record_family"], item["record_family"])
                        self.assertEqual(citation["record_id"], item["record_id"])

                self.assertEqual(missing_citation_seen, missing_citation_expected)

    def test_fixture_cases_do_not_use_workstation_paths_or_secrets(self) -> None:
        serialized = FIXTURE_PATH.read_text(encoding="utf-8")
        fixture_strings = tuple(self._fixture_strings(self.fixture))
        mac_home = "/" + "/".join(("Users", ""))
        unix_home = "/" + "/".join(("home", ""))
        windows_home = "C:" + "\\".join(("", "Users", ""))
        escaped_windows_home = "C:" + "\\\\".join(("", "Users", ""))

        self.assertNotIn(mac_home, serialized)
        self.assertNotIn(unix_home, serialized)
        self.assertFalse(
            any(windows_home in fixture_text for fixture_text in fixture_strings),
            msg="fixture strings must not contain Windows workstation home paths",
        )
        self.assertNotIn(escaped_windows_home, serialized)
        self.assertNotIn("sk-", serialized)
        self.assertNotIn("token=", serialized.lower())

    @classmethod
    def _fixture_strings(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return (value,)
        if isinstance(value, dict):
            strings: list[str] = []
            for key, item in value.items():
                strings.extend(cls._fixture_strings(key))
                strings.extend(cls._fixture_strings(item))
            return tuple(strings)
        if isinstance(value, list):
            strings = []
            for item in value:
                strings.extend(cls._fixture_strings(item))
            return tuple(strings)
        return ()


if __name__ == "__main__":
    unittest.main()
