#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh"

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

copy_repo_path() {
  local target="$1"
  local relative_path="$2"

  mkdir -p "${target}/$(dirname "${relative_path}")"
  cp -p "${repo_root}/${relative_path}" "${target}/${relative_path}"
}

copy_valid_repo() {
  local target="$1"
  local path

  mkdir -p "${target}"
  copy_repo_path "${target}" "README.md"
  copy_repo_path "${target}" "docs/phase-66-1-clean-host-rc-e2e-harness.md"
  copy_repo_path "${target}" "control-plane/aegisops/control_plane/publishable_paths.py"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"

  for path in \
    "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" \
    "docs/phase-51-6-authority-boundary-negative-test-policy.md" \
    "docs/phase-65-closeout-evaluation.md" \
    "docs/getting-started/first-user-journey.md" \
    "docs/getting-started/first-user-demo-report-export.md"; do
    copy_repo_path "${target}" "${path}"
  done

  for path in \
    "scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh" \
    "scripts/test-verify-phase-66-1-clean-host-rc-e2e-harness.sh" \
    "scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh" \
    "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh" \
    "scripts/verify-publishable-path-hygiene.sh"; do
    copy_repo_path "${target}" "${path}"
  done

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
    "${target}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
}

comment_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E/<!-- $ENV{TEXT} -->/g' \
    "${target}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 66.1 clean-host RC E2E harness"

missing_reference_repo="${workdir}/missing-reference"
copy_valid_repo "${missing_reference_repo}"
rm "${missing_reference_repo}/docs/phase-65-closeout-evaluation.md"
assert_fails_with "${missing_reference_repo}" "Missing Phase 66.1 reference docs/phase-65-closeout-evaluation.md"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 66\.1 clean-host RC E2E harness\]\(docs\/phase-66-1-clean-host-rc-e2e-harness\.md\)[^\n]*\n//m' \
  "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical Phase 66.1 boundary bullet"

missing_profile_repo="${workdir}/missing-profile-field"
copy_valid_repo "${missing_profile_repo}"
remove_doc_text "${missing_profile_repo}" \
  "| \`phase65_input_references\` | Phase 65 closeout and packaging artifacts consumed as subordinate input. | Phase 65 closure cannot satisfy RC E2E by inference. |"
assert_fails_with "${missing_profile_repo}" "Missing Phase 66.1 clean-host profile field"

commented_profile_repo="${workdir}/commented-profile-field"
copy_valid_repo "${commented_profile_repo}"
comment_doc_text "${commented_profile_repo}" \
  "| \`phase65_input_references\` | Phase 65 closeout and packaging artifacts consumed as subordinate input. | Phase 65 closure cannot satisfy RC E2E by inference. |"
assert_fails_with "${commented_profile_repo}" "Missing Phase 66.1 clean-host profile field"

missing_journey_step_repo="${workdir}/missing-journey-step"
copy_valid_repo "${missing_journey_step_repo}"
remove_doc_text "${missing_journey_step_repo}" "Wazuh-origin signal inspection"
assert_fails_with "${missing_journey_step_repo}" "Missing Phase 66.1 required journey step"

out_of_order_journey_repo="${workdir}/out-of-order-journey"
copy_valid_repo "${out_of_order_journey_repo}"
report_export_row="| 16 | Report export | Export command, export artifact reference, schema version, redaction review, source record identifiers, and non-secret result. | Reports are derived surfaces and cannot replace source records. |"
login_row="| 5 | Login | Operator role, selected profile, visible demo or RC labels, and access result. | Browser state and session state remain subordinate context. |"
remove_doc_text "${out_of_order_journey_repo}" "${report_export_row}"
LOGIN_ROW="${login_row}" REPORT_EXPORT_ROW="${report_export_row}" perl -0pi -e 's/\Q$ENV{LOGIN_ROW}\E/$ENV{REPORT_EXPORT_ROW}\n$ENV{LOGIN_ROW}/' \
  "${out_of_order_journey_repo}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
assert_fails_with "${out_of_order_journey_repo}" "Missing ordered Phase 66.1 required journey step"

missing_evidence_field_repo="${workdir}/missing-evidence-field"
copy_valid_repo "${missing_evidence_field_repo}"
remove_doc_text "${missing_evidence_field_repo}" \
  "\`shuffle_workflow_id\`, \`action_request_id\`, \`approval_decision_id\`, \`execution_receipt_id\`, \`reconciliation_id\`."
assert_fails_with "${missing_evidence_field_repo}" "Missing Phase 66.1 evidence packet field group"

missing_limitations_repo="${workdir}/missing-limitations"
copy_valid_repo "${missing_limitations_repo}"
remove_doc_text "${missing_limitations_repo}" \
  "It does not collect real design-partner evidence, prove real design-partner success, complete support-bundle review, complete restore dry-run proof, complete upgrade rehearsal proof, approve production rollout, approve self-service commercial readiness, or satisfy Phase 67 GA readiness."
assert_fails_with "${missing_limitations_repo}" "Missing Phase 66.1 accepted limitations boundary"

missing_verifier_script_repo="${workdir}/missing-verifier-script"
copy_valid_repo "${missing_verifier_script_repo}"
rm "${missing_verifier_script_repo}/scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh"
assert_fails_with "${missing_verifier_script_repo}" "Missing Phase 66.1 verifier script scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh"

ga_ready_repo="${workdir}/ga-ready"
copy_valid_repo "${ga_ready_repo}"
printf '%s\n' "Phase 66.1 proves GA readiness." >>"${ga_ready_repo}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
assert_fails_with "${ga_ready_repo}" "Forbidden Phase 66.1 clean-host RC E2E harness claim matched"

negation_bypass_repo="${workdir}/negation-bypass"
copy_valid_repo "${negation_bypass_repo}"
printf '%s\n' "No operator review occurred; Phase 66.1 proves GA readiness." >>"${negation_bypass_repo}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
assert_fails_with "${negation_bypass_repo}" "Forbidden Phase 66.1 clean-host RC E2E harness claim matched"

readme_overclaim_repo="${workdir}/readme-overclaim"
copy_valid_repo "${readme_overclaim_repo}"
printf '%s\n' "Phase 66.1 proves GA readiness." >>"${readme_overclaim_repo}/README.md"
assert_fails_with "${readme_overclaim_repo}" "Forbidden Phase 66.1 README claim matched"

commercial_ready_repo="${workdir}/commercial-ready"
copy_valid_repo "${commercial_ready_repo}"
printf '%s\n' "AegisOps is a self-service commercial replacement after this harness." >>"${commercial_ready_repo}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
assert_fails_with "${commercial_ready_repo}" "Forbidden Phase 66.1 clean-host RC E2E harness claim matched"

ai_authority_repo="${workdir}/ai-authority"
copy_valid_repo "${ai_authority_repo}"
printf '%s\n' "AI approves the action during this harness." >>"${ai_authority_repo}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
assert_fails_with "${ai_authority_repo}" "Forbidden Phase 66.1 clean-host RC E2E harness claim matched"

secret_repo="${workdir}/secret"
copy_valid_repo "${secret_repo}"
printf '%s\n' "token: abcdefghijklmnop" >>"${secret_repo}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
assert_fails_with "${secret_repo}" "production secret-looking value detected"

customer_private_repo="${workdir}/customer-private"
copy_valid_repo "${customer_private_repo}"
printf '%s\n' "The packet includes customer-private alert export." >>"${customer_private_repo}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
assert_fails_with "${customer_private_repo}" "customer-private data detected"

local_path_repo="${workdir}/local-path"
copy_valid_repo "${local_path_repo}"
printf 'Evidence path: /%s/example/aegisops/private\n' "Users" >>"${local_path_repo}/docs/phase-66-1-clean-host-rc-e2e-harness.md"
assert_fails_with "${local_path_repo}" "absolute path"

echo "Phase 66.1 clean-host RC E2E harness verifier self-test passed."
