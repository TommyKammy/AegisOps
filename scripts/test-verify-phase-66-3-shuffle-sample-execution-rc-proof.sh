#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh"

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
  copy_repo_path "${target}" "docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
  copy_repo_path "${target}" "control-plane/aegisops/control_plane/publishable_paths.py"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"

  for path in \
    "docs/phase-66-1-clean-host-rc-e2e-harness.md" \
    "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" \
    "docs/phase-51-6-authority-boundary-negative-test-policy.md" \
    "docs/deployment/shuffle-smb-single-node-profile-contract.md" \
    "docs/deployment/shuffle-reviewed-workflow-template-contract.md" \
    "docs/deployment/shuffle-notify-identity-owner-template-import-contract.md" \
    "docs/deployment/shuffle-manual-fallback-contract.md" \
    "docs/deployment/shuffle-authority-boundary-negative-tests.md" \
    "docs/deployment/case-timeline-authority-projection-contract.md" \
    "docs/phase-65-closeout-evaluation.md"; do
    copy_repo_path "${target}" "${path}"
  done

  for path in \
    "scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh" \
    "scripts/test-verify-phase-66-3-shuffle-sample-execution-rc-proof.sh" \
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
    "${target}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
}

comment_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E/<!-- $ENV{TEXT} -->/g' \
    "${target}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 66.3 Shuffle sample execution RC proof"

missing_reference_repo="${workdir}/missing-reference"
copy_valid_repo "${missing_reference_repo}"
rm "${missing_reference_repo}/docs/deployment/shuffle-reviewed-workflow-template-contract.md"
assert_fails_with "${missing_reference_repo}" "Missing Phase 66.3 reference docs/deployment/shuffle-reviewed-workflow-template-contract.md"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 66\.3 Shuffle sample execution RC proof\]\(docs\/phase-66-3-shuffle-sample-execution-rc-proof\.md\)[^\n]*\n//m' \
  "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical Phase 66.3 boundary bullet"

missing_authority_policy_baseline_repo="${workdir}/missing-authority-policy-baseline"
copy_valid_repo "${missing_authority_policy_baseline_repo}"
remove_doc_text "${missing_authority_policy_baseline_repo}" \
  "\`docs/phase-51-6-authority-boundary-negative-test-policy.md\`, "
assert_fails_with "${missing_authority_policy_baseline_repo}" "Missing required Phase 66.3 Shuffle sample execution proof term"

missing_action_request_row_repo="${workdir}/missing-action-request-row"
copy_valid_repo "${missing_action_request_row_repo}"
remove_doc_text "${missing_action_request_row_repo}" \
  "| \`action_request_id\` | AegisOps action request identifier for the delegated work. | Request text, ticket text, or workflow names cannot create action-request truth. |"
assert_fails_with "${missing_action_request_row_repo}" "Missing Phase 66.3 sample execution evidence field"

commented_receipt_row_repo="${workdir}/commented-receipt-row"
copy_valid_repo "${commented_receipt_row_repo}"
comment_doc_text "${commented_receipt_row_repo}" \
  "| \`execution_receipt_id\` | AegisOps normalized execution receipt linked to the Shuffle run. | Shuffle workflow success or callback payload alone cannot create execution receipt truth. |"
assert_fails_with "${commented_receipt_row_repo}" "Missing Phase 66.3 sample execution evidence field"

missing_delegation_term_repo="${workdir}/missing-delegation-term"
copy_valid_repo "${missing_delegation_term_repo}"
remove_doc_text "${missing_delegation_term_repo}" \
  "template identity, template version, owner, review status, correlation id, action request id, approval decision id, execution receipt id, normalized receipt reference, callback URL, callback secret reference, and idempotency key"
assert_fails_with "${missing_delegation_term_repo}" "Missing Phase 66.3 delegation, receipt, or reconciliation term"

missing_manual_fallback_citation_repo="${workdir}/missing-manual-fallback-citation"
copy_valid_repo "${missing_manual_fallback_citation_repo}"
remove_doc_text "${missing_manual_fallback_citation_repo}" \
  ", plus \`docs/deployment/shuffle-manual-fallback-contract.md\`"
assert_fails_with "${missing_manual_fallback_citation_repo}" "Missing Phase 66.3 delegation, receipt, or reconciliation term"

missing_manual_fallback_paths_repo="${workdir}/missing-manual-fallback-paths"
copy_valid_repo "${missing_manual_fallback_paths_repo}"
remove_doc_text "${missing_manual_fallback_paths_repo}" \
  " for unavailable, rejected, missing receipt, stale receipt, and mismatched receipt paths"
assert_fails_with "${missing_manual_fallback_paths_repo}" "Missing Phase 66.3 delegation, receipt, or reconciliation term"

missing_limitations_repo="${workdir}/missing-limitations"
copy_valid_repo "${missing_limitations_repo}"
remove_doc_text "${missing_limitations_repo}" \
  "It does not prove broad SOAR marketplace coverage, arbitrary connector import, autonomous remediation, Controlled Write readiness, Hard Write readiness, production customer workflow import, production automation authority, real design-partner success, Phase 66 closeout, Phase 67 GA readiness, or commercial replacement readiness."
assert_fails_with "${missing_limitations_repo}" "Missing Phase 66.3 accepted limitations boundary"

mutable_repository_revision_repo="${workdir}/mutable-repository-revision"
copy_valid_repo "${mutable_repository_revision_repo}"
printf '%s\n' "repository_revision: refs/remotes/origin/main" >>"${mutable_repository_revision_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${mutable_repository_revision_repo}" "mutable repository revision detected"

latest_repository_revision_repo="${workdir}/latest-repository-revision"
copy_valid_repo "${latest_repository_revision_repo}"
printf '%s\n' "repository_revision: latest" >>"${latest_repository_revision_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${latest_repository_revision_repo}" "non-immutable repository revision detected"

valid_repository_revision_repo="${workdir}/valid-repository-revision"
copy_valid_repo "${valid_repository_revision_repo}"
printf '%s\n' "repository_revision: 0123456789abcdef0123456789abcdef01234567" >>"${valid_repository_revision_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_passes "${valid_repository_revision_repo}"

invalid_shuffle_profile_repo="${workdir}/invalid-shuffle-profile"
copy_valid_repo "${invalid_shuffle_profile_repo}"
printf '%s\n' "shuffle_profile: enterprise-cluster" >>"${invalid_shuffle_profile_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${invalid_shuffle_profile_repo}" "invalid Shuffle profile detected"

valid_shuffle_profile_repo="${workdir}/valid-shuffle-profile"
copy_valid_repo "${valid_shuffle_profile_repo}"
printf '%s\n' "shuffle_profile: smb-single-node" >>"${valid_shuffle_profile_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_passes "${valid_shuffle_profile_repo}"

invalid_template_repo="${workdir}/invalid-template"
copy_valid_repo "${invalid_template_repo}"
printf '%s\n' "reviewed_template_id: unreviewed-notify-template" >>"${invalid_template_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${invalid_template_repo}" "invalid reviewed template detected"

direct_launch_repo="${workdir}/direct-launch"
copy_valid_repo "${direct_launch_repo}"
printf '%s\n' "direct_shuffle_launch: true" >>"${direct_launch_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${direct_launch_repo}" "bypass value detected"

direct_launch_enabled_repo="${workdir}/direct-launch-enabled"
copy_valid_repo "${direct_launch_enabled_repo}"
printf '%s\n' "Direct Shuffle launch is enabled for this sample." >>"${direct_launch_enabled_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${direct_launch_enabled_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

raw_callback_binding_repo="${workdir}/raw-callback-binding"
copy_valid_repo "${raw_callback_binding_repo}"
printf '%s\n' "callback_binding_reference: raw_forwarded_headers" >>"${raw_callback_binding_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${raw_callback_binding_repo}" "invalid callback binding detected"

inferred_callback_binding_repo="${workdir}/inferred-callback-binding"
copy_valid_repo "${inferred_callback_binding_repo}"
printf '%s\n' "callback_binding_reference: inferred_callback_identity" >>"${inferred_callback_binding_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${inferred_callback_binding_repo}" "invalid callback binding detected"

approval_bypass_repo="${workdir}/approval-bypass"
copy_valid_repo "${approval_bypass_repo}"
printf '%s\n' "Approval bypass is allowed for this Shuffle sample." >>"${approval_bypass_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${approval_bypass_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

missing_approval_repo="${workdir}/missing-approval"
copy_valid_repo "${missing_approval_repo}"
printf '%s\n' "approval_decision_id: missing" >>"${missing_approval_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${missing_approval_repo}" "missing required evidence value detected"

omitted_action_request_repo="${workdir}/omitted-action-request"
copy_valid_repo "${omitted_action_request_repo}"
printf '%s\n' "action_request_id: omitted" >>"${omitted_action_request_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${omitted_action_request_repo}" "missing required evidence value detected"

missing_receipt_repo="${workdir}/missing-receipt"
copy_valid_repo "${missing_receipt_repo}"
printf '%s\n' "execution_receipt_id: missing" >>"${missing_receipt_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${missing_receipt_repo}" "missing required evidence value detected"

hidden_limitation_repo="${workdir}/hidden-limitation"
copy_valid_repo "${hidden_limitation_repo}"
printf '%s\n' "limitation_references: hidden in Shuffle execution text" >>"${hidden_limitation_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${hidden_limitation_repo}" "hidden limitation references detected"

shuffle_reconciliation_truth_repo="${workdir}/shuffle-reconciliation-truth"
copy_valid_repo "${shuffle_reconciliation_truth_repo}"
printf '%s\n' "Shuffle workflow success is AegisOps reconciliation truth." >>"${shuffle_reconciliation_truth_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${shuffle_reconciliation_truth_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

shuffle_executes_records_repo="${workdir}/shuffle-executes-records"
copy_valid_repo "${shuffle_executes_records_repo}"
printf '%s\n' "Shuffle executes AegisOps records after approval." >>"${shuffle_executes_records_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${shuffle_executes_records_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

negation_bypass_authority_repo="${workdir}/negation-bypass-authority"
copy_valid_repo "${negation_bypass_authority_repo}"
printf '%s\n' "If callback cannot be verified, Shuffle approves AegisOps records." >>"${negation_bypass_authority_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${negation_bypass_authority_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

callback_receipt_shortcut_repo="${workdir}/callback-receipt-shortcut"
copy_valid_repo "${callback_receipt_shortcut_repo}"
printf '%s\n' "Callback payload creates execution receipt truth." >>"${callback_receipt_shortcut_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${callback_receipt_shortcut_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

workflow_name_approval_repo="${workdir}/workflow-name-approval"
copy_valid_repo "${workflow_name_approval_repo}"
printf '%s\n' "Workflow names imply approval decision binding." >>"${workflow_name_approval_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${workflow_name_approval_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

ga_ready_repo="${workdir}/ga-ready"
copy_valid_repo "${ga_ready_repo}"
printf '%s\n' "Phase 66.3 proves GA readiness." >>"${ga_ready_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${ga_ready_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

readme_ga_ready_repo="${workdir}/readme-ga-ready"
copy_valid_repo "${readme_ga_ready_repo}"
printf '%s\n' "Phase 66.3 proves GA readiness." >>"${readme_ga_ready_repo}/README.md"
assert_fails_with "${readme_ga_ready_repo}" "Forbidden Phase 66.3 README claim matched"

rc_pass_repo="${workdir}/rc-pass"
copy_valid_repo "${rc_pass_repo}"
printf '%s\n' "Phase 66.3 passes RC." >>"${rc_pass_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${rc_pass_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

broad_soar_repo="${workdir}/broad-soar"
copy_valid_repo "${broad_soar_repo}"
printf '%s\n' "The proof achieves broad SOAR marketplace coverage." >>"${broad_soar_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${broad_soar_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

safe_limitation_repo="${workdir}/safe-limitation"
copy_valid_repo "${safe_limitation_repo}"
printf '%s\n' "Phase 66.3 confirms production automation remains out of scope." >>"${safe_limitation_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_passes "${safe_limitation_repo}"

secret_repo="${workdir}/secret"
copy_valid_repo "${secret_repo}"
printf '%s\n' "api_key: abcdefghijklmnop" >>"${secret_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${secret_repo}" "production secret-looking value detected"

aws_secret_access_key_repo="${workdir}/aws-secret-access-key"
copy_valid_repo "${aws_secret_access_key_repo}"
printf '%s\n' "aws_secret_access_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" >>"${aws_secret_access_key_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${aws_secret_access_key_repo}" "production secret-looking value detected"

customer_private_repo="${workdir}/customer-private"
copy_valid_repo "${customer_private_repo}"
printf '%s\n' "The proof includes customer-private ticket export." >>"${customer_private_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${customer_private_repo}" "customer-private data detected"

customer_private_prohibition_repo="${workdir}/customer-private-prohibition"
copy_valid_repo "${customer_private_prohibition_repo}"
printf '%s\n' "The proof must not include customer-private ticket export." >>"${customer_private_prohibition_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_passes "${customer_private_prohibition_repo}"

echo "Phase 66.3 Shuffle sample execution RC proof verifier self-test passed."
