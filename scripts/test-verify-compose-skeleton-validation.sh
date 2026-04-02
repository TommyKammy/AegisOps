#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-compose-skeleton-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p \
    "${target}/docs" \
    "${target}/opensearch" \
    "${target}/n8n" \
    "${target}/proxy" \
    "${target}/ingest"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_file() {
  local target="$1"
  local path="$2"
  local content="$3"

  printf '%s\n' "${content}" >"${target}/${path}"
  git -C "${target}" add "${path}"
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit -q -m "fixture"
}

write_valid_naming_guide() {
  local target="$1"

  write_file "${target}" "docs/contributor-naming-guide.md" "# AegisOps Contributor Naming Guide

## Compose Projects

Examples:

- \`aegisops-opensearch\`
- \`aegisops-n8n\`
- \`aegisops-ingest\`
- \`aegisops-proxy\`"
}

write_valid_compose_files() {
  local target="$1"

  write_file "${target}" "opensearch/docker-compose.yml" "name: aegisops-opensearch
services:
  opensearch:
    image: opensearchproject/opensearch:2.19.0
  dashboards:
    image: opensearchproject/opensearch-dashboards:2.19.0"

  write_file "${target}" "n8n/docker-compose.yml" "name: aegisops-n8n
services:
  n8n:
    image: n8nio/n8n:1.89.2"

  write_file "${target}" "proxy/docker-compose.yml" "name: aegisops-proxy
services:
  proxy:
    image: nginx:1.27.0"

  write_file "${target}" "ingest/docker-compose.yml" "name: aegisops-ingest
services:
  collector:
    image: alpine:3.22.1
  parser:
    image: alpine:3.22.1"
}

write_valid_report() {
  local target="$1"

  write_file "${target}" "docs/compose-skeleton-validation.md" "# Compose Skeleton Validation

- Validation date: 2026-04-02
- Baseline references: \`docs/contributor-naming-guide.md\`, \`docs/requirements-baseline.md\`
- Verification command: \`bash scripts/verify-compose-skeleton-validation.sh\`
- Validation status: PASS

## Reviewed Artifacts

- \`opensearch/docker-compose.yml\`
- \`n8n/docker-compose.yml\`
- \`proxy/docker-compose.yml\`
- \`ingest/docker-compose.yml\`

## Naming Review Result

- Compose project names use the approved \`aegisops-\` namespace examples from the contributor naming guide.
- Service names remain aligned to the component roles shown in the checked skeletons: \`opensearch\`, \`dashboards\`, \`n8n\`, \`proxy\`, \`collector\`, and \`parser\`.

## Image Tag Review Result

- No checked compose artifact uses the \`latest\` image tag.

## Deviations

- No deviations found."
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
write_valid_naming_guide "${valid_repo}"
write_valid_compose_files "${valid_repo}"
write_valid_report "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_report_repo="${workdir}/missing-report"
create_repo "${missing_report_repo}"
write_valid_naming_guide "${missing_report_repo}"
write_valid_compose_files "${missing_report_repo}"
commit_fixture "${missing_report_repo}"
assert_fails_with "${missing_report_repo}" "Missing compose skeleton validation result document"

bad_project_name_repo="${workdir}/bad-project-name"
create_repo "${bad_project_name_repo}"
write_valid_naming_guide "${bad_project_name_repo}"
write_valid_compose_files "${bad_project_name_repo}"
write_file "${bad_project_name_repo}" "opensearch/docker-compose.yml" "name: opensearch
services:
  opensearch:
    image: opensearchproject/opensearch:2.19.0
  dashboards:
    image: opensearchproject/opensearch-dashboards:2.19.0"
write_valid_report "${bad_project_name_repo}"
commit_fixture "${bad_project_name_repo}"
assert_fails_with "${bad_project_name_repo}" "must use approved Compose project names"

latest_tag_repo="${workdir}/latest-tag"
create_repo "${latest_tag_repo}"
write_valid_naming_guide "${latest_tag_repo}"
write_valid_compose_files "${latest_tag_repo}"
write_file "${latest_tag_repo}" "proxy/docker-compose.yml" "name: aegisops-proxy
services:
  proxy:
    image: nginx:latest"
write_valid_report "${latest_tag_repo}"
commit_fixture "${latest_tag_repo}"
assert_fails_with "${latest_tag_repo}" "must not use the latest tag"

echo "verify-compose-skeleton-validation tests passed"
