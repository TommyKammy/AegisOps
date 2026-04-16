from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase16BootstrapContractDocsTests(unittest.TestCase):
    _REQUIRED_MIGRATIONS = (
        "0001_control_plane_schema_skeleton.sql",
        "0002_phase_14_reviewed_context_columns.sql",
        "0003_phase_15_assistant_advisory_draft_columns.sql",
        "0004_phase_20_action_request_binding_columns.sql",
        "0005_phase_23_approval_decision_rationale.sql",
        "0006_phase_23_lifecycle_transition_records.sql",
        "0007_phase_23_lifecycle_transition_subject_index.sql",
    )

    @staticmethod
    def _scope_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-16-release-state-and-first-boot-scope.md"

    @staticmethod
    def _normalized_migration_checksum(path: pathlib.Path) -> str:
        checksum_parts = (
            subprocess.check_output(
                ["cksum"],
                input=path.read_bytes().replace(b"\r", b""),
            )
            .decode()
            .strip()
            .split()[0:2]
        )
        return ":".join(checksum_parts)

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
            "AEGISOPS_FIRST_BOOT_PROXY_PORT=8080",
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
            "0006_phase_23_lifecycle_transition_records.sql",
            "0007_phase_23_lifecycle_transition_subject_index.sql",
            "requester_identity",
            "requested_payload",
            "decision_rationale",
            "lifecycle_transition_records",
            "lifecycle_transition_records_subject_latest_idx",
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

    def test_first_boot_entrypoint_rejects_unsupported_wildcard_host_values(self) -> None:
        for host_value in ("::", "*"):
            with self.subTest(host_value=host_value):
                result = self._run_entrypoint(
                    {
                        "AEGISOPS_CONTROL_PLANE_HOST": host_value,
                        "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": (
                            "postgresql://user:pass@postgres:5432/aegisops"
                        ),
                    }
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    "AEGISOPS_CONTROL_PLANE_HOST must remain an explicit IPv4 or DNS bind target for the reviewed first-boot path.",
                    result.stderr,
                )

    def test_first_boot_entrypoint_rejects_malformed_host_values(self) -> None:
        for host_value in ("999.0.0.1", "host name", "host..internal", "proxy:8080", "-edge"):
            with self.subTest(host_value=host_value):
                result = self._run_entrypoint(
                    {
                        "AEGISOPS_CONTROL_PLANE_HOST": host_value,
                        "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": (
                            "postgresql://user:pass@postgres:5432/aegisops"
                        ),
                    }
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    "AEGISOPS_CONTROL_PLANE_HOST must remain an explicit IPv4 or DNS bind target for the reviewed first-boot path.",
                    result.stderr,
                )

    def test_first_boot_entrypoint_allows_internal_compose_bind_host(self) -> None:
        result = self._run_entrypoint(
            {
                "AEGISOPS_CONTROL_PLANE_HOST": "0.0.0.0",
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "postgresql://user:pass@postgres:5432/aegisops",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("migration bootstrap", result.stderr)

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
            for migration_name in self._REQUIRED_MIGRATIONS:
                shutil.copy2(
                    REPO_ROOT / "postgres" / "control-plane" / "migrations" / migration_name,
                    migrations_dir / migration_name,
                )

            psql_path = temp_root / "fake-psql.sh"
            psql_log = temp_root / "fake-psql.log"
            psql_state_dir = temp_root / "fake-psql-state"
            psql_state_dir.mkdir()
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
  migration_name="$(basename "$file_path")"
  : > "$AEGISOPS_TEST_PSQL_STATE_DIR/$migration_name"
  printf 'migration:%s\\n' "$file_path" >> "$AEGISOPS_TEST_PSQL_LOG"
  exit 0
fi

if [ -n "$query_text" ]; then
  case "$query_text" in
    *"schema_migration_bootstrap"* )
      printf 'metadata:%s\\n' "$query_text" >> "$AEGISOPS_TEST_PSQL_LOG"
      case "$query_text" in
        *"SELECT migration_checksum"* )
          exit 0
          ;;
        *"INSERT INTO aegisops_control.schema_migration_bootstrap"* )
          exit 0
          ;;
        *)
          exit 0
          ;;
      esac
      ;;
  esac
  printf 'readiness:%s\\n' "$query_text" >> "$AEGISOPS_TEST_PSQL_LOG"
  if [ -f "$AEGISOPS_TEST_PSQL_STATE_DIR/0001_control_plane_schema_skeleton.sql" ]; then
    printf 'ready'
  else
    printf 'not-ready'
  fi
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
                    "AEGISOPS_TEST_PSQL_STATE_DIR": str(psql_state_dir),
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
            self.assertIn(
                f"migration:{migrations_dir / '0004_phase_20_action_request_binding_columns.sql'}",
                psql_log_text,
            )
            self.assertIn(
                f"migration:{migrations_dir / '0005_phase_23_approval_decision_rationale.sql'}",
                psql_log_text,
            )
            self.assertIn(
                f"migration:{migrations_dir / '0006_phase_23_lifecycle_transition_records.sql'}",
                psql_log_text,
            )
            self.assertIn(
                f"migration:{migrations_dir / '0007_phase_23_lifecycle_transition_subject_index.sql'}",
                psql_log_text,
            )
            self.assertIn("readiness:SELECT CASE", psql_log_text)

    def test_first_boot_entrypoint_is_restart_safe_and_does_not_replay_applied_migrations(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = pathlib.Path(tmpdir)
            migrations_dir = temp_root / "migrations"
            migrations_dir.mkdir()
            for migration_name in self._REQUIRED_MIGRATIONS:
                shutil.copy2(
                    REPO_ROOT / "postgres" / "control-plane" / "migrations" / migration_name,
                    migrations_dir / migration_name,
                )

            psql_path = temp_root / "fake-psql.sh"
            psql_log = temp_root / "fake-psql.log"
            psql_state = temp_root / "fake-psql.state"
            psql_path.write_text(
                """#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import re
import sys


def main() -> int:
    args = sys.argv[1:]
    file_path = ""
    query_text = ""

    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "-f":
            index += 1
            file_path = args[index]
        elif arg == "-c":
            index += 1
            query_text = args[index]
        index += 1

    log_path = pathlib.Path(os.environ["AEGISOPS_TEST_PSQL_LOG"])
    state_path = pathlib.Path(os.environ["AEGISOPS_TEST_PSQL_STATE"])
    if state_path.exists():
      state = json.loads(state_path.read_text(encoding="utf-8"))
    else:
      state = {"applied": []}

    if file_path:
      migration_name = pathlib.Path(file_path).name
      if migration_name in state["applied"]:
        print(f"duplicate migration replay: {migration_name}", file=sys.stderr)
        return 1
      state["applied"].append(migration_name)
      state_path.write_text(json.dumps(state), encoding="utf-8")
      with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"migration:{migration_name}\\n")
      return 0

    if query_text:
      if "schema_migration_bootstrap" in query_text:
        if "SELECT migration_checksum" in query_text:
          match = re.search(r"migration_name = '([^']+)'", query_text)
          if match is None:
            print("missing migration name lookup", file=sys.stderr)
            return 1
          sys.stdout.write(state.get("recorded", {}).get(match.group(1), ""))
          return 0

        if "INSERT INTO aegisops_control.schema_migration_bootstrap" in query_text:
          match = re.search(
            r"VALUES \\('([^']+)', '([^']+)'\\)",
            query_text,
          )
          if match is None:
            print("missing migration metadata insert", file=sys.stderr)
            return 1
          recorded = state.setdefault("recorded", {})
          recorded[match.group(1)] = match.group(2)
          state_path.write_text(json.dumps(state), encoding="utf-8")
          return 0

        return 0

      with log_path.open("a", encoding="utf-8") as handle:
        handle.write("readiness\\n")
      ready = "0001_control_plane_schema_skeleton.sql" in state["applied"]
      sys.stdout.write("ready" if ready else "not-ready")
      return 0

    print("unexpected psql invocation", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
""",
                encoding="utf-8",
            )
            psql_path.chmod(0o755)

            env = {
                "AEGISOPS_CONTROL_PLANE_HOST": "127.0.0.1",
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "postgresql://user:pass@postgres:5432/aegisops",
                "AEGISOPS_CONTROL_PLANE_BOOT_MODE": "first-boot",
                "AEGISOPS_CONTROL_PLANE_LOG_LEVEL": "INFO",
                "AEGISOPS_FIRST_BOOT_MIGRATIONS_DIR": str(migrations_dir),
                "AEGISOPS_FIRST_BOOT_PSQL_BIN": str(psql_path),
                "AEGISOPS_TEST_PSQL_LOG": str(psql_log),
                "AEGISOPS_TEST_PSQL_STATE": str(psql_state),
            }

            first_result = self._run_entrypoint(env)
            self.assertEqual(first_result.returncode, 0, first_result.stderr)

            second_result = self._run_entrypoint(env)
            self.assertEqual(second_result.returncode, 0, second_result.stderr)

            psql_log_lines = psql_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                psql_log_lines,
                [
                    "readiness",
                    "migration:0001_control_plane_schema_skeleton.sql",
                    "readiness",
                    "migration:0002_phase_14_reviewed_context_columns.sql",
                    "readiness",
                    "migration:0003_phase_15_assistant_advisory_draft_columns.sql",
                    "readiness",
                    "migration:0004_phase_20_action_request_binding_columns.sql",
                    "readiness",
                    "migration:0005_phase_23_approval_decision_rationale.sql",
                    "readiness",
                    "migration:0006_phase_23_lifecycle_transition_records.sql",
                    "readiness",
                    "migration:0007_phase_23_lifecycle_transition_subject_index.sql",
                    "readiness",
                    "readiness",
                    "readiness",
                    "readiness",
                    "readiness",
                    "readiness",
                    "readiness",
                    "readiness",
                    "readiness",
                    "readiness",
                ],
            )

    def test_first_boot_entrypoint_replays_0006_when_table_exists_without_backfill(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = pathlib.Path(tmpdir)
            migrations_dir = temp_root / "migrations"
            migrations_dir.mkdir()

            migration_checksums: dict[str, str] = {}
            for migration_name in self._REQUIRED_MIGRATIONS:
                source_path = REPO_ROOT / "postgres" / "control-plane" / "migrations" / migration_name
                destination_path = migrations_dir / migration_name
                shutil.copy2(source_path, destination_path)
                migration_checksums[migration_name] = self._normalized_migration_checksum(
                    destination_path
                )

            recorded_migrations = {
                migration_name: migration_checksums[migration_name]
                for migration_name in self._REQUIRED_MIGRATIONS
                if migration_name
                not in (
                    "0006_phase_23_lifecycle_transition_records.sql",
                    "0007_phase_23_lifecycle_transition_subject_index.sql",
                )
            }

            psql_path = temp_root / "fake-psql.sh"
            psql_log = temp_root / "fake-psql.log"
            psql_state = temp_root / "fake-psql.state"
            psql_state.write_text(
                json.dumps(
                    {
                        "recorded": recorded_migrations,
                        "ready": list(recorded_migrations),
                        "backfill_repaired": False,
                        "index_applied": False,
                    }
                ),
                encoding="utf-8",
            )
            psql_path.write_text(
                """#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import re
import sys


def classify_readiness_query(query_text: str) -> str:
    if "lifecycle_transition_records_subject_latest_idx" in query_text:
        return "0007_phase_23_lifecycle_transition_subject_index.sql"
    if "missing_subjects" in query_text and "lifecycle_transition_records" in query_text:
        return "0006_phase_23_lifecycle_transition_records.sql"
    if "decision_rationale" in query_text:
        return "0005_phase_23_approval_decision_rationale.sql"
    if "requested_payload" in query_text or "requester_identity" in query_text:
        return "0004_phase_20_action_request_binding_columns.sql"
    if "assistant_advisory_draft" in query_text:
        return "0003_phase_15_assistant_advisory_draft_columns.sql"
    if "reviewed_context" in query_text:
        return "0002_phase_14_reviewed_context_columns.sql"
    if (
        "approval_decision_records" in query_text
        or "action_execution_records" in query_text
        or "reconciliation_records" in query_text
        or "hunt_run_records" in query_text
    ):
        return "0001_control_plane_schema_skeleton.sql"
    if "lifecycle_transition_records" in query_text:
        return "0006_phase_23_lifecycle_transition_records.sql"
    return "0001_control_plane_schema_skeleton.sql"


def main() -> int:
    args = sys.argv[1:]
    file_path = ""
    query_text = ""

    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "-f":
            index += 1
            file_path = args[index]
        elif arg == "-c":
            index += 1
            query_text = args[index]
        index += 1

    log_path = pathlib.Path(os.environ["AEGISOPS_TEST_PSQL_LOG"])
    state_path = pathlib.Path(os.environ["AEGISOPS_TEST_PSQL_STATE"])
    state = json.loads(state_path.read_text(encoding="utf-8"))

    if file_path:
        migration_name = pathlib.Path(file_path).name
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"migration:{migration_name}\\n")
        if migration_name == "0006_phase_23_lifecycle_transition_records.sql":
            state["backfill_repaired"] = True
        elif migration_name == "0007_phase_23_lifecycle_transition_subject_index.sql":
            state["index_applied"] = True
        state_path.write_text(json.dumps(state), encoding="utf-8")
        return 0

    if query_text:
        if "schema_migration_bootstrap" in query_text:
            if "SELECT migration_checksum" in query_text:
                match = re.search(r"migration_name = '([^']+)'", query_text)
                if match is None:
                    print("missing migration name lookup", file=sys.stderr)
                    return 1
                sys.stdout.write(state["recorded"].get(match.group(1), ""))
                return 0

            if "INSERT INTO aegisops_control.schema_migration_bootstrap" in query_text:
                match = re.search(r"VALUES \\('([^']+)', '([^']+)'\\)", query_text)
                if match is None:
                    print("missing migration metadata insert", file=sys.stderr)
                    return 1
                state["recorded"][match.group(1)] = match.group(2)
                state_path.write_text(json.dumps(state), encoding="utf-8")
                with log_path.open("a", encoding="utf-8") as handle:
                    handle.write(f"metadata-insert:{match.group(1)}\\n")
                return 0

            return 0

        migration_name = classify_readiness_query(query_text)
        if migration_name == "0006_phase_23_lifecycle_transition_records.sql":
            backfill_aware = "missing_subjects" in query_text
            with log_path.open("a", encoding="utf-8") as handle:
                mode = "backfill-aware" if backfill_aware else "table-only"
                handle.write(f"readiness:{migration_name}:{mode}\\n")
            ready = state["backfill_repaired"] if backfill_aware else True
            sys.stdout.write("ready" if ready else "not-ready")
            return 0

        if migration_name == "0007_phase_23_lifecycle_transition_subject_index.sql":
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"readiness:{migration_name}\\n")
            sys.stdout.write("ready" if state["index_applied"] else "not-ready")
            return 0

        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"readiness:{migration_name}\\n")
        ready = migration_name in state.get("ready", [])
        sys.stdout.write("ready" if ready else "not-ready")
        return 0

    print("unexpected psql invocation", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
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
                    "AEGISOPS_TEST_PSQL_STATE": str(psql_state),
                }
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            log_lines = psql_log.read_text(encoding="utf-8").splitlines()
            self.assertIn(
                "readiness:0006_phase_23_lifecycle_transition_records.sql:backfill-aware",
                log_lines,
            )
            migration_index = log_lines.index(
                "migration:0006_phase_23_lifecycle_transition_records.sql"
            )
            metadata_index = log_lines.index(
                "metadata-insert:0006_phase_23_lifecycle_transition_records.sql"
            )
            self.assertLess(migration_index, metadata_index)

    def test_first_boot_entrypoint_fails_closed_when_recorded_migration_cannot_be_reproved(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = pathlib.Path(tmpdir)
            migrations_dir = temp_root / "migrations"
            migrations_dir.mkdir()

            migration_checksums: dict[str, str] = {}
            for migration_name in self._REQUIRED_MIGRATIONS:
                source_path = REPO_ROOT / "postgres" / "control-plane" / "migrations" / migration_name
                destination_path = migrations_dir / migration_name
                shutil.copy2(source_path, destination_path)
                migration_checksums[migration_name] = self._normalized_migration_checksum(
                    destination_path
                )

            psql_path = temp_root / "fake-psql.sh"
            psql_log = temp_root / "fake-psql.log"
            psql_state = temp_root / "fake-psql.state"
            psql_state.write_text(
                json.dumps(
                    {
                        "recorded": migration_checksums,
                        "ready": ["0001_control_plane_schema_skeleton.sql"],
                    }
                ),
                encoding="utf-8",
            )
            psql_path.write_text(
                """#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import re
import sys


def classify_readiness_query(query_text: str) -> str:
    if "lifecycle_transition_records_subject_latest_idx" in query_text:
        return "0007_phase_23_lifecycle_transition_subject_index.sql"
    if "missing_subjects" in query_text and "lifecycle_transition_records" in query_text:
        return "0006_phase_23_lifecycle_transition_records.sql"
    if "decision_rationale" in query_text:
        return "0005_phase_23_approval_decision_rationale.sql"
    if "requested_payload" in query_text or "requester_identity" in query_text:
        return "0004_phase_20_action_request_binding_columns.sql"
    if "assistant_advisory_draft" in query_text:
        return "0003_phase_15_assistant_advisory_draft_columns.sql"
    if "reviewed_context" in query_text:
        return "0002_phase_14_reviewed_context_columns.sql"
    if (
        "approval_decision_records" in query_text
        or "action_execution_records" in query_text
        or "reconciliation_records" in query_text
        or "hunt_run_records" in query_text
    ):
        return "0001_control_plane_schema_skeleton.sql"
    if "lifecycle_transition_records" in query_text:
        return "0006_phase_23_lifecycle_transition_records.sql"
    return "0001_control_plane_schema_skeleton.sql"


def main() -> int:
    args = sys.argv[1:]
    file_path = ""
    query_text = ""

    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "-f":
            index += 1
            file_path = args[index]
        elif arg == "-c":
            index += 1
            query_text = args[index]
        index += 1

    log_path = pathlib.Path(os.environ["AEGISOPS_TEST_PSQL_LOG"])
    state_path = pathlib.Path(os.environ["AEGISOPS_TEST_PSQL_STATE"])
    state = json.loads(state_path.read_text(encoding="utf-8"))

    if file_path:
        print("unexpected migration replay", file=sys.stderr)
        return 1

    if query_text:
        if "schema_migration_bootstrap" in query_text:
            if "SELECT migration_checksum" in query_text:
                match = re.search(r"migration_name = '([^']+)'", query_text)
                if match is None:
                    print("missing migration name lookup", file=sys.stderr)
                    return 1
                sys.stdout.write(state["recorded"].get(match.group(1), ""))
                return 0

            if "INSERT INTO aegisops_control.schema_migration_bootstrap" in query_text:
                print("unexpected migration metadata write", file=sys.stderr)
                return 1

            return 0

        migration_name = classify_readiness_query(query_text)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"readiness:{migration_name}\\n")
        ready = migration_name in state.get("ready", [])
        sys.stdout.write("ready" if ready else "not-ready")
        return 0

    print("unexpected psql invocation", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
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
                    "AEGISOPS_TEST_PSQL_STATE": str(psql_state),
                }
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "First-boot migration bootstrap could not prove reviewed schema state for recorded migration 0002_phase_14_reviewed_context_columns.sql.",
                result.stderr,
            )
            self.assertEqual(
                psql_log.read_text(encoding="utf-8").splitlines(),
                [
                    "readiness:0001_control_plane_schema_skeleton.sql",
                    "readiness:0002_phase_14_reviewed_context_columns.sql",
                ],
            )

    def test_first_boot_entrypoint_accepts_crlf_migration_checkouts_when_checksums_match(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = pathlib.Path(tmpdir)
            migrations_dir = temp_root / "migrations"
            migrations_dir.mkdir()

            migration_checksums: dict[str, str] = {}
            for migration_name in self._REQUIRED_MIGRATIONS:
                source_path = (
                    REPO_ROOT / "postgres" / "control-plane" / "migrations" / migration_name
                )
                destination_path = migrations_dir / migration_name
                source_text = source_path.read_text(encoding="utf-8")
                with destination_path.open("w", encoding="utf-8", newline="") as handle:
                    handle.write(source_text.replace("\n", "\r\n"))
                migration_checksums[migration_name] = self._normalized_migration_checksum(
                    source_path
                )

            psql_path = temp_root / "fake-psql.sh"
            psql_log = temp_root / "fake-psql.log"
            psql_state = temp_root / "fake-psql.state"
            psql_state.write_text(
                json.dumps(
                    {
                        "recorded": migration_checksums,
                        "ready": list(self._REQUIRED_MIGRATIONS),
                    }
                ),
                encoding="utf-8",
            )
            psql_path.write_text(
                """#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import re
import sys


def classify_readiness_query(query_text: str) -> str:
    if "lifecycle_transition_records_subject_latest_idx" in query_text:
        return "0007_phase_23_lifecycle_transition_subject_index.sql"
    if "missing_subjects" in query_text and "lifecycle_transition_records" in query_text:
        return "0006_phase_23_lifecycle_transition_records.sql"
    if "decision_rationale" in query_text:
        return "0005_phase_23_approval_decision_rationale.sql"
    if "requested_payload" in query_text or "requester_identity" in query_text:
        return "0004_phase_20_action_request_binding_columns.sql"
    if "assistant_advisory_draft" in query_text:
        return "0003_phase_15_assistant_advisory_draft_columns.sql"
    if "reviewed_context" in query_text:
        return "0002_phase_14_reviewed_context_columns.sql"
    if (
        "approval_decision_records" in query_text
        or "action_execution_records" in query_text
        or "reconciliation_records" in query_text
        or "hunt_run_records" in query_text
    ):
        return "0001_control_plane_schema_skeleton.sql"
    if "lifecycle_transition_records" in query_text:
        return "0006_phase_23_lifecycle_transition_records.sql"
    return "0001_control_plane_schema_skeleton.sql"


def main() -> int:
    args = sys.argv[1:]
    file_path = ""
    query_text = ""

    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "-f":
            index += 1
            file_path = args[index]
        elif arg == "-c":
            index += 1
            query_text = args[index]
        index += 1

    log_path = pathlib.Path(os.environ["AEGISOPS_TEST_PSQL_LOG"])
    state_path = pathlib.Path(os.environ["AEGISOPS_TEST_PSQL_STATE"])
    state = json.loads(state_path.read_text(encoding="utf-8"))

    if file_path:
        print("unexpected migration replay", file=sys.stderr)
        return 1

    if query_text:
        if "schema_migration_bootstrap" in query_text:
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"metadata:{query_text}\\n")
            if "SELECT migration_checksum" in query_text:
                match = re.search(r"migration_name = '([^']+)'", query_text)
                if match is None:
                    print("missing migration name lookup", file=sys.stderr)
                    return 1
                sys.stdout.write(state["recorded"].get(match.group(1), ""))
                return 0
            if "INSERT INTO aegisops_control.schema_migration_bootstrap" in query_text:
                return 0
            return 0

        migration_name = classify_readiness_query(query_text)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"readiness:{migration_name}\\n")
        ready = migration_name in state.get("ready", [])
        sys.stdout.write("ready" if ready else "not-ready")
        return 0

    print("unexpected psql invocation", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
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
                    "AEGISOPS_TEST_PSQL_STATE": str(psql_state),
                }
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "ok")
            self.assertEqual(result.stderr, "")

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
