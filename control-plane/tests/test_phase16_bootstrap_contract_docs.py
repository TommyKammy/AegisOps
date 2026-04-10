from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase16BootstrapContractDocsTests(unittest.TestCase):
    @staticmethod
    def _scope_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-16-release-state-and-first-boot-scope.md"

    def test_phase16_scope_doc_exists(self) -> None:
        design_doc = self._scope_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 16 design doc at {design_doc}")

    def test_phase16_scope_doc_defines_bootstrap_contracts(self) -> None:
        design_doc = self._scope_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 16 design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "Bootstrap Environment Contract",
            "Migration Bootstrap Contract",
            "Healthcheck and Readiness Contract",
            "Deployment-Entrypoint Contract",
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN",
            "must fail closed",
            "migration bootstrap",
            "Healthcheck success",
            "readiness",
            "deployment entrypoint",
        ):
            self.assertIn(term, text)

    def test_first_boot_bootstrap_artifacts_exist_and_stay_narrow(self) -> None:
        bootstrap_sample = REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "bootstrap.env.sample"
        compose_skeleton = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "docker-compose.yml"
        )
        entrypoint_skeleton = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "control-plane-entrypoint.sh"
        )

        for path in (bootstrap_sample, compose_skeleton, entrypoint_skeleton):
            self.assertTrue(path.exists(), f"expected first-boot artifact at {path}")

        bootstrap_text = bootstrap_sample.read_text(encoding="utf-8")
        for term in (
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN=",
            "AEGISOPS_CONTROL_PLANE_HOST=",
            "AEGISOPS_CONTROL_PLANE_PORT=",
            "AEGISOPS_CONTROL_PLANE_BOOT_MODE=first-boot",
            "AEGISOPS_CONTROL_PLANE_LOG_LEVEL=INFO",
            "Optional and deferred components below must remain non-blocking for first boot.",
            "AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL=",
            "AEGISOPS_CONTROL_PLANE_N8N_BASE_URL=",
            "AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL=",
            "AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL=",
        ):
            self.assertIn(term, bootstrap_text)

        compose_text = compose_skeleton.read_text(encoding="utf-8")
        for term in (
            "name: aegisops-first-boot",
            "control-plane:",
            "postgres:",
            "proxy:",
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN: ${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN:?set-in-untracked-runtime-env}",
            "AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL: ${AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL:-}",
            "AEGISOPS_CONTROL_PLANE_N8N_BASE_URL: ${AEGISOPS_CONTROL_PLANE_N8N_BASE_URL:-}",
            "AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL: ${AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL:-}",
            "AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL: ${AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL:-}",
            "do not add OpenSearch, n8n, analyst-assistant UI, or executor services here",
        ):
            self.assertIn(term, compose_text)

        entrypoint_text = entrypoint_skeleton.read_text(encoding="utf-8")
        for term in (
            "AEGISOPS_CONTROL_PLANE_BOOT_MODE",
            "AEGISOPS_CONTROL_PLANE_LOG_LEVEL",
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN",
            "migration bootstrap",
            "readiness",
            "OpenSearch, n8n, the full analyst-assistant surface, and executor wiring remain deferred",
            "exec \"$@\"",
        ):
            self.assertIn(term, entrypoint_text)

    def test_first_boot_entrypoint_requires_control_plane_host(self) -> None:
        result = self._run_entrypoint(
            {
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "postgresql://user:pass@postgres:5432/aegisops",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing required first-boot setting: AEGISOPS_CONTROL_PLANE_HOST", result.stderr)

    def test_first_boot_entrypoint_rejects_non_postgres_dsn(self) -> None:
        result = self._run_entrypoint(
            {
                "AEGISOPS_CONTROL_PLANE_HOST": "127.0.0.1",
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "mysql://user:pass@postgres:3306/aegisops",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN must be a PostgreSQL DSN for the first-boot runtime.",
            result.stderr,
        )

    def test_first_boot_entrypoint_rejects_direct_backend_publication_host(self) -> None:
        result = self._run_entrypoint(
            {
                "AEGISOPS_CONTROL_PLANE_HOST": "0.0.0.0",
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "postgresql://user:pass@postgres:5432/aegisops",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_HOST must not publish the control-plane backend directly.",
            result.stderr,
        )

    def test_first_boot_entrypoint_rejects_invalid_boot_mode(self) -> None:
        result = self._run_entrypoint(
            {
                "AEGISOPS_CONTROL_PLANE_HOST": "127.0.0.1",
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "postgresql://user:pass@postgres:5432/aegisops",
                "AEGISOPS_CONTROL_PLANE_BOOT_MODE": "serve-now",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_BOOT_MODE must remain first-boot for the reviewed startup path.",
            result.stderr,
        )

    def test_first_boot_entrypoint_rejects_invalid_log_level(self) -> None:
        result = self._run_entrypoint(
            {
                "AEGISOPS_CONTROL_PLANE_HOST": "127.0.0.1",
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "postgresql://user:pass@postgres:5432/aegisops",
                "AEGISOPS_CONTROL_PLANE_LOG_LEVEL": "TRACE",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_LOG_LEVEL must be one of DEBUG, INFO, WARNING, ERROR, or CRITICAL.",
            result.stderr,
        )

    def test_first_boot_entrypoint_fails_closed_without_migration_bootstrap_proof(self) -> None:
        result = self._run_entrypoint(
            {
                "AEGISOPS_CONTROL_PLANE_HOST": "127.0.0.1",
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "postgresql://user:pass@postgres:5432/aegisops",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("migration bootstrap", result.stderr)

    def test_first_boot_entrypoint_executes_command_after_migration_bootstrap_and_readiness_proof(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = pathlib.Path(tmpdir)
            migrations_dir = temp_root / "migrations"
            migrations_dir.mkdir()
            for migration_name in (
                "0001_control_plane_schema_skeleton.sql",
                "0002_phase_14_reviewed_context_columns.sql",
                "0003_phase_15_assistant_advisory_draft_columns.sql",
            ):
                shutil.copy2(
                    REPO_ROOT / "postgres" / "control-plane" / "migrations" / migration_name,
                    migrations_dir / migration_name,
                )

            psql_path = temp_root / "fake-psql.sh"
            psql_log = temp_root / "fake-psql.log"
            psql_path.write_text(
                """#!/bin/sh
set -eu
file_path=""
query_text=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    -f)
      shift
      file_path="$1"
      ;;
    -c)
      shift
      query_text="$1"
      ;;
  esac
  shift
done

if [ -n "$file_path" ]; then
  printf 'migration:%s\\n' "$file_path" >> "$AEGISOPS_TEST_PSQL_LOG"
  exit 0
fi

if [ -n "$query_text" ]; then
  printf 'readiness:%s\\n' "$query_text" >> "$AEGISOPS_TEST_PSQL_LOG"
  printf 'ready'
  exit 0
fi

echo "unexpected psql invocation" >&2
exit 1
""",
                encoding="utf-8",
            )
            psql_path.chmod(0o755)

            result = self._run_entrypoint(
                {
                    "AEGISOPS_CONTROL_PLANE_HOST": "127.0.0.1",
                    "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "postgresql://user:pass@postgres:5432/aegisops",
                    "AEGISOPS_CONTROL_PLANE_BOOT_MODE": "first-boot",
                    "AEGISOPS_CONTROL_PLANE_LOG_LEVEL": "INFO",
                    "AEGISOPS_FIRST_BOOT_MIGRATIONS_DIR": str(migrations_dir),
                    "AEGISOPS_FIRST_BOOT_PSQL_BIN": str(psql_path),
                    "AEGISOPS_TEST_PSQL_LOG": str(psql_log),
                }
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "ok")
            self.assertEqual(result.stderr, "")
            psql_log_text = psql_log.read_text(encoding="utf-8")
            self.assertIn(
                f"migration:{migrations_dir / '0001_control_plane_schema_skeleton.sql'}",
                psql_log_text,
            )
            self.assertIn(
                f"migration:{migrations_dir / '0002_phase_14_reviewed_context_columns.sql'}",
                psql_log_text,
            )
            self.assertIn(
                f"migration:{migrations_dir / '0003_phase_15_assistant_advisory_draft_columns.sql'}",
                psql_log_text,
            )
            self.assertIn("readiness:SELECT CASE", psql_log_text)

    @staticmethod
    def _run_entrypoint(env_overrides: dict[str, str]) -> subprocess.CompletedProcess[str]:
        entrypoint = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "control-plane-entrypoint.sh"
        )
        env = {
            "PATH": "/usr/bin:/bin",
            **env_overrides,
        }

        return subprocess.run(
            ["sh", str(entrypoint), "printf", "ok"],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )


if __name__ == "__main__":
    unittest.main()
