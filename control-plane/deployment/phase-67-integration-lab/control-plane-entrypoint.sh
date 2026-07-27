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
WITH required_constraints(
  table_name,
  constraint_name,
  constraint_type,
  constraint_definition_sha256
) AS (
  VALUES
    ('detector_lifecycle_records', 'detector_lifecycle_records_lifecycle_audit_references_check', 'c', 'baa018bbc9e92cdcdc66a3ef7348cf8ef25c3e44e1522325ddde82407be6384c'),
    ('detector_lifecycle_records', 'detector_lifecycle_records_lifecycle_state_check', 'c', '326c0e0c27344296c0fed67fdd2154697a994777632ba749357d1d918137b1da'),
    ('detector_lifecycle_records', 'detector_lifecycle_records_pkey', 'p', 'fb856795c560c3513a1abd6205472cd1e766cc37859113cc5aa76b4e2d272b7b'),
    ('false_positive_review_records', 'false_positive_review_records_check', 'c', 'c301f4f6b2114934d4ed303465343282c5d5f24deb560d9d1564a1c8a115af9f'),
    ('false_positive_review_records', 'false_positive_review_records_disposition_check', 'c', 'a6db0268ab4cc254070904bd80b5b9f9a1117c277b346bf02b4c02d81d61d94d'),
    ('false_positive_review_records', 'false_positive_review_records_dispute_state_check', 'c', '2d5f25807637aecca3c453bad6a92268f08edef259f3ef337750dbcb4257e567'),
    ('false_positive_review_records', 'false_positive_review_records_lifecycle_state_check', 'c', '5980dbdd0348b7e34b1056e74e91a4dffd1d02e44f4b5e6ae490f0bc92af579e'),
    ('false_positive_review_records', 'false_positive_review_records_recurrence_posture_check', 'c', '82156f1b791c32c6a58263b607d1717edfbaeba2c80b4eaa73a4a239e32daed1'),
    ('false_positive_review_records', 'false_positive_review_records_review_evidence_references_check', 'c', '049adf5e78e910c4701d246a7091aa8da825b7463e68307a42aec00f4743f112'),
    ('false_positive_review_records', 'false_positive_review_records_source_signal_handling_check', 'c', 'ac35853bca6023fe207581f73a23a17019947ae54fc8fbcb3f4730018411033a'),
    ('false_positive_review_records', 'false_positive_review_records_pkey', 'p', 'd533a279676c8fe30544a6d7f32aa3d5514981f9f76400a1b01f8f252270505c'),
    ('lifecycle_transition_records', 'lifecycle_transition_records_lifecycle_state_known_values', 'c', 'ef74ab603986603cd2ff2b00511ee728ac9f065d990aacae741d3dce390640ff'),
    ('lifecycle_transition_records', 'lifecycle_transition_records_previous_lifecycle_state_known_val', 'c', 'fefe9fb48ffe837ef6521937db37dd146676fe063f5b3cb5cd3b33c6b80b36ea'),
    ('lifecycle_transition_records', 'lifecycle_transition_records_previous_state_matches_subject_fam', 'c', '168b886ebcfa9bc75e364c714f6fb12e911190e6160498ba8ebc12e7864472d1'),
    ('lifecycle_transition_records', 'lifecycle_transition_records_state_matches_subject_family', 'c', 'f1c1cd1c9e8ffa25a7e45897033e496c488ff5226263bca00fb69bd1a1058896'),
    ('lifecycle_transition_records', 'lifecycle_transition_records_subject_family_matches', 'c', '140510440ec3b14bd340813f458665ef7adde6e2c780e47a460621d4850785a0'),
    ('suppression_proposal_records', 'suppression_proposal_records_check', 'c', 'c301f4f6b2114934d4ed303465343282c5d5f24deb560d9d1564a1c8a115af9f'),
    ('suppression_proposal_records', 'suppression_proposal_records_citation_references_check', 'c', '94d775f52f33dc14149c46d6db50988780d2c23b5093909675e6c8794b4ffe08'),
    ('suppression_proposal_records', 'suppression_proposal_records_lifecycle_state_check', 'c', '111609d959aecc0bf7bdc5c2dc2b7de5651042e3afe6eed619773ea61420d146'),
    ('suppression_proposal_records', 'suppression_proposal_records_scope_check', 'c', 'e2eabef5b9c4305c25884438a42404210babd99e34e13c4d34d8bf06ba48d01d'),
    ('suppression_proposal_records', 'suppression_proposal_records_source_signal_handling_check', 'c', 'a73e31642acad39f915fa3d5ab4c406ad523f098a0b78556e4a9491eb6fb780a'),
    ('suppression_proposal_records', 'suppression_proposal_records_pkey', 'p', '042287098cca89ed986f5908087860c2c25da2791bbcfbc6e1af47413feaac88')
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
    SELECT
      table_name,
      constraint_name,
      constraint_type,
      constraint_definition_sha256
    FROM required_constraints
    EXCEPT
    SELECT
      relation.relname::text,
      constraint_record.conname::text,
      constraint_record.contype::text,
      encode(
        sha256(
          convert_to(
            pg_get_constraintdef(constraint_record.oid, true),
            'UTF8'
          )
        ),
        'hex'
      )
    FROM pg_constraint AS constraint_record
    JOIN pg_class AS relation ON relation.oid = constraint_record.conrelid
    WHERE constraint_record.connamespace = 'aegisops_control'::regnamespace
      AND constraint_record.convalidated
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
