#!/bin/sh

set -eu

dsn_file="${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE:-}"
if [ -z "${dsn_file}" ] || [ ! -r "${dsn_file}" ]; then
  echo "Phase 67.1 control-plane DSN file is missing or unreadable: ${dsn_file}" >&2
  exit 1
fi

AEGISOPS_CONTROL_PLANE_POSTGRES_DSN="$(cat "${dsn_file}")"
if [ -z "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN}" ]; then
  echo "Phase 67.1 control-plane DSN file is empty: ${dsn_file}" >&2
  exit 1
fi
export AEGISOPS_CONTROL_PLANE_POSTGRES_DSN
unset AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE

# Let the reviewed first-boot entrypoint apply and prove its Phase 16 migration set,
# then return here instead of starting the server yet.
/opt/aegisops/bin/first-boot-entrypoint.sh /bin/true

migrations_dir="${AEGISOPS_FIRST_BOOT_MIGRATIONS_DIR:-/opt/aegisops/postgres-migrations}"

sql_literal() {
  printf '%s' "$1" | sed "s/'/''/g"
}

migration_readiness_query() {
  case "$1" in
    0008_phase_25_osquery_host_context_columns.sql)
      cat <<'EOF'
SELECT CASE WHEN (
  SELECT COUNT(*)
  FROM information_schema.columns
  WHERE table_schema = 'aegisops_control'
    AND (table_name, column_name) IN (
      VALUES
        ('evidence_records', 'provenance'),
        ('evidence_records', 'content'),
        ('observation_records', 'provenance'),
        ('observation_records', 'content')
    )
) = 4 THEN 'ready' ELSE 'not-ready' END;
EOF
      ;;
    0009_phase_26_external_ticket_reference_columns.sql)
      cat <<'EOF'
SELECT CASE WHEN (
  SELECT COUNT(*)
  FROM information_schema.columns
  WHERE table_schema = 'aegisops_control'
    AND (table_name, column_name) IN (
      VALUES
        ('alert_records', 'coordination_reference_id'),
        ('alert_records', 'coordination_target_type'),
        ('alert_records', 'coordination_target_id'),
        ('alert_records', 'ticket_reference_url'),
        ('case_records', 'coordination_reference_id'),
        ('case_records', 'coordination_target_type'),
        ('case_records', 'coordination_target_id'),
        ('case_records', 'ticket_reference_url')
    )
) = 8 THEN 'ready' ELSE 'not-ready' END;
EOF
      ;;
    0010_phase_28_action_request_idempotency_key_unique_index.sql)
      cat <<'EOF'
SELECT CASE
  WHEN EXISTS (
    SELECT 1
    FROM pg_indexes
    WHERE schemaname = 'aegisops_control'
      AND tablename = 'action_request_records'
      AND indexname = 'action_request_records_idempotency_key_key'
  )
  THEN 'ready' ELSE 'not-ready'
END;
EOF
      ;;
    0011_phase_28_reconciliation_correlation_lookup_index.sql)
      cat <<'EOF'
SELECT CASE
  WHEN EXISTS (
    SELECT 1
    FROM pg_indexes
    WHERE schemaname = 'aegisops_control'
      AND tablename = 'reconciliation_records'
      AND indexname = 'reconciliation_records_correlation_alert_latest_idx'
  )
  THEN 'ready' ELSE 'not-ready'
END;
EOF
      ;;
    0012_phase_32_ai_trace_latest_lookup_index.sql)
      cat <<'EOF'
SELECT CASE
  WHEN EXISTS (
    SELECT 1
    FROM pg_indexes
    WHERE schemaname = 'aegisops_control'
      AND tablename = 'ai_trace_records'
      AND indexname = 'ai_trace_records_latest_idx'
  )
  THEN 'ready' ELSE 'not-ready'
END;
EOF
      ;;
    0013_phase_61_detector_lifecycle_records.sql)
      cat <<'EOF'
SELECT CASE WHEN (
  SELECT COUNT(*)
  FROM information_schema.tables
  WHERE table_schema = 'aegisops_control'
    AND table_name IN (
      'detector_lifecycle_records',
      'false_positive_review_records',
      'suppression_proposal_records'
    )
) = 3 THEN 'ready' ELSE 'not-ready' END;
EOF
      ;;
    0014_phase_61_source_health_records.sql)
      cat <<'EOF'
SELECT CASE WHEN EXISTS (
  SELECT 1
  FROM information_schema.tables
  WHERE table_schema = 'aegisops_control'
    AND table_name = 'source_health_records'
) THEN 'ready' ELSE 'not-ready' END;
EOF
      ;;
    0015_phase_64_known_limitation_ownership_records.sql)
      cat <<'EOF'
SELECT CASE WHEN EXISTS (
  SELECT 1
  FROM information_schema.tables
  WHERE table_schema = 'aegisops_control'
    AND table_name = 'known_limitation_ownership_records'
) THEN 'ready' ELSE 'not-ready' END;
EOF
      ;;
    *)
      echo "Phase 67.1 does not recognize current-runtime migration: $1" >&2
      return 1
      ;;
  esac
}

prove_migration_state() {
  readiness_query="$(migration_readiness_query "$1")" || return 1
  readiness_status="$(
    psql -X "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN}" -tA -v ON_ERROR_STOP=1 \
      -c "${readiness_query}" |
      tr -d '[:space:]'
  )" || return 1
  [ "${readiness_status}" = "ready" ]
}

for migration_path in \
  "${migrations_dir}"/0008_*.sql \
  "${migrations_dir}"/0009_*.sql \
  "${migrations_dir}"/0010_*.sql \
  "${migrations_dir}"/0011_*.sql \
  "${migrations_dir}"/0012_*.sql \
  "${migrations_dir}"/0013_*.sql \
  "${migrations_dir}"/0014_*.sql \
  "${migrations_dir}"/0015_*.sql
do
  if [ ! -f "${migration_path}" ]; then
    echo "Phase 67.1 current-runtime migration is missing: ${migration_path}" >&2
    exit 1
  fi

  migration_name="$(basename "${migration_path}")"
  migration_checksum="$(tr -d '\r' <"${migration_path}" | cksum | awk '{print $1 ":" $2}')"
  migration_name_sql="$(sql_literal "${migration_name}")"
  recorded_checksum="$(
    psql -X "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN}" -tA -v ON_ERROR_STOP=1 \
      -c "SELECT migration_checksum FROM aegisops_control.schema_migration_bootstrap WHERE migration_name = '${migration_name_sql}';" |
      tr -d '[:space:]'
  )"

  if [ -n "${recorded_checksum}" ]; then
    if [ "${recorded_checksum}" != "${migration_checksum}" ]; then
      echo "Phase 67.1 detected migration checksum drift: ${migration_name}" >&2
      exit 1
    fi
    if ! prove_migration_state "${migration_name}"; then
      echo "Phase 67.1 could not prove reviewed schema state for recorded migration: ${migration_name}" >&2
      exit 1
    fi
    continue
  fi

  psql -X "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN}" -v ON_ERROR_STOP=1 \
    -f "${migration_path}" >/dev/null
  if ! prove_migration_state "${migration_name}"; then
    echo "Phase 67.1 could not prove reviewed schema state after applying migration: ${migration_name}" >&2
    exit 1
  fi
  migration_checksum_sql="$(sql_literal "${migration_checksum}")"
  psql -X "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN}" -v ON_ERROR_STOP=1 \
    -c "INSERT INTO aegisops_control.schema_migration_bootstrap (migration_name, migration_checksum) VALUES ('${migration_name_sql}', '${migration_checksum_sql}');" \
    >/dev/null
done

exec "$@"
