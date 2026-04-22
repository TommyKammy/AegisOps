from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30FOptionalExtensionVisibilityBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase30f_design_doc_exists_and_defines_optional_extension_visibility_boundary(
        self,
    ) -> None:
        text = self._read("docs/phase-30f-optional-extension-visibility-boundary.md")

        for term in (
            "AegisOps Phase 30F Optional-Extension Visibility Boundary",
            "Reviewed Phase 30F Boundary",
            "enabled",
            "disabled-by-default",
            "unavailable",
            "degraded",
            "assistant availability posture",
            "optional endpoint evidence",
            "optional network evidence",
            "ML shadow status",
            "degraded optional services",
            "optional-extension summary section",
            "family-specific detail panel",
            "mainline expectation note",
            "degraded optional-service visibility",
            "subordinate optional context",
            "mainline AegisOps-owned truth",
            "must not collapse family-specific meaning into a generic \"missing data\" badge",
            "present optional-extension badges as if they were authoritative lifecycle outcomes",
            "mainline expected behavior",
            "browser may show",
            "browser must not",
            "Safe implementation sequence",
            "shared taxonomy and wording",
            "summary section and family cards",
            "mainline expectation notes and degraded-service messaging",
            "validation",
            "README.md",
            "docs/phase-28-optional-endpoint-evidence-pack-boundary.md",
            "docs/phase-29-reviewed-ml-shadow-mode-boundary.md",
            "docs/phase-29-optional-suricata-evidence-pack-boundary.md",
            "docs/phase-30e-assistant-advisory-integration-boundary.md",
            "docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
