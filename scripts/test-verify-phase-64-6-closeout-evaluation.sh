#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-64-6-closeout-evaluation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

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

  if ! grep -Fiq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

copy_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/scripts" "${target}/control-plane/aegisops/control_plane"
  cp "${repo_root}/README.md" "${target}/README.md"
  cp "${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" "${target}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  cp "${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md" "${target}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
  cp "${repo_root}/docs/phase-63-closeout-evaluation.md" "${target}/docs/phase-63-closeout-evaluation.md"
  cp "${repo_root}/docs/phase-64-1-known-limitation-ownership-record-contract.md" "${target}/docs/phase-64-1-known-limitation-ownership-record-contract.md"
  cp "${repo_root}/docs/phase-64-1-reviewed-limitation-ownership-records.md" "${target}/docs/phase-64-1-reviewed-limitation-ownership-records.md"
  cp "${repo_root}/docs/phase-64-5-phase66-limitation-handoff.md" "${target}/docs/phase-64-5-phase66-limitation-handoff.md"
  cp "${repo_root}/docs/phase-64-closeout-evaluation.md" "${target}/docs/phase-64-closeout-evaluation.md"
  cp "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${target}/scripts/verify-publishable-path-hygiene.sh"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"
  cp "${repo_root}/control-plane/aegisops/control_plane/publishable_paths.py" "${target}/control-plane/aegisops/control_plane/publishable_paths.py"
  git -C "${target}" init -q
  git -C "${target}" config user.email "aegisops@example.invalid"
  git -C "${target}" config user.name "AegisOps Test"
  git -C "${target}" add README.md docs scripts control-plane/aegisops
  git -C "${target}" commit -q -m "fixture"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-64-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-64-closeout-evaluation.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 64 closeout evaluation: docs/phase-64-closeout-evaluation.md"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 64\.6 closeout evaluation\]\(docs\/phase-64-closeout-evaluation\.md\)[^\n]*\n/- Phase 64.6 closeout evaluation\\n/' \
  "${missing_readme_repo}/README.md"
assert_fails_with \
  "${missing_readme_repo}" \
  "Missing README canonical cross-phase boundary bullet"

missing_child_repo="${workdir}/missing-child"
copy_valid_repo "${missing_child_repo}"
remove_doc_text "${missing_child_repo}" \
  "| #1368 | Phase 64.3 operator limitation ownership surface | Closed. \`apps/operator-ui/src/app/operatorConsolePages/limitationOwnershipPages.tsx\`, route wiring, data-provider readers, list validators, and focused UI/data-provider tests prove operator visibility from backend-bound limitation records without browser, cache, UI, or workflow truth. |"
assert_fails_with \
  "${missing_child_repo}" \
  "Missing Phase 64 child issue outcome row in Child Issue Outcomes table"

missing_verifier_repo="${workdir}/missing-verifier"
copy_valid_repo "${missing_verifier_repo}"
remove_doc_text "${missing_verifier_repo}" \
  "- \`python3 -m unittest control-plane.tests.test_phase64_limitation_ownership_control_plane\`"
assert_fails_with \
  "${missing_verifier_repo}" \
  "Missing Phase 64 verifier evidence line in Verifier Evidence section"

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1371 --config <supervisor-config-path>`.*\n//m' \
  "${missing_issue_lint_repo}/docs/phase-64-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  "Missing Phase 64 issue-lint evidence line in Issue-lint evidence section"

missing_handoff_repo="${workdir}/missing-handoff"
copy_valid_repo "${missing_handoff_repo}"
remove_doc_text "${missing_handoff_repo}" \
  "Phase 66 can consume Phase 64 as one RC evidence input for known limitation ownership."
assert_fails_with \
  "${missing_handoff_repo}" \
  "Phase 66 can consume Phase 64 as one RC evidence input"

missing_limitations_repo="${workdir}/missing-limitations"
copy_valid_repo "${missing_limitations_repo}"
remove_doc_text "${missing_limitations_repo}" \
  "Phase 64 does not resolve limitations, close known limitation records, satisfy support-bundle evidence, accept release gates, approve RC gates, execute gate acceptance, prove Phase 66 RC readiness, prove Phase 67 GA readiness, or replace the Phase 51.3 gate contract."
assert_fails_with \
  "${missing_limitations_repo}" \
  "Missing Phase 64 accepted limitations boundary"

rc_ready_repo="${workdir}/rc-ready"
copy_valid_repo "${rc_ready_repo}"
printf '%s\n' "Phase 64 proves RC readiness." >>"${rc_ready_repo}/docs/phase-64-closeout-evaluation.md"
assert_fails_with \
  "${rc_ready_repo}" \
  "Forbidden Phase 64 closeout evaluation claim: phase 64 proves rc readiness"

support_complete_repo="${workdir}/support-complete"
copy_valid_repo "${support_complete_repo}"
printf '%s\n' "Support-bundle evidence is complete." >>"${support_complete_repo}/docs/phase-64-closeout-evaluation.md"
assert_fails_with \
  "${support_complete_repo}" \
  "Forbidden Phase 64 closeout evaluation claim: support-bundle evidence is complete"

ui_truth_repo="${workdir}/ui-truth"
copy_valid_repo "${ui_truth_repo}"
printf '%s\n' "UI display is limitation truth." >>"${ui_truth_repo}/docs/phase-64-closeout-evaluation.md"
assert_fails_with \
  "${ui_truth_repo}" \
  "Forbidden Phase 64 closeout evaluation claim: ui display is limitation truth"

ai_truth_repo="${workdir}/ai-truth"
copy_valid_repo "${ai_truth_repo}"
printf '%s\n' "AI summary is limitation truth." >>"${ai_truth_repo}/docs/phase-64-closeout-evaluation.md"
assert_fails_with \
  "${ai_truth_repo}" \
  "Forbidden Phase 64 closeout evaluation claim: ai summary is limitation truth"

verifier_truth_repo="${workdir}/verifier-truth"
copy_valid_repo "${verifier_truth_repo}"
printf '%s\n' "Verifier output is release truth." >>"${verifier_truth_repo}/docs/phase-64-closeout-evaluation.md"
assert_fails_with \
  "${verifier_truth_repo}" \
  "Forbidden Phase 64 closeout evaluation claim: verifier output is release truth"

secret_repo="${workdir}/secret"
copy_valid_repo "${secret_repo}"
printf '%s\n' "secret = actual-production-token" >>"${secret_repo}/docs/phase-64-closeout-evaluation.md"
assert_fails_with \
  "${secret_repo}" \
  "production secret-looking value detected"

path_repo="${workdir}/path"
copy_valid_repo "${path_repo}"
users_segment="Users"
printf '%s\n' "Operator note mentions /${users_segment}/local/repo." >>"${path_repo}/docs/phase-64-closeout-evaluation.md"
git -C "${path_repo}" add docs/phase-64-closeout-evaluation.md
git -C "${path_repo}" commit -q -m "path"
assert_fails_with \
  "${path_repo}" \
  "Forbidden Phase 64 closeout evaluation absolute path usage detected"

echo "Phase 64.6 closeout verifier self-test passes."
