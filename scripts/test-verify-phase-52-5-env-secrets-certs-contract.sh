#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-5-env-secrets-certs-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment" "${target}/control-plane/deployment/first-boot"
  printf '%s\n' "# AegisOps" "See [Phase 52.5 env secrets certs contract](docs/deployment/env-secrets-certs-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/env-secrets-certs-contract.md" \
    "${target}/docs/deployment/env-secrets-certs-contract.md"
  cp "${repo_root}/control-plane/deployment/first-boot/bootstrap.env.sample" \
    "${target}/control-plane/deployment/first-boot/bootstrap.env.sample"
  printf '%s\n' \
    "control-plane/deployment/first-boot/generated/" \
    "control-plane/deployment/first-boot/runtime/" \
    "control-plane/deployment/first-boot/secrets/" \
    "control-plane/deployment/first-boot/certs/" \
    >"${target}/.gitignore"
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
    "${target}/docs/deployment/env-secrets-certs-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/env-secrets-certs-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 52.5 env secrets certs contract"

missing_ignore_repo="${workdir}/missing-ignore"
create_valid_repo "${missing_ignore_repo}"
perl -0pi -e 's/control-plane\/deployment\/first-boot\/secrets\/\n//' \
  "${missing_ignore_repo}/.gitignore"
assert_fails_with \
  "${missing_ignore_repo}" \
  "Missing Phase 52.5 generated runtime ignore pattern: control-plane/deployment/first-boot/secrets/"

missing_binding_repo="${workdir}/missing-demo-token-binding"
create_valid_repo "${missing_binding_repo}"
remove_text_from_contract "${missing_binding_repo}" \
  "| \`AEGISOPS_DEMO_TOKEN_FILE\` | File reference for a generated demo token when demo mode is explicitly enabled. | Demo-only setup convenience. | Must not satisfy admin bootstrap, break-glass, Wazuh ingest, proxy boundary, OpenBao, or production credential checks. |"
assert_fails_with \
  "${missing_binding_repo}" \
  "Missing complete Phase 52.5 runtime binding row: AEGISOPS_DEMO_TOKEN_FILE"

missing_secret_class_repo="${workdir}/missing-break-glass-secret"
create_valid_repo "${missing_secret_class_repo}"
remove_text_from_contract "${missing_secret_class_repo}" \
  "| Break-glass token | \`AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE\` or \`AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH\`. | Demo tokens are separate from break-glass tokens. | Missing custody owner, trigger, and follow-up rotation evidence fails closed. |"
assert_fails_with \
  "${missing_secret_class_repo}" \
  "Missing complete Phase 52.5 secret custody row: Break-glass token"

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
printf '%s\n' "Placeholder secrets are valid credentials." \
  >>"${placeholder_secret_repo}/docs/deployment/env-secrets-certs-contract.md"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Forbidden Phase 52.5 env secrets certs contract claim: Placeholder secrets are valid credentials"

secret_looking_repo="${workdir}/secret-looking-value"
create_valid_repo "${secret_looking_repo}"
printf '%s\n' "admin_token = syntheticsecretvalue1234567890" \
  >>"${secret_looking_repo}/docs/deployment/env-secrets-certs-contract.md"
assert_fails_with \
  "${secret_looking_repo}" \
  "Forbidden Phase 52.5 env secrets certs contract: committed secret-looking value detected"

demo_token_truth_repo="${workdir}/demo-token-production-truth"
create_valid_repo "${demo_token_truth_repo}"
printf '%s\n' "Demo token is production truth." \
  >>"${demo_token_truth_repo}/docs/deployment/env-secrets-certs-contract.md"
assert_fails_with \
  "${demo_token_truth_repo}" \
  "Forbidden Phase 52.5 env secrets certs contract claim: Demo token is production truth"

demo_cert_truth_repo="${workdir}/demo-cert-production-truth"
create_valid_repo "${demo_cert_truth_repo}"
printf '%s\n' "Demo certificate is production truth." \
  >>"${demo_cert_truth_repo}/docs/deployment/env-secrets-certs-contract.md"
assert_fails_with \
  "${demo_cert_truth_repo}" \
  "Forbidden Phase 52.5 env secrets certs contract claim: Demo certificate is production truth"

missing_phase51_repo="${workdir}/missing-phase51-citation"
create_valid_repo "${missing_phase51_repo}"
remove_text_from_contract "${missing_phase51_repo}" \
  'This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
assert_fails_with \
  "${missing_phase51_repo}" \
  'Missing Phase 52.5 env secrets certs contract statement: This contract cites the Phase 51.6 authority-boundary negative-test policy'

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/env-secrets-certs-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.5 env secrets certs contract: workstation-local absolute path detected"

missing_env_sample_link_repo="${workdir}/missing-env-sample-link"
create_valid_repo "${missing_env_sample_link_repo}"
perl -0pi -e 's/docs\/deployment\/env-secrets-certs-contract\.md/docs\/deployment\/single-customer-release-bundle-inventory.md/' \
  "${missing_env_sample_link_repo}/control-plane/deployment/first-boot/bootstrap.env.sample"
assert_fails_with \
  "${missing_env_sample_link_repo}" \
  "First-boot bootstrap env sample must link the Phase 52.5 env secrets certs contract."

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 52.5 env secrets certs contract."

echo "Phase 52.5 env secrets certs contract negative and valid fixtures passed."
