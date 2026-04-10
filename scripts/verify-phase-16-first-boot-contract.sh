#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

scope_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md"
requirements_doc="${repo_root}/docs/requirements-baseline.md"
runtime_boundary_doc="${repo_root}/docs/control-plane-runtime-service-boundary.md"
runbook_doc="${repo_root}/docs/runbook.md"
readme_doc="${repo_root}/README.md"
bootstrap_env_sample="${repo_root}/control-plane/deployment/first-boot/bootstrap.env.sample"
compose_file="${repo_root}/control-plane/deployment/first-boot/docker-compose.yml"
entrypoint_file="${repo_root}/control-plane/deployment/first-boot/control-plane-entrypoint.sh"
migration_home="${repo_root}/postgres/control-plane/migrations"
postgres_readme="${repo_root}/postgres/control-plane/README.md"
postgres_schema="${repo_root}/postgres/control-plane/schema.sql"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_dir() {
  local path="$1"
  local message="$2"

  if [[ ! -d "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_fixed_string() {
  local file_path="$1"
  local expected="$2"
  local relative_path

  relative_path="${file_path#"${repo_root}/"}"
  if [[ "${relative_path}" == "${file_path}" ]]; then
    relative_path="${file_path}"
  fi

  if ! grep -Fqx -- "${expected}" "${file_path}" >/dev/null; then
    echo "Missing required line in ${relative_path}: ${expected}" >&2
    exit 1
  fi
}

require_absent_string() {
  local file_path="$1"
  local forbidden="$2"
  local message="$3"

  if grep -F -- "${forbidden}" "${file_path}" >/dev/null; then
    echo "${message}" >&2
    exit 1
  fi
}

require_file "${scope_doc}" "Missing Phase 16 scope document"
require_file "${requirements_doc}" "Missing requirements baseline doc"
require_file "${runtime_boundary_doc}" "Missing control-plane runtime boundary doc"
require_file "${runbook_doc}" "Missing runbook doc"
require_file "${readme_doc}" "Missing repository README"
require_file "${bootstrap_env_sample}" "Missing first-boot bootstrap env sample"
require_file "${compose_file}" "Missing first-boot compose skeleton"
require_file "${entrypoint_file}" "Missing first-boot entrypoint"
require_dir "${migration_home}" "Missing control-plane migration home"
require_file "${postgres_readme}" "Missing control-plane postgres README"
require_file "${postgres_schema}" "Missing control-plane schema baseline"

release_state_lines=(
  'That first-boot target is limited to the AegisOps control-plane service, PostgreSQL for control-plane state, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.'
  'OpenSearch, n8n, the full analyst-assistant surface, and the high-risk executor path remain optional, deferred, or non-blocking for first boot.'
)
for line in "${release_state_lines[@]}"; do
  require_fixed_string "${readme_doc}" "${line}"
done

requirements_lines=(
  'The approved Phase 16 first-boot target is limited to the AegisOps control-plane service, PostgreSQL for AegisOps-owned state, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.'
  'OpenSearch, n8n, the full analyst-assistant surface, the high-risk executor path, and broad source expansion remain optional, deferred, or non-blocking for first boot unless a later ADR approves a broader runtime floor.'
)
for line in "${requirements_lines[@]}"; do
  require_fixed_string "${requirements_doc}" "${line}"
done

runtime_boundary_lines=(
  'Within the approved Phase 16 release-state, the first-boot runtime target for this boundary is limited to the control-plane service, the reviewed PostgreSQL persistence dependency, the approved reverse proxy ingress boundary, and reviewed Wazuh-facing analytic-signal intake expectations.'
  'That first-boot target does not make OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path mandatory startup blockers.'
)
for line in "${runtime_boundary_lines[@]}"; do
  require_fixed_string "${runtime_boundary_doc}" "${line}"
done

runbook_lines=(
  'Until implementation-specific commands are approved, operators must treat first boot as limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.'
  'Operators must not treat optional OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path as first-boot prerequisites.'
)
for line in "${runbook_lines[@]}"; do
  require_fixed_string "${runbook_doc}" "${line}"
done

scope_lines=(
  '- `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` for the authoritative PostgreSQL connection string used by the control-plane runtime; and'
  'Optional environment variables such as `AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL`, `AEGISOPS_CONTROL_PLANE_N8N_BASE_URL`, `AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL`, and `AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL` must not become first-boot prerequisites.'
  'The reviewed migration asset home remains `postgres/control-plane/migrations/`.'
  'Readiness success means the control-plane runtime has loaded valid required bootstrap environment, can reach PostgreSQL through `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`, and has confirmed migration bootstrap success for the approved first-boot schema state.'
  'Compose or other repository-local boot surfaces may orchestrate startup order, but they must not redefine first-boot success to require OpenSearch, n8n, the analyst-assistant surface, or executor availability.'
)
for line in "${scope_lines[@]}"; do
  require_fixed_string "${scope_doc}" "${line}"
done

bootstrap_lines=(
  'AEGISOPS_CONTROL_PLANE_HOST=127.0.0.1'
  'AEGISOPS_CONTROL_PLANE_PORT=8080'
  'AEGISOPS_CONTROL_PLANE_POSTGRES_DSN=postgresql://<user>:<password>@postgres:5432/aegisops_control_plane'
  '# Optional and deferred components below must remain non-blocking for first boot.'
  'AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL='
  'AEGISOPS_CONTROL_PLANE_N8N_BASE_URL='
  'AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL='
  'AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL='
)
for line in "${bootstrap_lines[@]}"; do
  require_fixed_string "${bootstrap_env_sample}" "${line}"
done

compose_lines=(
  'name: aegisops-first-boot'
  '  control-plane:'
  '  postgres:'
  '  proxy:'
  '      - serve'
  '      AEGISOPS_CONTROL_PLANE_POSTGRES_DSN: ${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN:?set-in-untracked-runtime-env}'
  '      AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL: ${AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL:-}'
  '      AEGISOPS_CONTROL_PLANE_N8N_BASE_URL: ${AEGISOPS_CONTROL_PLANE_N8N_BASE_URL:-}'
  '      AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL: ${AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL:-}'
  '      AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL: ${AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL:-}'
  '      - ../../../postgres/control-plane/migrations:/opt/aegisops/postgres-migrations:ro'
  '    # optional extensions remain out of scope for this first-boot skeleton'
  '    # do not add OpenSearch, n8n, analyst-assistant UI, or executor services here'
)
for line in "${compose_lines[@]}"; do
  require_fixed_string "${compose_file}" "${line}"
done

require_absent_string "${compose_file}" '  opensearch:' \
  'First-boot compose must not define first-boot service: opensearch'
require_absent_string "${compose_file}" '  n8n:' \
  'First-boot compose must not define first-boot service: n8n'
require_absent_string "${compose_file}" '  analyst-assistant:' \
  'First-boot compose must not define first-boot service: analyst-assistant'
require_absent_string "${compose_file}" '  executor:' \
  'First-boot compose must not define first-boot service: executor'
require_absent_string "${compose_file}" '      - runtime' \
  'First-boot compose must not launch the one-shot runtime snapshot renderer.'

entrypoint_lines=(
  '# Phase 16 first-boot skeleton only.'
  'require_non_empty "AEGISOPS_CONTROL_PLANE_HOST" "${AEGISOPS_CONTROL_PLANE_HOST:-}"'
  'require_non_empty "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN" "${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN:-}"'
  '    echo "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN must be a PostgreSQL DSN for the first-boot skeleton." >&2'
  '    echo "AEGISOPS_CONTROL_PLANE_PORT must be an integer for the first-boot skeleton." >&2'
  'MIGRATIONS_DIR="${AEGISOPS_FIRST_BOOT_MIGRATIONS_DIR:-/opt/aegisops/postgres-migrations}"'
  'PSQL_BIN="${AEGISOPS_FIRST_BOOT_PSQL_BIN:-psql}"'
  '        fail_closed "First-boot migration bootstrap requires psql to prove PostgreSQL reachability and readiness."'
  '      fail_closed "First-boot migration bootstrap is missing reviewed migration asset: ${migration_name}"'
  '      fail_closed "First-boot migration bootstrap failed while applying ${migration_name}: ${migration_output}"'
  '    fail_closed "First-boot readiness proof failed during PostgreSQL verification: ${readiness_output}"'
  '    fail_closed "First-boot readiness proof failed: migration bootstrap could not prove the expected reviewed schema state."'
  '# OpenSearch, n8n, the full analyst-assistant surface, and executor wiring remain deferred.'
  'exec "$@"'
)
for line in "${entrypoint_lines[@]}"; do
  require_fixed_string "${entrypoint_file}" "${line}"
done

postgres_lines=(
  'This directory reserves the reviewed repository home for future AegisOps-owned control-plane schema and migration assets.'
  'These repository assets do not authorize live deployment, production data migration, or credentials.'
)
for line in "${postgres_lines[@]}"; do
  require_fixed_string "${postgres_readme}" "${line}"
done

for migration_file in \
  "0001_control_plane_schema_skeleton.sql" \
  "0002_phase_14_reviewed_context_columns.sql" \
  "0003_phase_15_assistant_advisory_draft_columns.sql"; do
  require_file "${migration_home}/${migration_file}" "Missing reviewed control-plane migration asset"
done

echo "Phase 16 release-state and first-boot contract remain aligned."
