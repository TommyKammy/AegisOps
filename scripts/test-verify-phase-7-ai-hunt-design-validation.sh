#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-7-ai-hunt-design-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_docs=(
  "docs/adr/0001-phase-7-ai-hunt-plane-and-external-ai-data-boundary.md"
  "docs/control-plane-state-model.md"
  "docs/safe-query-gateway-and-tool-policy.md"
  "docs/asset-identity-privilege-context-baseline.md"
  "docs/retention-evidence-and-replay-readiness-baseline.md"
  "docs/secops-domain-model.md"
  "docs/phase-7-ai-hunt-evaluation-baseline.md"
  "docs/phase-7-ai-hunt-design-validation.md"
)

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs/adr"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_required_docs() {
  local target="$1"
  local doc=""

  for doc in "${required_docs[@]}"; do
    mkdir -p "${target}/$(dirname "${doc}")"
    cp "${repo_root}/${doc}" "${target}/${doc}"
    git -C "${target}" add "${doc}"
  done
}

remove_text_from_doc() {
  local target="$1"
  local doc="$2"
  local expected_text="$3"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${target}/${doc}"
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

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_required_docs "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_validation_repo="${workdir}/missing-validation"
create_repo "${missing_validation_repo}"
write_required_docs "${missing_validation_repo}"
remove_doc "${missing_validation_repo}" "docs/phase-7-ai-hunt-design-validation.md"
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 7 AI hunt design validation record:"

missing_cross_link_repo="${workdir}/missing-cross-link"
create_repo "${missing_cross_link_repo}"
write_required_docs "${missing_cross_link_repo}"
remove_text_from_doc "${missing_cross_link_repo}" "docs/phase-7-ai-hunt-evaluation-baseline.md" "It supplements \`docs/adr/0001-phase-7-ai-hunt-plane-and-external-ai-data-boundary.md\`, \`docs/safe-query-gateway-and-tool-policy.md\`, \`docs/asset-identity-privilege-context-baseline.md\`, and \`docs/retention-evidence-and-replay-readiness-baseline.md\` by defining how future AI hunt behavior must be challenged before any live AI-assisted path is treated as trustworthy."
commit_fixture "${missing_cross_link_repo}"
assert_fails_with "${missing_cross_link_repo}" "Missing Phase 7 evaluation baseline statement"

missing_domain_model_repo="${workdir}/missing-domain-model"
create_repo "${missing_domain_model_repo}"
write_required_docs "${missing_domain_model_repo}"
remove_doc "${missing_domain_model_repo}" "docs/secops-domain-model.md"
commit_fixture "${missing_domain_model_repo}"
assert_fails_with "${missing_domain_model_repo}" "Missing SecOps domain model document:"

missing_hunt_semantics_cross_link_repo="${workdir}/missing-hunt-semantics-cross-link"
create_repo "${missing_hunt_semantics_cross_link_repo}"
write_required_docs "${missing_hunt_semantics_cross_link_repo}"
remove_text_from_doc "${missing_hunt_semantics_cross_link_repo}" "docs/asset-identity-privilege-context-baseline.md" "It supplements \`docs/secops-domain-model.md\`, \`docs/auth-baseline.md\`, and \`docs/adr/0001-phase-7-ai-hunt-plane-and-external-ai-data-boundary.md\` by defining the smallest reviewed context model AegisOps may use when hunts reason about hosts, users, service accounts, groups, aliases, ownership, and criticality."
commit_fixture "${missing_hunt_semantics_cross_link_repo}"
assert_fails_with "${missing_hunt_semantics_cross_link_repo}" "Missing Phase 7 hunt semantics cross-link statement"

missing_artifact_listing_repo="${workdir}/missing-artifact-listing"
create_repo "${missing_artifact_listing_repo}"
write_required_docs "${missing_artifact_listing_repo}"
remove_text_from_doc "${missing_artifact_listing_repo}" "docs/phase-7-ai-hunt-design-validation.md" "- \`docs/control-plane-state-model.md\`"
commit_fixture "${missing_artifact_listing_repo}"
assert_fails_with "${missing_artifact_listing_repo}" "Phase 7 design validation record must list required artifact: docs/control-plane-state-model.md"

echo "verify-phase-7-ai-hunt-design-validation tests passed"
