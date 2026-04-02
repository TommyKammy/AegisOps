#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-contributor-naming-guide-doc.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/docs/contributor-naming-guide.md"
  git -C "${target}" add docs/contributor-naming-guide.md
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit -q -m "fixture"
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

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_doc "${valid_repo}" "# AegisOps Contributor Naming Guide

## Purpose

Guide text.

## Baseline Source

docs/requirements-baseline.md remains the source of truth for naming policy.

## Naming Rules

### Hosts

- aegisops-opensearch-node-01
- aegisops-n8n-node

### Compose Projects

- aegisops-opensearch

### OpenSearch Indexes

- aegisops-logs-windows-*
- aegisops-logs-saas-*
- aegisops-findings-*

### Detectors

- aegisops-windows-suspicious-powershell-high

### n8n Workflows

- aegisops_enrich_ip_reputation

### Environment Variables and Secrets

- AEGISOPS_OPENSEARCH_ADMIN_PASSWORD"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_saas_repo="${workdir}/missing-saas"
create_repo "${missing_saas_repo}"
write_doc "${missing_saas_repo}" "# AegisOps Contributor Naming Guide

## Purpose

Guide text.

## Baseline Source

docs/requirements-baseline.md remains the source of truth for naming policy.

## Naming Rules

### Hosts

- aegisops-opensearch-node-01
- aegisops-n8n-node

### Compose Projects

- aegisops-opensearch

### OpenSearch Indexes

- aegisops-logs-windows-*
- aegisops-findings-*

### Detectors

- aegisops-windows-suspicious-powershell-high

### n8n Workflows

- aegisops_enrich_ip_reputation

### Environment Variables and Secrets

- AEGISOPS_OPENSEARCH_ADMIN_PASSWORD"
commit_fixture "${missing_saas_repo}"
assert_fails_with "${missing_saas_repo}" "aegisops-logs-saas-*"

echo "verify-contributor-naming-guide-doc tests passed"
