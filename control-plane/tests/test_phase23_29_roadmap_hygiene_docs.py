from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase2329RoadmapHygieneDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_repo_uses_phase23_29_roadmap_name_for_top_level_entrypoints(self) -> None:
        roadmap_path = REPO_ROOT / "docs/Revised Phase23-29 Epic Roadmap.md"
        stale_roadmap_path = REPO_ROOT / "docs/Revised Phase23-20 Epic Roadmap.md"

        self.assertTrue(roadmap_path.exists(), f"expected document at {roadmap_path}")
        self.assertFalse(
            stale_roadmap_path.exists(),
            f"stale roadmap path should be removed: {stale_roadmap_path}",
        )

        roadmap_text = self._read("docs/Revised Phase23-29 Epic Roadmap.md")
        self.assertIn("# Revised Phase 23-29 Epic Roadmap", roadmap_text)
        self.assertIn("Phases 23-29", roadmap_text)
        self.assertIn("docs/non-goals-and-expansion-guardrails.md", roadmap_text)

        for relative_path in (
            "README.md",
            "docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md",
            "docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract-validation.md",
        ):
            with self.subTest(path=relative_path):
                text = self._read(relative_path)
                self.assertNotIn("docs/Revised Phase23-20 Epic Roadmap.md", text)
                if relative_path != "README.md":
                    self.assertIn("docs/Revised Phase23-29 Epic Roadmap.md", text)


if __name__ == "__main__":
    unittest.main()
