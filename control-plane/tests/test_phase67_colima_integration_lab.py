from __future__ import annotations

import os
import pathlib
import shutil
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
                f'AEGISOPS_LAB_RUNTIME_ROOT="{runtime_root}"',
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
                'AEGISOPS_LAB_PROXY_PORT="19443"',
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
                'AEGISOPS_LAB_PROXY_PORT="29443"',
                runtime_env.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (
                    runtime_root / "secrets" / "postgres-password"
                ).read_text(encoding="utf-8"),
                postgres_secret,
            )

    def test_runtime_environment_supports_whitespace_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            bootstrap = home / "bootstrap.env"
            bootstrap.write_text(
                (LAB_DIR / "bootstrap.env.sample")
                .read_text(encoding="utf-8")
                .replace(
                    "AEGISOPS_LAB_RUNTIME_ROOT=${HOME}/.local/share/aegisops/"
                    "phase-67-integration-lab",
                    'AEGISOPS_LAB_RUNTIME_ROOT="${HOME}/.local/share/aegisops/'
                    'phase 67 integration lab"',
                ),
                encoding="utf-8",
            )

            result = self._run_init(home, bootstrap)
            self.assertEqual(result.returncode, 0, result.stderr)
            runtime_root = (
                home / ".local" / "share" / "aegisops" / "phase 67 integration lab"
            )
            runtime_env = runtime_root / "runtime.env"
            sourced = subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; printf "%s" "${AEGISOPS_LAB_RUNTIME_ROOT}"',
                    "phase67-runtime-env-test",
                    str(runtime_env),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(sourced.returncode, 0, sourced.stderr)
            self.assertEqual(sourced.stdout, str(runtime_root))

            docker_bin = shutil.which("docker")
            if docker_bin is not None:
                rendered = subprocess.run(
                    [
                        docker_bin,
                        "compose",
                        "--env-file",
                        str(runtime_env),
                        "-f",
                        str(LAB_DIR / "docker-compose.yml"),
                        "config",
                        "--format",
                        "json",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(rendered.returncode, 0, rendered.stderr)
                self.assertIn(str(runtime_root / "proxy-certs"), rendered.stdout)

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
            self.assertTrue(
                (
                    cert_dir.parent / "proxy-certificate-recreate-required"
                ).is_file()
            )
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

    def test_logs_rejects_options_after_service_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            init_result = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            env = os.environ.copy()
            env["HOME"] = str(home)

            for follow_option in ("--follow", "-f"):
                with self.subTest(follow_option=follow_option):
                    result = subprocess.run(
                        [
                            "bash",
                            str(LAB_DIR / "logs.sh"),
                            "control-plane",
                            follow_option,
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                        env=env,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(
                        "pass only service names for a bounded snapshot",
                        result.stderr,
                    )

    def test_wazuh_substrate_rejects_unreviewed_tracked_changes(self) -> None:
        prepare = (LAB_DIR / "prepare-substrates.sh").read_text(encoding="utf-8")
        self.assertIn('diff --quiet HEAD -- \\\n  . ":(exclude)', prepare)
        self.assertLess(
            prepare.index("diff --quiet HEAD --"),
            prepare.index("require_command docker"),
        )
        self.assertIn("replace_admin_hash(current, placeholder)", prepare)
        self.assertIn(
            "unreviewed changes outside the managed admin hash",
            prepare,
        )

    def test_wazuh_certificate_bundle_requires_valid_chains_and_key_pairs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_dir = pathlib.Path(tmpdir)
            ca_key = cert_dir / "ca.key"
            ca_cert = cert_dir / "ca.pem"
            leaf_key = cert_dir / "leaf.key"
            leaf_request = cert_dir / "leaf.csr"
            leaf_cert = cert_dir / "leaf.pem"
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-keyout",
                    str(ca_key),
                    "-out",
                    str(ca_cert),
                    "-days",
                    "30",
                    "-subj",
                    "/CN=Phase67 Test CA",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-keyout",
                    str(leaf_key),
                    "-out",
                    str(leaf_request),
                    "-subj",
                    "/CN=wazuh.indexer",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "openssl",
                    "x509",
                    "-req",
                    "-in",
                    str(leaf_request),
                    "-CA",
                    str(ca_cert),
                    "-CAkey",
                    str(ca_key),
                    "-CAcreateserial",
                    "-out",
                    str(leaf_cert),
                    "-days",
                    "30",
                    "-sha256",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            for root_name in ("root-ca.pem", "root-ca-manager.pem"):
                shutil.copy2(ca_cert, cert_dir / root_name)
            for certificate_name, key_name in (
                ("wazuh.indexer.pem", "wazuh.indexer-key.pem"),
                ("admin.pem", "admin-key.pem"),
                ("wazuh.manager.pem", "wazuh.manager-key.pem"),
                ("wazuh.dashboard.pem", "wazuh.dashboard-key.pem"),
            ):
                shutil.copy2(leaf_cert, cert_dir / certificate_name)
                shutil.copy2(leaf_key, cert_dir / key_name)

            validation_command = (
                'source "$1"; validate_wazuh_certificate_bundle "$2"'
            )
            valid = subprocess.run(
                [
                    "bash",
                    "-c",
                    validation_command,
                    "phase67-wazuh-cert-test",
                    str(LAB_DIR / "lab-common.sh"),
                    str(cert_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(valid.returncode, 0, valid.stderr)

            (cert_dir / "wazuh.dashboard.pem").write_text(
                "corrupt certificate\n",
                encoding="utf-8",
            )
            invalid = subprocess.run(
                [
                    "bash",
                    "-c",
                    validation_command,
                    "phase67-wazuh-cert-test",
                    str(LAB_DIR / "lab-common.sh"),
                    str(cert_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(invalid.returncode, 0)

    def test_up_recreates_services_after_certificate_rotation(self) -> None:
        up = (LAB_DIR / "up.sh").read_text(encoding="utf-8")
        self.assertIn("proxy-certificate-recreate-required", up)
        self.assertIn("wazuh-certificate-recreate-required", up)
        self.assertIn("--force-recreate", up)
        self.assertIn('rm -f "${proxy_recreate_marker}"', up)

    def test_prepare_substrates_blocks_dirty_tracked_wazuh_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            runtime_root = (
                home / ".local" / "share" / "aegisops" / "phase-67-integration-lab"
            )
            wazuh_source = runtime_root / "substrates" / "wazuh-docker"
            internal_users = (
                wazuh_source
                / "single-node"
                / "config"
                / "wazuh_indexer"
                / "internal_users.yml"
            )
            manager_config = (
                wazuh_source
                / "single-node"
                / "config"
                / "wazuh_cluster"
                / "wazuh_manager.conf"
            )
            internal_users.parent.mkdir(parents=True)
            manager_config.parent.mkdir(parents=True)
            internal_users.write_text(
                'admin:\n  hash: "reviewed-placeholder"\nreserved:\n  enabled: true\n',
                encoding="utf-8",
            )
            manager_config.write_text("<ossec_config />\n", encoding="utf-8")
            subprocess.run(
                ["git", "init", "-q", str(wazuh_source)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(wazuh_source), "config", "user.name", "Phase67 Test"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(wazuh_source),
                    "config",
                    "user.email",
                    "phase67-test@example.invalid",
                ],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(wazuh_source), "add", "."],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(wazuh_source), "commit", "-qm", "fixture"],
                check=True,
            )
            pinned_commit = subprocess.run(
                ["git", "-C", str(wazuh_source), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            bootstrap = home / "bootstrap.env"
            bootstrap.write_text(
                (LAB_DIR / "bootstrap.env.sample")
                .read_text(encoding="utf-8")
                .replace(
                    "499184cbeb44fc1086791d11ad4b9bdcb77a9bb9",
                    pinned_commit,
                ),
                encoding="utf-8",
            )
            init_result = self._run_init(home, bootstrap)
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            manager_config.write_text("<unreviewed />\n", encoding="utf-8")
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["AEGISOPS_LAB_BOOTSTRAP_ENV"] = str(bootstrap)

            result = subprocess.run(
                ["bash", str(LAB_DIR / "prepare-substrates.sh")],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "Wazuh substrate has unreviewed tracked changes outside",
                result.stderr,
            )

    def test_down_works_when_generated_secrets_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            init_result = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            runtime_root = (
                home / ".local" / "share" / "aegisops" / "phase-67-integration-lab"
            )
            shutil.rmtree(runtime_root / "secrets")

            fake_bin = home / "bin"
            fake_bin.mkdir()
            docker_log = home / "docker.log"
            fake_docker = fake_bin / "docker"
            fake_docker.write_text(
                "#!/usr/bin/env bash\n"
                'printf "%s\\n" "$*" >"${AEGISOPS_FAKE_DOCKER_LOG}"\n',
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
            env["AEGISOPS_FAKE_DOCKER_LOG"] = str(docker_log)

            result = subprocess.run(
                ["bash", str(LAB_DIR / "down.sh")],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            invocation = docker_log.read_text(encoding="utf-8")
            self.assertIn("--context colima-mac-studio-solo compose", invocation)
            self.assertIn("down --remove-orphans", invocation)

    def test_status_accepts_evidence_flag_without_explicit_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            init_result = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            fake_bin = home / "bin"
            fake_bin.mkdir()
            fake_docker = fake_bin / "docker"
            fake_docker.write_text(
                "#!/usr/bin/env bash\n"
                'printf "phase67-status\\n"\n',
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["PATH"] = f"{fake_bin}:{env['PATH']}"

            result = subprocess.run(
                ["bash", str(LAB_DIR / "status.sh"), "--write-evidence"],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("phase67-status", result.stdout)
            self.assertIn("evidence=", result.stdout)
            evidence_dir = (
                home
                / ".local"
                / "share"
                / "aegisops"
                / "phase-67-integration-lab"
                / "evidence"
            )
            evidence_files = list(evidence_dir.glob("status-full-*.txt"))
            self.assertEqual(len(evidence_files), 1)
            self.assertIn(
                "phase67-status",
                evidence_files[0].read_text(encoding="utf-8"),
            )

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
