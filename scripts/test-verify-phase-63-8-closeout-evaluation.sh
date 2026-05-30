#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-63-8-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-63-closeout-evaluation.md" "${target}/docs/phase-63-closeout-evaluation.md"
  cp "${repo_root}/README.md" "${target}/README.md"
  cp "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${target}/scripts/verify-publishable-path-hygiene.sh"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"
  cp "${repo_root}/control-plane/aegisops/control_plane/publishable_paths.py" "${target}/control-plane/aegisops/control_plane/publishable_paths.py"
  git -C "${target}" init -q
  git -C "${target}" config user.email "aegisops@example.invalid"
  git -C "${target}" config user.name "AegisOps Test"
  git -C "${target}" add README.md docs/phase-63-closeout-evaluation.md scripts/verify-publishable-path-hygiene.sh control-plane/aegisops
  git -C "${target}" commit -q -m "fixture"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-63-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs" "${missing_doc_repo}/scripts" "${missing_doc_repo}/control-plane/aegisops/control_plane"
cp "${repo_root}/README.md" "${missing_doc_repo}/README.md"
cp "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${missing_doc_repo}/scripts/verify-publishable-path-hygiene.sh"
: >"${missing_doc_repo}/control-plane/aegisops/__init__.py"
: >"${missing_doc_repo}/control-plane/aegisops/control_plane/__init__.py"
cp "${repo_root}/control-plane/aegisops/control_plane/publishable_paths.py" "${missing_doc_repo}/control-plane/aegisops/control_plane/publishable_paths.py"
git -C "${missing_doc_repo}" init -q
git -C "${missing_doc_repo}" config user.email "aegisops@example.invalid"
git -C "${missing_doc_repo}" config user.name "AegisOps Test"
git -C "${missing_doc_repo}" add README.md scripts/verify-publishable-path-hygiene.sh control-plane/aegisops
git -C "${missing_doc_repo}" commit -q -m "fixture"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 63 closeout evaluation: docs/phase-63-closeout-evaluation.md"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 63\.8 closeout evaluation\]\(docs\/phase-63-closeout-evaluation\.md\)[^\n]*\n/- Phase 63.8 closeout evaluation\\n/' \
  "${missing_readme_repo}/README.md"
assert_fails_with \
  "${missing_readme_repo}" \
  "Missing README canonical cross-phase boundary bullet"

missing_child_repo="${workdir}/missing-child"
copy_valid_repo "${missing_child_repo}"
remove_doc_text "${missing_child_repo}" \
  "| #1337 | Phase 63.6 evidence-pack UI | Closed. \`apps/operator-ui/src/app/OperatorRoutes.casework.evidence-pack.test.tsx\`, \`apps/operator-ui/src/app/operatorConsolePages/caseDetailSurfaces.tsx\`, and \`apps/operator-ui/src/operatorDataProvider/detailReaders.ts\` prove linked evidence packs render only from verified backend case detail as subordinate context and fail closed on cache, browser, authority, readiness, source, custody, provenance, confidence, freshness, and field drift. |"
assert_fails_with \
  "${missing_child_repo}" \
  "Missing Phase 63 child issue outcome row in Child Issue Outcomes table"

child_outside_table_repo="${workdir}/child-outside-table"
copy_valid_repo "${child_outside_table_repo}"
remove_doc_text "${child_outside_table_repo}" \
  "| #1336 | Phase 63.5 evidence freshness and provenance projection | Closed. \`docs/phase-63-5-evidence-freshness-provenance-projection.md\`, validation notes, projection code, and focused tests prove freshness, custody, confidence, provenance, conflict, source mismatch, unavailable-source, uncertainty, and projection-time revalidation for case workbench and AI-grounding consumers. |"
printf '%s\n' \
  "| #1336 | Phase 63.5 evidence freshness and provenance projection | Closed. \`docs/phase-63-5-evidence-freshness-provenance-projection.md\`, validation notes, projection code, and focused tests prove freshness, custody, confidence, provenance, conflict, source mismatch, unavailable-source, uncertainty, and projection-time revalidation for case workbench and AI-grounding consumers. |" \
  >>"${child_outside_table_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${child_outside_table_repo}" \
  "Missing Phase 63 child issue outcome row in Child Issue Outcomes table"

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1339 --config <supervisor-config-path>`.*\n//m' \
  "${missing_issue_lint_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  "Missing Phase 63 issue-lint evidence line in Issue-lint evidence section"

missing_issue_lint_summary_repo="${workdir}/missing-issue-lint-summary"
copy_valid_repo "${missing_issue_lint_summary_repo}"
remove_doc_text "${missing_issue_lint_summary_repo}" \
  'Each command should report `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, and `high_risk_blocking_ambiguity=none` before Phase 63 is considered fully closed.'
assert_fails_with \
  "${missing_issue_lint_summary_repo}" \
  "missing_required=none"

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
remove_doc_text "${missing_authority_repo}" \
  "AegisOps records remain authoritative for alert, case, evidence request, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth."
assert_fails_with \
  "${missing_authority_repo}" \
  "AegisOps records remain authoritative"

missing_limitations_repo="${workdir}/missing-limitations"
copy_valid_repo "${missing_limitations_repo}"
remove_doc_text "${missing_limitations_repo}" \
  "Phase 63 does not implement Phase 64 limitation ownership, Phase 65 upgrade work, Phase 66 RC proof, Phase 67 GA proof, Beta readiness, RC readiness, GA readiness, self-service commercial readiness, or commercial replacement readiness."
assert_fails_with \
  "${missing_limitations_repo}" \
  "Missing Phase 63 accepted limitations boundary"

missing_handoff_repo="${workdir}/missing-handoff"
copy_valid_repo "${missing_handoff_repo}"
remove_doc_text "${missing_handoff_repo}" \
  "Phase 66 can consume Phase 63 as one RC evidence input for Evidence Expansion v1."
assert_fails_with \
  "${missing_handoff_repo}" \
  "Phase 66 can consume Phase 63 as one RC evidence input"

release_truth_repo="${workdir}/release-truth"
copy_valid_repo "${release_truth_repo}"
printf '%s\n' "Verifier output is release truth." >>"${release_truth_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${release_truth_repo}" \
  "Forbidden Phase 63 closeout evaluation claim: verifier output is release truth"

issue_lint_truth_repo="${workdir}/issue-lint-truth"
copy_valid_repo "${issue_lint_truth_repo}"
printf '%s\n' "Issue-lint output is release truth." >>"${issue_lint_truth_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${issue_lint_truth_repo}" \
  "Forbidden Phase 63 closeout evaluation claim: issue-lint output is release truth"

rc_ready_repo="${workdir}/rc-ready"
copy_valid_repo "${rc_ready_repo}"
printf '%s\n' "Phase 63 proves RC readiness." >>"${rc_ready_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${rc_ready_repo}" \
  "Forbidden Phase 63 closeout evaluation claim: phase 63 proves rc readiness"

endpoint_remediation_repo="${workdir}/endpoint-remediation"
copy_valid_repo "${endpoint_remediation_repo}"
printf '%s\n' "Endpoint remediation is implemented." >>"${endpoint_remediation_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${endpoint_remediation_repo}" \
  "Forbidden Phase 63 closeout evaluation claim: endpoint remediation is implemented"

broad_source_repo="${workdir}/broad-source"
copy_valid_repo "${broad_source_repo}"
printf '%s\n' "Broad evidence-source marketplace is implemented." >>"${broad_source_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${broad_source_repo}" \
  "Forbidden Phase 63 closeout evaluation claim: broad evidence-source marketplace is implemented"

ui_authority_repo="${workdir}/ui-authority"
copy_valid_repo "${ui_authority_repo}"
printf '%s\n' "UI state approves evidence." >>"${ui_authority_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${ui_authority_repo}" \
  "Forbidden Phase 63 closeout evaluation claim: ui state approves evidence"

secret_repo="${workdir}/secret"
copy_valid_repo "${secret_repo}"
printf '%s\n' "secret = actual-production-token" >>"${secret_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${secret_repo}" \
  "production secret-looking value detected"

path_repo="${workdir}/path"
copy_valid_repo "${path_repo}"
users_segment="Users"
printf '%s\n' "Local workspace /${users_segment}/someone/AegisOps is required." >>"${path_repo}/docs/phase-63-closeout-evaluation.md"
assert_fails_with \
  "${path_repo}" \
  "workstation-local absolute path"

echo "Phase 63.8 closeout verifier negative fixtures pass."
