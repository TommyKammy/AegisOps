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
WITH required_columns(table_name, column_name, udt_name, is_nullable, column_default) AS (
  VALUES
    ('evidence_records', 'provenance', 'jsonb', 'NO', $default$'{}'::jsonb$default$),
    ('evidence_records', 'content', 'jsonb', 'NO', $default$'{}'::jsonb$default$),
    ('observation_records', 'provenance', 'jsonb', 'NO', $default$'{}'::jsonb$default$),
    ('observation_records', 'content', 'jsonb', 'NO', $default$'{}'::jsonb$default$)
)
SELECT CASE WHEN NOT EXISTS (
  SELECT table_name, column_name, udt_name, is_nullable, column_default
  FROM required_columns
  EXCEPT
  SELECT table_name, column_name, udt_name, is_nullable, column_default
  FROM information_schema.columns
  WHERE table_schema = 'aegisops_control'
) THEN 'ready' ELSE 'not-ready' END;
EOF
      ;;
    0009_phase_26_external_ticket_reference_columns.sql)
      cat <<'EOF'
WITH required_columns(table_name, column_name, udt_name, is_nullable) AS (
  VALUES
    ('alert_records', 'coordination_reference_id', 'text', 'YES'),
    ('alert_records', 'coordination_target_type', 'text', 'YES'),
    ('alert_records', 'coordination_target_id', 'text', 'YES'),
    ('alert_records', 'ticket_reference_url', 'text', 'YES'),
    ('case_records', 'coordination_reference_id', 'text', 'YES'),
    ('case_records', 'coordination_target_type', 'text', 'YES'),
    ('case_records', 'coordination_target_id', 'text', 'YES'),
    ('case_records', 'ticket_reference_url', 'text', 'YES')
),
required_constraints(table_name, constraint_name, constraint_definition) AS (
  VALUES
    (
      'alert_records',
      'alert_records_coordination_reference_fields_complete',
      $constraint$CHECK (coordination_reference_id IS NULL AND coordination_target_type IS NULL AND coordination_target_id IS NULL AND ticket_reference_url IS NULL OR NULLIF(btrim(coordination_reference_id), ''::text) IS NOT NULL AND NULLIF(btrim(coordination_target_type), ''::text) IS NOT NULL AND NULLIF(btrim(coordination_target_id), ''::text) IS NOT NULL AND NULLIF(btrim(ticket_reference_url), ''::text) IS NOT NULL)$constraint$
    ),
    (
      'alert_records',
      'alert_records_coordination_target_type_reviewed',
      $constraint$CHECK (coordination_target_type IS NULL OR (coordination_target_type = ANY (ARRAY['glpi'::text, 'zammad'::text])))$constraint$
    ),
    (
      'alert_records',
      'alert_records_ticket_reference_url_https',
      $constraint$CHECK (ticket_reference_url IS NULL OR ticket_reference_url ~* '^https://[^/?#[:space:]]+([/?#][^[:space:]]*)?$'::text)$constraint$
    ),
    (
      'alert_records',
      'alert_records_coordination_reference_id_bounded',
      $constraint$CHECK (coordination_reference_id IS NULL OR char_length(coordination_reference_id) <= 128)$constraint$
    ),
    (
      'alert_records',
      'alert_records_coordination_target_type_bounded',
      $constraint$CHECK (coordination_target_type IS NULL OR char_length(coordination_target_type) <= 32)$constraint$
    ),
    (
      'alert_records',
      'alert_records_coordination_target_id_bounded',
      $constraint$CHECK (coordination_target_id IS NULL OR char_length(coordination_target_id) <= 256)$constraint$
    ),
    (
      'alert_records',
      'alert_records_ticket_reference_url_bounded',
      $constraint$CHECK (ticket_reference_url IS NULL OR char_length(ticket_reference_url) <= 2048)$constraint$
    ),
    (
      'case_records',
      'case_records_coordination_reference_fields_complete',
      $constraint$CHECK (coordination_reference_id IS NULL AND coordination_target_type IS NULL AND coordination_target_id IS NULL AND ticket_reference_url IS NULL OR NULLIF(btrim(coordination_reference_id), ''::text) IS NOT NULL AND NULLIF(btrim(coordination_target_type), ''::text) IS NOT NULL AND NULLIF(btrim(coordination_target_id), ''::text) IS NOT NULL AND NULLIF(btrim(ticket_reference_url), ''::text) IS NOT NULL)$constraint$
    ),
    (
      'case_records',
      'case_records_coordination_target_type_reviewed',
      $constraint$CHECK (coordination_target_type IS NULL OR (coordination_target_type = ANY (ARRAY['glpi'::text, 'zammad'::text])))$constraint$
    ),
    (
      'case_records',
      'case_records_ticket_reference_url_https',
      $constraint$CHECK (ticket_reference_url IS NULL OR ticket_reference_url ~* '^https://[^/?#[:space:]]+([/?#][^[:space:]]*)?$'::text)$constraint$
    ),
    (
      'case_records',
      'case_records_coordination_reference_id_bounded',
      $constraint$CHECK (coordination_reference_id IS NULL OR char_length(coordination_reference_id) <= 128)$constraint$
    ),
    (
      'case_records',
      'case_records_coordination_target_type_bounded',
      $constraint$CHECK (coordination_target_type IS NULL OR char_length(coordination_target_type) <= 32)$constraint$
    ),
    (
      'case_records',
      'case_records_coordination_target_id_bounded',
      $constraint$CHECK (coordination_target_id IS NULL OR char_length(coordination_target_id) <= 256)$constraint$
    ),
    (
      'case_records',
      'case_records_ticket_reference_url_bounded',
      $constraint$CHECK (ticket_reference_url IS NULL OR char_length(ticket_reference_url) <= 2048)$constraint$
    )
)
SELECT CASE WHEN NOT EXISTS (
    SELECT table_name, column_name, udt_name, is_nullable
    FROM required_columns
    EXCEPT
    SELECT table_name, column_name, udt_name, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
      AND column_default IS NULL
  )
  AND NOT EXISTS (
    SELECT table_name, constraint_name, constraint_definition
    FROM required_constraints
    EXCEPT
    SELECT
      relation.relname,
      constraint_record.conname,
      pg_get_constraintdef(constraint_record.oid, true)
    FROM pg_constraint AS constraint_record
    JOIN pg_class AS relation ON relation.oid = constraint_record.conrelid
    WHERE constraint_record.connamespace = 'aegisops_control'::regnamespace
      AND constraint_record.contype = 'c'
      AND constraint_record.convalidated
  )
THEN 'ready' ELSE 'not-ready' END;
EOF
      ;;
    0010_phase_28_action_request_idempotency_key_unique_index.sql)
      cat <<'EOF'
SELECT CASE
  WHEN EXISTS (
    SELECT 1
    FROM pg_index
    WHERE indexrelid = 'aegisops_control.action_request_records_idempotency_key_key'::regclass
      AND indrelid = 'aegisops_control.action_request_records'::regclass
      AND indisvalid
      AND indisunique
      AND indnkeyatts = 1
      AND indnatts = 1
      AND indexprs IS NULL
      AND indpred IS NULL
      AND pg_get_indexdef(indexrelid, 1, true) = 'idempotency_key'
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
    FROM pg_index
    WHERE indexrelid = 'aegisops_control.reconciliation_records_correlation_alert_latest_idx'::regclass
      AND indrelid = 'aegisops_control.reconciliation_records'::regclass
      AND indisvalid
      AND NOT indisunique
      AND indnkeyatts = 3
      AND indnatts = 3
      AND indexprs IS NULL
      AND pg_get_indexdef(indexrelid) = 'CREATE INDEX reconciliation_records_correlation_alert_latest_idx ON aegisops_control.reconciliation_records USING btree (correlation_key, compared_at DESC, reconciliation_id DESC) WHERE (alert_id IS NOT NULL)'
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
    FROM pg_index
    WHERE indexrelid = 'aegisops_control.ai_trace_records_latest_idx'::regclass
      AND indrelid = 'aegisops_control.ai_trace_records'::regclass
      AND indisvalid
      AND NOT indisunique
      AND indnkeyatts = 2
      AND indnatts = 2
      AND indexprs IS NULL
      AND indpred IS NULL
      AND pg_get_indexdef(indexrelid) = 'CREATE INDEX ai_trace_records_latest_idx ON aegisops_control.ai_trace_records USING btree (generated_at DESC, ai_trace_id DESC)'
  )
  THEN 'ready' ELSE 'not-ready'
END;
EOF
      ;;
    0013_phase_61_detector_lifecycle_records.sql)
      cat <<'EOF'
WITH required_constraints(table_name, constraint_name) AS (
  VALUES
    ('detector_lifecycle_records', 'detector_lifecycle_records_lifecycle_audit_references_check'),
    ('detector_lifecycle_records', 'detector_lifecycle_records_lifecycle_state_check'),
    ('detector_lifecycle_records', 'detector_lifecycle_records_pkey'),
    ('false_positive_review_records', 'false_positive_review_records_check'),
    ('false_positive_review_records', 'false_positive_review_records_disposition_check'),
    ('false_positive_review_records', 'false_positive_review_records_dispute_state_check'),
    ('false_positive_review_records', 'false_positive_review_records_lifecycle_state_check'),
    ('false_positive_review_records', 'false_positive_review_records_recurrence_posture_check'),
    ('false_positive_review_records', 'false_positive_review_records_review_evidence_references_check'),
    ('false_positive_review_records', 'false_positive_review_records_source_signal_handling_check'),
    ('false_positive_review_records', 'false_positive_review_records_pkey'),
    ('suppression_proposal_records', 'suppression_proposal_records_check'),
    ('suppression_proposal_records', 'suppression_proposal_records_citation_references_check'),
    ('suppression_proposal_records', 'suppression_proposal_records_lifecycle_state_check'),
    ('suppression_proposal_records', 'suppression_proposal_records_scope_check'),
    ('suppression_proposal_records', 'suppression_proposal_records_source_signal_handling_check'),
    ('suppression_proposal_records', 'suppression_proposal_records_pkey')
)
SELECT CASE
  WHEN (
    SELECT array_agg(column_name::text ORDER BY ordinal_position)
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
      AND table_name = 'detector_lifecycle_records'
  ) = ARRAY[
    'detector_lifecycle_id', 'owner', 'source_family', 'source_catalog_entry',
    'detector_identifier', 'expected_signal_posture', 'review_cadence',
    'rollback_owner', 'disable_owner', 'lifecycle_audit_references',
    'lifecycle_state', 'disabled_reason', 'rollback_reason',
    'review_overdue_reason', 'created_at', 'updated_at'
  ]::text[]
  AND (
    SELECT array_agg(column_name::text ORDER BY ordinal_position)
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
      AND table_name = 'false_positive_review_records'
  ) = ARRAY[
    'false_positive_review_id', 'detector_lifecycle_id', 'source_family',
    'source_catalog_entry', 'alert_id', 'case_id', 'evidence_ids', 'owner',
    'disposition', 'disposition_rationale', 'dispute_state',
    'recurrence_posture', 'review_evidence_references',
    'source_signal_handling', 'lifecycle_state', 'created_at', 'updated_at'
  ]::text[]
  AND (
    SELECT array_agg(column_name::text ORDER BY ordinal_position)
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
      AND table_name = 'suppression_proposal_records'
  ) = ARRAY[
    'suppression_proposal_id', 'detector_lifecycle_id', 'source_family',
    'source_catalog_entry', 'alert_id', 'case_id', 'evidence_ids', 'owner',
    'rationale', 'citation_references', 'expires_at', 'review_cadence',
    'expected_signal_impact', 'scope', 'source_signal_handling',
    'lifecycle_state', 'created_at', 'updated_at'
  ]::text[]
  AND NOT EXISTS (
    SELECT table_name, constraint_name FROM required_constraints
    EXCEPT
    SELECT relation.relname, constraint_record.conname
    FROM pg_constraint AS constraint_record
    JOIN pg_class AS relation ON relation.oid = constraint_record.conrelid
    WHERE constraint_record.connamespace = 'aegisops_control'::regnamespace
  )
  AND (
    SELECT COUNT(*)
    FROM pg_constraint
    WHERE conrelid = 'aegisops_control.lifecycle_transition_records'::regclass
      AND conname IN (
        'lifecycle_transition_records_subject_family_matches',
        'lifecycle_transition_records_state_matches_subject_family',
        'lifecycle_transition_records_previous_state_matches_subject_family'
      )
  ) = 3
  AND (
    (
      SELECT COUNT(*)
      FROM pg_constraint
      WHERE conrelid = 'aegisops_control.lifecycle_transition_records'::regclass
        AND conname IN (
          'lifecycle_transition_records_lifecycle_state_known',
          'lifecycle_transition_records_previous_lifecycle_state_known'
        )
    ) = 2
    OR
    (
      SELECT COUNT(*)
      FROM pg_constraint
      WHERE conrelid = 'aegisops_control.lifecycle_transition_records'::regclass
        AND conname IN (
          'lifecycle_transition_records_lifecycle_state_known_values',
          'lifecycle_transition_records_previous_lifecycle_state_known_values'
        )
    ) = 2
  )
  THEN 'ready' ELSE 'not-ready'
END;
EOF
      ;;
    0014_phase_61_source_health_records.sql)
      cat <<'EOF'
WITH required_constraints(constraint_name) AS (
  VALUES
    ('source_health_records_cache_sourced_check'),
    ('source_health_records_check'),
    ('source_health_records_check1'),
    ('source_health_records_credential_posture_check'),
    ('source_health_records_detector_drift_check'),
    ('source_health_records_display_state_authority_check'),
    ('source_health_records_evidence_references_check'),
    ('source_health_records_health_state_check'),
    ('source_health_records_reviewed_state_check'),
    ('source_health_records_source_native_authority_check'),
    ('source_health_records_pkey')
)
SELECT CASE
  WHEN (
    SELECT array_agg(column_name::text ORDER BY ordinal_position)
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
      AND table_name = 'source_health_records'
  ) = ARRAY[
    'source_health_id', 'source_family', 'source_catalog_entry', 'health_state',
    'reviewed_state', 'reviewed_at', 'observed_at', 'detector_drift',
    'credential_posture', 'evidence_references', 'operator_visible_reason',
    'source_native_authority', 'display_state_authority', 'cache_sourced',
    'lifecycle_state', 'created_at', 'updated_at'
  ]::text[]
  AND NOT EXISTS (
    SELECT constraint_name FROM required_constraints
    EXCEPT
    SELECT conname
    FROM pg_constraint
    WHERE conrelid = 'aegisops_control.source_health_records'::regclass
  )
  AND (
    SELECT COUNT(*)
    FROM pg_constraint
    WHERE conrelid = 'aegisops_control.lifecycle_transition_records'::regclass
      AND conname IN (
        'lifecycle_transition_records_subject_family_matches',
        'lifecycle_transition_records_state_matches_subject_family',
        'lifecycle_transition_records_previous_state_matches_subject_family'
      )
  ) = 3
  THEN 'ready' ELSE 'not-ready'
END;
EOF
      ;;
    0015_phase_64_known_limitation_ownership_records.sql)
      cat <<'EOF'
WITH required_constraints(constraint_name) AS (
  VALUES
    ('known_limitation_ownership_record_phase66_handoff_posture_check'),
    ('known_limitation_ownership_records_authority_boundary_check'),
    ('known_limitation_ownership_records_check'),
    ('known_limitation_ownership_records_check1'),
    ('known_limitation_ownership_records_evidence_references_check'),
    ('known_limitation_ownership_records_review_state_check'),
    ('known_limitation_ownership_records_severity_check'),
    ('known_limitation_ownership_records_pkey')
)
SELECT CASE
  WHEN (
    SELECT array_agg(column_name::text ORDER BY ordinal_position)
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
      AND table_name = 'known_limitation_ownership_records'
  ) = ARRAY[
    'limitation_id', 'title', 'severity', 'affected_surface', 'owner',
    'mitigation', 'evidence_references', 'review_state', 'review_cadence',
    'due_date', 'accepted_risk_posture', 'phase66_handoff_posture',
    'authority_boundary', 'readiness_claim', 'lifecycle_state',
    'created_at', 'updated_at'
  ]::text[]
  AND NOT EXISTS (
    SELECT constraint_name FROM required_constraints
    EXCEPT
    SELECT conname
    FROM pg_constraint
    WHERE conrelid = 'aegisops_control.known_limitation_ownership_records'::regclass
  )
  AND (
    SELECT COUNT(*)
    FROM pg_constraint
    WHERE conrelid = 'aegisops_control.lifecycle_transition_records'::regclass
      AND conname IN (
        'lifecycle_transition_records_subject_family_matches',
        'lifecycle_transition_records_lifecycle_state_known_values',
        'lifecycle_transition_records_previous_lifecycle_state_known_values',
        'lifecycle_transition_records_state_matches_subject_family',
        'lifecycle_transition_records_previous_state_matches_subject_family'
      )
  ) = 5
  THEN 'ready' ELSE 'not-ready'
END;
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
