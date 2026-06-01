#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-65-1-release-bundle-inventory.sh"

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

  mkdir -p "${target}/docs/deployment" "${target}/scripts" "${target}/control-plane/aegisops/control_plane"
  cp "${repo_root}/README.md" "${target}/README.md"
  cp "${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" "${target}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  cp "${repo_root}/docs/phase-51-5-competitive-gap-matrix.md" "${target}/docs/phase-51-5-competitive-gap-matrix.md"
  cp "${repo_root}/docs/phase-64-closeout-evaluation.md" "${target}/docs/phase-64-closeout-evaluation.md"
  cp "${repo_root}/docs/phase-65-1-release-bundle-inventory.md" "${target}/docs/phase-65-1-release-bundle-inventory.md"
  cp "${repo_root}/docs/deployment/single-customer-release-bundle-inventory.md" "${target}/docs/deployment/single-customer-release-bundle-inventory.md"
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
    "${target}/docs/phase-65-1-release-bundle-inventory.md"
}

replace_doc_text() {
  local target="$1"
  local from_text="$2"
  local to_text="$3"

  FROM_TEXT="${from_text}" TO_TEXT="${to_text}" perl -0pi -e 's/\Q$ENV{FROM_TEXT}\E/$ENV{TO_TEXT}/g' \
    "${target}/docs/phase-65-1-release-bundle-inventory.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 65.1 release bundle inventory: docs/phase-65-1-release-bundle-inventory.md"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 65\.1 release bundle inventory\]\(docs\/phase-65-1-release-bundle-inventory\.md\)[^\n]*\n//m' \
  "${missing_readme_repo}/README.md"
assert_fails_with \
  "${missing_readme_repo}" \
  "Missing README canonical cross-phase boundary bullet"

missing_deployment_inventory_repo="${workdir}/missing-deployment-inventory"
copy_valid_repo "${missing_deployment_inventory_repo}"
rm "${missing_deployment_inventory_repo}/docs/deployment/single-customer-release-bundle-inventory.md"
assert_fails_with \
  "${missing_deployment_inventory_repo}" \
  "Missing single-customer release bundle inventory baseline"

missing_version_repo="${workdir}/missing-version"
copy_valid_repo "${missing_version_repo}"
remove_doc_text "${missing_version_repo}" "The inventory identifier is \`phase-65-release-bundle-inventory-v1\`."
assert_fails_with \
  "${missing_version_repo}" \
  "Missing required Phase 65.1 inventory term"

missing_owner_repo="${workdir}/missing-owner"
copy_valid_repo "${missing_owner_repo}"
remove_doc_text "${missing_owner_repo}" "| Release notes artifact set | AegisOps maintainers |"
assert_fails_with \
  "${missing_owner_repo}" \
  "Missing Phase 65.1 artifact inventory row with owner, evidence, and version binding"

missing_class_repo="${workdir}/missing-class"
copy_valid_repo "${missing_class_repo}"
remove_doc_text "${missing_class_repo}" "| Supportability evidence artifact set | IT Operations, Information Systems Department |"
assert_fails_with \
  "${missing_class_repo}" \
  "Missing Phase 65.1 artifact inventory row with owner, evidence, and version binding"

missing_evidence_repo="${workdir}/missing-evidence"
copy_valid_repo "${missing_evidence_repo}"
remove_doc_text "${missing_evidence_repo}" "evidence reference for every required artifact class;"
assert_fails_with \
  "${missing_evidence_repo}" \
  "Missing required Phase 65.1 inventory term"

missing_revision_binding_repo="${workdir}/missing-revision-binding"
copy_valid_repo "${missing_revision_binding_repo}"
remove_doc_text "${missing_revision_binding_repo}" "repository revision or reviewed tag;"
assert_fails_with \
  "${missing_revision_binding_repo}" \
  "Missing required Phase 65.1 inventory term"

missing_approval_binding_repo="${workdir}/missing-approval-binding"
copy_valid_repo "${missing_approval_binding_repo}"
remove_doc_text "${missing_approval_binding_repo}" "issue or change record that approved the bundle for beta/design-partner packaging review."
assert_fails_with \
  "${missing_approval_binding_repo}" \
  "Missing required Phase 65.1 inventory term"

missing_row_evidence_repo="${workdir}/missing-row-evidence"
copy_valid_repo "${missing_row_evidence_repo}"
replace_doc_text \
  "${missing_row_evidence_repo}" \
  "| Install artifact set | Platform maintainers | Install entrypoint, profile selection, runtime env sample, preflight output, and bounded install evidence reference. | \`install-artifacts:<repository-revision>\` | Phase 65.2 offline install bundle contract. |" \
  "| Install artifact set | Platform maintainers |  | \`install-artifacts:<repository-revision>\` | Phase 65.2 offline install bundle contract. |"
assert_fails_with \
  "${missing_row_evidence_repo}" \
  "Missing Phase 65.1 artifact inventory row with owner, evidence, and version binding"

missing_exclusion_repo="${workdir}/missing-exclusion"
copy_valid_repo "${missing_exclusion_repo}"
remove_doc_text "${missing_exclusion_repo}" "hosted update service behavior;"
assert_fails_with \
  "${missing_exclusion_repo}" \
  "Missing required Phase 65.1 inventory term"

missing_extended_exclusion_repo="${workdir}/missing-extended-exclusion"
copy_valid_repo "${missing_extended_exclusion_repo}"
remove_doc_text "${missing_extended_exclusion_repo}" "silent auto-upgrade behavior;"
assert_fails_with \
  "${missing_extended_exclusion_repo}" \
  "Missing required Phase 65.1 inventory term"

missing_sbom_exclusion_repo="${workdir}/missing-sbom-exclusion"
copy_valid_repo "${missing_sbom_exclusion_repo}"
remove_doc_text "${missing_sbom_exclusion_repo}" "SBOM generation, checksum generation, or signing implementation;"
assert_fails_with \
  "${missing_sbom_exclusion_repo}" \
  "Missing required Phase 65.1 inventory term"

unbound_version_repo="${workdir}/unbound-version"
copy_valid_repo "${unbound_version_repo}"
replace_doc_text \
  "${unbound_version_repo}" \
  "| Release notes artifact set | AegisOps maintainers | Release notes reference naming changes, known limitations, operator verification, rollback pointer, and support-bundle pointer. | \`release-notes:<repository-revision>\` | Phase 65.3 release channel metadata. |" \
  "| Release notes artifact set | AegisOps maintainers | Release notes reference naming changes, known limitations, operator verification, rollback pointer, and support-bundle pointer. |  | Phase 65.3 release channel metadata. |"
printf '%s\n' "\`release-notes:<repository-revision>\` appears in a detached note only." >>"${unbound_version_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${unbound_version_repo}" \
  "Missing Phase 65.1 artifact inventory row with owner, evidence, and version binding"

rc_ready_repo="${workdir}/rc-ready"
copy_valid_repo "${rc_ready_repo}"
printf '%s\n' "Phase 65.1 proves RC readiness." >>"${rc_ready_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${rc_ready_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: phase 65.1 proves rc readiness"

ga_ready_repo="${workdir}/ga-ready"
copy_valid_repo "${ga_ready_repo}"
printf '%s\n' "Phase 65.1 proves GA readiness." >>"${ga_ready_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${ga_ready_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: phase 65.1 proves ga readiness"

direct_rc_ready_repo="${workdir}/direct-rc-ready"
copy_valid_repo "${direct_rc_ready_repo}"
printf '%s\n' "Phase 65.1 is RC ready." >>"${direct_rc_ready_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${direct_rc_ready_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: phase 65.1 is rc ready"

direct_ga_ready_repo="${workdir}/direct-ga-ready"
copy_valid_repo "${direct_ga_ready_repo}"
printf '%s\n' "Phase 65.1 is GA ready." >>"${direct_ga_ready_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${direct_ga_ready_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: phase 65.1 is ga ready"

hyphenated_rc_ready_repo="${workdir}/hyphenated-rc-ready"
copy_valid_repo "${hyphenated_rc_ready_repo}"
printf '%s\n' "Phase 65.1 is RC-ready." >>"${hyphenated_rc_ready_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${hyphenated_rc_ready_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: direct RC/GA readiness assertion"

hyphenated_ga_ready_repo="${workdir}/hyphenated-ga-ready"
copy_valid_repo "${hyphenated_ga_ready_repo}"
printf '%s\n' "Phase 65.1 is GA-ready." >>"${hyphenated_ga_ready_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${hyphenated_ga_ready_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: direct RC/GA readiness assertion"

combined_rc_ga_ready_repo="${workdir}/combined-rc-ga-ready"
copy_valid_repo "${combined_rc_ga_ready_repo}"
printf '%s\n' "Phase 65.1 is RC/GA ready." >>"${combined_rc_ga_ready_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${combined_rc_ga_ready_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: direct RC/GA readiness assertion"

hosted_update_ready_repo="${workdir}/hosted-update-ready"
copy_valid_repo "${hosted_update_ready_repo}"
printf '%s\n' "This inventory establishes hosted update service readiness." >>"${hosted_update_ready_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${hosted_update_ready_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: excluded-scope readiness assertion"

billing_ready_repo="${workdir}/billing-ready"
copy_valid_repo "${billing_ready_repo}"
printf '%s\n' "Phase 65.1 proves billing readiness." >>"${billing_ready_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${billing_ready_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: excluded-scope readiness assertion"

verifier_truth_repo="${workdir}/verifier-truth"
copy_valid_repo "${verifier_truth_repo}"
printf '%s\n' "Verifier output is readiness truth." >>"${verifier_truth_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${verifier_truth_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: verifier output is readiness truth"

issue_lint_truth_repo="${workdir}/issue-lint-truth"
copy_valid_repo "${issue_lint_truth_repo}"
printf '%s\n' "Issue-lint output is release truth." >>"${issue_lint_truth_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${issue_lint_truth_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: issue-lint output is release truth"

secret_repo="${workdir}/secret"
copy_valid_repo "${secret_repo}"
printf '%s\n' "secret = actual-production-token" >>"${secret_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${secret_repo}" \
  "production secret-looking value detected"

yaml_secret_repo="${workdir}/yaml-secret"
copy_valid_repo "${yaml_secret_repo}"
printf '%s\n' "password: actual-production-token" >>"${yaml_secret_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${yaml_secret_repo}" \
  "production secret-looking value detected"

placeholder_credential_repo="${workdir}/placeholder-credential"
copy_valid_repo "${placeholder_credential_repo}"
printf '%s\n' "password: <placeholder>" >>"${placeholder_credential_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${placeholder_credential_repo}" \
  "production secret-looking value detected"

customer_private_repo="${workdir}/customer-private"
copy_valid_repo "${customer_private_repo}"
printf '%s\n' "customer-private data: Acme incident payload" >>"${customer_private_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${customer_private_repo}" \
  "customer-private data detected"

bare_customer_private_repo="${workdir}/bare-customer-private"
copy_valid_repo "${bare_customer_private_repo}"
printf '%s\n' "customer-private: Acme incident payload" >>"${bare_customer_private_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${bare_customer_private_repo}" \
  "customer-private data detected"

customer_private_incident_repo="${workdir}/customer-private-incident"
copy_valid_repo "${customer_private_incident_repo}"
printf '%s\n' "customer-private incident: Acme incident payload" >>"${customer_private_incident_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${customer_private_incident_repo}" \
  "customer-private data detected"

wrapped_verifier_truth_repo="${workdir}/wrapped-verifier-truth"
copy_valid_repo "${wrapped_verifier_truth_repo}"
printf '%s\n' "Verifier output is readiness" "truth." >>"${wrapped_verifier_truth_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with \
  "${wrapped_verifier_truth_repo}" \
  "Forbidden Phase 65.1 release bundle inventory claim: verifier output is readiness truth"

path_repo="${workdir}/path"
copy_valid_repo "${path_repo}"
users_segment="Users"
printf '%s\n' "Operator note mentions /${users_segment}/local/repo." >>"${path_repo}/docs/phase-65-1-release-bundle-inventory.md"
git -C "${path_repo}" add docs/phase-65-1-release-bundle-inventory.md
git -C "${path_repo}" commit -q -m "path"
assert_fails_with \
  "${path_repo}" \
  "Forbidden Phase 65.1 release bundle inventory absolute path usage detected"

echo "Phase 65.1 release bundle inventory verifier self-test passes."
