from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = CONTROL_PLANE_ROOT.parent
DOCKER_COMPOSE_RENDER_TIMEOUT_SECONDS = 30
DOCKER_COMPOSE_DRY_RUN_TIMEOUT_SECONDS = 120
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.models import AlertRecord
from aegisops.control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import FakePostgresBackend, make_store


class Phase17BootPathValidationTests(unittest.TestCase):
    def test_first_boot_compose_dry_run_covers_reviewed_bring_up_path(self) -> None:
        docker_bin = shutil.which("docker")
        if docker_bin is None:
            self.skipTest("docker CLI is not available in PATH")

        compose_path = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "docker-compose.yml"
        )
        self.assertTrue(compose_path.exists(), f"expected first-boot compose at {compose_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = pathlib.Path(tmpdir) / ".env"
            env_path.write_text(
                "\n".join(
                    (
                        (
                            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN="
                            "postgresql://aegisops.control_plane:secret@postgres:5432/"
                            "aegisops.control_plane"
                        ),
                        "AEGISOPS_CONTROL_PLANE_POSTGRES_PASSWORD=secret",
                        "",
                    )
                ),
                encoding="utf-8",
            )

            self._validate_first_boot_compose_boot_path(
                docker_bin,
                compose_path,
                env_path,
            )

    def test_first_boot_compose_uses_hermetic_contract_checks_when_daemon_is_unavailable(
        self,
    ) -> None:
        compose_path = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "docker-compose.yml"
        )
        self.assertTrue(compose_path.exists(), f"expected first-boot compose at {compose_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = pathlib.Path(tmpdir) / ".env"
            env_path.write_text(
                "\n".join(
                    (
                        (
                            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN="
                            "postgresql://aegisops.control_plane:secret@postgres:5432/"
                            "aegisops.control_plane"
                        ),
                        "AEGISOPS_CONTROL_PLANE_POSTGRES_PASSWORD=secret",
                        "",
                    )
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                self,
                "_run_docker_compose",
                side_effect=(
                    self._completed_process(stdout="postgres\ncontrol-plane\nproxy\n"),
                    self._completed_process(
                        stdout="\n".join(
                            (
                                "name: aegisops-first-boot",
                                "services:",
                                "  control-plane:",
                                "    image: aegisops-control-plane:first-boot",
                                "    depends_on:",
                                "      postgres:",
                                "        condition: service_started",
                                "    environment:",
                                "      AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE: /run/aegisops-secrets/control-plane-postgres-dsn",
                                "      AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH: \"\"",
                                "      AEGISOPS_CONTROL_PLANE_BOOT_MODE: first-boot",
                                "      AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE: /run/aegisops-secrets/wazuh-shared-secret",
                                "      AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH: \"\"",
                                "      AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE: /run/aegisops-secrets/wazuh-reverse-proxy-secret",
                                "      AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH: \"\"",
                                "      AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS: 172.20.0.10/32",
                                "      AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE: /run/aegisops-secrets/protected-surface-reverse-proxy-secret",
                                "      AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH: \"\"",
                                "      AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS: 172.20.0.10/32",
                                "      AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT: svc-aegisops-proxy-control-plane",
                                "      AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER: authentik",
                                "      AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE: /run/aegisops-secrets/admin-bootstrap-token",
                                "      AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH: \"\"",
                                "      AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE: /run/aegisops-secrets/break-glass-token",
                                "      AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH: \"\"",
                                "      AEGISOPS_OPENBAO_ADDRESS: \"\"",
                                "      AEGISOPS_OPENBAO_TOKEN: \"\"",
                                "      AEGISOPS_OPENBAO_TOKEN_FILE: \"\"",
                                "      AEGISOPS_OPENBAO_KV_MOUNT: secret",
                                "  postgres:",
                                "    image: postgres:16.4",
                                "  proxy:",
                                '    image: nginx:1.27.0',
                                "    ports:",
                                '      - mode: ingress',
                                '        published: "8080"',
                                "networks:",
                                "  default:",
                                "    name: aegisops-first-boot_default",
                                "",
                            )
                        )
                    ),
                ),
            ) as run_compose, mock.patch.object(
                self,
                "_docker_daemon_is_available",
                return_value=False,
            ):
                self._validate_first_boot_compose_boot_path(
                    "/usr/bin/docker",
                    compose_path,
                    env_path,
                )

        self.assertEqual(run_compose.call_count, 2)

    def test_first_boot_compose_hermetic_contract_checks_fail_on_compose_drift(self) -> None:
        with self.assertRaisesRegex(
            AssertionError,
            r"expected rendered compose contract to include",
        ):
            self._assert_compose_render_contract(
                "\n".join(
                    (
                        "name: aegisops-first-boot",
                        "services:",
                        "  control-plane:",
                        "    image: aegisops-control-plane:first-boot",
                        "    depends_on:",
                        "      postgres:",
                        "    environment:",
                        "      AEGISOPS_CONTROL_PLANE_BOOT_MODE: first-boot",
                        "  postgres:",
                        "    image: postgres:16.4",
                        "networks:",
                        "  default:",
                        "    name: aegisops-first-boot_default",
                        "",
                    )
                )
            )

    def test_first_boot_compose_timeout_policy_allows_more_time_for_dry_run(self) -> None:
        self.assertEqual(
            self._docker_compose_timeout_seconds("config", "--services"),
            DOCKER_COMPOSE_RENDER_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            self._docker_compose_timeout_seconds("config"),
            DOCKER_COMPOSE_RENDER_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            self._docker_compose_timeout_seconds("up", "--dry-run"),
            DOCKER_COMPOSE_DRY_RUN_TIMEOUT_SECONDS,
        )

    def test_postgresql_runtime_persists_records_across_service_restart(self) -> None:
        backend = FakePostgresBackend()
        seed_service = self._make_service(backend)
        persisted_alert = seed_service.persist_record(
            AlertRecord(
                alert_id="alert-phase17-restart",
                finding_id="finding-phase17-restart",
                analytic_signal_id=None,
                case_id=None,
                lifecycle_state="new",
            )
        )

        restarted_service = self._make_service(backend)

        self.assertEqual(
            restarted_service.describe_runtime().persistence_mode,
            "postgresql",
        )
        self.assertEqual(
            restarted_service.get_record(AlertRecord, persisted_alert.alert_id),
            persisted_alert,
        )

        inspection = restarted_service.inspect_records("alert")
        self.assertEqual(inspection.total_records, 1)
        self.assertEqual(inspection.records[0]["alert_id"], persisted_alert.alert_id)
        self.assertEqual(inspection.records[0]["finding_id"], "finding-phase17-restart")

    def test_postgresql_runtime_rejects_invalid_record_state_fail_closed(self) -> None:
        backend = FakePostgresBackend()
        service = self._make_service(backend)

        with self.assertRaisesRegex(
            ValueError,
            r"alert record 'alert-phase17-invalid' has invalid lifecycle_state 'invalid'",
        ):
            service.persist_record(
                AlertRecord(
                    alert_id="alert-phase17-invalid",
                    finding_id="finding-phase17-invalid",
                    analytic_signal_id=None,
                    case_id=None,
                    lifecycle_state="invalid",
                )
            )

        restarted_service = self._make_service(backend)
        self.assertIsNone(
            restarted_service.get_record(AlertRecord, "alert-phase17-invalid")
        )
        inspection = restarted_service.inspect_records("alert")
        self.assertEqual(inspection.total_records, 0)
        self.assertEqual(inspection.records, ())

    @staticmethod
    def _make_service(backend: FakePostgresBackend) -> AegisOpsControlPlaneService:
        store, _ = make_store(backend)
        return AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

    def _validate_first_boot_compose_boot_path(
        self,
        docker_bin: str,
        compose_path: pathlib.Path,
        env_path: pathlib.Path,
    ) -> None:
        services_result = self._run_docker_compose(
            docker_bin,
            compose_path,
            env_path,
            "config",
            "--services",
        )
        self.assertEqual(
            services_result.returncode,
            0,
            f"expected compose services render to pass\nstdout:\n{services_result.stdout}\nstderr:\n{services_result.stderr}",
        )
        self._assert_compose_services_contract(services_result.stdout)

        rendered_config_result = self._run_docker_compose(
            docker_bin,
            compose_path,
            env_path,
            "config",
        )
        self.assertEqual(
            rendered_config_result.returncode,
            0,
            f"expected compose config render to pass\nstdout:\n{rendered_config_result.stdout}\nstderr:\n{rendered_config_result.stderr}",
        )
        self._assert_compose_render_contract(rendered_config_result.stdout)

        if not self._docker_daemon_is_available(docker_bin):
            return

        dry_run_result = self._run_docker_compose(
            docker_bin,
            compose_path,
            env_path,
            "up",
            "--dry-run",
        )
        self.assertEqual(
            dry_run_result.returncode,
            0,
            f"expected compose dry-run bring-up to pass\nstdout:\n{dry_run_result.stdout}\nstderr:\n{dry_run_result.stderr}",
        )
        self._assert_compose_dry_run_contract(
            "\n".join((dry_run_result.stdout, dry_run_result.stderr))
        )

    def _assert_compose_services_contract(self, services_output: str) -> None:
        self.assertCountEqual(
            services_output.splitlines(),
            ["control-plane", "postgres", "proxy"],
        )

    def _assert_compose_render_contract(self, rendered_config: str) -> None:
        for term in (
            "name: aegisops-first-boot",
            "services:",
            "  control-plane:",
            "    image: aegisops-control-plane:first-boot",
            "    depends_on:",
            "      postgres:",
            "      AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE:",
            "      AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH:",
            "      AEGISOPS_CONTROL_PLANE_BOOT_MODE: first-boot",
            "      AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE:",
            "      AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH:",
            "      AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE:",
            "      AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH:",
            "      AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS:",
            "      AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE:",
            "      AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH:",
            "      AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS:",
            "      AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT:",
            "      AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER:",
            "      AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE:",
            "      AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH:",
            "      AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE:",
            "      AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH:",
            "      AEGISOPS_OPENBAO_ADDRESS:",
            "      AEGISOPS_OPENBAO_TOKEN:",
            "      AEGISOPS_OPENBAO_TOKEN_FILE:",
            "      AEGISOPS_OPENBAO_KV_MOUNT: secret",
            "  postgres:",
            "    image: postgres:16.4",
            "  proxy:",
            "    image: nginx:1.27.0",
            "    ports:",
            '      - mode: ingress',
            '        published: "8080"',
            "networks:",
            "  default:",
            "    name: aegisops-first-boot_default",
        ):
            self.assertIn(
                term,
                rendered_config,
                f"expected rendered compose contract to include {term!r}",
            )

    def _assert_compose_dry_run_contract(self, dry_run_output: str) -> None:
        for term in (
            "Network aegisops-first-boot_default",
            "Container aegisops-first-boot-postgres-1",
            "Container aegisops-first-boot-control-plane-1",
            "Container aegisops-first-boot-proxy-1",
        ):
            self.assertIn(term, dry_run_output)

    def _docker_daemon_is_available(self, docker_bin: str) -> bool:
        try:
            result = subprocess.run(
                [
                    docker_bin,
                    "info",
                    "--format",
                    "{{.ServerVersion}}",
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            return False
        return result.returncode == 0

    @staticmethod
    def _completed_process(
        *,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["docker", "compose"],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    def _docker_compose_timeout_seconds(self, *compose_args: str) -> int:
        if compose_args[:2] == ("up", "--dry-run"):
            return DOCKER_COMPOSE_DRY_RUN_TIMEOUT_SECONDS
        return DOCKER_COMPOSE_RENDER_TIMEOUT_SECONDS

    def _run_docker_compose(
        self,
        docker_bin: str,
        compose_path: pathlib.Path,
        env_path: pathlib.Path,
        *compose_args: str,
    ) -> subprocess.CompletedProcess[str]:
        timeout_seconds = self._docker_compose_timeout_seconds(*compose_args)
        try:
            return subprocess.run(
                [
                    docker_bin,
                    "compose",
                    "-f",
                    str(compose_path),
                    "--env-file",
                    str(env_path),
                    *compose_args,
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(
                f"docker compose command timed out after {timeout_seconds} seconds:"
                f" {' '.join(exc.cmd)}"
            )


if __name__ == "__main__":
    unittest.main()
