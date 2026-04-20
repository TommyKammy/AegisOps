#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-positive-smb-value-proposition.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_valid_docs() {
  local target="$1"

  cat <<'EOF' > "${target}/README.md"
# AegisOps

AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model.

The primary deployment target is a single-company or single-business-unit deployment with roughly 250 to 1,500 managed endpoints, 2 to 6 business-hours SecOps operators, and 1 to 3 designated approvers or escalation owners.

The target operating assumption is business-hours review with explicit after-hours escalation, not a 24x7 staffed SOC.
EOF

  cat <<'EOF' > "${target}/docs/architecture.md"
# AegisOps Architecture Overview

AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model.

The primary deployment target is a single-company or single-business-unit deployment with roughly 250 to 1,500 managed endpoints, 2 to 6 business-hours SecOps operators, and 1 to 3 designated approvers or escalation owners.

The target operating assumption is business-hours review with explicit after-hours escalation, not a 24x7 staffed SOC.
EOF

  cat <<'EOF' > "${target}/docs/Revised Phase23-29 Epic Roadmap.md"
# Revised Phase 23-29 Epic Roadmap

AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model.

The primary deployment target is a single-company or single-business-unit deployment with roughly 250 to 1,500 managed endpoints, 2 to 6 business-hours SecOps operators, and 1 to 3 designated approvers or escalation owners.

The target operating assumption is business-hours review with explicit after-hours escalation, not a 24x7 staffed SOC.

Phases 23-29 hardening, ergonomics, and bounded-extension work must be evaluated against this deployment target before scope expands.
EOF

  git -C "${target}" add README.md docs/architecture.md "docs/Revised Phase23-29 Epic Roadmap.md"
}

remove_text_from_doc() {
  local target="$1"
  local path="$2"
  local expected_text="$3"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${target}/${path}"
  git -C "${target}" add "${path}"
}

append_text_to_doc() {
  local target="$1"
  local path="$2"
  local text="$3"

  printf '\n%s\n' "${text}" >> "${target}/${path}"
  git -C "${target}" add "${path}"
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
write_valid_docs "${valid_repo}"
cp "${repo_root}/docs/requirements-baseline.md" "${valid_repo}/docs/requirements-baseline.md"
git -C "${valid_repo}" add docs/requirements-baseline.md
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

windows_path_repo="${workdir}/windows-path"
create_repo "${windows_path_repo}"
write_valid_docs "${windows_path_repo}"
cp "${repo_root}/docs/requirements-baseline.md" "${windows_path_repo}/docs/requirements-baseline.md"
git -C "${windows_path_repo}" add docs/requirements-baseline.md
commit_fixture "${windows_path_repo}"
windows_style_path="${windows_path_repo//\//\\}"
assert_passes "${windows_path_repo}"
if ! bash "${verifier}" "${windows_style_path}" >"${pass_stdout}" 2>"${pass_stderr}"; then
  echo "Expected verifier to normalize Windows-style repository roots: ${windows_style_path}" >&2
  cat "${pass_stderr}" >&2
  exit 1
fi

missing_roadmap_repo="${workdir}/missing-roadmap"
create_repo "${missing_roadmap_repo}"
write_valid_docs "${missing_roadmap_repo}"
cp "${repo_root}/docs/requirements-baseline.md" "${missing_roadmap_repo}/docs/requirements-baseline.md"
git -C "${missing_roadmap_repo}" add docs/requirements-baseline.md
rm "${missing_roadmap_repo}/docs/Revised Phase23-29 Epic Roadmap.md"
git -C "${missing_roadmap_repo}" add -u "docs/Revised Phase23-29 Epic Roadmap.md"
commit_fixture "${missing_roadmap_repo}"
assert_fails_with "${missing_roadmap_repo}" "Missing Phase 23 roadmap document:"

missing_target_profile_repo="${workdir}/missing-target-profile"
create_repo "${missing_target_profile_repo}"
write_valid_docs "${missing_target_profile_repo}"
cp "${repo_root}/docs/requirements-baseline.md" "${missing_target_profile_repo}/docs/requirements-baseline.md"
git -C "${missing_target_profile_repo}" add docs/requirements-baseline.md
remove_text_from_doc "${missing_target_profile_repo}" "docs/architecture.md" "The primary deployment target is a single-company or single-business-unit deployment with roughly 250 to 1,500 managed endpoints, 2 to 6 business-hours SecOps operators, and 1 to 3 designated approvers or escalation owners."
commit_fixture "${missing_target_profile_repo}"
assert_fails_with "${missing_target_profile_repo}" "Missing architecture deployment target profile:"

roadmap_contradiction_repo="${workdir}/roadmap-contradiction"
create_repo "${roadmap_contradiction_repo}"
write_valid_docs "${roadmap_contradiction_repo}"
cp "${repo_root}/docs/requirements-baseline.md" "${roadmap_contradiction_repo}/docs/requirements-baseline.md"
git -C "${roadmap_contradiction_repo}" add docs/requirements-baseline.md
append_text_to_doc "${roadmap_contradiction_repo}" "docs/Revised Phase23-29 Epic Roadmap.md" "Multi-tenant packaging is in scope for this roadmap slice."
commit_fixture "${roadmap_contradiction_repo}"
assert_fails_with "${roadmap_contradiction_repo}" "Forbidden roadmap out-of-scope contradiction: Multi-tenant packaging is in scope for this roadmap slice."

requirements_siem_contradiction_repo="${workdir}/requirements-siem-contradiction"
create_repo "${requirements_siem_contradiction_repo}"
write_valid_docs "${requirements_siem_contradiction_repo}"
cp "${repo_root}/docs/requirements-baseline.md" "${requirements_siem_contradiction_repo}/docs/requirements-baseline.md"
git -C "${requirements_siem_contradiction_repo}" add docs/requirements-baseline.md
append_text_to_doc "${requirements_siem_contradiction_repo}" "docs/requirements-baseline.md" "AegisOps is a generic SIEM replacement for broad enterprise operations."
commit_fixture "${requirements_siem_contradiction_repo}"
assert_fails_with "${requirements_siem_contradiction_repo}" "Forbidden requirements baseline contradiction marker: AegisOps is a generic SIEM replacement for broad enterprise operations."

requirements_scope_contradiction_repo="${workdir}/requirements-scope-contradiction"
create_repo "${requirements_scope_contradiction_repo}"
write_valid_docs "${requirements_scope_contradiction_repo}"
cp "${repo_root}/docs/requirements-baseline.md" "${requirements_scope_contradiction_repo}/docs/requirements-baseline.md"
git -C "${requirements_scope_contradiction_repo}" add docs/requirements-baseline.md
append_text_to_doc "${requirements_scope_contradiction_repo}" "docs/requirements-baseline.md" "Multi-tenant packaging is in scope for this roadmap slice."
commit_fixture "${requirements_scope_contradiction_repo}"
assert_fails_with "${requirements_scope_contradiction_repo}" "Forbidden requirements baseline out-of-scope contradiction: Multi-tenant packaging is in scope for this roadmap slice."

echo "Positive SMB value proposition verifier tests passed."
