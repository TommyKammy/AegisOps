#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
readme_path="${repo_root}/postgres/control-plane/README.md"
schema_path="${repo_root}/postgres/control-plane/schema.sql"
migration_path="${repo_root}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"
forward_migration_path="${repo_root}/postgres/control-plane/migrations/0002_phase_14_reviewed_context_columns.sql"

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing control-plane schema README: ${readme_path}" >&2
  exit 1
fi

if [[ ! -f "${schema_path}" ]]; then
  echo "Missing control-plane schema manifest: ${schema_path}" >&2
  exit 1
fi

if [[ ! -f "${migration_path}" ]]; then
  echo "Missing control-plane schema migration: ${migration_path}" >&2
  exit 1
fi

if [[ ! -f "${forward_migration_path}" ]]; then
  echo "Missing Phase 14 forward control-plane migration: ${forward_migration_path}" >&2
  exit 1
fi

require_fixed_string() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" "${file_path}" >/dev/null; then
    echo "Missing required line in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

require_pattern() {
  local file_path="$1"
  local pattern="$2"
  local message="$3"

  if ! grep -En "${pattern}" "${file_path}" >/dev/null; then
    echo "${message}" >&2
    exit 1
  fi
}

require_table_contains_line() {
  local file_path="$1"
  local table_name="$2"
  local needle="$3"

  if ! awk -v table_name="${table_name}" -v needle="${needle}" '
    { sub(/\r$/, "", $0) }
    $0 == "create table if not exists aegisops_control." table_name " (" { in_table = 1; next }
    in_table && $0 == ");" { in_table = 0 }
    in_table && index($0, needle) > 0 { found = 1 }
    END { exit found ? 0 : 1 }
  ' "${file_path}"; then
    echo "Missing required line in ${file_path} within ${table_name}_records: ${needle}" >&2
    exit 1
  fi
}

require_pattern "${readme_path}" '^# Control-Plane Schema v1$' \
  "Control-plane schema README must declare the v1 baseline."
require_pattern "${readme_path}" 'runtime-ready control-plane schema baseline' \
  "Control-plane schema README must describe the reviewed runtime-ready baseline."
require_pattern "${readme_path}" 'do(es)? not authorize live deployment, production data migration, or credentials' \
  "Control-plane schema README must forbid live deployment, production migration, or credentials."
require_pattern "${readme_path}" 'n8n-owned PostgreSQL metadata and execution-state tables' \
  "Control-plane schema README must preserve the n8n ownership boundary."
require_pattern "${readme_path}" 'Future work remains explicit' \
  "Control-plane schema README must keep future work explicit."

require_fixed_string "${schema_path}" "-- Control-plane schema v1 for the AegisOps-owned PostgreSQL boundary."
require_fixed_string "${schema_path}" "-- runtime_baseline: reviewed_v1"
require_fixed_string "${schema_path}" "-- schema: aegisops_control"
require_fixed_string "${schema_path}" "create schema if not exists aegisops_control;"
require_pattern "${schema_path}" 'reconciliation boundary' \
  "Control-plane schema manifest must document the reconciliation boundary."

require_fixed_string "${migration_path}" "-- Control-plane schema v1 baseline migration."
require_pattern "${migration_path}" '^begin;$' \
  "Control-plane migration must start an explicit transaction."
require_pattern "${migration_path}" '^commit;$' \
  "Control-plane migration must end an explicit transaction."
require_pattern "${migration_path}" '^create schema if not exists aegisops_control;$' \
  "Control-plane migration must reserve the aegisops_control schema."

require_fixed_string "${forward_migration_path}" "-- Phase 14 forward migration for reviewed_context on identity-rich reviewed record families."
require_pattern "${forward_migration_path}" '^begin;$' \
  "Phase 14 forward migration must start an explicit transaction."
require_pattern "${forward_migration_path}" '^commit;$' \
  "Phase 14 forward migration must end an explicit transaction."
require_fixed_string "${forward_migration_path}" "alter table if exists aegisops_control.alert_records"
require_fixed_string "${forward_migration_path}" "alter table if exists aegisops_control.analytic_signal_records"
require_fixed_string "${forward_migration_path}" "alter table if exists aegisops_control.case_records"
require_fixed_string "${forward_migration_path}" "alter table if exists aegisops_control.recommendation_records"
require_fixed_string "${forward_migration_path}" "  add column if not exists reviewed_context jsonb not null default '{}'::jsonb;"

record_families=(
  "alert"
  "case"
  "evidence"
  "observation"
  "lead"
  "recommendation"
  "approval_decision"
  "action_request"
  "hunt"
  "hunt_run"
  "ai_trace"
  "reconciliation"
)

for family in "${record_families[@]}"; do
  require_pattern "${schema_path}" "^create table if not exists aegisops_control\\.${family}_records \\($" \
    "Control-plane schema manifest must materialize ${family}_records."
  require_pattern "${schema_path}" "^\\s+lifecycle_state text not null,$" \
    "Control-plane schema manifest must define lifecycle_state columns."
  require_pattern "${migration_path}" "^create table if not exists aegisops_control\\.${family}_records \\($" \
    "Control-plane migration must materialize ${family}_records."
done

for family in alert analytic_signal case recommendation; do
  require_table_contains_line "${schema_path}" "${family}_records" "reviewed_context jsonb not null default '{}'::jsonb,"
done

require_pattern "${schema_path}" 'check \(' \
  "Control-plane schema manifest must constrain lifecycle states with explicit checks."
require_pattern "${schema_path}" 'linked_execution_run_ids text\[\] not null default '\''\{\}'\''::text\[\]' \
  "Control-plane schema manifest must preserve explicit reconciliation linkage to execution-plane records."

if grep -Ein '^[[:space:]]*insert[[:space:]]' "${schema_path}" >/dev/null; then
  echo "Control-plane schema manifest must not seed live control-plane data." >&2
  exit 1
fi

if grep -Ein '^[[:space:]]*insert[[:space:]]' "${migration_path}" >/dev/null; then
  echo "Control-plane migration must not seed live control-plane data." >&2
  exit 1
fi

echo "Control-plane schema assets match the reviewed v1 baseline."
