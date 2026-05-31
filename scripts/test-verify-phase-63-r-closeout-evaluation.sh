#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-63-r-closeout-evaluation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

copy_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-63-closeout-evaluation.md" "${target}/docs/phase-63-closeout-evaluation.md"
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
perl -0pi -e 's/\| #1352 \| 63\.R\.4 Decompose AI grounding adapter seams \| Closed\. Extracted AI grounding payload, prompt-validation, and validation helpers while preserving cited advisory grounding and no-authority behavior\. \|\n//' \
  "${missing_issue_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_repo}" \
  "Missing Phase 63.R closeout evidence: | #1352 | 63.R.4 Decompose AI grounding adapter seams | Closed. Extracted AI grounding payload, prompt-validation, and validation helpers while preserving cited advisory grounding and no-authority behavior. |"

missing_measurement_repo="${workdir}/missing-measurement"
copy_valid_repo "${missing_measurement_repo}"
perl -0pi -e 's/\| Evidence source registry catalogs \| `evidence_source_registry\.py` \| Registry data and validation catalog rules lived with registry entrypoints\. \| Registry data and validation catalog helpers are split while preserving the bounded `osquery_host_state` and `malwarebazaar_hash_reputation` registry\. \|\n//' \
  "${missing_measurement_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${missing_measurement_repo}" \
  'Missing Phase 63.R closeout evidence: | Evidence source registry catalogs | `evidence_source_registry.py` | Registry data and validation catalog rules lived with registry entrypoints. | Registry data and validation catalog helpers are split while preserving the bounded `osquery_host_state` and `malwarebazaar_hash_reputation` registry. |'

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/`node <codex-supervisor-root>\/dist\/index\.js issue-lint 1354 --config <supervisor-config-path>`\n//' \
  "${missing_issue_lint_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  "Missing Phase 63.R closeout evidence: \`node <codex-supervisor-root>/dist/index.js issue-lint 1354 --config <supervisor-config-path>\`"

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
perl -0pi -e 's/Phase 63\.R does not add product behavior, evidence-source breadth, new evidence collection, case truth, approval truth, execution truth, reconciliation truth, release truth, gate truth, readiness truth, AI authority, UI authority, browser authority, source-native authority, verifier authority, issue-lint authority, Controlled Write, or Hard Write\.//' \
  "${missing_authority_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing Phase 63.R closeout evidence: Phase 63.R does not add product behavior"

missing_handoff_repo="${workdir}/missing-handoff"
copy_valid_repo "${missing_handoff_repo}"
perl -0pi -e 's/Phase 64, Phase 65, and Phase 66 may consume the split modules, focused extraction tests, registry verifier evidence, unchanged maintainability guard, and explicit non-expansion posture as reviewed maintainability evidence only\.//' \
  "${missing_handoff_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${missing_handoff_repo}" \
  "Missing Phase 63.R closeout evidence: Phase 64, Phase 65, and Phase 66 may consume the split modules"

forbidden_repo="${workdir}/forbidden"
copy_valid_repo "${forbidden_repo}"
printf '%s\n' "Phase 63.R proves RC readiness." >>"${forbidden_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${forbidden_repo}" \
  "Forbidden Phase 63.R closeout evaluation claim: Phase 63.R proves RC readiness"

baseline_hide_repo="${workdir}/baseline-hide"
copy_valid_repo "${baseline_hide_repo}"
printf '%s\n' "Maintainability baseline was raised to hide a new Phase 63.R hotspot" >>"${baseline_hide_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${baseline_hide_repo}" \
  "Forbidden Phase 63.R closeout evaluation claim: Maintainability baseline was raised to hide a new Phase 63.R hotspot"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 63.R closeout evaluation: workstation-local absolute path detected"

echo "Phase 63.R closeout evaluation verifier tests passed."
