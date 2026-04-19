from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase27Day2HardeningValidationTests(unittest.TestCase):
    @staticmethod
    def _validation_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-27-day-2-hardening-validation.md"

    def test_phase27_validation_doc_exists_and_covers_reviewed_drills(self) -> None:
        validation_doc = self._validation_doc()
        self.assertTrue(
            validation_doc.exists(),
            f"expected Phase 27 validation doc at {validation_doc}",
        )

        validation_text = validation_doc.read_text(encoding="utf-8")

        for term in (
            "Validation status: PASS",
            "docs/runbook.md",
            "docs/auth-baseline.md",
            "docs/smb-footprint-and-deployment-profile-baseline.md",
            "control-plane/tests/test_service_persistence_restore_readiness.py",
            "control-plane/tests/test_runtime_secret_boundary.py",
            "restore",
            "degraded-mode",
            "identity-boundary",
            "secret rotation",
            "secret-backend unavailability",
            "IdP outage",
            "delegation outage",
            "source-health",
            "repo-owned verification path",
            "bash scripts/verify-phase-27-day-2-hardening-validation.sh",
        ):
            self.assertIn(term, validation_text)


if __name__ == "__main__":
    unittest.main()
