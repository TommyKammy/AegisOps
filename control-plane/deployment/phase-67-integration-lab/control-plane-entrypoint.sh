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
    ('suppression_proposal_records', 'suppression_proposal_records_check', 'c', 'c301f4f6b2114934d4ed303465343282c5d5f24deb560d9d1564a1c8a115af9f'),
    ('suppression_proposal_records', 'suppression_proposal_records_citation_references_check', 'c', '94d775f52f33dc14149c46d6db50988780d2c23b5093909675e6c8794b4ffe08'),
    ('suppression_proposal_records', 'suppression_proposal_records_lifecycle_state_check', 'c', '111609d959aecc0bf7bdc5c2dc2b7de5651042e3afe6eed619773ea61420d146'),
    ('suppression_proposal_records', 'suppression_proposal_records_scope_check', 'c', 'e2eabef5b9c4305c25884438a42404210babd99e34e13c4d34d8bf06ba48d01d'),
    ('suppression_proposal_records', 'suppression_proposal_records_source_signal_handling_check', 'c', 'a73e31642acad39f915fa3d5ab4c406ad523f098a0b78556e4a9491eb6fb780a'),
    ('suppression_proposal_records', 'suppression_proposal_records_pkey', 'p', '042287098cca89ed986f5908087860c2c25da2791bbcfbc6e1af47413feaac88')
),
required_table_signatures(table_name, column_definition_sha256) AS (
  VALUES
    ('detector_lifecycle_records', 'c8fc21a6b5137a90c9b0590994e7894a3530d1832b06b3877375437c0a0f84ef'),
    ('false_positive_review_records', 'f7be4ff9d0f0a60bf0c44fd2532ef74aefcf0e22e80111d9d17426cf2c2e9bc3'),
    ('suppression_proposal_records', 'ae202414690ff4276e6cf7536cb2994f6a61693af34f29335f6a322f4e7c2b5b')
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
    SELECT table_name, column_definition_sha256
    FROM required_table_signatures
    EXCEPT
    SELECT
      table_name,
      encode(
        sha256(
          convert_to(
            string_agg(
              ordinal_position::text || '|' ||
              column_name || '|' ||
              data_type || '|' ||
              udt_name || '|' ||
              is_nullable || '|' ||
              COALESCE(column_default, '<NULL>'),
              E'\n' ORDER BY ordinal_position
            ),
            'UTF8'
          )
        ),
        'hex'
      )
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
    GROUP BY table_name
  )
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
WITH required_constraints(
  table_name,
  constraint_name,
  constraint_type,
  constraint_definition_sha256
) AS (
  VALUES
    ('source_health_records', 'source_health_records_cache_sourced_check', 'c', 'c0eecfc71b9e55e2ee8d2712cbee1448497f847711f67a4f74977155de559920'),
    ('source_health_records', 'source_health_records_check', 'c', 'f7d22a54742633931e33d0df4430e6c84110dfdbbb20c2eee2e52393b3cd7ff5'),
    ('source_health_records', 'source_health_records_check1', 'c', 'a9f67478d1b055d8498c001972c3fbf3d3f99a9dc14f8d32553a4d8c82fe3fbe'),
    ('source_health_records', 'source_health_records_credential_posture_check', 'c', '6979b4a597cc0fdb2f8ce6edea86403e778c9b4da7a4c0945b1c4ead3ac51913'),
    ('source_health_records', 'source_health_records_detector_drift_check', 'c', 'eb75b6976ba1e6a9ad6da2df2dc6f89eece6ac4c51dbcbbff546facd396e0981'),
    ('source_health_records', 'source_health_records_display_state_authority_check', 'c', 'daeefd502d0af4b63e4c1c0efea68ee48d08c7ebcd17d6f012c09874aea2cb89'),
    ('source_health_records', 'source_health_records_evidence_references_check', 'c', '450241642dd9e29a7ac9bb598411f364434e92f83cd25690cd7ad4a9ab506147'),
    ('source_health_records', 'source_health_records_health_state_check', 'c', '440efb2ab8aca4681d5a969106cb9573679f8cb3f6a311c72e36b68aaa312b2c'),
    ('source_health_records', 'source_health_records_reviewed_state_check', 'c', '22815d84e2c821c4f835794d31097373c4aa56c6009f7b28ccc3f6e3861a0628'),
    ('source_health_records', 'source_health_records_source_native_authority_check', 'c', 'fe00860392a891d58a3708c82454acb3747291fb8a3c3379514de9fcbcb47d7b'),
    ('source_health_records', 'source_health_records_pkey', 'p', '62226b9278f392cb0ce33d6a4115fe2ccd4fdddf286f3116bb6fc1b6447dead1')
),
required_table_signatures(table_name, column_definition_sha256) AS (
  VALUES
    ('source_health_records', 'cb6ee538dcb158f0bc6a25bddd04f9ff6f38c3a5d2fb88d0922cf06f0cf555f7')
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
    SELECT table_name, column_definition_sha256
    FROM required_table_signatures
    EXCEPT
    SELECT
      table_name,
      encode(
        sha256(
          convert_to(
            string_agg(
              ordinal_position::text || '|' ||
              column_name || '|' ||
              data_type || '|' ||
              udt_name || '|' ||
              is_nullable || '|' ||
              COALESCE(column_default, '<NULL>'),
              E'\n' ORDER BY ordinal_position
            ),
            'UTF8'
          )
        ),
        'hex'
      )
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
    GROUP BY table_name
  )
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
    0015_phase_64_known_limitation_ownership_records.sql)
      cat <<'EOF'
WITH required_constraints(
  table_name,
  constraint_name,
  constraint_type,
  constraint_definition_sha256
) AS (
  VALUES
    ('known_limitation_ownership_records', 'known_limitation_ownership_record_phase66_handoff_posture_check', 'c', 'f88e5cdaaa4b0079bfcadd42c335b0b22722fd4f856ed1e1a609b4fdf6589f6f'),
    ('known_limitation_ownership_records', 'known_limitation_ownership_records_authority_boundary_check', 'c', '46daf54580215aa96626061e70ada968b8eca7506f102bbf242e7d3d62e11f1d'),
    ('known_limitation_ownership_records', 'known_limitation_ownership_records_check', 'c', '828ea502b4ba467f5c4722d1f91d14829c47459bc5e59be5f21b635cde9b27ad'),
    ('known_limitation_ownership_records', 'known_limitation_ownership_records_check1', 'c', 'e72e32c4789dfb782250e110d7104ea61047ce5ad83901bb77ebc42a2f079b33'),
    ('known_limitation_ownership_records', 'known_limitation_ownership_records_evidence_references_check', 'c', '450241642dd9e29a7ac9bb598411f364434e92f83cd25690cd7ad4a9ab506147'),
    ('known_limitation_ownership_records', 'known_limitation_ownership_records_review_state_check', 'c', 'd5c803f97e228707f2073928298c16525d0745fb4beab331923c96b2556a6a4e'),
    ('known_limitation_ownership_records', 'known_limitation_ownership_records_severity_check', 'c', '411666e04294ee4749c61ca9b01cb8fe5bc0ea1ab6a390570114ffee7499d37c'),
    ('known_limitation_ownership_records', 'known_limitation_ownership_records_pkey', 'p', '03632a7197298f23150518683fc2be1ae9699c3975cad9443532eb7e99815469'),
    ('lifecycle_transition_records', 'lifecycle_transition_records_lifecycle_state_known_values', 'c', 'ef74ab603986603cd2ff2b00511ee728ac9f065d990aacae741d3dce390640ff'),
    ('lifecycle_transition_records', 'lifecycle_transition_records_previous_lifecycle_state_known_val', 'c', 'fefe9fb48ffe837ef6521937db37dd146676fe063f5b3cb5cd3b33c6b80b36ea'),
    ('lifecycle_transition_records', 'lifecycle_transition_records_previous_state_matches_subject_fam', 'c', 'ea647d71bbb5b19a89e675e6a89c74f6172e2c04c27864f8a018d6af4cddd4e1'),
    ('lifecycle_transition_records', 'lifecycle_transition_records_state_matches_subject_family', 'c', '56829e22566a5973397174a2c18d77ecb0c387f25d9c2555d39bc34ce9b0113c'),
    ('lifecycle_transition_records', 'lifecycle_transition_records_subject_family_matches', 'c', 'e2595161f20c3faf32d1891f26f6c8eeeb08c40c73a6db8ebb495bdec6fb7bba')
),
required_table_signatures(table_name, column_definition_sha256) AS (
  VALUES
    ('known_limitation_ownership_records', '6854488c1104636fedc6452212aedaf545a2a3447ebde3b47af026b693bb8f1e')
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
    SELECT table_name, column_definition_sha256
    FROM required_table_signatures
    EXCEPT
    SELECT
      table_name,
      encode(
        sha256(
          convert_to(
            string_agg(
              ordinal_position::text || '|' ||
              column_name || '|' ||
              data_type || '|' ||
              udt_name || '|' ||
              is_nullable || '|' ||
              COALESCE(column_default, '<NULL>'),
              E'\n' ORDER BY ordinal_position
            ),
            'UTF8'
          )
        ),
        'hex'
      )
    FROM information_schema.columns
    WHERE table_schema = 'aegisops_control'
    GROUP BY table_name
  )
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
    0016_phase_67_action_execution_dispatching_state.sql)
      cat <<'EOF'
SELECT CASE
  WHEN EXISTS (
    SELECT 1
    FROM pg_constraint AS constraint_record
    JOIN pg_class AS relation ON relation.oid = constraint_record.conrelid
    WHERE constraint_record.connamespace = 'aegisops_control'::regnamespace
      AND relation.relname = 'action_execution_records'
      AND constraint_record.conname = 'action_execution_records_lifecycle_state_check'
      AND constraint_record.contype = 'c'
      AND constraint_record.convalidated
      AND encode(
        sha256(
          convert_to(
            pg_get_constraintdef(constraint_record.oid, true),
            'UTF8'
          )
        ),
        'hex'
      ) = '5b340453651de616ba658ab802f574a909f04bccf7e7c483a5ba92c6d50b8c9e'
  )
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

reviewed_schema_catalog_query() {
  cat <<'EOF'
WITH expected_catalog_hashes(catalog_name, catalog_sha256) AS (
  VALUES
    ('columns', 'd906ba1ab5288c94b5c277c1aad60d6ddf499ad2aed55a2abde8729e639d3443'),
    ('constraints', '5de18095fdfcf3c0d223a45280d3b96a699dde0ebdc6e11328a1a936fb39d8de'),
    ('indexes', 'ba3907928c1c026b50f3a9e37c870d6c0008dddb2ebeccf9001cf937898c7d4f')
),
actual_catalog_hashes(catalog_name, catalog_sha256) AS (
  SELECT
    'columns',
    encode(
      sha256(
        convert_to(
          string_agg(
            table_name || '|' || ordinal_position::text || '|' ||
            column_name || '|' || data_type || '|' || udt_name || '|' ||
            is_nullable || '|' || COALESCE(column_default, '<NULL>'),
            E'\n' ORDER BY table_name, ordinal_position
          ),
          'UTF8'
        )
      ),
      'hex'
    )
  FROM information_schema.columns
  WHERE table_schema = 'aegisops_control'
  UNION ALL
  SELECT
    'constraints',
    encode(
      sha256(
        convert_to(
          string_agg(
            relation.relname || '|' || constraint_record.conname || '|' ||
            constraint_record.contype::text || '|' ||
            constraint_record.convalidated::text || '|' ||
            pg_get_constraintdef(constraint_record.oid, true),
            E'\n' ORDER BY relation.relname, constraint_record.conname
          ),
          'UTF8'
        )
      ),
      'hex'
    )
  FROM pg_constraint AS constraint_record
  JOIN pg_class AS relation ON relation.oid = constraint_record.conrelid
  JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
  WHERE namespace.nspname = 'aegisops_control'
  UNION ALL
  SELECT
    'indexes',
    encode(
      sha256(
        convert_to(
          string_agg(
            tablename || '|' || indexname || '|' || indexdef,
            E'\n' ORDER BY tablename, indexname
          ),
          'UTF8'
        )
      ),
      'hex'
    )
  FROM pg_indexes
  WHERE schemaname = 'aegisops_control'
)
SELECT CASE
  WHEN NOT EXISTS (
    SELECT catalog_name, catalog_sha256
    FROM expected_catalog_hashes
    EXCEPT
    SELECT catalog_name, catalog_sha256
    FROM actual_catalog_hashes
  )
  AND NOT EXISTS (
    SELECT catalog_name, catalog_sha256
    FROM actual_catalog_hashes
    EXCEPT
    SELECT catalog_name, catalog_sha256
    FROM expected_catalog_hashes
  )
  THEN 'ready' ELSE 'not-ready'
END;
EOF
}

prove_delegated_migration_definitions() {
  catalog_status="$(
    psql -X "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN}" -tA -v ON_ERROR_STOP=1 \
      -c "$(reviewed_schema_catalog_query)" |
      tr -d '[:space:]'
  )" || return 1
  [ "${catalog_status}" = "ready" ]
}

for migration_path in \
  "${migrations_dir}"/0008_*.sql \
  "${migrations_dir}"/0009_*.sql \
  "${migrations_dir}"/0010_*.sql \
  "${migrations_dir}"/0011_*.sql \
  "${migrations_dir}"/0012_*.sql \
  "${migrations_dir}"/0013_*.sql \
  "${migrations_dir}"/0014_*.sql \
  "${migrations_dir}"/0015_*.sql \
  "${migrations_dir}"/0016_*.sql
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

# Migrations 0001-0007 are delegated to the first-boot entrypoint. Reprove the
# complete final catalog after 0008-0016 apply so reviewed later evolution of
# those early tables is accepted while any column, constraint, or index drift
# still fails before the service process starts.
if ! prove_delegated_migration_definitions; then
  echo "Phase 67.1 could not prove final schema definitions for delegated migrations 0001-0007." >&2
  exit 1
fi

exec "$@"
