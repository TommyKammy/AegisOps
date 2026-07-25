from __future__ import annotations

import os
import pathlib
import stat
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
LAB_DIR = REPO_ROOT / "control-plane" / "deployment" / "phase-67-integration-lab"


class Phase67ColimaIntegrationLabTests(unittest.TestCase):
    def test_required_lab_commands_are_executable(self) -> None:
        for name in (
            "preflight.sh",
            "init.sh",
            "prepare-substrates.sh",
            "up.sh",
            "status.sh",
            "logs.sh",
            "down.sh",
            "cleanup.sh",
            "destroy-data.sh",
            "smoke-core.sh",
        ):
            path = LAB_DIR / name
            self.assertTrue(path.is_file(), f"missing Phase 67.1 command: {name}")
            self.assertTrue(os.access(path, os.X_OK), f"command is not executable: {name}")

    def test_ci_runs_verifier_and_adversarial_self_test(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "bash scripts/verify-phase-67-1-colima-integration-lab.sh", workflow
        )
        self.assertIn(
            "bash scripts/test-verify-phase-67-1-colima-integration-lab.sh", workflow
        )

    def test_init_generates_untracked_runtime_secrets_and_tls(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["AEGISOPS_LAB_BOOTSTRAP_ENV"] = str(LAB_DIR / "bootstrap.env.sample")

            result = subprocess.run(
                ["bash", str(LAB_DIR / "init.sh")],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            runtime_root = (
                home / ".local" / "share" / "aegisops" / "phase-67-integration-lab"
            )
            runtime_env = runtime_root / "runtime.env"
            self.assertTrue(runtime_env.is_file())
            self.assertEqual(
                stat.S_IMODE(runtime_env.stat().st_mode),
                0o600,
            )
            self.assertIn(
                f"AEGISOPS_LAB_RUNTIME_ROOT={runtime_root}",
                runtime_env.read_text(encoding="utf-8"),
            )

            for name in (
                "postgres-password",
                "control-plane-postgres-dsn",
                "wazuh-ingest-shared-secret",
                "wazuh-ingest-proxy-secret",
                "protected-surface-proxy-secret",
                "admin-bootstrap-token",
                "break-glass-token",
                "wazuh-indexer-password",
                "wazuh-api-password",
                "shuffle-opensearch-password",
                "shuffle-encryption-modifier",
            ):
                secret = runtime_root / "secrets" / name
                self.assertTrue(secret.is_file(), f"missing generated secret: {name}")
                self.assertEqual(stat.S_IMODE(secret.stat().st_mode), 0o600)
                self.assertTrue(secret.read_text(encoding="utf-8").strip())

            shuffle_password = (
                runtime_root / "secrets" / "shuffle-opensearch-password"
            ).read_text(encoding="utf-8")
            self.assertRegex(shuffle_password, r"[A-Z]")
            self.assertRegex(shuffle_password, r"[a-z]")
            self.assertRegex(shuffle_password, r"[0-9]")
            self.assertRegex(shuffle_password, r"[^A-Za-z0-9]")

            self.assertTrue((runtime_root / "proxy-certs" / "lab.crt").is_file())
            self.assertTrue((runtime_root / "proxy-certs" / "lab.key").is_file())

    def test_normal_cleanup_and_destroy_boundaries_are_distinct(self) -> None:
        down = (LAB_DIR / "down.sh").read_text(encoding="utf-8")
        cleanup = (LAB_DIR / "cleanup.sh").read_text(encoding="utf-8")
        destroy = (LAB_DIR / "destroy-data.sh").read_text(encoding="utf-8")

        self.assertNotIn("--volumes", down)
        self.assertNotIn("--volumes", cleanup)
        self.assertIn("--volumes", destroy)
        self.assertIn("--confirm-destroy-phase-67-lab-data", destroy)


if __name__ == "__main__":
    unittest.main()
