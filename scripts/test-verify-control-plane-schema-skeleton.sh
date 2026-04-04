#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-control-plane-schema-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/postgres/control-plane/migrations"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_valid_fixture() {
  local target="$1"

  printf '%s\n' \
    "# Control-Plane Schema Skeleton" \
    "" \
    "This directory reserves the reviewed repository home for future AegisOps-owned control-plane schema and migration assets." \
    "" \
    "These files are placeholders only, are not production-ready, and do not authorize a live service, datastore deployment, credentials, or runtime migration execution." \
    "" \
    "The reserved schema boundary is \`aegisops_control\`, kept separate from n8n-owned PostgreSQL metadata and execution-state tables." \
    "" \
    "The initial placeholder record-family homes tracked here are:" \
    "" \
    "- \`alert_records\`" \
    "- \`case_records\`" \
    "- \`evidence_records\`" \
    "- \`observation_records\`" \
    "- \`lead_records\`" \
    "- \`recommendation_records\`" \
    "- \`approval_decision_records\`" \
    "- \`action_request_records\`" \
    "- \`hunt_records\`" \
    "- \`hunt_run_records\`" \
    "- \`ai_trace_records\`" \
    "- \`reconciliation_records\`" \
    >"${target}/postgres/control-plane/README.md"

  printf '%s\n' \
    "-- Control-plane schema skeleton for the future AegisOps-owned PostgreSQL boundary." \
    "-- Placeholder only. Not production-ready." \
    "-- schema: aegisops_control" \
    "create schema if not exists aegisops_control;" \
    "" \
    "-- table: alert_records" \
    "-- table: case_records" \
    "-- table: evidence_records" \
    "-- table: observation_records" \
    "-- table: lead_records" \
    "-- table: recommendation_records" \
    "-- table: approval_decision_records" \
    "-- table: action_request_records" \
    "-- table: hunt_records" \
    "-- table: hunt_run_records" \
    "-- table: ai_trace_records" \
    "-- table: reconciliation_records" \
    >"${target}/postgres/control-plane/schema.sql"

  printf '%s\n' \
    "-- Migration skeleton only. Do not run in production." \
    "begin;" \
    "create schema if not exists aegisops_control;" \
    "-- reserve table home: alert_records" \
    "-- reserve table home: case_records" \
    "-- reserve table home: evidence_records" \
    "-- reserve table home: observation_records" \
    "-- reserve table home: lead_records" \
    "-- reserve table home: recommendation_records" \
    "-- reserve table home: approval_decision_records" \
    "-- reserve table home: action_request_records" \
    "-- reserve table home: hunt_records" \
    "-- reserve table home: hunt_run_records" \
    "-- reserve table home: ai_trace_records" \
    "-- reserve table home: reconciliation_records" \
    "commit;" \
    >"${target}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"

  git -C "${target}" add postgres/control-plane/README.md
  git -C "${target}" add postgres/control-plane/schema.sql
  git -C "${target}" add postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql
  git -C "${target}" commit -q -m "fixture"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_valid_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_readme_repo="${workdir}/missing-readme"
create_repo "${missing_readme_repo}"
git -C "${missing_readme_repo}" commit -q --allow-empty -m "fixture"
assert_fails_with "${missing_readme_repo}" "Missing control-plane schema skeleton README"

missing_schema_repo="${workdir}/missing-schema"
create_repo "${missing_schema_repo}"
printf '%s\n' "# Control-Plane Schema Skeleton" >"${missing_schema_repo}/postgres/control-plane/README.md"
printf '%s\n' "-- Migration skeleton only. Do not run in production." >"${missing_schema_repo}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"
git -C "${missing_schema_repo}" add postgres/control-plane/README.md
git -C "${missing_schema_repo}" add postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql
git -C "${missing_schema_repo}" commit -q -m "fixture"
assert_fails_with "${missing_schema_repo}" "Missing control-plane schema skeleton manifest"

missing_family_repo="${workdir}/missing-family"
create_repo "${missing_family_repo}"
write_valid_fixture "${missing_family_repo}"
printf '%s\n' \
  "-- Control-plane schema skeleton for the future AegisOps-owned PostgreSQL boundary." \
  "-- Placeholder only. Not production-ready." \
  "-- schema: aegisops_control" \
  "create schema if not exists aegisops_control;" \
  "" \
  "-- table: alert_records" \
  "-- table: case_records" \
  "-- table: evidence_records" \
  "-- table: observation_records" \
  "-- table: lead_records" \
  "-- table: recommendation_records" \
  "-- table: approval_decision_records" \
  "-- table: action_request_records" \
  "-- table: hunt_records" \
  "-- table: hunt_run_records" \
  >"${missing_family_repo}/postgres/control-plane/schema.sql"
git -C "${missing_family_repo}" add postgres/control-plane/schema.sql
git -C "${missing_family_repo}" commit -q -m "fixture update"
assert_fails_with "${missing_family_repo}" "-- table: ai_trace_records"

missing_reconciliation_family_repo="${workdir}/missing-reconciliation-family"
create_repo "${missing_reconciliation_family_repo}"
write_valid_fixture "${missing_reconciliation_family_repo}"
printf '%s\n' \
  "-- Control-plane schema skeleton for the future AegisOps-owned PostgreSQL boundary." \
  "-- Placeholder only. Not production-ready." \
  "-- schema: aegisops_control" \
  "create schema if not exists aegisops_control;" \
  "" \
  "-- table: alert_records" \
  "-- table: case_records" \
  "-- table: evidence_records" \
  "-- table: observation_records" \
  "-- table: lead_records" \
  "-- table: recommendation_records" \
  "-- table: approval_decision_records" \
  "-- table: action_request_records" \
  "-- table: hunt_records" \
  "-- table: hunt_run_records" \
  "-- table: ai_trace_records" \
  >"${missing_reconciliation_family_repo}/postgres/control-plane/schema.sql"
git -C "${missing_reconciliation_family_repo}" add postgres/control-plane/schema.sql
git -C "${missing_reconciliation_family_repo}" commit -q -m "fixture update"
assert_fails_with "${missing_reconciliation_family_repo}" "-- table: reconciliation_records"

seed_repo="${workdir}/seed"
create_repo "${seed_repo}"
write_valid_fixture "${seed_repo}"
printf '%s\n' \
  "-- Migration skeleton only. Do not run in production." \
  "begin;" \
  "create schema if not exists aegisops_control;" \
  "-- reserve table home: alert_records" \
  "-- reserve table home: case_records" \
  "-- reserve table home: evidence_records" \
  "-- reserve table home: observation_records" \
  "-- reserve table home: lead_records" \
  "-- reserve table home: recommendation_records" \
  "-- reserve table home: approval_decision_records" \
  "-- reserve table home: action_request_records" \
  "-- reserve table home: hunt_records" \
  "-- reserve table home: hunt_run_records" \
  "-- reserve table home: ai_trace_records" \
  "-- reserve table home: reconciliation_records" \
  "insert into aegisops_control.alert_records (alert_id) values ('alert-1');" \
  "commit;" \
  >"${seed_repo}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"
git -C "${seed_repo}" add postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql
git -C "${seed_repo}" commit -q -m "fixture update"
assert_fails_with "${seed_repo}" "must not seed live control-plane data"

echo "verify-control-plane-schema-skeleton tests passed"
