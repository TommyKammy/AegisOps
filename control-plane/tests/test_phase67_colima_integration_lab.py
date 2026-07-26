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
    def _run_init(
        self, home: pathlib.Path, bootstrap: pathlib.Path
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["AEGISOPS_LAB_BOOTSTRAP_ENV"] = str(bootstrap)
        return subprocess.run(
            ["bash", str(LAB_DIR / "init.sh")],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

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
            result = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
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

    def test_init_reapplies_bootstrap_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            bootstrap = home / "bootstrap.env"
            bootstrap_text = (LAB_DIR / "bootstrap.env.sample").read_text(
                encoding="utf-8"
            )
            bootstrap.write_text(
                bootstrap_text.replace(
                    "AEGISOPS_LAB_PROXY_PORT=18443",
                    "AEGISOPS_LAB_PROXY_PORT=19443",
                ),
                encoding="utf-8",
            )

            first = self._run_init(home, bootstrap)
            self.assertEqual(first.returncode, 0, first.stderr)
            runtime_root = (
                home / ".local" / "share" / "aegisops" / "phase-67-integration-lab"
            )
            runtime_env = runtime_root / "runtime.env"
            postgres_secret = (
                runtime_root / "secrets" / "postgres-password"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "AEGISOPS_LAB_PROXY_PORT=19443",
                runtime_env.read_text(encoding="utf-8"),
            )

            bootstrap.write_text(
                bootstrap.read_text(encoding="utf-8").replace(
                    "AEGISOPS_LAB_PROXY_PORT=19443",
                    "AEGISOPS_LAB_PROXY_PORT=29443",
                ),
                encoding="utf-8",
            )
            second = self._run_init(home, bootstrap)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn(
                "AEGISOPS_LAB_PROXY_PORT=29443",
                runtime_env.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (
                    runtime_root / "secrets" / "postgres-password"
                ).read_text(encoding="utf-8"),
                postgres_secret,
            )

    def test_init_rotates_proxy_certificate_near_expiry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            first = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(first.returncode, 0, first.stderr)
            cert_dir = (
                home
                / ".local"
                / "share"
                / "aegisops"
                / "phase-67-integration-lab"
                / "proxy-certs"
            )
            key_path = cert_dir / "lab.key"
            cert_path = cert_dir / "lab.crt"
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-sha256",
                    "-nodes",
                    "-keyout",
                    str(key_path),
                    "-out",
                    str(cert_path),
                    "-days",
                    "1",
                    "-subj",
                    "/CN=localhost",
                    "-addext",
                    "subjectAltName=DNS:localhost,IP:127.0.0.1",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            near_expiry_fingerprint = subprocess.run(
                ["openssl", "x509", "-in", str(cert_path), "-noout", "-fingerprint"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout

            second = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(second.returncode, 0, second.stderr)
            renewed_fingerprint = subprocess.run(
                ["openssl", "x509", "-in", str(cert_path), "-noout", "-fingerprint"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            self.assertNotEqual(renewed_fingerprint, near_expiry_fingerprint)
            subprocess.run(
                [
                    "openssl",
                    "x509",
                    "-checkend",
                    "604800",
                    "-noout",
                    "-in",
                    str(cert_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_selected_scope_checks_only_published_ports(self) -> None:
        expected = {
            "core": ["PROXY"],
            "wazuh": ["PROXY", "WAZUH_DASHBOARD"],
            "shuffle": ["PROXY", "SHUFFLE_FRONTEND"],
            "full": ["PROXY", "WAZUH_DASHBOARD", "SHUFFLE_FRONTEND"],
        }
        for scope, port_names in expected.items():
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; selected_port_names "$2"',
                    "phase67-port-test",
                    str(LAB_DIR / "lab-common.sh"),
                    scope,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), port_names)

    def test_selected_scope_rejects_duplicate_ports(self) -> None:
        env = os.environ.copy()
        env.update(
            {
                "AEGISOPS_LAB_PROXY_PORT": "18443",
                "AEGISOPS_LAB_WAZUH_DASHBOARD_PORT": "18443",
                "AEGISOPS_LAB_SHUFFLE_FRONTEND_PORT": "13001",
            }
        )
        result = subprocess.run(
            [
                "bash",
                "-c",
                'source "$1"; assert_unique_selected_ports full',
                "phase67-port-test",
                str(LAB_DIR / "lab-common.sh"),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("assigns duplicate host port 18443", result.stderr)

    def test_current_runtime_migrations_require_schema_readiness(self) -> None:
        entrypoint = (LAB_DIR / "control-plane-entrypoint.sh").read_text(
            encoding="utf-8"
        )
        for migration_name in (
            "0008_phase_25_osquery_host_context_columns.sql",
            "0009_phase_26_external_ticket_reference_columns.sql",
            "0010_phase_28_action_request_idempotency_key_unique_index.sql",
            "0011_phase_28_reconciliation_correlation_lookup_index.sql",
            "0012_phase_32_ai_trace_latest_lookup_index.sql",
            "0013_phase_61_detector_lifecycle_records.sql",
            "0014_phase_61_source_health_records.sql",
            "0015_phase_64_known_limitation_ownership_records.sql",
        ):
            self.assertIn(migration_name, entrypoint)
        self.assertGreaterEqual(
            entrypoint.count('prove_migration_state "${migration_name}"'),
            2,
        )
        self.assertIn(
            "could not prove reviewed schema state for recorded migration",
            entrypoint,
        )
        self.assertIn(
            "'false_positive_review_id', 'detector_lifecycle_id'",
            entrypoint,
        )
        self.assertIn(
            "'lifecycle_transition_records_lifecycle_state_known_values'",
            entrypoint,
        )

    def test_custom_bootstrap_documentation_keeps_override_exported(self) -> None:
        readme = (LAB_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("export AEGISOPS_LAB_BOOTSTRAP_ENV=", readme)
        self.assertIn("Keep `AEGISOPS_LAB_BOOTSTRAP_ENV` exported", readme)

    def test_network_validation_rejects_non_host_addresses(self) -> None:
        preflight = (LAB_DIR / "preflight.sh").read_text(encoding="utf-8")
        self.assertIn("requested.network_address", preflight)
        self.assertIn("requested.broadcast_address", preflight)
        self.assertIn("service IPv4 values must be usable host addresses", preflight)

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
