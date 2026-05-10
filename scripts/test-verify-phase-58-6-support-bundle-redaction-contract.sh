#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-58-6-support-bundle-redaction-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-58-6-support-bundle-redaction-contract.md" \
    "${target}/docs/phase-58-6-support-bundle-redaction-contract.md"
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

remove_text_from_contract() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-58-6-support-bundle-redaction-contract.md"
}

append_to_contract() {
  local target="$1"
  local text="$2"

  printf '%s\n' "${text}" \
    >>"${target}/docs/phase-58-6-support-bundle-redaction-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

external_url_repo="${workdir}/external-url"
create_valid_repo "${external_url_repo}"
append_to_contract \
  "${external_url_repo}" \
  "Use https://example.com/home/docs/support-bundle-contract.md as reviewed external reference context."
assert_passes "${external_url_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-58-6-support-bundle-redaction-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 58.6 support bundle redaction contract"

missing_allowed_content_repo="${workdir}/missing-allowed-content"
create_valid_repo "${missing_allowed_content_repo}"
remove_text_from_contract "${missing_allowed_content_repo}" \
  "| \`redaction_manifest\` | Redaction families applied, scan result, retained limitations, and explicit subordinate-evidence boundary. |"
assert_fails_with \
  "${missing_allowed_content_repo}" \
  "Missing Phase 58.6 support bundle redaction contract statement: | \`redaction_manifest\` | Redaction families applied, scan result, retained limitations, and explicit subordinate-evidence boundary. |"

missing_forbidden_content_repo="${workdir}/missing-forbidden-content"
create_valid_repo "${missing_forbidden_content_repo}"
remove_text_from_contract "${missing_forbidden_content_repo}" \
  "| \`tokens_and_headers\` | Reject authorization headers, cookies, bearer tokens, forwarded headers, raw host or tenant hints, and client-supplied identity fields. |"
assert_fails_with \
  "${missing_forbidden_content_repo}" \
  "Missing Phase 58.6 support bundle redaction contract statement: | \`tokens_and_headers\` | Reject authorization headers, cookies, bearer tokens, forwarded headers, raw host or tenant hints, and client-supplied identity fields. |"

missing_redaction_rule_repo="${workdir}/missing-redaction-rule"
create_valid_repo "${missing_redaction_rule_repo}"
remove_text_from_contract "${missing_redaction_rule_repo}" \
  "| \`certs_and_keys\` | Replace cert and key material with reviewed fingerprints, expiry metadata, issuer class, or custody references. |"
assert_fails_with \
  "${missing_redaction_rule_repo}" \
  "Missing Phase 58.6 support bundle redaction contract statement: | \`certs_and_keys\` | Replace cert and key material with reviewed fingerprints, expiry metadata, issuer class, or custody references. |"

missing_failure_state_repo="${workdir}/missing-failure-state"
create_valid_repo "${missing_failure_state_repo}"
remove_text_from_contract "${missing_failure_state_repo}" \
  "| \`private_payload_leakage\` | Bundle output contains raw customer payloads, raw logs, raw tickets, raw webhook bodies, screenshots, or private support notes. | Reject the bundle and retain bounded summaries only. |"
assert_fails_with \
  "${missing_failure_state_repo}" \
  "Missing Phase 58.6 support bundle redaction contract statement: | \`private_payload_leakage\` | Bundle output contains raw customer payloads, raw logs, raw tickets, raw webhook bodies, screenshots, or private support notes. | Reject the bundle and retain bounded summaries only. |"

secret_value_repo="${workdir}/secret-value"
create_valid_repo "${secret_value_repo}"
append_to_contract "${secret_value_repo}" "support_password = ExampleSecretValue12345"
assert_fails_with \
  "${secret_value_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: secret-looking value"

authorization_header_repo="${workdir}/authorization-header"
create_valid_repo "${authorization_header_repo}"
append_to_contract "${authorization_header_repo}" "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456"
assert_fails_with \
  "${authorization_header_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: secret-looking value"

credential_url_repo="${workdir}/credential-url"
create_valid_repo "${credential_url_repo}"
append_to_contract "${credential_url_repo}" "postgres://support:credentialvalue12345@db.internal/aegisops"
assert_fails_with \
  "${credential_url_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: secret-looking value"

cert_material_repo="${workdir}/cert-material"
create_valid_repo "${cert_material_repo}"
append_to_contract "${cert_material_repo}" "-----BEGIN CERTIFICATE-----"
assert_fails_with \
  "${cert_material_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: secret-looking value"

private_key_repo="${workdir}/private-key"
create_valid_repo "${private_key_repo}"
append_to_contract "${private_key_repo}" "-----BEGIN PRIVATE KEY-----"
assert_fails_with \
  "${private_key_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: secret-looking value"

workstation_path_repo="${workdir}/workstation-path"
create_valid_repo "${workstation_path_repo}"
macos_home_fragment="/""Users/example"
append_to_contract "${workstation_path_repo}" "Retain ${macos_home_fragment}/support-bundle/raw.log as evidence."
assert_fails_with \
  "${workstation_path_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: workstation-local path"

linux_workstation_path_repo="${workdir}/linux-workstation-path"
create_valid_repo "${linux_workstation_path_repo}"
linux_home_fragment="/""home/example"
append_to_contract "${linux_workstation_path_repo}" "Retain ${linux_home_fragment}/support-bundle/raw.log as evidence."
assert_fails_with \
  "${linux_workstation_path_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: workstation-local path"

windows_workstation_path_repo="${workdir}/windows-workstation-path"
create_valid_repo "${windows_workstation_path_repo}"
windows_home_fragment="D:""\\Users\\example"
append_to_contract "${windows_workstation_path_repo}" "Retain ${windows_home_fragment}\\support-bundle\\raw.log as evidence."
assert_fails_with \
  "${windows_workstation_path_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: workstation-local path"

windows_slash_workstation_path_repo="${workdir}/windows-slash-workstation-path"
create_valid_repo "${windows_slash_workstation_path_repo}"
slash="/"
windows_slash_home_fragment="C:${slash}Users${slash}example"
append_to_contract "${windows_slash_workstation_path_repo}" "Retain ${windows_slash_home_fragment}/support-bundle/raw.log as evidence."
assert_fails_with \
  "${windows_slash_workstation_path_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: workstation-local path"

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
append_to_contract "${workflow_truth_repo}" "Support bundle is workflow truth."
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: support bundle is workflow truth"

private_payload_repo="${workdir}/private-payload"
create_valid_repo "${private_payload_repo}"
append_to_contract "${private_payload_repo}" "Raw customer payloads are included by default."
assert_fails_with \
  "${private_payload_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: raw customer payloads are included by default"

private_ticket_repo="${workdir}/private-ticket"
create_valid_repo "${private_ticket_repo}"
append_to_contract "${private_ticket_repo}" "Private ticket contents are included by default."
assert_fails_with \
  "${private_ticket_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: private ticket contents are included by default"

support_operator_repo="${workdir}/support-operator"
create_valid_repo "${support_operator_repo}"
append_to_contract "${support_operator_repo}" "Support collaborator is an operator."
assert_fails_with \
  "${support_operator_repo}" \
  "Forbidden Phase 58.6 support bundle redaction contract claim: support collaborator is an operator"

echo "Phase 58.6 support bundle redaction contract verifier rejects missing coverage, secret-looking values, workstation paths, private payloads, and authority expansion."
