#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-67-1-colima-integration-lab.sh"
workdir="$(mktemp -d)"
trap 'chmod -R u+w "${workdir}" 2>/dev/null || true; rm -rf "${workdir}"' EXIT

copy_fixture() {
  local target="$1"
  mkdir -p \
    "${target}/scripts" \
    "${target}/control-plane/deployment" \
    "${target}/.github/workflows"
  cp -R "${repo_root}/control-plane/deployment/phase-67-integration-lab" \
    "${target}/control-plane/deployment/"
  cp "${repo_root}/README.md" "${target}/README.md"
  cp "${repo_root}/control-plane/README.md" "${target}/control-plane/README.md"
  cp "${repo_root}/.gitignore" "${target}/.gitignore"
  cp "${repo_root}/.dockerignore" "${target}/.dockerignore"
  cp "${repo_root}/.github/workflows/ci.yml" "${target}/.github/workflows/ci.yml"
}

assert_passes() {
  local target="$1"
  if ! bash "${verifier}" "${target}" >"${workdir}/stdout" 2>"${workdir}/stderr"; then
    cat "${workdir}/stderr" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"
  if bash "${verifier}" "${target}" >"${workdir}/stdout" 2>"${workdir}/stderr"; then
    echo "Expected verifier failure for ${target}" >&2
    exit 1
  fi
  grep -F -- "${expected}" "${workdir}/stderr" >/dev/null || {
    echo "Expected verifier stderr to contain: ${expected}" >&2
    cat "${workdir}/stderr" >&2
    exit 1
  }
}

valid="${workdir}/valid"
copy_fixture "${valid}"
assert_passes "${valid}"

context_mutation="${workdir}/context-mutation"
copy_fixture "${context_mutation}"
printf '\ndocker context use default\n' >>"${context_mutation}/control-plane/deployment/phase-67-integration-lab/up.sh"
assert_fails_with "${context_mutation}" 'must not mutate the global Docker context'

socket_mount="${workdir}/socket-mount"
copy_fixture "${socket_mount}"
printf '\n# /var/run/docker.sock:/var/run/docker.sock\n' >>"${socket_mount}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with "${socket_mount}" 'must not mount the Docker socket'

destructive_cleanup="${workdir}/destructive-cleanup"
copy_fixture "${destructive_cleanup}"
printf '\n# accidental cleanup option: --volumes\n' \
  >>"${destructive_cleanup}/control-plane/deployment/phase-67-integration-lab/down.sh"
assert_fails_with "${destructive_cleanup}" 'must preserve named volumes'

emulation_drift="${workdir}/emulation-drift"
copy_fixture "${emulation_drift}"
perl -0pi -e 's/AEGISOPS_LAB_ALLOW_EMULATION=yes/AEGISOPS_LAB_ALLOW_EMULATION=no/' \
  "${emulation_drift}/control-plane/deployment/phase-67-integration-lab/bootstrap.env.sample"
assert_fails_with "${emulation_drift}" 'AEGISOPS_LAB_ALLOW_EMULATION=yes'

latest_image="${workdir}/latest-image"
copy_fixture "${latest_image}"
printf '\n# image: example.invalid/lab:latest\n' >>"${latest_image}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with "${latest_image}" 'must not use latest tags'

migration_proof_drift="${workdir}/migration-proof-drift"
copy_fixture "${migration_proof_drift}"
perl -0pi -e 's/prove_migration_state/prove_removed_migration_state/g' \
  "${migration_proof_drift}/control-plane/deployment/phase-67-integration-lab/control-plane-entrypoint.sh"
assert_fails_with "${migration_proof_drift}" 'prove_migration_state'

certificate_renewal_drift="${workdir}/certificate-renewal-drift"
copy_fixture "${certificate_renewal_drift}"
perl -0pi -e 's/openssl x509 -checkend 604800/openssl x509 -noout/' \
  "${certificate_renewal_drift}/control-plane/deployment/phase-67-integration-lab/init.sh"
assert_fails_with "${certificate_renewal_drift}" 'openssl x509 -checkend 604800'

echo "Phase 67.1 verifier rejects context, socket, cleanup, emulation, image, migration-proof, and certificate-renewal drift."
