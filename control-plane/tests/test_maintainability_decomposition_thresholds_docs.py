from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class MaintainabilityDecompositionThresholdsDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_thresholds_doc_exists_and_captures_repo_specific_backlog_triggers(self) -> None:
        text = self._read("docs/maintainability-decomposition-thresholds.md")

        for term in (
            "# AegisOps Maintainability Decomposition Thresholds and Backlog Triggers",
            "This document converts the recent `service.py` refactor experience into a lightweight rule for when AegisOps should open another maintainability backlog",
            "`#592`",
            "`#610`",
            "`#633`",
            "responsibility count",
            "authority-path mixing",
            "optional-extension mixing",
            "regression-test coupling",
            "operator-surface overlap",
            "line count alone is not enough",
            "open another maintainability refactor backlog",
            "continue extending the hotspot in place",
            "`control-plane/aegisops_control_plane/service.py`",
            "`control-plane/aegisops_control_plane/restore_readiness.py`",
            "A hotspot should move to backlog creation when",
            "A hotspot can stay in place for the current issue only when",
            "backlog trigger",
            "decomposition threshold",
        ):
            self.assertIn(term, text)

    def test_architecture_and_review_entrypoints_link_to_thresholds_doc(self) -> None:
        expected_link = "docs/maintainability-decomposition-thresholds.md"

        for relative_path in (
            "docs/architecture.md",
            "docs/templates/issue-template.md",
            "docs/templates/pull-request-review-checklist.md",
            "docs/control-plane-service-internal-boundaries.md",
        ):
            with self.subTest(path=relative_path):
                self.assertIn(expected_link, self._read(relative_path))

    def test_documentation_ownership_map_tracks_thresholds_doc(self) -> None:
        text = self._read("docs/documentation-ownership-map.md")
        self.assertIn(
            "| `docs/maintainability-decomposition-thresholds.md` | Maintainability decomposition thresholds and backlog triggers | IT Operations, Information Systems Department |",
            text,
        )


if __name__ == "__main__":
    unittest.main()
