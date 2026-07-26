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
        self,
        home: pathlib.Path,
        bootstrap: pathlib.Path,
        docker_volumes: tuple[str, ...] = (),
        docker_volume_list_exit: int = 0,
    ) -> subprocess.CompletedProcess[str]:
        fake_bin = home / "fake-bin"
        fake_bin.mkdir(exist_ok=True)
        fake_docker = fake_bin / "docker"
        fake_docker.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'if [[ "$*" == *" volume ls --quiet"* ]]; then\n'
            '  printf "%s" "${PHASE67_TEST_DOCKER_VOLUMES:-}"\n'
            '  exit "${PHASE67_TEST_DOCKER_VOLUME_LIST_EXIT:-0}"\n'
            "fi\n"
            'echo "unexpected docker invocation: $*" >&2\n'
            "exit 1\n",
            encoding="utf-8",
        )
        fake_docker.chmod(0o755)
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["AEGISOPS_LAB_BOOTSTRAP_ENV"] = str(bootstrap)
        env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
        env["PHASE67_TEST_DOCKER_VOLUMES"] = "".join(
            f"{volume}\n" for volume in docker_volumes
        )
        env["PHASE67_TEST_DOCKER_VOLUME_LIST_EXIT"] = str(
            docker_volume_list_exit
        )
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

    def test_init_marks_deleted_proxy_pair_for_recreation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            first = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(first.returncode, 0, first.stderr)
            runtime_root = (
                home / ".local" / "share" / "aegisops" / "phase-67-integration-lab"
            )
            marker = runtime_root / "proxy-certificate-recreate-required"
            self.assertFalse(marker.exists())
            (runtime_root / "proxy-certs" / "lab.key").unlink()
            (runtime_root / "proxy-certs" / "lab.crt").unlink()

            second = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertTrue(marker.is_file())

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

    def test_published_ports_map_to_expected_compose_services(self) -> None:
        expected = {
            "PROXY": "proxy",
            "WAZUH_DASHBOARD": "wazuh-dashboard",
            "SHUFFLE_FRONTEND": "shuffle-frontend",
        }
        for port_name, service_name in expected.items():
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; service_name_for_published_port "$2"',
                    "phase67-port-service-test",
                    str(LAB_DIR / "lab-common.sh"),
                    port_name,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), service_name)

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

    def test_selected_scope_checks_only_active_service_addresses(self) -> None:
        expected = {
            "core": ["PROXY", "CONTROL_PLANE", "POSTGRES"],
            "wazuh": [
                "PROXY",
                "CONTROL_PLANE",
                "POSTGRES",
                "WAZUH_MANAGER",
                "WAZUH_INDEXER",
                "WAZUH_DASHBOARD",
            ],
            "shuffle": [
                "PROXY",
                "CONTROL_PLANE",
                "POSTGRES",
                "SHUFFLE_BACKEND",
                "SHUFFLE_OPENSEARCH",
                "SHUFFLE_FRONTEND",
            ],
            "full": [
                "PROXY",
                "CONTROL_PLANE",
                "POSTGRES",
                "WAZUH_MANAGER",
                "WAZUH_INDEXER",
                "WAZUH_DASHBOARD",
                "SHUFFLE_BACKEND",
                "SHUFFLE_OPENSEARCH",
                "SHUFFLE_FRONTEND",
            ],
        }
        for scope, address_names in expected.items():
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; selected_address_names "$2"',
                    "phase67-address-test",
                    str(LAB_DIR / "lab-common.sh"),
                    scope,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), address_names)

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
        self.assertIn("AND indnkeyatts = 1", entrypoint)
        self.assertIn("AND indnatts = 1", entrypoint)
        self.assertIn("AND indexprs IS NULL", entrypoint)
        self.assertIn("AND indpred IS NULL", entrypoint)
        self.assertIn(
            "pg_get_indexdef(indexrelid, 1, true) = 'idempotency_key'",
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
        common = (LAB_DIR / "lab-common.sh").read_text(encoding="utf-8")
        prepare = (LAB_DIR / "prepare-substrates.sh").read_text(encoding="utf-8")
        up = (LAB_DIR / "up.sh").read_text(encoding="utf-8")
        self.assertIn('diff --quiet HEAD -- \\\n    . ":(exclude)', common)
        self.assertLess(
            prepare.index("assert_reviewed_wazuh_checkout"),
            prepare.index("require_command docker"),
        )
        self.assertLess(
            up.index("assert_reviewed_wazuh_checkout"),
            up.index("validate_wazuh_certificate_bundle"),
        )
        self.assertIn("assert_reviewed_file_digest", up)
        self.assertIn("record_reviewed_file_digest", prepare)
        self.assertLess(
            prepare.index("record_reviewed_file_digest"),
            prepare.index("wazuh-certificate-recreate-required"),
        )
        self.assertIn(
            "The next wazuh/full up.sh run will force service recreation.",
            prepare,
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
            wazuh_source = pathlib.Path(tmpdir) / "wazuh-docker"
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
            manager_config.write_text("<unreviewed />\n", encoding="utf-8")

            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; assert_reviewed_wazuh_checkout "$2" "$3" "$4"',
                    "phase67-wazuh-checkout-test",
                    str(LAB_DIR / "lab-common.sh"),
                    str(wazuh_source),
                    pinned_commit,
                    "single-node/config/wazuh_indexer/internal_users.yml",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "Wazuh substrate has unreviewed tracked changes outside",
                result.stderr,
            )

    def test_reviewed_file_digest_rejects_post_prepare_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            reviewed_file = root / "internal_users.yml"
            digest_file = root / "internal_users.sha256"
            reviewed_file.write_text("reviewed\n", encoding="utf-8")
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    (
                        'source "$1"; '
                        'record_reviewed_file_digest "$2" "$3"; '
                        'printf "changed\\n" >"$2"; '
                        'assert_reviewed_file_digest "$2" "$3"'
                    ),
                    "phase67-reviewed-digest-test",
                    str(LAB_DIR / "lab-common.sh"),
                    str(reviewed_file),
                    str(digest_file),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("changed after substrate preparation", result.stderr)

    def test_init_rejects_unreviewed_runtime_pins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            bootstrap = home / "bootstrap.env"
            bootstrap.write_text(
                (LAB_DIR / "bootstrap.env.sample")
                .read_text(encoding="utf-8")
                .replace("AEGISOPS_LAB_WAZUH_VERSION=4.14.6", "AEGISOPS_LAB_WAZUH_VERSION=4.15.0"),
                encoding="utf-8",
            )
            result = self._run_init(home, bootstrap)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "must remain at reviewed version 4.14.6",
                result.stderr,
            )

    def test_init_refuses_to_replace_missing_initialized_credential(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            first = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(first.returncode, 0, first.stderr)
            runtime_root = (
                home / ".local" / "share" / "aegisops" / "phase-67-integration-lab"
            )
            missing_credential = runtime_root / "secrets" / "postgres-password"
            missing_credential.unlink()

            second = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertNotEqual(second.returncode, 0)
            self.assertIn(
                "initialized runtime is missing credential postgres-password",
                second.stderr,
            )
            self.assertFalse(missing_credential.exists())

    def test_init_rejects_preserved_volumes_when_runtime_environment_is_missing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            first = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(first.returncode, 0, first.stderr)
            runtime_root = (
                home / ".local" / "share" / "aegisops" / "phase-67-integration-lab"
            )
            runtime_env = runtime_root / "runtime.env"
            postgres_secret = runtime_root / "secrets" / "postgres-password"
            runtime_env.unlink()
            postgres_secret.unlink()

            second = self._run_init(
                home,
                LAB_DIR / "bootstrap.env.sample",
                docker_volumes=("aegisops-phase67-lab-postgres-data",),
            )

            self.assertNotEqual(second.returncode, 0)
            self.assertIn(
                "runtime.env is missing while preserved Phase 67.1 volumes exist",
                second.stderr,
            )
            self.assertFalse(postgres_secret.exists())
            self.assertFalse(runtime_env.exists())

    def test_init_fails_closed_when_preserved_volumes_cannot_be_enumerated(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            result = self._run_init(
                home,
                LAB_DIR / "bootstrap.env.sample",
                docker_volume_list_exit=1,
            )
            runtime_root = (
                home / ".local" / "share" / "aegisops" / "phase-67-integration-lab"
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "could not enumerate Docker volumes before initializing",
                result.stderr,
            )
            self.assertFalse((runtime_root / "runtime.env").exists())
            self.assertFalse((runtime_root / "secrets").exists())

    def test_evidence_header_records_runtime_artifact_state_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            (root / "control-plane").mkdir()
            migrations = root / "postgres" / "control-plane" / "migrations"
            migrations.mkdir(parents=True)
            runtime_file = root / "control-plane" / "main.py"
            runtime_file.write_text("print('reviewed')\n", encoding="utf-8")
            (migrations / "0001.sql").write_text("SELECT 1;\n", encoding="utf-8")
            (root / ".dockerignore").write_text("**\n!control-plane/**\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.name", "Phase 67 test"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "config",
                    "user.email",
                    "phase67-test@example.invalid",
                ],
                check=True,
            )
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(root), "commit", "-qm", "fixture"],
                check=True,
            )
            clean_evidence = root / "clean.evidence"
            dirty_evidence = root / "dirty.evidence"

            def write_header(output: pathlib.Path) -> dict[str, str]:
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        (
                            'source "$1"; REPO_ROOT="$2"; '
                            'write_evidence_header "$3"'
                        ),
                        "phase67-evidence-header-test",
                        str(LAB_DIR / "lab-common.sh"),
                        str(root),
                        str(output),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return dict(
                    line.split("=", 1)
                    for line in output.read_text(encoding="utf-8").splitlines()
                )

            clean = write_header(clean_evidence)
            self.assertEqual(clean["repository_runtime_state"], "clean")
            self.assertRegex(
                clean["repository_runtime_artifact_sha256"], r"^[0-9a-f]{64}$"
            )

            runtime_file.write_text("print('local edit')\n", encoding="utf-8")
            dirty = write_header(dirty_evidence)
            self.assertEqual(dirty["repository_runtime_state"], "dirty")
            self.assertNotEqual(
                dirty["repository_runtime_artifact_sha256"],
                clean["repository_runtime_artifact_sha256"],
            )

    def test_runtime_root_rejects_dotdot_and_symlink_escapes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            allowed_root = home / ".local" / "share" / "aegisops"
            outside_root = home / ".ssh"
            allowed_root.mkdir(parents=True)
            outside_root.mkdir()
            (allowed_root / "escape").symlink_to(outside_root, target_is_directory=True)
            candidates = (
                allowed_root / ".." / ".." / ".." / ".ssh" / "phase67",
                allowed_root / "escape" / "phase67",
            )
            env = os.environ.copy()
            env["HOME"] = str(home)
            for candidate in candidates:
                with self.subTest(candidate=candidate):
                    result = subprocess.run(
                        [
                            "bash",
                            "-c",
                            'source "$1"; assert_safe_runtime_root "$2"',
                            "phase67-runtime-root-test",
                            str(LAB_DIR / "lab-common.sh"),
                            str(candidate),
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                        env=env,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(
                        "runtime root must remain below",
                        result.stderr,
                    )

    def test_preflight_scope_and_evidence_contracts_are_explicit(self) -> None:
        preflight = (LAB_DIR / "preflight.sh").read_text(encoding="utf-8")
        bootstrap = (LAB_DIR / "bootstrap.env.sample").read_text(encoding="utf-8")
        self.assertIn('selected_address_names "${scope}"', preflight)
        self.assertIn('selected_port_names "${scope}"', preflight)
        self.assertIn("project_network_subnets", preflight)
        self.assertIn("ARM64 service execution is unavailable", preflight)
        self.assertIn('mktemp "${evidence_dir}/preflight-${scope}-', preflight)
        self.assertIn("AEGISOPS_LAB_ALLOW_EMULATION=no", bootstrap)

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
                'case "$*" in\n'
                '  *" network inspect "*|*" volume inspect "*) exit 1 ;;\n'
                '  *" compose "*) printf "%s\\n" "$*" >"${AEGISOPS_FAKE_DOCKER_LOG}" ;;\n'
                "esac\n",
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

    def test_destroy_rejects_foreign_project_resources(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            init_result = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            fake_bin = home / "bin"
            fake_bin.mkdir()
            docker_log = home / "docker.log"
            fake_docker = fake_bin / "docker"
            fake_docker.write_text(
                "#!/usr/bin/env bash\n"
                'printf "%s\\n" "$*" >>"${AEGISOPS_FAKE_DOCKER_LOG}"\n'
                'case "$*" in\n'
                '  *" ps --all --quiet "*) printf "foreign-container\\n" ;;\n'
                '  *" container inspect foreign-container "*) '
                'printf "66.0|aegisops-phase67-lab\\n" ;;\n'
                '  *" network inspect "*|*" volume inspect "*) exit 1 ;;\n'
                "esac\n",
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
            env["AEGISOPS_FAKE_DOCKER_LOG"] = str(docker_log)

            result = subprocess.run(
                [
                    "bash",
                    str(LAB_DIR / "destroy-data.sh"),
                    "--confirm-destroy-phase-67-lab-data",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "exists without the Phase 67.1 ownership label",
                result.stderr,
            )
            self.assertNotIn(
                " compose ",
                docker_log.read_text(encoding="utf-8"),
            )

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

            for _ in range(2):
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
            evidence_files = list(evidence_dir.glob("status-full-*"))
            self.assertEqual(len(evidence_files), 2)
            for evidence_file in evidence_files:
                self.assertIn(
                    "phase67-status",
                    evidence_file.read_text(encoding="utf-8"),
                )

    def test_normal_cleanup_and_destroy_boundaries_are_distinct(self) -> None:
        up = (LAB_DIR / "up.sh").read_text(encoding="utf-8")
        down = (LAB_DIR / "down.sh").read_text(encoding="utf-8")
        cleanup = (LAB_DIR / "cleanup.sh").read_text(encoding="utf-8")
        destroy = (LAB_DIR / "destroy-data.sh").read_text(encoding="utf-8")

        self.assertNotIn("force_recreate_arguments", up)
        self.assertIn('if [[ "${force_recreate}" == true ]]', up)
        self.assertNotIn("--volumes", down)
        self.assertNotIn("--volumes", cleanup)
        self.assertIn("--volumes", destroy)
        self.assertIn("--confirm-destroy-phase-67-lab-data", destroy)
        self.assertIn("assert_phase67_compose_project_ownership", down)
        self.assertIn("assert_phase67_compose_project_ownership", destroy)


if __name__ == "__main__":
    unittest.main()
