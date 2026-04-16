#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-16-first-boot-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

create_repo() {
  local target="$1"

  mkdir -p \
    "${target}/docs" \
    "${target}/control-plane/deployment/first-boot" \
    "${target}/postgres/control-plane/migrations"
}

copy_fixture() {
  local target="$1"

  cp "${repo_root}/README.md" "${target}/README.md"
  cp "${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md" "${target}/docs/phase-16-release-state-and-first-boot-scope.md"
  cp "${repo_root}/docs/requirements-baseline.md" "${target}/docs/requirements-baseline.md"
  cp "${repo_root}/docs/control-plane-runtime-service-boundary.md" "${target}/docs/control-plane-runtime-service-boundary.md"
  cp "${repo_root}/docs/runbook.md" "${target}/docs/runbook.md"
  cp "${repo_root}/control-plane/deployment/first-boot/bootstrap.env.sample" "${target}/control-plane/deployment/first-boot/bootstrap.env.sample"
  cp "${repo_root}/control-plane/deployment/first-boot/docker-compose.yml" "${target}/control-plane/deployment/first-boot/docker-compose.yml"
  cp "${repo_root}/control-plane/deployment/first-boot/control-plane-entrypoint.sh" "${target}/control-plane/deployment/first-boot/control-plane-entrypoint.sh"
  cp "${repo_root}/postgres/control-plane/README.md" "${target}/postgres/control-plane/README.md"
  cp "${repo_root}/postgres/control-plane/schema.sql" "${target}/postgres/control-plane/schema.sql"
  cp "${repo_root}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql" "${target}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"
  cp "${repo_root}/postgres/control-plane/migrations/0002_phase_14_reviewed_context_columns.sql" "${target}/postgres/control-plane/migrations/0002_phase_14_reviewed_context_columns.sql"
  cp "${repo_root}/postgres/control-plane/migrations/0003_phase_15_assistant_advisory_draft_columns.sql" "${target}/postgres/control-plane/migrations/0003_phase_15_assistant_advisory_draft_columns.sql"
  cp "${repo_root}/postgres/control-plane/migrations/0004_phase_20_action_request_binding_columns.sql" "${target}/postgres/control-plane/migrations/0004_phase_20_action_request_binding_columns.sql"
  cp "${repo_root}/postgres/control-plane/migrations/0005_phase_23_approval_decision_rationale.sql" "${target}/postgres/control-plane/migrations/0005_phase_23_approval_decision_rationale.sql"
  cp "${repo_root}/postgres/control-plane/migrations/0006_phase_23_lifecycle_transition_records.sql" "${target}/postgres/control-plane/migrations/0006_phase_23_lifecycle_transition_records.sql"
}

remove_text() {
  local path="$1"
  local text="$2"

  REMOVE_TEXT="${text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${path}"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >/dev/null 2>"${workdir}/stderr"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${workdir}/stderr" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >/dev/null 2>"${workdir}/stderr"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${workdir}/stderr" >/dev/null; then
    echo "Expected verifier stderr to contain: ${expected}" >&2
    cat "${workdir}/stderr" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
copy_fixture "${valid_repo}"
assert_passes "${valid_repo}"

readme_drift_repo="${workdir}/readme-drift"
create_repo "${readme_drift_repo}"
copy_fixture "${readme_drift_repo}"
remove_text "${readme_drift_repo}/README.md" \
  'That first-boot target is limited to the AegisOps control-plane service, PostgreSQL for control-plane state, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.'
assert_fails_with "${readme_drift_repo}" 'Missing required line in README.md: That first-boot target is limited to the AegisOps control-plane service, PostgreSQL for control-plane state, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.'

optional_blocker_repo="${workdir}/optional-blocker"
create_repo "${optional_blocker_repo}"
copy_fixture "${optional_blocker_repo}"
cat <<'EOF' >>"${optional_blocker_repo}/control-plane/deployment/first-boot/docker-compose.yml"
  opensearch:
    image: opensearchproject/opensearch:2
EOF
assert_fails_with "${optional_blocker_repo}" 'First-boot compose must not define first-boot service: opensearch'

entrypoint_drift_repo="${workdir}/entrypoint-drift"
create_repo "${entrypoint_drift_repo}"
copy_fixture "${entrypoint_drift_repo}"
remove_text "${entrypoint_drift_repo}/control-plane/deployment/first-boot/control-plane-entrypoint.sh" \
  'exec "$@"'
assert_fails_with "${entrypoint_drift_repo}" 'Missing required line in control-plane/deployment/first-boot/control-plane-entrypoint.sh: exec "$@"'

missing_migration_repo="${workdir}/missing-migration"
create_repo "${missing_migration_repo}"
copy_fixture "${missing_migration_repo}"
rm "${missing_migration_repo}/postgres/control-plane/migrations/0006_phase_23_lifecycle_transition_records.sql"
assert_fails_with "${missing_migration_repo}" 'Missing reviewed control-plane migration asset'

echo "Phase 16 first-boot verifier catches release-state drift and optional boot blockers."
