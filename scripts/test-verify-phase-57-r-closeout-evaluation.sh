#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-57-r-closeout-evaluation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

copy_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-57-closeout-evaluation.md" "${target}/docs/phase-57-closeout-evaluation.md"
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
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_issue_repo="${workdir}/missing-issue"
copy_valid_repo "${missing_issue_repo}"
perl -0pi -e 's/\| #1227 \| Phase 57\.R\.3 Extract backup \/ restore payload codec and validation boundaries \| Closed\. Extracted backup codec and restore validation helpers while preserving restore validation, fail-closed behavior, public facade compatibility, and durable-state cleanliness expectations\. \|\n//' \
  "${missing_issue_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_repo}" \
  "Missing Phase 57.R closeout evidence: | #1227 | Phase 57.R.3 Extract backup / restore payload codec and validation boundaries | Closed. Extracted backup codec and restore validation helpers while preserving restore validation, fail-closed behavior, public facade compatibility, and durable-state cleanliness expectations. |"

missing_measurement_repo="${workdir}/missing-measurement"
copy_valid_repo "${missing_measurement_repo}"
perl -0pi -e 's/\| Restore backup \/ validation runtime split \| `restore_readiness_backup_restore\.py` \| 1,494 lines \| 1,562 lines across `restore_readiness_backup_restore\.py`, `restore_backup_codec\.py`, and `restore_backup_validation\.py`; the original module is down to 495 lines\. \|\n//' \
  "${missing_measurement_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${missing_measurement_repo}" \
  'Missing Phase 57.R closeout evidence: | Restore backup / validation runtime split | `restore_readiness_backup_restore.py` | 1,494 lines | 1,562 lines across `restore_readiness_backup_restore.py`, `restore_backup_codec.py`, and `restore_backup_validation.py`; the original module is down to 495 lines. |'

missing_handoff_repo="${workdir}/missing-handoff"
copy_valid_repo "${missing_handoff_repo}"
perl -0pi -e 's/Phase 58 can consume the extracted admin modules, restore backup codec, restore validation helper, restore\/readiness test shards, ADR-0019 inventory, and unchanged maintainability guard as a reviewed pre-refactor baseline\.//' \
  "${missing_handoff_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${missing_handoff_repo}" \
  "Missing Phase 57.R closeout evidence: Phase 58 can consume the extracted admin modules, restore backup codec, restore validation helper, restore/readiness test shards, ADR-0019 inventory, and unchanged maintainability guard as a reviewed pre-refactor baseline."

baseline_hide_repo="${workdir}/baseline-hide"
copy_valid_repo "${baseline_hide_repo}"
printf '%s\n' "Maintainability baseline was raised to hide a new hotspot" >>"${baseline_hide_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${baseline_hide_repo}" \
  "Forbidden Phase 57.R closeout evaluation claim: Maintainability baseline was raised to hide a new hotspot"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 57.R closeout evaluation: workstation-local absolute path detected"

echo "Phase 57.R closeout evaluation verifier tests passed."
