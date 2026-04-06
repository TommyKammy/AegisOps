#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/phase-9-control-plane-runtime-boundary-validation.md"
readme_path="${repo_root}/README.md"
architecture_doc="${repo_root}/docs/architecture.md"
state_model_doc="${repo_root}/docs/control-plane-state-model.md"
boundary_doc="${repo_root}/docs/control-plane-runtime-service-boundary.md"
structure_doc="${repo_root}/docs/repository-structure-baseline.md"
runtime_readme="${repo_root}/control-plane/README.md"
postgres_readme="${repo_root}/postgres/control-plane/README.md"

bash "${script_dir}/verify-control-plane-runtime-service-boundary-doc.sh" "${repo_root}"
bash "${script_dir}/verify-control-plane-runtime-skeleton.sh" "${repo_root}"
bash "${script_dir}/verify-repository-structure-doc.sh" "${repo_root}"
bash "${script_dir}/verify-repository-skeleton.sh" "${repo_root}"

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

require_file "${readme_path}" "Missing repository overview"
require_file "${architecture_doc}" "Missing architecture overview"
require_file "${state_model_doc}" "Missing control-plane state model"
require_file "${boundary_doc}" "Missing control-plane runtime boundary document"
require_file "${structure_doc}" "Missing repository structure baseline"
require_file "${runtime_readme}" "Missing control-plane runtime README"
require_file "${postgres_readme}" "Missing PostgreSQL control-plane README"
require_file "${validation_doc}" "Missing Phase 9 control-plane runtime boundary validation record"

validation_required_phrases=(
  '# Phase 9 Control-Plane Runtime Boundary Validation'
  '- Validation date: 2026-04-05'
  '- Validation scope: Phase 9 control-plane runtime-boundary review covering the approved live service boundary, top-level repository placement, persistence-contract separation, and explicit Phase 9 scope limits'
  '- Baseline references: `README.md`, `docs/architecture.md`, `docs/control-plane-state-model.md`, `docs/control-plane-runtime-service-boundary.md`, `docs/repository-structure-baseline.md`, `control-plane/README.md`, `postgres/control-plane/README.md`'
  '- Verification commands: `bash scripts/verify-control-plane-runtime-service-boundary-doc.sh`, `bash scripts/verify-control-plane-runtime-skeleton.sh`, `bash scripts/verify-repository-structure-doc.sh`, `bash scripts/verify-repository-skeleton.sh`, `bash scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh`'
  '- Validation status: PASS'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed the repository now reserves `control-plane/` as the approved live application home for the first AegisOps-owned control-plane service.'
  'Confirmed `postgres/control-plane/` remains the reviewed persistence-contract home for schema and migration assets rather than the repository home for runtime application code.'
  'Confirmed the runtime-boundary document keeps OpenSearch as the analytics and detection plane, keeps n8n as the execution plane, and defines the control-plane service as the authoritative owner of AegisOps platform records and reconciliation behavior.'
  'Confirmed the approved Phase 9 slice includes only the minimum internal control-plane runtime needed to materialize authoritative state and reconcile against external systems.'
  'Confirmed analyst UI, live telemetry expansion, AI runtime, and write-capable response execution remain explicitly out of scope for this boundary.'
  '`README.md` must continue to describe `control-plane/` as the live application home and `postgres/control-plane/` as the separate persistence-contract home.'
  '`docs/architecture.md` must continue to define the AegisOps control plane as the authoritative owner of the policy-sensitive path across substrate boundaries.'
  '`docs/control-plane-state-model.md` must continue to define the ownership split that the runtime-boundary document implements.'
  '`docs/control-plane-runtime-service-boundary.md` must continue to define the approved runtime responsibilities, repository placement, Phase 9 scope, and explicit non-goals for the first live control-plane service.'
  '`docs/repository-structure-baseline.md` must continue to describe `control-plane/` as the approved top-level repository home for live control-plane application code while keeping `postgres/` as the PostgreSQL deployment and persistence-contract area.'
  '`control-plane/README.md` and `postgres/control-plane/README.md` must continue to preserve the split between runtime application code and persistence-contract assets.'
  'No deviations found.'
)

for phrase in "${validation_required_phrases[@]}"; do
  require_fixed_string "${validation_doc}" "${phrase}"
done

required_artifacts=(
  "README.md"
  "docs/architecture.md"
  "docs/control-plane-state-model.md"
  "docs/control-plane-runtime-service-boundary.md"
  "docs/repository-structure-baseline.md"
  "control-plane/README.md"
  "postgres/control-plane/README.md"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 9 boundary artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 9 boundary validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

require_fixed_string "${readme_path}" '- **Control Plane Runtime** — future authoritative AegisOps service boundary for platform state and reconciliation'
require_fixed_string "${readme_path}" 'Within `control-plane/`, the first live AegisOps-owned control-plane runtime will live as application code and service-local tests.'
require_fixed_string "${readme_path}" 'Within `postgres/`, the `control-plane/` directory reserves the repository home for placeholder AegisOps-owned control-plane schema and migration assets. It does not introduce a live datastore or runtime migration flow.'
require_fixed_string "${architecture_doc}" 'The AegisOps control plane is the authoritative owner of policy-sensitive records, approval decisions, evidence linkage, action intent, and reconciliation truth across substrate boundaries.'
require_fixed_string "${structure_doc}" '| `control-plane/` | Live AegisOps control-plane application code, service bootstrapping, adapters, tests, and service-local documentation for the approved runtime boundary. |'
require_fixed_string "${runtime_readme}" 'This directory is the approved repository home for live AegisOps control-plane application code.'
require_fixed_string "${postgres_readme}" 'This directory reserves the reviewed repository home for future AegisOps-owned control-plane schema and migration assets.'

echo "Phase 9 control-plane runtime boundary validation record and cross-links remain reviewable and fail closed."
