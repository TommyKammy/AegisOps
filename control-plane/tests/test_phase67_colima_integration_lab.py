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

    def test_docker_context_excludes_generated_credentials_and_certificates(
        self,
    ) -> None:
        dockerignore = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")
        for excluded_path in (
            "control-plane/deployment/first-boot/generated/",
            "control-plane/deployment/first-boot/runtime/",
            "control-plane/deployment/first-boot/secrets/",
            "control-plane/deployment/first-boot/certs/",
            "control-plane/deployment/phase-67-integration-lab/runtime.env",
            "control-plane/deployment/phase-67-integration-lab/runtime/",
            "control-plane/deployment/phase-67-integration-lab/secrets/",
            "control-plane/deployment/phase-67-integration-lab/certs/",
            "control-plane/deployment/phase-67-integration-lab/evidence/",
            "control-plane/deployment/phase-67-integration-lab/substrates/",
        ):
            self.assertIn(excluded_path, dockerignore)

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
                "wazuh-dashboard-password",
                "shuffle-opensearch-password",
                "shuffle-encryption-modifier",
            ):
                secret = runtime_root / "secrets" / name
                self.assertTrue(secret.is_file(), f"missing generated secret: {name}")
                self.assertEqual(stat.S_IMODE(secret.stat().st_mode), 0o600)
                self.assertTrue(secret.read_text(encoding="utf-8").strip())

            for strong_password_name in (
                "wazuh-dashboard-password",
                "shuffle-opensearch-password",
            ):
                strong_password = (
                    runtime_root / "secrets" / strong_password_name
                ).read_text(encoding="utf-8")
                self.assertRegex(strong_password, r"[A-Z]")
                self.assertRegex(strong_password, r"[a-z]")
                self.assertRegex(strong_password, r"[0-9]")
                self.assertRegex(strong_password, r"[^A-Za-z0-9]")

            certificate = runtime_root / "proxy-certs" / "lab.crt"
            self.assertTrue(certificate.is_file())
            self.assertTrue((runtime_root / "proxy-certs" / "lab.key").is_file())
            self.assertEqual(
                (
                    runtime_root
                    / "proxy-certs"
                    / "wazuh-upstream-root-ca.pem"
                ).read_bytes(),
                certificate.read_bytes(),
            )
            certificate_text = subprocess.run(
                [
                    "openssl",
                    "x509",
                    "-in",
                    str(certificate),
                    "-noout",
                    "-text",
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            for required_san in (
                "DNS:localhost",
                "DNS:wazuh.localhost",
                "DNS:shuffle.localhost",
                "IP Address:127.0.0.1",
            ):
                self.assertIn(required_san, certificate_text)

            proxy_secret = (
                runtime_root / "secrets" / "protected-surface-proxy-secret"
            ).read_text(encoding="utf-8").strip()
            runtime_auth = runtime_root / "proxy-certs" / "runtime-auth.conf"
            self.assertEqual(stat.S_IMODE(runtime_auth.stat().st_mode), 0o600)
            runtime_auth_text = runtime_auth.read_text(encoding="utf-8")
            self.assertIn(
                f'proxy_set_header X-AegisOps-Proxy-Secret "{proxy_secret}";',
                runtime_auth_text,
            )
            self.assertIn(
                'proxy_set_header X-AegisOps-Authenticated-Identity '
                '"phase67-lab-platform-admin";',
                runtime_auth_text,
            )
            self.assertIn(
                'proxy_set_header X-AegisOps-Authenticated-Role '
                '"platform_admin";',
                runtime_auth_text,
            )
            self.assertFalse(
                (runtime_root / "proxy-certificate-recreate-required").exists()
            )

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

    def test_init_rejects_suffix_only_proxy_certificate_sans(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            first = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(first.returncode, 0, first.stderr)
            runtime_root = (
                home
                / ".local"
                / "share"
                / "aegisops"
                / "phase-67-integration-lab"
            )
            cert_dir = runtime_root / "proxy-certs"
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
                    "30",
                    "-subj",
                    "/CN=localhost.invalid",
                    "-addext",
                    "subjectAltName="
                    "DNS:localhost.invalid,"
                    "DNS:wazuh.localhost.invalid,"
                    "DNS:shuffle.localhost.invalid,"
                    "IP:127.0.0.10",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            suffix_only_fingerprint = subprocess.run(
                ["openssl", "x509", "-in", str(cert_path), "-noout", "-fingerprint"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout

            second = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertTrue(
                (runtime_root / "proxy-certificate-recreate-required").is_file()
            )
            renewed_fingerprint = subprocess.run(
                ["openssl", "x509", "-in", str(cert_path), "-noout", "-fingerprint"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            self.assertNotEqual(renewed_fingerprint, suffix_only_fingerprint)
            san_entries = subprocess.run(
                [
                    "openssl",
                    "x509",
                    "-in",
                    str(cert_path),
                    "-noout",
                    "-text",
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            for required_san in (
                "DNS:localhost",
                "DNS:wazuh.localhost",
                "DNS:shuffle.localhost",
                "IP Address:127.0.0.1",
            ):
                self.assertIn(required_san, san_entries)
            self.assertNotIn("localhost.invalid", san_entries)
            self.assertNotIn("127.0.0.10", san_entries)

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

    def test_init_marks_changed_runtime_proxy_identity_for_recreation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            first = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(first.returncode, 0, first.stderr)
            runtime_root = (
                home / ".local" / "share" / "aegisops" / "phase-67-integration-lab"
            )
            marker = runtime_root / "proxy-certificate-recreate-required"
            proxy_secret = (
                runtime_root / "secrets" / "protected-surface-proxy-secret"
            )
            proxy_secret.write_text("a" * 64 + "\n", encoding="utf-8")

            second = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertTrue(marker.is_file())
            self.assertIn(
                'proxy_set_header X-AegisOps-Proxy-Secret "' + "a" * 64 + '";',
                (
                    runtime_root / "proxy-certs" / "runtime-auth.conf"
                ).read_text(encoding="utf-8"),
            )
            init_script = (LAB_DIR / "init.sh").read_text(encoding="utf-8")
            auth_update = init_script.index(
                'if ! cmp -s "${proxy_runtime_auth_staging}" '
                '"${proxy_runtime_auth}"; then'
            )
            self.assertLess(
                init_script.index(
                    ': >"${proxy_recreate_marker}"',
                    auth_update,
                ),
                init_script.index(
                    'mv "${proxy_runtime_auth_staging}" "${proxy_runtime_auth}"',
                    auth_update,
                ),
            )

    def test_selected_scope_checks_only_published_ports(self) -> None:
        expected = {
            "core": ["PROXY"],
            "wazuh": ["PROXY"],
            "shuffle": ["PROXY"],
            "full": ["PROXY"],
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
        expected = {"PROXY": "proxy"}
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

    def test_user_interfaces_are_available_only_through_the_proxy(self) -> None:
        compose = (LAB_DIR / "docker-compose.yml").read_text(encoding="utf-8")
        proxy = (LAB_DIR / "config" / "control-plane.conf").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("AEGISOPS_LAB_WAZUH_DASHBOARD_PORT", compose)
        self.assertNotIn("AEGISOPS_LAB_SHUFFLE_FRONTEND_PORT", compose)
        self.assertIn("server_name wazuh.localhost;", proxy)
        self.assertIn("server_name shuffle.localhost;", proxy)
        self.assertIn("proxy_pass $phase67_wazuh_dashboard;", proxy)
        self.assertIn("proxy_pass $phase67_shuffle_frontend;", proxy)
        self.assertIn(
            "allow ${AEGISOPS_LAB_CONTROL_PLANE_IPV4};",
            proxy,
        )
        self.assertIn(
            "AEGISOPS_LAB_CONTROL_PLANE_IPV4: "
            "${AEGISOPS_LAB_CONTROL_PLANE_IPV4:-172.31.67.20}",
            compose,
        )
        self.assertIn(
            "NGINX_ENVSUBST_FILTER: ^AEGISOPS_LAB_CONTROL_PLANE_IPV4$",
            compose,
        )
        self.assertIn(
            "./config/control-plane.conf:"
            "/etc/nginx/templates/control-plane.conf.template:ro",
            compose,
        )

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
            "0016_phase_67_action_execution_dispatching_state.sql",
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
        self.assertIn(
            "'lifecycle_transition_records_previous_lifecycle_state_known_val'",
            entrypoint,
        )
        self.assertIn("constraint_definition_sha256", entrypoint)
        self.assertIn("constraint_record.contype::text", entrypoint)
        self.assertIn(
            "sha256(\n"
            "          convert_to(\n"
            "            pg_get_constraintdef(constraint_record.oid, true),",
            entrypoint,
        )
        self.assertIn("AND constraint_record.convalidated", entrypoint)
        self.assertIn(
            "e2595161f20c3faf32d1891f26f6c8ee"
            "eb08c40c73a6db8ebb495bdec6fb7bba",
            entrypoint,
        )
        self.assertIn(
            "c0eecfc71b9e55e2ee8d2712cbee144"
            "8497f847711f67a4f74977155de559920",
            entrypoint,
        )
        self.assertIn(
            "f88e5cdaaa4b0079bfcadd42c335b0b2"
            "2722fd4f856ed1e1a609b4fdf6589f6f",
            entrypoint,
        )
        self.assertGreaterEqual(entrypoint.count("constraint_definition_sha256"), 3)
        self.assertGreaterEqual(entrypoint.count("column_definition_sha256"), 3)
        self.assertIn("COALESCE(column_default, '<NULL>')", entrypoint)
        self.assertIn(
            "c8fc21a6b5137a90c9b0590994e7894a"
            "3530d1832b06b3877375437c0a0f84ef",
            entrypoint,
        )
        self.assertIn(
            "cb6ee538dcb158f0bc6a25bddd04f9ff"
            "6f38c3a5d2fb88d0922cf06f0cf555f7",
            entrypoint,
        )
        self.assertIn(
            "6854488c1104636fedc6452212aedaf54"
            "5a2a3447ebde3b47af026b693bb8f1e",
            entrypoint,
        )
        phase13_readiness = entrypoint.split(
            "0013_phase_61_detector_lifecycle_records.sql)",
            maxsplit=1,
        )[1].split(
            "0014_phase_61_source_health_records.sql)",
            maxsplit=1,
        )[0]
        phase14_readiness = entrypoint.split(
            "0014_phase_61_source_health_records.sql)",
            maxsplit=1,
        )[1].split(
            "0015_phase_64_known_limitation_ownership_records.sql)",
            maxsplit=1,
        )[0]
        phase15_readiness = entrypoint.split(
            "0015_phase_64_known_limitation_ownership_records.sql)",
            maxsplit=1,
        )[1].split(
            "0016_phase_67_action_execution_dispatching_state.sql)",
            maxsplit=1,
        )[0]
        self.assertNotIn(
            "lifecycle_transition_records_subject_family_matches",
            phase13_readiness,
        )
        self.assertNotIn(
            "lifecycle_transition_records_subject_family_matches",
            phase14_readiness,
        )
        self.assertIn(
            "lifecycle_transition_records_subject_family_matches",
            phase15_readiness,
        )
        phase16_readiness = entrypoint.split(
            "0016_phase_67_action_execution_dispatching_state.sql)",
            maxsplit=1,
        )[1]
        self.assertIn(
            "action_execution_records_lifecycle_state_check",
            phase16_readiness,
        )
        self.assertIn(
            "5b340453651de616ba658ab802f574a909f04bccf7e7c483a5ba92c6d50b8c9e",
            phase16_readiness,
        )
        self.assertIn("AND indnkeyatts = 1", entrypoint)
        self.assertIn("AND indnatts = 1", entrypoint)
        self.assertIn("AND indexprs IS NULL", entrypoint)
        self.assertIn("AND indpred IS NULL", entrypoint)
        self.assertIn(
            "pg_get_indexdef(indexrelid, 1, true) = 'idempotency_key'",
            entrypoint,
        )
        self.assertIn(
            "pg_get_indexdef(indexrelid) = 'CREATE INDEX "
            "reconciliation_records_correlation_alert_latest_idx ON "
            "aegisops_control.reconciliation_records USING btree "
            "(correlation_key, compared_at DESC, reconciliation_id DESC) "
            "WHERE (alert_id IS NOT NULL)'",
            entrypoint,
        )
        self.assertIn(
            "pg_get_indexdef(indexrelid) = 'CREATE INDEX "
            "ai_trace_records_latest_idx ON aegisops_control.ai_trace_records "
            "USING btree (generated_at DESC, ai_trace_id DESC)'",
            entrypoint,
        )
        self.assertIn(
            "('evidence_records', 'provenance', 'jsonb', 'NO', "
            "$default$'{}'::jsonb$default$)",
            entrypoint,
        )
        self.assertIn(
            "SELECT table_name, column_name, udt_name, is_nullable, column_default",
            entrypoint,
        )
        self.assertIn("AND column_default IS NULL", entrypoint)
        self.assertIn(
            "pg_get_constraintdef(constraint_record.oid, true)",
            entrypoint,
        )
        self.assertIn(
            "CHECK (coordination_target_type IS NULL OR "
            "(coordination_target_type = ANY "
            "(ARRAY['glpi'::text, 'zammad'::text])))",
            entrypoint,
        )
        self.assertIn("prove_delegated_migration_definitions", entrypoint)
        self.assertIn(
            "final schema definitions for delegated migrations 0001-0007",
            entrypoint,
        )
        for catalog_hash in (
            "d906ba1ab5288c94b5c277c1aad60d6d"
            "df499ad2aed55a2abde8729e639d3443",
            "5de18095fdfcf3c0d223a45280d3b96a"
            "699dde0ebdc6e11328a1a936fb39d8de",
            "ba3907928c1c026b50f3a9e37c870d6c"
            "0008dddb2ebeccf9001cf937898c7d4f",
        ):
            self.assertIn(catalog_hash, entrypoint)
        self.assertLess(
            entrypoint.rindex('"${migrations_dir}"/0016_*.sql'),
            entrypoint.index("if ! prove_delegated_migration_definitions"),
        )
        self.assertLess(
            entrypoint.index("if ! prove_delegated_migration_definitions"),
            entrypoint.index('exec "$@"'),
        )

    def test_scope_narrowing_rejects_running_excluded_services(self) -> None:
        command = (
            'source "$1"; '
            'compose_scope() { printf "%s\\n" "${PHASE67_RUNNING_SERVICES:-}"; }; '
            'assert_no_running_excluded_services "$2"'
        )
        for scope, running_service in (
            ("core", "wazuh-dashboard"),
            ("core", "shuffle-orborus"),
            ("wazuh", "shuffle-frontend"),
            ("wazuh", "shuffle-orborus"),
            ("shuffle", "wazuh-manager"),
        ):
            with self.subTest(scope=scope, running_service=running_service):
                env = os.environ.copy()
                env["PHASE67_RUNNING_SERVICES"] = (
                    f"postgres\n{running_service}\n"
                )
                rejected = subprocess.run(
                    [
                        "bash",
                        "-c",
                        command,
                        "phase67-scope-test",
                        str(LAB_DIR / "lab-common.sh"),
                        scope,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=env,
                )
                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn(
                    f"scope '{scope}' excludes running services: "
                    f"{running_service}",
                    rejected.stderr,
                )

        env = os.environ.copy()
        env["PHASE67_RUNNING_SERVICES"] = "wazuh-dashboard\nshuffle-frontend\n"
        accepted = subprocess.run(
            [
                "bash",
                "-c",
                command,
                "phase67-scope-test",
                str(LAB_DIR / "lab-common.sh"),
                "full",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_every_external_runtime_image_is_digest_pinned(self) -> None:
        compose = (LAB_DIR / "docker-compose.yml").read_text(encoding="utf-8")
        for line in compose.splitlines():
            stripped = line.strip()
            if not stripped.startswith("image:"):
                continue
            image = stripped.removeprefix("image:").strip()
            if image.endswith("-control-plane:local"):
                continue
            self.assertRegex(image, r"@sha256:[0-9a-f]{64}$")

        dockerfile = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "Dockerfile"
        ).read_text(encoding="utf-8")
        self.assertRegex(
            dockerfile.splitlines()[0],
            r"^FROM python:3\.12-slim-bookworm@sha256:[0-9a-f]{64}$",
        )
        prepare = (LAB_DIR / "prepare-substrates.sh").read_text(encoding="utf-8")
        self.assertRegex(
            prepare,
            r'cert_image="wazuh/wazuh-certs-generator:0\.0\.4'
            r'@sha256:[0-9a-f]{64}"',
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

    def test_logs_requires_positive_bounded_integer_tail(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = pathlib.Path(tmpdir)
            init_result = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            base_env = os.environ.copy()
            base_env["HOME"] = str(home)

            for log_tail in ("all", "0", "-1", "01", "10001", " 200"):
                for service_arguments in ((), ("control-plane",)):
                    with self.subTest(
                        log_tail=log_tail,
                        service_arguments=service_arguments,
                    ):
                        env = base_env.copy()
                        env["AEGISOPS_LAB_LOG_TAIL"] = log_tail
                        result = subprocess.run(
                            [
                                "bash",
                                str(LAB_DIR / "logs.sh"),
                                *service_arguments,
                            ],
                            check=False,
                            capture_output=True,
                            text=True,
                            env=env,
                        )
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn(
                            "must be an integer from 1 through 10000",
                            result.stderr,
                        )

            logs = (LAB_DIR / "logs.sh").read_text(encoding="utf-8")
            self.assertEqual(logs.count('--tail "${log_tail}"'), 2)

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
            prepare.index("assert_reviewed_wazuh_checkout"),
            prepare.index('"${LAB_DIR}/preflight.sh" --scope wazuh'),
        )
        self.assertLess(
            prepare.index('"${LAB_DIR}/preflight.sh" --scope wazuh'),
            prepare.index("docker_lab run --rm"),
        )
        self.assertLess(
            up.index("assert_reviewed_wazuh_checkout"),
            up.index("validate_wazuh_certificate_bundle"),
        )
        self.assertIn("assert_reviewed_file_digest", up)
        self.assertIn("record_reviewed_file_digest", prepare)
        self.assertIn(
            "mark_wazuh_recreation_required\n"
            '  docker_lab cp "${cert_container}:/certificates/." "${cert_dir}"',
            prepare,
        )
        self.assertIn(
            'internal_users="${AEGISOPS_LAB_WAZUH_CONFIG_DIR}/'
            'wazuh_indexer/internal_users.yml"\n'
            "mark_wazuh_recreation_required\n"
            "python3 -",
            prepare,
        )
        self.assertIn(
            "The next wazuh/full up.sh run will force service recreation.",
            prepare,
        )
        self.assertIn("normalize_managed_hashes(current)", prepare)
        self.assertIn('"kibanaserver", dashboard_hash', prepare)
        self.assertIn(
            '("kibanaro", "logstash", "readall", "snapshotrestore")',
            prepare,
        )
        self.assertIn(
            "unreviewed changes outside managed hashes",
            prepare,
        )
        self.assertIn(
            'proxy_wazuh_trust="${AEGISOPS_LAB_PROXY_CERT_DIR}/'
            'wazuh-upstream-root-ca.pem"',
            prepare,
        )
        self.assertLess(
            prepare.index(': >"${proxy_recreate_marker}"'),
            prepare.index('mv "${proxy_wazuh_trust_staging}"'),
        )
        self.assertIn("proxy Wazuh trust certificate is stale", up)

        proxy_config = (LAB_DIR / "config" / "control-plane.conf").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "proxy_ssl_trusted_certificate "
            "/etc/nginx/certs/wazuh-upstream-root-ca.pem;",
            proxy_config,
        )
        self.assertIn("proxy_ssl_verify on;", proxy_config)
        self.assertNotIn("proxy_ssl_verify off;", proxy_config)
        runtime_location = proxy_config.split("location = /runtime {", maxsplit=1)[1]
        runtime_location = runtime_location.split("}", maxsplit=1)[0]
        self.assertIn(
            "include /etc/nginx/certs/runtime-auth.conf;",
            runtime_location,
        )
        smoke_core = (LAB_DIR / "smoke-core.sh").read_text(encoding="utf-8")
        self.assertIn("for endpoint in healthz readyz runtime; do", smoke_core)

    def test_wazuh_certificate_bundle_requires_valid_chains_and_key_pairs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_dir = pathlib.Path(tmpdir)
            ca_key = cert_dir / "ca.key"
            ca_cert = cert_dir / "ca.pem"
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
            for root_name in ("root-ca.pem", "root-ca-manager.pem"):
                shutil.copy2(ca_cert, cert_dir / root_name)

            def create_leaf(
                identity: str,
                certificate_name: str,
                key_name: str,
                include_san: bool,
            ) -> None:
                request = cert_dir / f"{identity}.csr"
                subprocess.run(
                    [
                        "openssl",
                        "req",
                        "-newkey",
                        "rsa:2048",
                        "-nodes",
                        "-keyout",
                        str(cert_dir / key_name),
                        "-out",
                        str(request),
                        "-subj",
                        f"/CN={identity}",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                sign_command = [
                    "openssl",
                    "x509",
                    "-req",
                    "-in",
                    str(request),
                    "-CA",
                    str(ca_cert),
                    "-CAkey",
                    str(ca_key),
                    "-CAcreateserial",
                    "-out",
                    str(cert_dir / certificate_name),
                    "-days",
                    "30",
                    "-sha256",
                ]
                if include_san:
                    extensions = cert_dir / f"{identity}.ext"
                    extensions.write_text(
                        f"subjectAltName=DNS:{identity}\n",
                        encoding="utf-8",
                    )
                    sign_command.extend(["-extfile", str(extensions)])
                subprocess.run(
                    sign_command,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            create_leaf(
                "wazuh.indexer",
                "wazuh.indexer.pem",
                "wazuh.indexer-key.pem",
                True,
            )
            create_leaf("admin", "admin.pem", "admin-key.pem", False)
            create_leaf(
                "wazuh.manager",
                "wazuh.manager.pem",
                "wazuh.manager-key.pem",
                True,
            )
            create_leaf(
                "wazuh.dashboard",
                "wazuh.dashboard.pem",
                "wazuh.dashboard-key.pem",
                True,
            )

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

            dashboard_certificate = (cert_dir / "wazuh.dashboard.pem").read_bytes()
            dashboard_key = (cert_dir / "wazuh.dashboard-key.pem").read_bytes()
            shutil.copy2(
                cert_dir / "wazuh.indexer.pem",
                cert_dir / "wazuh.dashboard.pem",
            )
            shutil.copy2(
                cert_dir / "wazuh.indexer-key.pem",
                cert_dir / "wazuh.dashboard-key.pem",
            )
            wrong_identity = subprocess.run(
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
            self.assertNotEqual(wrong_identity.returncode, 0)
            (cert_dir / "wazuh.dashboard.pem").write_bytes(dashboard_certificate)
            (cert_dir / "wazuh.dashboard-key.pem").write_bytes(dashboard_key)

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
        self.assertIn('proxy_config_state="${AEGISOPS_LAB_RUNTIME_ROOT}/', up)
        self.assertIn("proxy-config.sha256", up)
        self.assertIn('cat "${LAB_DIR}/config/nginx.conf"', up)
        self.assertIn('cat "${LAB_DIR}/config/control-plane.conf"', up)
        self.assertIn("wazuh-certificate-recreate-required", up)
        self.assertIn("--force-recreate", up)
        self.assertIn('rm -f "${proxy_recreate_marker}"', up)
        self.assertLess(
            up.index('mv "${proxy_config_state_staging}" "${proxy_config_state}"'),
            up.index('rm -f "${proxy_recreate_marker}"'),
        )

    def test_status_evidence_records_running_control_plane_image_id(self) -> None:
        status = (LAB_DIR / "status.sh").read_text(encoding="utf-8")
        self.assertIn(
            'compose_scope "${scope}" ps --all --quiet control-plane',
            status,
        )
        self.assertIn("control_plane_container_image_id", status)
        self.assertIn("^sha256:[0-9a-f]{64}$", status)

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

    def test_init_migrates_dashboard_credential_once_then_fails_closed(
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
            dashboard_credential = (
                runtime_root / "secrets" / "wazuh-dashboard-password"
            )

            legacy_runtime_lines = [
                line
                for line in runtime_env.read_text(encoding="utf-8").splitlines()
                if not line.startswith("AEGISOPS_LAB_WAZUH_DASHBOARD_PASSWORD=")
            ]
            runtime_env.write_text(
                "\n".join(legacy_runtime_lines) + "\n",
                encoding="utf-8",
            )
            dashboard_credential.unlink()

            migrated = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            self.assertTrue(dashboard_credential.is_file())
            self.assertIn(
                "AEGISOPS_LAB_WAZUH_DASHBOARD_PASSWORD=",
                runtime_env.read_text(encoding="utf-8"),
            )

            dashboard_credential.unlink()
            missing = self._run_init(home, LAB_DIR / "bootstrap.env.sample")
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn(
                "initialized runtime is missing credential "
                "wazuh-dashboard-password",
                missing.stderr,
            )
            self.assertFalse(dashboard_credential.exists())

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
        self.assertIn("binfmt_handler_enabled", preflight)
        self.assertIn(
            "grep -qx enabled /proc/sys/fs/binfmt_misc/status",
            preflight,
        )
        self.assertIn(
            'grep -qx enabled "${handler_path}"',
            preflight,
        )
        self.assertIn("'test -x /mnt/lima-rosetta/rosetta'", preflight)
        self.assertNotIn(
            "test -e /proc/sys/fs/binfmt_misc/qemu-",
            preflight,
        )
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
                'case "$*" in\n'
                '  *" ps --all --quiet control-plane") '
                'printf "phase67-control-plane\\n" ;;\n'
                '  *" inspect --format {{.Image}} phase67-control-plane") '
                'printf "sha256:%064d\\n" 0 ;;\n'
                '  *) printf "phase67-status\\n" ;;\n'
                "esac\n",
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
                evidence_text = evidence_file.read_text(encoding="utf-8")
                self.assertIn("phase67-status", evidence_text)
                self.assertIn(
                    "control_plane_container_image_id=sha256:"
                    + "0" * 64,
                    evidence_text,
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
