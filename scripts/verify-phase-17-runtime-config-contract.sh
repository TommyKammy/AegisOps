#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
contract_doc="${repo_root}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
validation_doc="${repo_root}/docs/phase-17-runtime-config-contract-validation.md"
phase16_scope_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md"
runtime_boundary_doc="${repo_root}/docs/control-plane-runtime-service-boundary.md"
network_doc="${repo_root}/docs/network-exposure-and-access-path-policy.md"
storage_doc="${repo_root}/docs/storage-layout-and-mount-policy.md"
readme_doc="${repo_root}/README.md"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_fixed_string() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" "${file_path}" >/dev/null; then
    echo "Missing required line in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

require_file "${contract_doc}" "Missing Phase 17 runtime config contract doc"
require_file "${validation_doc}" "Missing Phase 17 validation record"
require_file "${phase16_scope_doc}" "Missing Phase 16 first-boot scope doc"
require_file "${runtime_boundary_doc}" "Missing control-plane runtime boundary doc"
require_file "${network_doc}" "Missing network exposure policy doc"
require_file "${storage_doc}" "Missing storage layout policy doc"
require_file "${readme_doc}" "Missing repository README"

contract_required_lines=(
  '# AegisOps Phase 17 Runtime Config Contract and Boot Command Expectations'
  '## 1. Purpose'
  '## 2. Phase 17 Contract Goal'
  '## 3. Runtime Config Contract'
  '### 3.1 Approved Required Runtime Environment Keys'
  '### 3.2 Approved Defaults and Fail-Closed Rules'
  '### 3.3 Approved Optional and Deferred Environment Keys'
  '## 4. Boot Command Expectations'
  '### 4.1 Control-Plane Service Process'
  '### 4.2 Migration Bootstrap Expectations'
  '### 4.3 Reverse-Proxy Exposure Model'
  '## 5. Phase 16 Placeholders That Become Concrete Runtime Expectations'
  '## 6. Alignment and Non-Expansion Rules'
  'The approved required runtime environment keys for Phase 17 first boot are:'
  '- `AEGISOPS_CONTROL_PLANE_HOST`'
  '- `AEGISOPS_CONTROL_PLANE_PORT`'
  '- `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`'
  '- `AEGISOPS_CONTROL_PLANE_BOOT_MODE`'
  '- `AEGISOPS_CONTROL_PLANE_LOG_LEVEL`'
  'If any required key is absent, empty, malformed, contradictory, or would violate the approved reverse-proxy-first exposure model, startup must fail closed.'
  '- `AEGISOPS_CONTROL_PLANE_HOST=127.0.0.1`'
  '- `AEGISOPS_CONTROL_PLANE_PORT=8080`'
  '- `AEGISOPS_CONTROL_PLANE_BOOT_MODE=first-boot`'
  '- `AEGISOPS_CONTROL_PLANE_LOG_LEVEL=INFO`'
  '`AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` has no approved repository default and must come from an untracked runtime secret source or operator-provided runtime env file.'
  '`AEGISOPS_CONTROL_PLANE_HOST` must fail closed if set to a wildcard or convenience value that would bypass the approved proxy boundary, including `0.0.0.0` for direct user-network publication in the first-boot path.'
  '`AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` must fail closed unless it is a PostgreSQL DSN for the AegisOps-owned control-plane datastore boundary.'
  'The approved optional and deferred environment keys remain:'
  '- `AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL`'
  '- `AEGISOPS_CONTROL_PLANE_N8N_BASE_URL`'
  '- `AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL`'
  '- `AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL`'
  'Their absence must not block control-plane startup, migration bootstrap, liveness, or readiness for the reviewed Phase 17 first-boot path.'
  'The reviewed boot command shape is:'
  '1. validate required runtime config'
  '2. validate the reviewed migration asset set'
  '3. prove PostgreSQL reachability'
  '4. apply the required forward migration bootstrap set'
  '5. verify the expected first-boot schema state'
  '6. exec the control-plane service process'
  'The boot command must not background the control-plane service process, split migration bootstrap into an undocumented sidecar, or report readiness before migration bootstrap succeeds.'
  'Migration bootstrap remains part of the approved normal boot sequence for `AEGISOPS_CONTROL_PLANE_BOOT_MODE=first-boot`.'
  'The reviewed migration asset home remains `postgres/control-plane/migrations/`.'
  'Any such failure must fail closed and stop the boot command before normal service admission.'
  'Phase 17 keeps the approved reverse proxy as the only reviewed user-facing ingress path.'
  'Repository-local boot surfaces must not publish the control-plane backend port directly to user networks or the public internet.'
  'The control-plane backend port must remain an internal service port.'
  'The following items remain deferred and must stay visibly out of the initial bring-up contract:'
  '- live Wazuh integration wiring;'
  '- optional OpenSearch extension wiring or OpenSearch-dependent readiness;'
  '- n8n, Shuffle, or executor connectivity as startup blockers;'
  '- the thin operator UI or analyst-assistant surface; and'
  '- destructive schema repair, downgrade logic, or ad hoc bootstrap shortcuts.'
  '`docs/phase-16-release-state-and-first-boot-scope.md` remains the normative source for the approved runtime floor.'
)

for line in "${contract_required_lines[@]}"; do
  require_fixed_string "${contract_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 17 Runtime Config Contract and Boot Command Validation'
  '- Validation date: 2026-04-10'
  '- Validation scope: Phase 17 review of the approved first-boot runtime config contract, required and optional environment keys, reviewed defaults, fail-closed boot behavior, migration-bootstrap sequencing, reverse-proxy-only exposure expectations, and explicit Phase 16-to-Phase 17 carry-forward boundaries'
  "- Baseline references: \`docs/phase-17-runtime-config-contract-and-boot-command-expectations.md\`, \`docs/phase-16-release-state-and-first-boot-scope.md\`, \`docs/control-plane-runtime-service-boundary.md\`, \`docs/network-exposure-and-access-path-policy.md\`, \`docs/storage-layout-and-mount-policy.md\`, \`README.md\`"
  "- Verification commands: \`bash scripts/verify-phase-17-runtime-config-contract.sh\`, \`bash scripts/test-verify-phase-17-runtime-config-contract.sh\`"
  '- Validation status: PASS'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed the Phase 17 contract makes the approved first-boot runtime environment keys explicit enough to drive image, Compose, and entrypoint implementation without reopening the approved runtime floor.'
  'Confirmed `AEGISOPS_CONTROL_PLANE_HOST`, `AEGISOPS_CONTROL_PLANE_PORT`, `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`, `AEGISOPS_CONTROL_PLANE_BOOT_MODE`, and `AEGISOPS_CONTROL_PLANE_LOG_LEVEL` are the approved required first-boot runtime keys and that startup must fail closed when they are absent, empty, malformed, contradictory, or exposure-bypassing.'
  'Confirmed the reviewed local defaults stay narrow by allowing `127.0.0.1`, `8080`, `first-boot`, and `INFO` while keeping `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` without a repository default.'
  'Confirmed the Phase 17 contract keeps `AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL`, `AEGISOPS_CONTROL_PLANE_N8N_BASE_URL`, `AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL`, and `AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL` explicitly optional and non-blocking for the first-boot path.'
  'Confirmed the approved boot command shape keeps migration bootstrap in the normal first-boot path by requiring runtime-config validation, migration-asset validation, PostgreSQL reachability proof, forward migration application, schema-state verification, and only then `exec` of the control-plane service process.'
  'Confirmed migration bootstrap failure remains fail-closed when reviewed migration assets are missing, PostgreSQL is unreachable, a forward migration fails, required migrations are only partially applied, or the expected reviewed schema state cannot be proven after execution.'
  'Confirmed the reverse proxy remains the only approved user-facing ingress path and that repository-local boot surfaces must not publish the control-plane backend port directly to user networks or the public internet.'
  'Confirmed the Phase 17 contract turns the reviewed Phase 16 first-boot skeleton environment keys, entrypoint sequencing, migration-home requirement, liveness-versus-readiness distinction, and reverse-proxy-first access model into concrete runtime expectations without making OpenSearch, n8n, Shuffle, executor wiring, thin UI work, or destructive schema shortcuts part of initial bring-up.'
  "The issue requested review against \`Phase 16-21 Epic Roadmap.md\`, but that roadmap file was not present in the local worktree and could not be located via repository search during this turn."
  '`docs/network-exposure-and-access-path-policy.md` must continue to keep the reverse proxy as the approved ingress boundary and disallow direct backend publication as a substitute.'
  "- Requested comparison target \`Phase 16-21 Epic Roadmap.md\` was unavailable in the local worktree during this validation snapshot."
)

for line in "${validation_required_lines[@]}"; do
  require_fixed_string "${validation_doc}" "${line}"
done

required_artifacts=(
  "docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
  "docs/phase-17-runtime-config-contract-validation.md"
  "docs/phase-16-release-state-and-first-boot-scope.md"
  "docs/control-plane-runtime-service-boundary.md"
  "docs/network-exposure-and-access-path-policy.md"
  "docs/storage-layout-and-mount-policy.md"
  "README.md"
  "scripts/verify-phase-17-runtime-config-contract.sh"
  "scripts/test-verify-phase-17-runtime-config-contract.sh"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 17 artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 17 validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

echo "Phase 17 runtime config contract remains explicit and reviewable."
