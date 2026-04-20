from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class NonGoalsExpansionGuardrailsDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_canonical_guardrails_registry_exists_and_consolidates_cross_phase_boundaries(
        self,
    ) -> None:
        text = self._read("docs/non-goals-and-expansion-guardrails.md")

        for term in (
            "# AegisOps Non-Goals and Expansion Guardrails",
            "canonical cross-phase reference",
            "AegisOps must not become a self-built replacement for all SIEM features or all SOAR features.",
            "Assistant and ML paths remain advisory-only and non-authoritative.",
            "Optional or transitional substrates remain subordinate to the AegisOps control-plane authority model.",
            "Subordinate evidence packs remain optional augmentation, not a new product core or authority surface.",
            "External coordination or ticketing systems remain non-authoritative coordination targets.",
            "Fail-closed handling remains mandatory when reviewed provenance, scope, auth context, or boundary signals are missing, malformed, or only partially trusted.",
            "Future roadmap work, PRs, ADRs, and validation notes should cite this registry when checking whether a proposed expansion widens AegisOps beyond the approved control-plane thesis.",
        ):
            self.assertIn(term, text)

    def test_main_entrypoints_link_to_canonical_guardrails_registry(self) -> None:
        expected_link = "docs/non-goals-and-expansion-guardrails.md"

        for relative_path in (
            "README.md",
            "docs/architecture.md",
            "docs/requirements-baseline.md",
        ):
            with self.subTest(path=relative_path):
                self.assertIn(expected_link, self._read(relative_path))


if __name__ == "__main__":
    unittest.main()
