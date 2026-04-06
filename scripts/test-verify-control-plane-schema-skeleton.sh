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
    "# Control-Plane Schema v1" \
    "" \
    "This directory contains the reviewed runtime-ready control-plane schema baseline for the AegisOps-owned PostgreSQL boundary." \
    "" \
    "The schema remains separate from n8n-owned PostgreSQL metadata and execution-state tables even when both live on the same engine class." \
    "" \
    "These repository assets do not authorize live deployment, production data migration, or credentials." \
    "" \
    "Future work remains explicit: online rollout sequencing, environment-specific access controls, and additional index tuning stay out of scope for this baseline." \
    >"${target}/postgres/control-plane/README.md"

  printf '%s\n' \
    "-- Control-plane schema v1 for the AegisOps-owned PostgreSQL boundary." \
    "-- runtime_baseline: reviewed_v1" \
    "-- schema: aegisops_control" \
    "-- reconciliation boundary: control-plane records keep mismatch state explicit without collapsing into n8n-owned execution tables." \
    "create schema if not exists aegisops_control;" \
    "" \
    "create table if not exists aegisops_control.alert_records (" \
    "  alert_id text primary key," \
    "  finding_id text not null," \
    "  analytic_signal_id text," \
    "  case_id text," \
    "  lifecycle_state text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  check (lifecycle_state in ('new','triaged','investigating','escalated_to_case','closed','reopened','superseded'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.case_records (" \
    "  case_id text primary key," \
    "  alert_id text," \
    "  finding_id text," \
    "  evidence_ids text[] not null," \
    "  lifecycle_state text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  check (finding_id is not null or alert_id is not null)," \
    "  check (cardinality(evidence_ids) >= 1)," \
    "  check (lifecycle_state in ('open','investigating','pending_action','contained_pending_validation','closed','reopened','superseded'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.evidence_records (" \
    "  evidence_id text primary key," \
    "  source_record_id text not null," \
    "  alert_id text," \
    "  case_id text," \
    "  source_system text not null," \
    "  collector_identity text not null," \
    "  acquired_at timestamptz not null," \
    "  derivation_relationship text," \
    "  lifecycle_state text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  check (alert_id is not null or case_id is not null)," \
    "  check (lifecycle_state in ('collected','validated','linked','superseded','withdrawn'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.observation_records (" \
    "  observation_id text primary key," \
    "  hunt_id text," \
    "  hunt_run_id text," \
    "  alert_id text," \
    "  case_id text," \
    "  supporting_evidence_ids text[] not null," \
    "  author_identity text not null," \
    "  observed_at timestamptz not null," \
    "  scope_statement text not null," \
    "  lifecycle_state text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  check (hunt_id is not null or hunt_run_id is not null or alert_id is not null or case_id is not null)," \
    "  check (cardinality(supporting_evidence_ids) >= 1)," \
    "  check (lifecycle_state in ('captured','confirmed','challenged','superseded','withdrawn'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.lead_records (" \
    "  lead_id text primary key," \
    "  observation_id text," \
    "  finding_id text," \
    "  hunt_run_id text," \
    "  alert_id text," \
    "  case_id text," \
    "  triage_owner text not null," \
    "  triage_rationale text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  lifecycle_state text not null," \
    "  check (observation_id is not null or finding_id is not null or hunt_run_id is not null)," \
    "  check (lifecycle_state in ('open','triaged','promoted_to_alert','promoted_to_case','closed','superseded'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.recommendation_records (" \
    "  recommendation_id text primary key," \
    "  lead_id text," \
    "  hunt_run_id text," \
    "  alert_id text," \
    "  case_id text," \
    "  ai_trace_id text," \
    "  review_owner text not null," \
    "  intended_outcome text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  lifecycle_state text not null," \
    "  check (lead_id is not null or hunt_run_id is not null or alert_id is not null or case_id is not null)," \
    "  check (lifecycle_state in ('proposed','under_review','accepted','rejected','materialized','superseded','withdrawn'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.approval_decision_records (" \
    "  approval_decision_id text primary key," \
    "  action_request_id text not null," \
    "  approver_identities text[] not null," \
    "  target_snapshot jsonb not null," \
    "  payload_hash text not null," \
    "  decided_at timestamptz," \
    "  lifecycle_state text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  check (cardinality(approver_identities) >= 1)," \
    "  check (lifecycle_state in ('pending','approved','rejected','expired','canceled','superseded'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.action_request_records (" \
    "  action_request_id text primary key," \
    "  approval_decision_id text," \
    "  case_id text," \
    "  alert_id text," \
    "  finding_id text," \
    "  idempotency_key text not null," \
    "  target_scope jsonb not null," \
    "  payload_hash text not null," \
    "  requested_at timestamptz not null," \
    "  expires_at timestamptz," \
    "  lifecycle_state text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  check (case_id is not null or alert_id is not null or finding_id is not null)," \
    "  check (lifecycle_state in ('draft','pending_approval','approved','rejected','expired','canceled','superseded','executing','completed','failed','unresolved'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.hunt_records (" \
    "  hunt_id text primary key," \
    "  hypothesis_statement text not null," \
    "  hypothesis_version text not null," \
    "  owner_identity text not null," \
    "  scope_boundary text not null," \
    "  opened_at timestamptz not null," \
    "  alert_id text," \
    "  case_id text," \
    "  lifecycle_state text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  check (lifecycle_state in ('draft','active','on_hold','concluded','closed','superseded'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.hunt_run_records (" \
    "  hunt_run_id text primary key," \
    "  hunt_id text not null," \
    "  scope_snapshot jsonb not null," \
    "  execution_plan_reference text not null," \
    "  output_linkage jsonb not null default '{}'::jsonb," \
    "  started_at timestamptz," \
    "  completed_at timestamptz," \
    "  lifecycle_state text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  check (lifecycle_state in ('planned','running','completed','canceled','superseded','unresolved'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.ai_trace_records (" \
    "  ai_trace_id text primary key," \
    "  subject_linkage jsonb not null," \
    "  model_identity text not null," \
    "  prompt_version text not null," \
    "  generated_at timestamptz not null," \
    "  material_input_refs text[] not null default '{}'::text[]," \
    "  reviewer_identity text not null," \
    "  lifecycle_state text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  check (lifecycle_state in ('generated','under_review','accepted_for_reference','rejected_for_reference','superseded','withdrawn'))" \
    ");" \
    "" \
    "create table if not exists aegisops_control.reconciliation_records (" \
    "  reconciliation_id text primary key," \
    "  subject_linkage jsonb not null," \
    "  finding_id text," \
    "  analytic_signal_id text," \
    "  execution_run_id text," \
    "  linked_execution_run_ids text[] not null default '{}'::text[]," \
    "  correlation_key text not null," \
    "  mismatch_summary text not null," \
    "  compared_at timestamptz not null," \
    "  lifecycle_state text not null," \
    "  created_at timestamptz not null default timezone('utc', now())," \
    "  updated_at timestamptz not null default timezone('utc', now())," \
    "  check (finding_id is not null or analytic_signal_id is not null or execution_run_id is not null)," \
    "  check (lifecycle_state in ('pending','matched','mismatched','stale','resolved','superseded'))" \
    ");" \
    >"${target}/postgres/control-plane/schema.sql"

  cp "${target}/postgres/control-plane/schema.sql" \
    "${target}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"
  perl -0pi -e "s/^-- Control-plane schema v1 for the AegisOps-owned PostgreSQL boundary\\./-- Control-plane schema v1 baseline migration./" \
    "${target}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"
  perl -0pi -e "s/\\A(-- Control-plane schema v1 baseline migration\\.\\n)/\$1begin;\\n/" \
    "${target}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"
  printf '\ncommit;\n' >>"${target}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"

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
assert_fails_with "${missing_readme_repo}" "Missing control-plane schema README"

placeholder_readme_repo="${workdir}/placeholder-readme"
create_repo "${placeholder_readme_repo}"
write_valid_fixture "${placeholder_readme_repo}"
printf '%s\n' \
  "# Control-Plane Schema Skeleton" \
  "" \
  "These files are placeholders only." \
  >"${placeholder_readme_repo}/postgres/control-plane/README.md"
git -C "${placeholder_readme_repo}" add postgres/control-plane/README.md
git -C "${placeholder_readme_repo}" commit -q -m "fixture update"
assert_fails_with "${placeholder_readme_repo}" "Control-plane schema README must declare the v1 baseline"

missing_table_repo="${workdir}/missing-table"
create_repo "${missing_table_repo}"
write_valid_fixture "${missing_table_repo}"
awk '/^create table if not exists aegisops_control\.reconciliation_records \(/ {exit} {print}' \
  "${missing_table_repo}/postgres/control-plane/schema.sql" \
  >"${missing_table_repo}/postgres/control-plane/schema.sql.tmp"
mv "${missing_table_repo}/postgres/control-plane/schema.sql.tmp" \
  "${missing_table_repo}/postgres/control-plane/schema.sql"
git -C "${missing_table_repo}" add postgres/control-plane/schema.sql
git -C "${missing_table_repo}" commit -q -m "fixture update"
assert_fails_with "${missing_table_repo}" "must materialize reconciliation_records"

missing_reconciliation_link_repo="${workdir}/missing-reconciliation-link"
create_repo "${missing_reconciliation_link_repo}"
write_valid_fixture "${missing_reconciliation_link_repo}"
perl -0pi -e "s/\\n  linked_execution_run_ids text\\[\\] not null default '\\{\\}'::text\\[\\],//" \
  "${missing_reconciliation_link_repo}/postgres/control-plane/schema.sql"
git -C "${missing_reconciliation_link_repo}" add postgres/control-plane/schema.sql
git -C "${missing_reconciliation_link_repo}" commit -q -m "fixture update"
assert_fails_with "${missing_reconciliation_link_repo}" "must preserve explicit reconciliation linkage to execution-plane records"

schema_seed_repo="${workdir}/schema-seed"
create_repo "${schema_seed_repo}"
write_valid_fixture "${schema_seed_repo}"
printf '\ninsert into aegisops_control.alert_records (alert_id, finding_id, lifecycle_state) values (''a'', ''f'', ''new'');\n' \
  >>"${schema_seed_repo}/postgres/control-plane/schema.sql"
git -C "${schema_seed_repo}" add postgres/control-plane/schema.sql
git -C "${schema_seed_repo}" commit -q -m "fixture update"
assert_fails_with "${schema_seed_repo}" "must not seed live control-plane data"

echo "verify-control-plane-schema-skeleton tests passed"
