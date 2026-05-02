#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh"
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
  cp -R "${repo_root}/control-plane/aegisops_control_plane" \
    "${target}/control-plane/aegisops_control_plane"
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

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

unclassified_repo="${workdir}/unclassified-root-file"
create_valid_repo "${unclassified_repo}"
printf '%s\n' "\"\"\"Fixture root file intentionally missing from the shim inventory.\"\"\"" \
  >"${unclassified_repo}/control-plane/aegisops_control_plane/new_root_shim.py"
assert_fails_with \
  "${unclassified_repo}" \
  "Phase 52.6.1 root shim inventory is missing root file rows: new_root_shim.py"

behavior_change_repo="${workdir}/behavior-change-claim"
create_valid_repo "${behavior_change_repo}"
printf '%s\n' "This contract changes runtime behavior." \
  >>"${behavior_change_repo}/${contract_path}"
assert_fails_with \
  "${behavior_change_repo}" \
  "Forbidden Phase 52.6.1 root shim inventory claim: This contract changes runtime behavior."

phase29_owner_repo="${workdir}/phase29-production-owner"
create_valid_repo "${phase29_owner_repo}"
perl -0pi -e 's/\| `phase29_shadow_dataset\.py` \| `ml_shadow` \| compatibility adapter \| Retain as a Phase29 legacy adapter; `ml_shadow\/dataset\.py` is the domain-owned `ml_shadow` implementation\. \|/\| `phase29_shadow_dataset.py` \| `ml_shadow` \| retained owner \| Retain as a Phase29 production owner. \|/' \
  "${phase29_owner_repo}/${contract_path}"
assert_fails_with \
  "${phase29_owner_repo}" \
  "Phase 52.6.1 root shim inventory must classify Phase29 root files as compatibility adapters separate from domain-owned ml_shadow implementations: phase29_shadow_dataset.py"

immediate_deletion_repo="${workdir}/immediate-deletion-claim"
create_valid_repo "${immediate_deletion_repo}"
printf '%s\n' "Legacy root shims may be deleted immediately." \
  >>"${immediate_deletion_repo}/${contract_path}"
assert_fails_with \
  "${immediate_deletion_repo}" \
  "Forbidden Phase 52.6.1 root shim inventory claim: Legacy root shims may be deleted immediately."

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/${contract_path}"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.6.1 root shim inventory: workstation-local absolute path detected"

missing_publishable_hygiene_repo="${workdir}/missing-publishable-hygiene"
create_valid_repo "${missing_publishable_hygiene_repo}"
perl -0pi -e 's/\nRun `bash scripts\/verify-publishable-path-hygiene\.sh`\.\n//' \
  "${missing_publishable_hygiene_repo}/${contract_path}"
assert_fails_with \
  "${missing_publishable_hygiene_repo}" \
  "Missing Phase 52.6.1 root shim inventory statement: Run \`bash scripts/verify-publishable-path-hygiene.sh\`."

subordinate_inventory_rows_repo="${workdir}/subordinate-inventory-rows"
create_valid_repo "${subordinate_inventory_rows_repo}"
perl -0pi -e 's/alias rows, and operator-facing text remain subordinate context/alias rows, inventory rows, and operator-facing text remain subordinate context/' \
  "${subordinate_inventory_rows_repo}/${contract_path}"
assert_fails_with \
  "${subordinate_inventory_rows_repo}" \
  "Missing Phase 52.6.1 root shim inventory statement: Wazuh, Shuffle, tickets, assistant output, generated config, CLI status, demo data, adapters, DTOs, projections, summaries, compatibility shims, alias rows, and operator-facing text remain subordinate context."

echo "Phase 52.6.1 root shim inventory verifier negative and valid fixtures passed."
