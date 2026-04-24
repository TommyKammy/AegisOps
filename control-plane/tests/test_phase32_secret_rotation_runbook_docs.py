from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase32SecretRotationRunbookDocsTests(unittest.TestCase):
    def test_runbook_defines_reviewed_upgrade_contract(self) -> None:
        runbook_path = REPO_ROOT / "docs" / "runbook.md"
        smb_baseline_path = REPO_ROOT / "docs" / "smb-footprint-and-deployment-profile-baseline.md"
        phase17_contract_path = (
            REPO_ROOT / "docs" / "phase-17-runtime-config-contract-and-boot-command-expectations.md"
        )

        self.assertTrue(runbook_path.exists(), f"expected runbook at {runbook_path}")
        self.assertTrue(smb_baseline_path.exists(), f"expected SMB footprint baseline at {smb_baseline_path}")
        self.assertTrue(
            phase17_contract_path.exists(),
            f"expected Phase 17 runtime contract at {phase17_contract_path}",
        )

        runbook_text = runbook_path.read_text(encoding="utf-8")
        normalized_runbook_text = runbook_text.lower()

        for term in (
            "reviewed upgrade path",
            "approved maintenance window",
            "the reviewed repository revision or release identifier selected for the change window",
            "the latest postgresql-aware backup completed successfully before the upgrade begins",
            "the reviewed runtime env file still matches the approved phase 17 runtime contract",
            "operators must not treat optional opensearch, n8n, shuffle, assistant, or executor surfaces as upgrade prerequisites",
            "the reviewed upgrade sequence is:",
            "capture the pre-upgrade readiness, runtime, compose status, and bounded logs through the approved reverse-proxy-first boundary before changing the running stack",
            "apply the reviewed repository revision or release through the repo-owned first-boot compose path without widening ingress, publishing the backend port directly, or introducing ha or multi-node choreography",
            "re-run the documented startup path from section 2 and confirm migration bootstrap, postgresql reachability, and reverse-proxy admission complete under the reviewed first-boot contract",
            "compare the post-upgrade `/runtime` output, readiness evidence, and operator-visible queue state against the pre-change evidence before ending maintenance",
            "rollback must begin the same day if the upgraded environment cannot satisfy the reviewed readiness path",
            "the minimum evidence set for a reviewed upgrade window is:",
            "the approved maintenance window, named operator, and reason for change;",
            "the pre-change backup custody confirmation and restore point selected for rollback readiness;",
            "the repository revision or release identifier before and after the change;",
            "the pre-change and post-change results for `curl -fsS http://127.0.0.1:<proxy-port>/readyz`, `curl -fsS http://127.0.0.1:<proxy-port>/runtime`, and `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml ps`;",
            "the bounded compose-log capture for the upgrade window; and",
            "the rollback decision, including whether rollback was not needed or which restore point was used.",
            "this reviewed upgrade path stays aligned with `docs/smb-footprint-and-deployment-profile-baseline.md` by keeping upgrades inside one business-hours maintenance window, preserving same-day rollback readiness, and avoiding ha or fleet-orchestration claims.",
        ):
            self.assertIn(term.lower(), normalized_runbook_text)

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
            self.assertIn(term.lower(), normalized_runbook_text)

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
