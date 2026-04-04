#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
readme_path="${repo_root}/postgres/control-plane/README.md"
schema_path="${repo_root}/postgres/control-plane/schema.sql"
migration_path="${repo_root}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing control-plane schema skeleton README: ${readme_path}" >&2
  exit 1
fi

if [[ ! -f "${schema_path}" ]]; then
  echo "Missing control-plane schema skeleton manifest: ${schema_path}" >&2
  exit 1
fi

if [[ ! -f "${migration_path}" ]]; then
  echo "Missing control-plane schema skeleton migration: ${migration_path}" >&2
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

reject_live_ddl() {
  local file_path="$1"
  local artifact_label="$2"
  local forbidden_pattern='^[[:space:]]*(create[[:space:]]+(table|index|unique[[:space:]]+index|view|materialized[[:space:]]+view|sequence|trigger|function)|alter[[:space:]]+(table|index|schema)|drop[[:space:]]+(table|index|view|materialized[[:space:]]+view|sequence|trigger|function|schema)|insert[[:space:]]|update[[:space:]]|delete[[:space:]]+from|truncate[[:space:]]+table|comment[[:space:]]+on[[:space:]]|grant[[:space:]]|revoke[[:space:]])'

  if grep -Ein "${forbidden_pattern}" "${file_path}" >/dev/null; then
    echo "${artifact_label} must not contain live implementation DDL beyond the approved placeholder boundary." >&2
    exit 1
  fi
}

require_pattern "${readme_path}" '^# Control-Plane Schema Skeleton$' \
  "Control-plane schema skeleton README must declare the placeholder skeleton."
require_pattern "${readme_path}" 'placeholder' \
  "Control-plane schema skeleton README must state that the assets are placeholders."
require_pattern "${readme_path}" 'not production-ready' \
  "Control-plane schema skeleton README must state that the assets are not production-ready."
require_pattern "${readme_path}" 'do(es)? not authorize a live service, datastore deployment, credentials, or runtime migration execution' \
  "Control-plane schema skeleton README must forbid live deployment or credentials."

require_fixed_string "${schema_path}" "-- Control-plane schema skeleton for the future AegisOps-owned PostgreSQL boundary."
require_fixed_string "${schema_path}" "-- Placeholder only. Not production-ready."
require_fixed_string "${schema_path}" "create schema if not exists aegisops_control;"
require_pattern "${schema_path}" '^-- schema: aegisops_control$' \
  "Control-plane schema skeleton manifest must name the aegisops_control schema."

require_fixed_string "${migration_path}" "-- Migration skeleton only. Do not run in production."
require_pattern "${migration_path}" '^begin;$' \
  "Control-plane migration skeleton must start an explicit transaction."
require_pattern "${migration_path}" '^commit;$' \
  "Control-plane migration skeleton must end an explicit transaction."
require_pattern "${migration_path}" '^create schema if not exists aegisops_control;$' \
  "Control-plane migration skeleton must reserve the aegisops_control schema."

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
  require_fixed_string "${schema_path}" "-- table: ${family}_records"
  require_fixed_string "${migration_path}" "-- reserve table home: ${family}_records"
done

if grep -Ein '^[[:space:]]*insert[[:space:]]' "${schema_path}" >/dev/null; then
  echo "Control-plane schema skeleton manifest must not seed live control-plane data." >&2
  exit 1
fi

if grep -Ein '^[[:space:]]*insert[[:space:]]' "${migration_path}" >/dev/null; then
  echo "Control-plane migration skeleton must not seed live control-plane data." >&2
  exit 1
fi

reject_live_ddl "${schema_path}" "Control-plane schema skeleton manifest"
reject_live_ddl "${migration_path}" "Control-plane migration skeleton"

echo "Control-plane schema skeleton matches the approved placeholder contract."
