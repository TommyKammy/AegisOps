#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-44-47-boundary-docs.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_docs=(
  "docs/phase-44-pilot-ingress-and-operator-surface-closure-boundary.md"
  "docs/phase-44-pilot-ingress-and-operator-surface-closure-validation.md"
  "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-boundary.md"
  "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-validation.md"
  "docs/phase-46-approval-execution-reconciliation-operations-pack-boundary.md"
  "docs/phase-46-approval-execution-reconciliation-operations-pack-validation.md"
  "docs/phase-47-control-plane-responsibility-decomposition-boundary.md"
  "docs/phase-47-control-plane-responsibility-decomposition-validation.md"
)

boundary_docs=(
  "docs/phase-44-pilot-ingress-and-operator-surface-closure-boundary.md"
  "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-boundary.md"
  "docs/phase-46-approval-execution-reconciliation-operations-pack-boundary.md"
  "docs/phase-47-control-plane-responsibility-decomposition-boundary.md"
)

validation_docs=(
  "docs/phase-44-pilot-ingress-and-operator-surface-closure-validation.md"
  "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-validation.md"
  "docs/phase-46-approval-execution-reconciliation-operations-pack-validation.md"
  "docs/phase-47-control-plane-responsibility-decomposition-validation.md"
)

write_file() {
  local target="$1"
  local path="$2"
  local content="$3"

  mkdir -p "$(dirname "${target}/${path}")"
  printf '%s\n' "${content}" >"${target}/${path}"
}

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"

  for doc in "${required_docs[@]}"; do
    write_file "${target}" "${doc}" "# ${doc}

Required Phase 44-47 fixture content."
  done

  {
    echo "# AegisOps"
    echo
    echo "## Phase 44-47 closure contracts"
    echo
    echo "Phase 44-47 boundary docs:"
    for doc in "${boundary_docs[@]}"; do
      echo "- \`${doc}\`"
    done
    echo
    echo "Phase 44-47 validation docs:"
    for doc in "${validation_docs[@]}"; do
      echo "- \`${doc}\`"
    done
    echo
    echo "AegisOps control-plane records remain authoritative."
    echo "The operator UI, proxy, Zammad, assistant, optional evidence, downstream receipts, and maintainability projections remain subordinate context."
  } >"${target}/README.md"

  {
    echo "# AegisOps Non-Goals and Expansion Guardrails"
    echo
    echo "## Phase 44-47 Closed Pilot-Readiness Guardrails"
    echo
    echo "The closed Phase 44-47 contracts cover pilot ingress, daily SOC queue, approval/execution/reconciliation operations, and control-plane responsibility decomposition."
    echo
    echo "AegisOps control-plane records remain authoritative."
    echo "No later roadmap item may use these closed phases to infer new runtime behavior, browser authority, ticket authority, assistant authority, optional-evidence authority, or commercial-readiness claims."
    echo
    echo "Phase 44-47 boundary docs:"
    for doc in "${boundary_docs[@]}"; do
      echo "- \`${doc}\`"
    done
  } >"${target}/docs/non-goals-and-expansion-guardrails.md"
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
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-46-approval-execution-reconciliation-operations-pack-validation.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing required Phase 44-47 boundary or validation doc: docs/phase-46-approval-execution-reconciliation-operations-pack-validation.md"

missing_non_goals_link_repo="${workdir}/missing-non-goals-link"
create_valid_repo "${missing_non_goals_link_repo}"
perl -0pi -e 's/- `docs\/phase-47-control-plane-responsibility-decomposition-boundary\.md`\n//' \
  "${missing_non_goals_link_repo}/docs/non-goals-and-expansion-guardrails.md"
assert_fails_with \
  "${missing_non_goals_link_repo}" \
  "Missing Phase 44-47 boundary cross-link in docs/non-goals-and-expansion-guardrails.md: docs/phase-47-control-plane-responsibility-decomposition-boundary.md"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
perl -0pi -e 's/- `docs\/phase-45-daily-soc-queue-and-operator-ux-hardening-validation\.md`\n//' \
  "${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "Missing Phase 44-47 validation handoff cross-link in README.md: docs/phase-45-daily-soc-queue-and-operator-ux-hardening-validation.md"

echo "verify-phase-44-47-boundary-docs tests passed"
