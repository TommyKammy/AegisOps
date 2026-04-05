#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "README.md"
  "docs/architecture.md"
  "docs/control-plane-state-model.md"
  "docs/control-plane-runtime-service-boundary.md"
  "docs/repository-structure-baseline.md"
  "docs/phase-9-control-plane-runtime-boundary-validation.md"
  "control-plane/README.md"
  "control-plane/main.py"
  "control-plane/aegisops_control_plane/__init__.py"
  "control-plane/aegisops_control_plane/config.py"
  "control-plane/aegisops_control_plane/service.py"
  "control-plane/aegisops_control_plane/adapters/__init__.py"
  "control-plane/aegisops_control_plane/adapters/opensearch.py"
  "control-plane/aegisops_control_plane/adapters/postgres.py"
  "control-plane/aegisops_control_plane/adapters/n8n.py"
  "control-plane/tests/test_runtime_skeleton.py"
  "control-plane/config/local.env.sample"
  "postgres/control-plane/README.md"
)

create_repo() {
  local target="$1"

  mkdir -p "${target}/.codex-supervisor" "${target}/.github/workflows" \
    "${target}/config" "${target}/docs" "${target}/ingest" "${target}/n8n" \
    "${target}/opensearch" "${target}/proxy" "${target}/scripts" \
    "${target}/sigma" "${target}/control-plane/aegisops_control_plane/adapters" \
    "${target}/control-plane/tests" "${target}/control-plane/config" \
    "${target}/postgres/control-plane"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"

  touch "${target}/.codex-supervisor/.gitkeep" \
    "${target}/.github/workflows/.gitkeep" \
    "${target}/config/.gitkeep" \
    "${target}/ingest/.gitkeep" \
    "${target}/n8n/.gitkeep" \
    "${target}/opensearch/.gitkeep" \
    "${target}/proxy/.gitkeep" \
    "${target}/scripts/.gitkeep" \
    "${target}/sigma/.gitkeep"
  printf '# fixture\n' > "${target}/.env.sample"
  printf 'fixture license\n' > "${target}/LICENSE.txt"
  git -C "${target}" add .codex-supervisor/.gitkeep .github/workflows/.gitkeep \
    config/.gitkeep ingest/.gitkeep n8n/.gitkeep opensearch/.gitkeep \
    proxy/.gitkeep scripts/.gitkeep sigma/.gitkeep .env.sample LICENSE.txt
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
remove_doc "${missing_validation_repo}" "docs/phase-9-control-plane-runtime-boundary-validation.md"
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 9 control-plane runtime boundary validation record:"

missing_readme_cross_link_repo="${workdir}/missing-readme-cross-link"
create_repo "${missing_readme_cross_link_repo}"
write_required_artifacts "${missing_readme_cross_link_repo}"
remove_text_from_doc "${missing_readme_cross_link_repo}" "README.md" 'Within `postgres/`, the `control-plane/` directory reserves the repository home for placeholder AegisOps-owned control-plane schema and migration assets. It does not introduce a live datastore or runtime migration flow.'
commit_fixture "${missing_readme_cross_link_repo}"
assert_fails_with "${missing_readme_cross_link_repo}" "Missing required line in ${missing_readme_cross_link_repo}/README.md"

missing_artifact_listing_repo="${workdir}/missing-artifact-listing"
create_repo "${missing_artifact_listing_repo}"
write_required_artifacts "${missing_artifact_listing_repo}"
remove_text_from_doc "${missing_artifact_listing_repo}" "docs/phase-9-control-plane-runtime-boundary-validation.md" '- `control-plane/README.md`'
commit_fixture "${missing_artifact_listing_repo}"
assert_fails_with "${missing_artifact_listing_repo}" "Phase 9 boundary validation record must list required artifact: control-plane/README.md"

modified_validation_status_repo="${workdir}/modified-validation-status"
create_repo "${modified_validation_status_repo}"
write_required_artifacts "${modified_validation_status_repo}"
replace_text_in_doc "${modified_validation_status_repo}" "docs/phase-9-control-plane-runtime-boundary-validation.md" "- Validation status: PASS" "- Validation status: PASS (temporary)"
commit_fixture "${modified_validation_status_repo}"
assert_fails_with "${modified_validation_status_repo}" "Missing required line in ${modified_validation_status_repo}/docs/phase-9-control-plane-runtime-boundary-validation.md: - Validation status: PASS"

echo "verify-phase-9-control-plane-runtime-boundary-validation tests passed"
