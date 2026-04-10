from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = CONTROL_PLANE_ROOT.parent
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import AlertRecord
from aegisops_control_plane.service import AegisOpsControlPlaneService
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
                            "postgresql://aegisops_control_plane:secret@postgres:5432/"
                            "aegisops_control_plane"
                        ),
                        "AEGISOPS_CONTROL_PLANE_POSTGRES_PASSWORD=secret",
                        "",
                    )
                ),
                encoding="utf-8",
            )

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
            self.assertCountEqual(
                services_result.stdout.splitlines(),
                ["control-plane", "postgres", "proxy"],
            )

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

            output = "\n".join((dry_run_result.stdout, dry_run_result.stderr))
            for term in (
                "Network aegisops-first-boot_default",
                "Container aegisops-first-boot-postgres-1",
                "Container aegisops-first-boot-control-plane-1",
                "Container aegisops-first-boot-proxy-1",
            ):
                self.assertIn(term, output)

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

    def _run_docker_compose(
        self,
        docker_bin: str,
        compose_path: pathlib.Path,
        env_path: pathlib.Path,
        *compose_args: str,
    ) -> subprocess.CompletedProcess[str]:
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
                timeout=30,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(
                "docker compose command timed out after 30 seconds:"
                f" {' '.join(exc.cmd)}"
            )


if __name__ == "__main__":
    unittest.main()
