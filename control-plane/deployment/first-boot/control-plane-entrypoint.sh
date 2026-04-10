#!/usr/bin/env sh

set -eu

# Reviewed first-boot control-plane entrypoint.
# This entrypoint validates the approved runtime contract, proves
# migration bootstrap success, and then hands off to the runtime
# service process as the final foreground command.

require_non_empty() {
  var_name="$1"
  var_value="${2:-}"

  if [ -z "${var_value}" ] || [ "${var_value}" = "<set-me>" ]; then
    echo "Missing required first-boot setting: ${var_name}" >&2
    exit 1
  fi
}

require_non_empty "AEGISOPS_CONTROL_PLANE_HOST" "${AEGISOPS_CONTROL_PLANE_HOST:-}"
require_non_empty "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN" "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN:-}"

host_value="${AEGISOPS_CONTROL_PLANE_HOST:-}"
case "${host_value}" in
  0.0.0.0|::|*)
    if [ "${host_value}" = "0.0.0.0" ] || [ "${host_value}" = "::" ] || [ "${host_value}" = "*" ]; then
      echo "AEGISOPS_CONTROL_PLANE_HOST must not publish the control-plane backend directly." >&2
      exit 1
    fi
    ;;
esac

dsn_value="${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN:-}"
case "${dsn_value}" in
  postgresql://*|postgres://*)
    ;;
  *)
    echo "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN must be a PostgreSQL DSN for the first-boot runtime." >&2
    exit 1
    ;;
esac

port_value="${AEGISOPS_CONTROL_PLANE_PORT:-8080}"
case "${port_value}" in
  ''|*[!0-9]*)
    echo "AEGISOPS_CONTROL_PLANE_PORT must be an integer for the first-boot runtime." >&2
    exit 1
    ;;
esac

if [ "${port_value}" -lt 1 ] || [ "${port_value}" -gt 65535 ]; then
  echo "AEGISOPS_CONTROL_PLANE_PORT must stay within the reviewed listen-port range." >&2
  exit 1
fi

boot_mode_value="${AEGISOPS_CONTROL_PLANE_BOOT_MODE:-first-boot}"
case "${boot_mode_value}" in
  first-boot)
    ;;
  *)
    echo "AEGISOPS_CONTROL_PLANE_BOOT_MODE must remain first-boot for the reviewed startup path." >&2
    exit 1
    ;;
esac

log_level_value="${AEGISOPS_CONTROL_PLANE_LOG_LEVEL:-INFO}"
case "${log_level_value}" in
  DEBUG|INFO|WARNING|ERROR|CRITICAL)
    ;;
  *)
    echo "AEGISOPS_CONTROL_PLANE_LOG_LEVEL must be one of DEBUG, INFO, WARNING, ERROR, or CRITICAL." >&2
    exit 1
    ;;
esac

fail_closed() {
  echo "$1" >&2
  exit 1
}

MIGRATIONS_DIR="${AEGISOPS_FIRST_BOOT_MIGRATIONS_DIR:-/opt/aegisops/postgres-migrations}"
PSQL_BIN="${AEGISOPS_FIRST_BOOT_PSQL_BIN:-psql}"
REQUIRED_MIGRATIONS="
0001_control_plane_schema_skeleton.sql
0002_phase_14_reviewed_context_columns.sql
0003_phase_15_assistant_advisory_draft_columns.sql
"

resolve_psql_bin() {
  case "${PSQL_BIN}" in
    */*)
      if [ ! -x "${PSQL_BIN}" ]; then
        fail_closed "First-boot migration bootstrap requires an executable PostgreSQL client: ${PSQL_BIN}"
      fi
      ;;
    *)
      if ! command -v "${PSQL_BIN}" >/dev/null 2>&1; then
        fail_closed "First-boot migration bootstrap requires psql to prove PostgreSQL reachability and readiness."
      fi
      PSQL_BIN="$(command -v "${PSQL_BIN}")"
      ;;
  esac
}

run_psql() {
  "${PSQL_BIN}" -X "${dsn_value}" -v ON_ERROR_STOP=1 "$@"
}

require_migration_assets() {
  if [ ! -d "${MIGRATIONS_DIR}" ]; then
    fail_closed "First-boot migration bootstrap requires reviewed migration assets at ${MIGRATIONS_DIR}."
  fi

  for migration_name in ${REQUIRED_MIGRATIONS}; do
    if [ ! -f "${MIGRATIONS_DIR}/${migration_name}" ]; then
      fail_closed "First-boot migration bootstrap is missing reviewed migration asset: ${migration_name}"
    fi
  done
}

apply_migration_bootstrap() {
  for migration_name in ${REQUIRED_MIGRATIONS}; do
    migration_path="${MIGRATIONS_DIR}/${migration_name}"
    if ! migration_output="$(run_psql -f "${migration_path}" 2>&1)"; then
      fail_closed "First-boot migration bootstrap failed while applying ${migration_name}: ${migration_output}"
    fi
  done
}

verify_readiness_proof() {
  readiness_query=$(cat <<'EOF'
SELECT CASE
  WHEN EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'aegisops_control'
      AND table_name = 'alert_records'
  )
  AND EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
      AND table_name = 'recommendation_records'
      AND column_name = 'assistant_advisory_draft'
  )
  AND EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
      AND table_name = 'ai_trace_records'
      AND column_name = 'assistant_advisory_draft'
  )
  THEN 'ready'
  ELSE 'not-ready'
END;
EOF
)

  if ! readiness_output="$(run_psql -tA -c "${readiness_query}" 2>&1)"; then
    fail_closed "First-boot readiness proof failed during PostgreSQL verification: ${readiness_output}"
  fi

  readiness_output="$(printf '%s' "${readiness_output}" | tr -d '[:space:]')"
  if [ "${readiness_output}" != "ready" ]; then
    fail_closed "First-boot readiness proof failed: migration bootstrap could not prove the expected reviewed schema state."
  fi
}

: "${PGCONNECT_TIMEOUT:=5}"
export PGCONNECT_TIMEOUT

require_migration_assets
resolve_psql_bin
apply_migration_bootstrap
verify_readiness_proof

# OpenSearch, n8n, the full analyst-assistant surface, and executor wiring remain deferred.

exec "$@"
