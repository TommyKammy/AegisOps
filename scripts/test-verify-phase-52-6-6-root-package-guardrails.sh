#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-6-6-root-package-guardrails.sh"
contract_path="docs/adr/0014-phase-52-6-1-root-shim-inventory-and-deprecation-contract.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/adr" "${target}/control-plane"
  cp "${repo_root}/${contract_path}" "${target}/${contract_path}"
  cp -R "${repo_root}/control-plane/aegisops" \
    "${target}/control-plane/aegisops"
  cp -R "${repo_root}/control-plane/aegisops_control_plane" \
    "${target}/control-plane/aegisops_control_plane"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    cat "${fail_stdout}" >&2
    exit 1
  fi

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

root_count_growth_repo="${workdir}/root-count-growth"
create_valid_repo "${root_count_growth_repo}"
printf '%s\n' '"""Fixture root file that must not pass without policy."""' \
  >"${root_count_growth_repo}/control-plane/aegisops/control_plane/new_flat_owner.py"
assert_fails_with \
  "${root_count_growth_repo}" \
  "Phase 52.6.6 root package guardrail expected 12 direct root Python files, found 13."

phase_numbered_root_repo="${workdir}/phase-numbered-root"
create_valid_repo "${phase_numbered_root_repo}"
printf '%s\n' '"""Fixture phase-numbered root file."""' \
  >"${phase_numbered_root_repo}/control-plane/aegisops/control_plane/phase52_new_owner.py"
assert_fails_with \
  "${phase_numbered_root_repo}" \
  "Phase 52.6.6 root package guardrail rejects phase-numbered root filenames: phase52_new_owner.py"

phase_numbered_prefix_repo="${workdir}/phase-numbered-prefix-root"
create_valid_repo "${phase_numbered_prefix_repo}"
printf '%s\n' '"""Fixture phase-numbered prefix root file."""' \
  >"${phase_numbered_prefix_repo}/control-plane/aegisops/control_plane/phase52foo.py"
assert_fails_with \
  "${phase_numbered_prefix_repo}" \
  "Phase 52.6.6 root package guardrail rejects phase-numbered root filenames: phase52foo.py"

missing_retained_owner_policy_repo="${workdir}/missing-retained-owner-policy"
create_valid_repo "${missing_retained_owner_policy_repo}"
perl -0pi -e 's/\n## 5\.3 Phase 52\.6\.6 Retained Root Owner Policy.*?(?=\n## 6\. Phase29 Boundary)//s' \
  "${missing_retained_owner_policy_repo}/${contract_path}"
assert_fails_with \
  "${missing_retained_owner_policy_repo}" \
  "Missing Phase 52.6.6 retained root owner policy statement: After Phase 52.6.6, the only retained root owner files are"

truncated_retained_owner_policy_repo="${workdir}/truncated-retained-owner-policy"
create_valid_repo "${truncated_retained_owner_policy_repo}"
perl -0pi -e 's/No other direct root Python file may be promoted to retained owner status without a later accepted ADR or issue-specific contract that names the root file, authoritative owner, caller evidence, focused regression coverage, rollback path, and authority-boundary impact\./No other direct root Python file may be promoted to retained owner status without a later accepted ADR or issue-specific contract/' \
  "${truncated_retained_owner_policy_repo}/${contract_path}"
assert_fails_with \
  "${truncated_retained_owner_policy_repo}" \
  "Missing Phase 52.6.6 retained root owner policy statement: No other direct root Python file may be promoted to retained owner status without a later accepted ADR or issue-specific contract that names the root file, authoritative owner, caller evidence, focused regression coverage, rollback path, and authority-boundary impact."

extra_retained_owner_repo="${workdir}/extra-retained-owner"
create_valid_repo "${extra_retained_owner_repo}"
perl -0pi -e 's/\| `action_policy\.py` \| `actions` \| simple shim \|/\| `action_policy.py` \| `actions` \| retained owner \|/' \
  "${extra_retained_owner_repo}/${contract_path}"
assert_fails_with \
  "${extra_retained_owner_repo}" \
  "Phase 52.6.6 retained root owner set mismatch: unexpected retained owner rows: action_policy.py"

invalid_classification_repo="${workdir}/invalid-classification"
create_valid_repo "${invalid_classification_repo}"
perl -0pi -e 's/\| `action_policy\.py` \| `actions` \| simple shim \|/\| `action_policy.py` \| `actions` \| simple shim typo \|/' \
  "${invalid_classification_repo}/${contract_path}"
assert_fails_with \
  "${invalid_classification_repo}" \
  "Phase 52.6.6 root package guardrail found invalid root inventory classifications: action_policy.py: simple shim typo"

service_policy_removed_repo="${workdir}/service-policy-removed"
create_valid_repo "${service_policy_removed_repo}"
perl -0pi -e 's/\n`service\.py` is not a retained owner; it is the single retained compatibility blocker and the public `service\.py` facade stays a retained compatibility blocker under ADR-0003 and ADR-0010 until a later facade transition issue supersedes that policy\.\n/\n/' \
  "${service_policy_removed_repo}/${contract_path}"
assert_fails_with \
  "${service_policy_removed_repo}" \
  'Missing Phase 52.6.6 retained root owner policy statement: `service.py` is not a retained owner'

future_blockers_removed_repo="${workdir}/future-blockers-removed"
create_valid_repo "${future_blockers_removed_repo}"
perl -0pi -e 's/\n## 7\. Deprecation Decision Rules/\n## 7. Deprecation Decision Rules/' \
  "${future_blockers_removed_repo}/${contract_path}"
perl -0pi -e 's/\nThe future public package rename, outer `control-plane\/` directory rename, retained-root owner relocation, and `service\.py` facade relocation remain blocked until a later accepted ADR names caller evidence, replacement paths, deprecation window, focused regression coverage, rollback path, and authority-boundary impact\.//' \
  "${future_blockers_removed_repo}/${contract_path}"
assert_fails_with \
  "${future_blockers_removed_repo}" \
  'Missing Phase 52.6.6 future blocker statement: The future public package rename, outer `control-plane/` directory rename'

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/${contract_path}"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.6.6 root package guardrail artifact: workstation-local absolute path detected"

echo "Phase 52.6.6 root package guardrail verifier negative and valid fixtures passed."
