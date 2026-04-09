#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
scope_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md"
validation_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-validation.md"
runtime_boundary_doc="${repo_root}/docs/control-plane-runtime-service-boundary.md"
architecture_doc="${repo_root}/docs/architecture.md"
network_doc="${repo_root}/docs/network-exposure-and-access-path-policy.md"
storage_doc="${repo_root}/docs/storage-layout-and-mount-policy.md"
compose_overview_doc="${repo_root}/docs/compose-skeleton-overview.md"
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

require_file "${scope_doc}" "Missing Phase 16 release-state scope document"
require_file "${validation_doc}" "Missing Phase 16 validation record"
require_file "${runtime_boundary_doc}" "Missing control-plane runtime boundary doc"
require_file "${architecture_doc}" "Missing architecture overview doc"
require_file "${network_doc}" "Missing network exposure policy doc"
require_file "${storage_doc}" "Missing storage layout policy doc"
require_file "${compose_overview_doc}" "Missing compose skeleton overview doc"
require_file "${readme_doc}" "Missing repository README"

scope_required_lines=(
  '# AegisOps Phase 16 Release-State and First-Boot Scope'
  '## 1. Purpose'
  '## 2. Approved Phase 16 Release-State'
  '## 3. First-Boot In-Scope Runtime Components'
  '## 4. First-Boot Explicitly Out of Scope'
  '## 5. Phase 16 Definition of Done'
  '## 6. Bootstrap Environment Contract'
  '## 7. Migration Bootstrap Contract'
  '## 8. Healthcheck and Readiness Contract'
  '## 9. Deployment-Entrypoint Contract'
  '## 10. Boundary and Alignment Notes'
  'This document defines the approved Phase 16 release-state and first-boot scope for bootable AegisOps.'
  'This document defines release-state and review scope only. It does not approve concrete containerization, live Wazuh integration wiring, analyst UI implementation, or broad runtime expansion beyond the first-boot boundary described here.'
  'The approved Phase 16 release-state is a repository baseline that is ready to enter Phase 17 runtime bring-up with one narrow bootability target.'
  '- the AegisOps control-plane service as the authoritative runtime boundary;'
  '- PostgreSQL as the AegisOps-owned persistence dependency for control-plane state;'
  '- the approved reverse proxy access boundary for controlled ingress; and'
  '- reviewed Wazuh-facing runtime expectations for upstream analytic-signal intake.'
  'Phase 16 release-state means those components are the required bootability floor.'
  'It does not mean every adjacent substrate tracked in the repository must boot on day one, and it does not redefine optional repository assets as mandatory first-boot dependencies.'
  'The first bootable AegisOps runtime includes the following in-scope components:'
  '- a live AegisOps control-plane service rooted under `control-plane/`;'
  '- the reviewed PostgreSQL boundary for AegisOps-owned control-plane records;'
  '- the approved reverse proxy path for controlled user-facing ingress and administrative exposure control; and'
  '- reviewed runtime expectations that the control-plane service can accept Wazuh-originated analytic-signal inputs without requiring Wazuh to become the authority for downstream alert, case, approval, or reconciliation truth.'
  'The first-boot scope is intentionally narrow.'
  'The following items are explicitly out of scope for the Phase 16 first-boot release-state:'
  '- optional OpenSearch extension runtime or OpenSearch-dependent first-boot success criteria;'
  '- n8n as a required first-boot dependency or orchestration prerequisite;'
  '- the full interactive analyst-assistant surface;'
  '- the high-risk executor path or write-capable response execution; and'
  '- broad source coverage beyond the narrow Wazuh-facing runtime expectation required for first boot.'
  'Phase 16 is done when the repository baseline unambiguously states that:'
  '- first boot requires the AegisOps control-plane service, PostgreSQL, and the approved reverse proxy boundary;'
  '- Wazuh-facing runtime expectations are limited to reviewed upstream analytic-signal intake expectations rather than live end-to-end substrate wiring;'
  '- OpenSearch, n8n, the full analyst-assistant surface, the high-risk executor, and broad source expansion remain optional, deferred, or non-blocking for first boot; and'
  '- later phases can use this document as the bootability target for Phase 17 runtime bring-up without reopening what counts as the minimum first-boot runtime.'
  'The first-boot bootstrap environment contract exists to keep Phase 17 runtime bring-up narrow, reviewable, and fail-closed.'
  'The required first-boot bootstrap inputs are:'
  '- `AEGISOPS_CONTROL_PLANE_HOST` for the control-plane bind host;'
  '- `AEGISOPS_CONTROL_PLANE_PORT` for the control-plane listen port;'
  '- `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` for the authoritative PostgreSQL connection string used by the control-plane runtime; and'
  '- repository-local runtime wiring needed to keep the reverse proxy on the approved ingress path instead of exposing backend services directly.'
  '`AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` is required bootstrap state for first boot.'
  '`AEGISOPS_CONTROL_PLANE_HOST` and `AEGISOPS_CONTROL_PLANE_PORT` may use reviewed local defaults only when those defaults preserve the approved reverse-proxy-first access model.'
  'Optional environment variables such as `AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL`, `AEGISOPS_CONTROL_PLANE_N8N_BASE_URL`, `AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL`, and `AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL` must not become first-boot prerequisites.'
  'If required bootstrap state is absent, malformed, contradictory, or would bypass the approved reverse proxy boundary, the runtime must fail closed and refuse first-boot startup rather than inferring a broader or less safe environment.'
  'Migration bootstrap is part of the first-boot contract because the control-plane runtime is not allowed to treat an unverified PostgreSQL schema as implicitly ready.'
  'The reviewed migration asset home remains `postgres/control-plane/migrations/`.'
  'First boot must run the reviewed forward migration set needed for the approved control-plane schema before the runtime is treated as ready to serve authoritative control-plane state.'
  'Migration bootstrap success means the required reviewed migration set completes without error and leaves the control-plane schema at the expected first-boot revision.'
  'Migration bootstrap failure includes missing migration assets, a PostgreSQL connection failure, an unapplied required migration, a partially applied migration set, or any schema mismatch that would make authoritative control-plane writes ambiguous.'
  'If migration bootstrap cannot prove the expected reviewed schema state, the deployment entrypoint must fail closed and refuse normal runtime startup.'
  'Phase 16 does not approve automatic destructive repair, downgrade behavior, or ad hoc schema recreation as a first-boot fallback.'
  'The first-boot runtime contract requires a narrow distinction between process liveness and readiness for authoritative control-plane work.'
  'Healthcheck success means the control-plane process is running and can answer a minimal self-health probe without asserting that dependencies are ready.'
  'Readiness success means the control-plane runtime has loaded valid required bootstrap environment, can reach PostgreSQL through `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`, and has confirmed migration bootstrap success for the approved first-boot schema state.'
  'Readiness must not depend on optional OpenSearch, n8n, Shuffle, or isolated-executor connectivity during the first-boot scope.'
  'If the runtime cannot prove required bootstrap state, PostgreSQL reachability, or reviewed migration completion, readiness must fail closed.'
  'The reverse proxy and any repository-local deployment surface must treat readiness failure as a refusal to admit normal traffic to the control-plane runtime.'
  'Any repository-local deployment entrypoint for first boot, including future Compose-backed bring-up, must preserve the approved control-plane, PostgreSQL, and reverse-proxy boundary instead of introducing a broader runtime dependency set.'
  'The deployment entrypoint must supply the reviewed required bootstrap environment, execute migration bootstrap before declaring readiness, and stop startup if the migration contract or readiness contract is not satisfied.'
  'The deployment entrypoint must not treat direct backend port publication, optional substrate availability, or placeholder repository defaults as acceptable substitutes for the approved first-boot contract.'
  'Compose or other repository-local boot surfaces may orchestrate startup order, but they must not redefine first-boot success to require OpenSearch, n8n, the analyst-assistant surface, or executor availability.'
  'Phase 16 therefore approves deployment-entrypoint expectations, not concrete image build details, health endpoint implementation, or live deployment automation.'
)

for line in "${scope_required_lines[@]}"; do
  require_fixed_string "${scope_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 16 Release-State and First-Boot Scope Validation'
  '- Validation date: 2026-04-09'
  '- Validation scope: Phase 16 review of the approved first-boot runtime boundary, required first-boot components, explicit non-blocking optional components, bootstrap-environment and migration-bootstrap requirements, healthcheck and readiness rules, deployment-entrypoint expectations, Wazuh-facing runtime expectations, and the definition of done that gates Phase 17 runtime bring-up'
  "- Baseline references: \`docs/phase-16-release-state-and-first-boot-scope.md\`, \`docs/control-plane-runtime-service-boundary.md\`, \`docs/architecture.md\`, \`docs/network-exposure-and-access-path-policy.md\`, \`docs/storage-layout-and-mount-policy.md\`, \`docs/compose-skeleton-overview.md\`, \`README.md\`"
  "- Verification commands: \`bash scripts/verify-phase-16-release-state-and-first-boot-scope.sh\`, \`bash scripts/test-verify-phase-16-release-state-and-first-boot-scope.sh\`"
  '- Validation status: PASS'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed Phase 16 now defines one approved bootability target for the first live AegisOps runtime instead of treating every tracked substrate as a first-boot dependency.'
  'Confirmed the required first-boot runtime is limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.'
  'Confirmed OpenSearch remains an optional extension rather than a mandatory first-boot dependency.'
  'Confirmed n8n remains optional or deferred and does not block the first bootable runtime target.'
  'Confirmed the full interactive analyst-assistant surface, the high-risk executor path, and broad source coverage remain outside the first-boot definition.'
  'Confirmed the bootstrap environment contract now makes `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` required first-boot state while keeping optional OpenSearch, n8n, Shuffle, and isolated-executor variables non-blocking for first boot.'
  'Confirmed the migration bootstrap contract requires the reviewed `postgres/control-plane/migrations/` asset set to succeed before authoritative runtime readiness is claimed and refuses destructive fallback or schema recreation shortcuts.'
  'Confirmed the healthcheck and readiness contract distinguishes process liveness from readiness and fails closed when required bootstrap state, PostgreSQL reachability, or reviewed migration completion cannot be proven.'
  'Confirmed the deployment-entrypoint contract keeps Compose or other repository-local boot surfaces limited to approved first-boot wiring and does not let optional substrates or direct backend exposure redefine success.'
  'Confirmed the Phase 16 definition of done gives Phase 17 a clear bootability target without approving concrete containerization or live substrate wiring in this phase.'
  "The issue requested review against \`Phase 16-21 Epic Roadmap.md\`, but that roadmap file was not present in the local worktree and could not be located via repository search during this turn."
  '`docs/compose-skeleton-overview.md` must continue to treat repository-tracked compose assets as placeholder-safe boot surfaces rather than as self-authorizing deployment truth.'
  "- Requested comparison target \`Phase 16-21 Epic Roadmap.md\` was unavailable in the local worktree during this validation snapshot."
)

for line in "${validation_required_lines[@]}"; do
  require_fixed_string "${validation_doc}" "${line}"
done

required_artifacts=(
  "docs/phase-16-release-state-and-first-boot-scope.md"
  "docs/phase-16-release-state-and-first-boot-validation.md"
  "docs/control-plane-runtime-service-boundary.md"
  "docs/architecture.md"
  "docs/network-exposure-and-access-path-policy.md"
  "docs/storage-layout-and-mount-policy.md"
  "docs/compose-skeleton-overview.md"
  "README.md"
  "scripts/verify-phase-16-release-state-and-first-boot-scope.sh"
  "scripts/test-verify-phase-16-release-state-and-first-boot-scope.sh"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 16 artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 16 validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

echo "Phase 16 release-state and first-boot scope remain explicit and reviewable."
