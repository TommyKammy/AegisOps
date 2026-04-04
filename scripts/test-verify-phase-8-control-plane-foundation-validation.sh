#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-8-control-plane-foundation-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "README.md"
  "docs/control-plane-state-model.md"
  "docs/repository-structure-baseline.md"
  "docs/phase-8-control-plane-foundation-validation.md"
  "postgres/control-plane/README.md"
  "postgres/control-plane/schema.sql"
  "postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"
)

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/postgres/control-plane/migrations"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_required_artifacts() {
  local target="$1"
  local artifact=""

  for artifact in "${required_artifacts[@]}"; do
    mkdir -p "${target}/$(dirname "${artifact}")"
    cp "${repo_root}/${artifact}" "${target}/${artifact}"
    git -C "${target}" add "${artifact}"
  done
}

remove_text_from_doc() {
  local target="$1"
  local doc="$2"
  local expected_text="$3"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${target}/${doc}"
  git -C "${target}" add "${doc}"
}

replace_text_in_doc() {
  local target="$1"
  local doc="$2"
  local old_text="$3"
  local new_text="$4"

  OLD_TEXT="${old_text}" NEW_TEXT="${new_text}" perl -0pi -e 's/\Q$ENV{OLD_TEXT}\E/$ENV{NEW_TEXT}/g' "${target}/${doc}"
  git -C "${target}" add "${doc}"
}

remove_doc() {
  local target="$1"
  local doc="$2"

  rm -f "${target}/${doc}"
  git -C "${target}" add -A "${doc}"
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
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
write_required_artifacts "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_validation_repo="${workdir}/missing-validation"
create_repo "${missing_validation_repo}"
write_required_artifacts "${missing_validation_repo}"
remove_doc "${missing_validation_repo}" "docs/phase-8-control-plane-foundation-validation.md"
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 8 control-plane foundation validation record:"

missing_state_model_cross_link_repo="${workdir}/missing-state-model-cross-link"
create_repo "${missing_state_model_cross_link_repo}"
write_required_artifacts "${missing_state_model_cross_link_repo}"
remove_text_from_doc "${missing_state_model_cross_link_repo}" "docs/control-plane-state-model.md" 'The repository may materialize a version-controlled schema baseline for that future boundary under `postgres/control-plane/`, including reviewed schema manifests and migration files that keep the approved record-family boundary explicit without authorizing live deployment, credentials, or production migration execution in this phase.'
commit_fixture "${missing_state_model_cross_link_repo}"
assert_fails_with "${missing_state_model_cross_link_repo}" "Missing required line in ${missing_state_model_cross_link_repo}/docs/control-plane-state-model.md"

missing_schema_boundary_repo="${workdir}/missing-schema-boundary"
create_repo "${missing_schema_boundary_repo}"
write_required_artifacts "${missing_schema_boundary_repo}"
remove_text_from_doc "${missing_schema_boundary_repo}" "postgres/control-plane/README.md" 'The schema remains separate from n8n-owned PostgreSQL metadata and execution-state tables even when both live on the same engine class.'
commit_fixture "${missing_schema_boundary_repo}"
assert_fails_with "${missing_schema_boundary_repo}" "Control-plane schema README must preserve the n8n ownership boundary"

missing_artifact_listing_repo="${workdir}/missing-artifact-listing"
create_repo "${missing_artifact_listing_repo}"
write_required_artifacts "${missing_artifact_listing_repo}"
remove_text_from_doc "${missing_artifact_listing_repo}" "docs/phase-8-control-plane-foundation-validation.md" '- `README.md`'
commit_fixture "${missing_artifact_listing_repo}"
assert_fails_with "${missing_artifact_listing_repo}" "Phase 8 foundation validation record must list required artifact: README.md"

modified_validation_status_repo="${workdir}/modified-validation-status"
create_repo "${modified_validation_status_repo}"
write_required_artifacts "${modified_validation_status_repo}"
replace_text_in_doc "${modified_validation_status_repo}" "docs/phase-8-control-plane-foundation-validation.md" "- Validation status: PASS" "- Validation status: PASS (temporary)"
commit_fixture "${modified_validation_status_repo}"
assert_fails_with "${modified_validation_status_repo}" "Missing required line in ${modified_validation_status_repo}/docs/phase-8-control-plane-foundation-validation.md: - Validation status: PASS"

missing_reconciliation_record_repo="${workdir}/missing-reconciliation-record"
create_repo "${missing_reconciliation_record_repo}"
write_required_artifacts "${missing_reconciliation_record_repo}"
remove_text_from_doc "${missing_reconciliation_record_repo}" "postgres/control-plane/README.md" '- `reconciliation_records`'
commit_fixture "${missing_reconciliation_record_repo}"
assert_fails_with "${missing_reconciliation_record_repo}" "Missing required line in ${missing_reconciliation_record_repo}/postgres/control-plane/README.md: - \`reconciliation_records\`"

echo "verify-phase-8-control-plane-foundation-validation tests passed"
