#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-57-1-rbac-role-matrix-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

copy_artifacts() {
  local target="$1"

  mkdir -p \
    "${target}/docs" \
    "${target}/apps/operator-ui/src/auth" \
    "${target}/scripts"
  cp "${repo_root}/docs/phase-57-1-rbac-role-matrix-contract.md" \
    "${target}/docs/phase-57-1-rbac-role-matrix-contract.md"
  cp "${repo_root}/apps/operator-ui/src/auth/roleMatrix.ts" \
    "${target}/apps/operator-ui/src/auth/roleMatrix.ts"
  cp "${repo_root}/apps/operator-ui/src/auth/roleMatrix.test.ts" \
    "${target}/apps/operator-ui/src/auth/roleMatrix.test.ts"
  cp "${repo_root}/apps/operator-ui/src/auth/session.test.ts" \
    "${target}/apps/operator-ui/src/auth/session.test.ts"
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

valid_repo="${workdir}/valid"
copy_artifacts "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_artifacts "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-57-1-rbac-role-matrix-contract.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 57.1 RBAC role matrix contract"

missing_role_repo="${workdir}/missing-support-role"
copy_artifacts "${missing_role_repo}"
perl -0pi -e 's/"support_operator",//g; s/\| `support_operator` \| read-only \| read-only \| denied \| denied \| denied \| support-only \| denied \| denied \| denied \| denied \|\n//g' \
  "${missing_role_repo}/apps/operator-ui/src/auth/roleMatrix.ts" \
  "${missing_role_repo}/docs/phase-57-1-rbac-role-matrix-contract.md"
assert_fails_with \
  "${missing_role_repo}" \
  'Missing Phase 57.1 RBAC role matrix contract statement: | `support_operator` | read-only | read-only | denied | denied | denied | support-only | denied | denied | denied | denied |'

missing_negative_repo="${workdir}/missing-negative"
copy_artifacts "${missing_negative_repo}"
perl -0pi -e 's/Negative tests must reject support operator workflow authority, external collaborator workflow authority, UI role cache as authority, self-approval through role confusion, and admin configuration rewriting historical truth\.//g' \
  "${missing_negative_repo}/docs/phase-57-1-rbac-role-matrix-contract.md"
assert_fails_with \
  "${missing_negative_repo}" \
  "Missing Phase 57.1 RBAC role matrix contract statement: Negative tests must reject support operator workflow authority, external collaborator workflow authority, UI role cache as authority, self-approval through role confusion, and admin configuration rewriting historical truth."

missing_access_repo="${workdir}/missing-no-authority"
copy_artifacts "${missing_access_repo}"
perl -0pi -e 's/"no_authority"/"denied"/g; s/no-authority/denied/g' \
  "${missing_access_repo}/apps/operator-ui/src/auth/roleMatrix.ts" \
  "${missing_access_repo}/apps/operator-ui/src/auth/roleMatrix.test.ts" \
  "${missing_access_repo}/docs/phase-57-1-rbac-role-matrix-contract.md"
assert_fails_with \
  "${missing_access_repo}" \
  'Missing Phase 57.1 RBAC role matrix contract statement: | `external_collaborator` | read-only | read-only | denied | denied | denied | denied | denied | no-authority | denied | denied |'

local_path_repo="${workdir}/local-path"
copy_artifacts "${local_path_repo}"
printf '\nLocal debug path: %s\n' "/""Users/example/AegisOps" >> \
  "${local_path_repo}/docs/phase-57-1-rbac-role-matrix-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Phase 57.1 RBAC artifacts contain workstation-local absolute paths"

echo "verify-phase-57-1-rbac-role-matrix-contract tests passed"
