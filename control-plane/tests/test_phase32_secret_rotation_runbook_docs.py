from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase32SecretRotationRunbookDocsTests(unittest.TestCase):
    def test_runbook_defines_reviewed_secret_rotation_and_break_glass_contract(self) -> None:
        runbook_path = REPO_ROOT / "docs" / "runbook.md"
        auth_baseline_path = REPO_ROOT / "docs" / "auth-baseline.md"

        self.assertTrue(runbook_path.exists(), f"expected runbook at {runbook_path}")
        self.assertTrue(auth_baseline_path.exists(), f"expected auth baseline at {auth_baseline_path}")

        runbook_text = runbook_path.read_text(encoding="utf-8")
        auth_baseline_text = auth_baseline_path.read_text(encoding="utf-8")
        normalized_runbook_text = runbook_text.lower()

        for term in (
            "## 5. secret rotation and break-glass custody",
            "### 5.1 reviewed secret sources and actively managed bindings",
            "### 5.2 reviewed secret rotation checklist",
            "### 5.3 bootstrap token and break-glass custody checklist",
            "openbao references remain the preferred reviewed managed-secret boundary",
            "mounted secret files remain the reviewed first-boot and local bootstrap path",
            "the postgresql dsn",
            "the wazuh ingest shared secret",
            "the reverse-proxy boundary secret",
            "the admin bootstrap token",
            "the break-glass token",
            "capture the exact repository revision or release identifier",
            "perform a fresh openbao read or remount the reviewed secret file before restarting or reloading the affected runtime",
            "operators must not treat a cached prior secret read, placeholder credential, or ad hoc copied value as proof of rotation success.",
            "if the reviewed backend secret source is unavailable, unreadable, stale, or resolves to an empty value, rotation must stop and remain failed closed.",
            "break-glass material must remain separately custodied from routine operator credentials",
            "after any break-glass use, operators must rotate the exposed bootstrap or break-glass material before the environment returns to normal operation",
            "the trigger for break-glass use, including the failed reviewed path that made the exception necessary",
        ):
            self.assertIn(term, normalized_runbook_text)

        self.assertIn(
            "Any managed-secret integration must fail closed when the backend is unavailable, the referenced secret is unreadable, or the resolved value is empty or stale.",
            auth_baseline_text,
        )
        self.assertIn(
            "The initial reviewed credential families for this delivery model are the PostgreSQL DSN, Wazuh ingest secrets, reverse-proxy boundary secret, admin bootstrap and break-glass tokens",
            auth_baseline_text,
        )


if __name__ == "__main__":
    unittest.main()
