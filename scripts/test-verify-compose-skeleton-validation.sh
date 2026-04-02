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
    "${target}/postgres" \
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
- \`aegisops-postgres\`
- \`aegisops-ingest\`
- \`aegisops-proxy\`"
}

write_valid_network_policy() {
  local target="$1"

  write_file "${target}" "docs/network-exposure-and-access-path-policy.md" "# AegisOps Network Exposure and Access Path Policy

All user-facing UI access must traverse the approved reverse proxy.
Direct unaudited publication of service ports to general user networks or the public internet is not approved."
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

  write_file "${target}" "postgres/docker-compose.yml" "name: aegisops-postgres
services:
  postgres:
    image: postgres:16.4"

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

write_valid_env_samples() {
  local target="$1"

  write_file "${target}" ".env.sample" "# Sample environment file for repository structure only.
# Do not store real secrets or active environment values in this repository."

  write_file "${target}" "n8n/.env.sample" "# Sample environment placeholders for the n8n compose skeleton only.
# Do not use these placeholder values in production.

AEGISOPS_POSTGRES_PASSWORD=placeholder-not-a-secret
AEGISOPS_N8N_ENCRYPTION_KEY=placeholder-not-a-secret"

  write_file "${target}" "postgres/.env.sample" "# Sample environment placeholders for the PostgreSQL compose skeleton only.
# Do not use these placeholder values in production.

AEGISOPS_POSTGRES_PASSWORD=placeholder-not-a-secret"
}

write_valid_report() {
  local target="$1"

  write_file "${target}" "docs/compose-skeleton-validation.md" "# Compose Skeleton Validation

- Validation date: 2026-04-02
- Baseline references: \`docs/contributor-naming-guide.md\`, \`docs/requirements-baseline.md\`, \`docs/network-exposure-and-access-path-policy.md\`
- Verification command: \`bash scripts/verify-compose-skeleton-validation.sh\`
- Validation status: PASS

## Reviewed Artifacts

- \`.env.sample\`
- \`opensearch/docker-compose.yml\`
- \`n8n/docker-compose.yml\`
- \`n8n/.env.sample\`
- \`postgres/docker-compose.yml\`
- \`postgres/.env.sample\`
- \`proxy/docker-compose.yml\`
- \`ingest/docker-compose.yml\`

## Naming Review Result

- Compose project names use the approved \`aegisops-\` namespace examples from the contributor naming guide.
- Service names remain aligned to the component roles shown in the checked skeletons: \`opensearch\`, \`dashboards\`, \`n8n\`, \`postgres\`, \`proxy\`, \`collector\`, and \`parser\`.

## Image Tag Review Result

- No checked compose artifact uses the \`latest\` image tag.

## Secret and Env Review Result

- No checked compose or sample env artifact contains a live secret or production-sensitive value.
- No active \`.env\` file is committed; only tracked \`.env.sample\` placeholders are present.

## Exposure Review Result

- No checked compose skeleton publishes backend services directly with \`ports:\`.
- Backend access assumptions remain aligned to \`docs/network-exposure-and-access-path-policy.md\` and the approved reverse proxy or internal-only access model.

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
write_valid_network_policy "${valid_repo}"
write_valid_compose_files "${valid_repo}"
write_valid_env_samples "${valid_repo}"
write_valid_report "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_report_repo="${workdir}/missing-report"
create_repo "${missing_report_repo}"
write_valid_naming_guide "${missing_report_repo}"
write_valid_network_policy "${missing_report_repo}"
write_valid_compose_files "${missing_report_repo}"
write_valid_env_samples "${missing_report_repo}"
commit_fixture "${missing_report_repo}"
assert_fails_with "${missing_report_repo}" "Missing compose skeleton validation result document"

bad_project_name_repo="${workdir}/bad-project-name"
create_repo "${bad_project_name_repo}"
write_valid_naming_guide "${bad_project_name_repo}"
write_valid_network_policy "${bad_project_name_repo}"
write_valid_compose_files "${bad_project_name_repo}"
write_valid_env_samples "${bad_project_name_repo}"
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
write_valid_network_policy "${latest_tag_repo}"
write_valid_compose_files "${latest_tag_repo}"
write_valid_env_samples "${latest_tag_repo}"
write_file "${latest_tag_repo}" "proxy/docker-compose.yml" "name: aegisops-proxy
services:
  proxy:
    image: nginx:latest"
write_valid_report "${latest_tag_repo}"
commit_fixture "${latest_tag_repo}"
assert_fails_with "${latest_tag_repo}" "must not use the latest tag"

active_env_repo="${workdir}/active-env"
create_repo "${active_env_repo}"
write_valid_naming_guide "${active_env_repo}"
write_valid_network_policy "${active_env_repo}"
write_valid_compose_files "${active_env_repo}"
write_valid_env_samples "${active_env_repo}"
write_valid_report "${active_env_repo}"
write_file "${active_env_repo}" "n8n/.env" "AEGISOPS_POSTGRES_PASSWORD=supersecret"
commit_fixture "${active_env_repo}"
assert_fails_with "${active_env_repo}" "must not commit active .env files"

live_secret_repo="${workdir}/live-secret"
create_repo "${live_secret_repo}"
write_valid_naming_guide "${live_secret_repo}"
write_valid_network_policy "${live_secret_repo}"
write_valid_compose_files "${live_secret_repo}"
write_valid_env_samples "${live_secret_repo}"
write_file "${live_secret_repo}" "postgres/.env.sample" "# Sample environment placeholders for the PostgreSQL compose skeleton only.
# Do not use these placeholder values in production.

AEGISOPS_POSTGRES_PASSWORD=supersecret"
write_valid_report "${live_secret_repo}"
commit_fixture "${live_secret_repo}"
assert_fails_with "${live_secret_repo}" "must not contain live secret-looking values"

direct_exposure_repo="${workdir}/direct-exposure"
create_repo "${direct_exposure_repo}"
write_valid_naming_guide "${direct_exposure_repo}"
write_valid_network_policy "${direct_exposure_repo}"
write_valid_compose_files "${direct_exposure_repo}"
write_valid_env_samples "${direct_exposure_repo}"
write_file "${direct_exposure_repo}" "postgres/docker-compose.yml" "name: aegisops-postgres
services:
  postgres:
    image: postgres:16.4
    ports:
      - \"5432:5432\""
write_valid_report "${direct_exposure_repo}"
commit_fixture "${direct_exposure_repo}"
assert_fails_with "${direct_exposure_repo}" "must not publish backend services directly with ports"

echo "verify-compose-skeleton-validation tests passed"
