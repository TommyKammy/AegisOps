#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/phase-8-control-plane-foundation-validation.md"
readme_path="${repo_root}/README.md"
structure_doc="${repo_root}/docs/repository-structure-baseline.md"
state_model_doc="${repo_root}/docs/control-plane-state-model.md"
control_plane_readme="${repo_root}/postgres/control-plane/README.md"
schema_path="${repo_root}/postgres/control-plane/schema.sql"
migration_path="${repo_root}/postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"

bash "${script_dir}/verify-control-plane-state-model-doc.sh" "${repo_root}"
bash "${script_dir}/verify-control-plane-schema-skeleton.sh" "${repo_root}"

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
require_file "${structure_doc}" "Missing repository structure baseline"
require_file "${state_model_doc}" "Missing control-plane state model document"
require_file "${control_plane_readme}" "Missing control-plane schema README"
require_file "${schema_path}" "Missing control-plane schema manifest"
require_file "${migration_path}" "Missing control-plane schema migration"
require_file "${validation_doc}" "Missing Phase 8 control-plane foundation validation record"

validation_required_phrases=(
  "# Phase 8 Control-Plane MVP Foundation Validation"
  "- Validation date: 2026-04-05"
  "- Validation scope: Phase 8 control-plane MVP foundation review covering the baseline state model, the materialized PostgreSQL control-plane schema v1 boundary, repository placement, and reviewer-facing cross-links for the AegisOps-owned control-plane foundation"
  "- Baseline references: \`README.md\`, \`docs/control-plane-state-model.md\`, \`docs/repository-structure-baseline.md\`, \`postgres/control-plane/README.md\`, \`postgres/control-plane/schema.sql\`, \`postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql\`"
  "- Verification commands: \`bash scripts/verify-control-plane-state-model-doc.sh\`, \`bash scripts/verify-control-plane-schema-skeleton.sh\`, \`bash scripts/verify-phase-8-control-plane-foundation-validation.sh\`"
  "- Validation status: PASS"
  "## Required Foundation Artifacts"
  "## Review Outcome"
  "## Cross-Link Review"
  "## Deviations"
  "Confirmed the control-plane state model remains the normative source for ownership, source-of-truth boundaries, and future reconciliation duties."
  "Confirmed the repository now materializes \`postgres/control-plane/\` as the reviewed schema v1 home for AegisOps-owned control-plane records without authorizing live deployment, production data migration, or credentials."
  "Confirmed the PostgreSQL control-plane boundary stays explicitly separate from n8n-owned metadata and execution-state tables through the \`aegisops_control\` schema boundary and dedicated control-plane record families, including reconciliation state."
  "Confirmed the schema contract now requires executable reviewed table DDL, explicit lifecycle-state constraints, and reconciliation linkage instead of placeholder comments, while still rejecting seed data in version-controlled baseline assets."
  "Confirmed the foundation artifact set keeps reviewer-facing alignment between the top-level repository description, the repository-structure baseline, the control-plane state model, and the PostgreSQL control-plane baseline assets."
  "\`README.md\` must continue to describe \`postgres/control-plane/\` as the repository home for the reviewed control-plane schema baseline so contributor-facing orientation stays aligned with the approved repository layout."
  "\`docs/repository-structure-baseline.md\` must continue to describe \`postgres/\` as the home for the reviewed control-plane schema and migration baseline while keeping \`control-plane/\` separate as the live runtime application home."
  "\`docs/control-plane-state-model.md\` must continue to cite \`postgres/control-plane/\` as the version-controlled schema baseline home for the future boundary so the state-model baseline and repository skeleton stay cross-linked."
  "\`postgres/control-plane/README.md\`, \`postgres/control-plane/schema.sql\`, and \`postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql\` must continue to agree on the \`aegisops_control\` boundary and the materialized homes for \`alert\`, \`case\`, \`evidence\`, \`observation\`, \`lead\`, \`recommendation\`, \`approval_decision\`, \`action_request\`, \`hunt\`, \`hunt_run\`, \`ai_trace\`, and \`reconciliation\` records."
  "\`postgres/control-plane/README.md\` and the schema verifier must continue to make the runtime-ready v1 baseline reviewable while keeping future rollout, access-control, and index-tuning work explicit."
  "This validation record must remain aligned with the reviewed foundation artifacts above and fail closed if any required artifact, required cross-link, schema-boundary statement, or record-family alignment is removed."
  "No deviations found."
)

for phrase in "${validation_required_phrases[@]}"; do
  require_fixed_string "${validation_doc}" "${phrase}"
done

required_artifacts=(
  "README.md"
  "docs/control-plane-state-model.md"
  "docs/repository-structure-baseline.md"
  "postgres/control-plane/README.md"
  "postgres/control-plane/schema.sql"
  "postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 8 foundation artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 8 foundation validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

require_fixed_string "${readme_path}" 'Within `postgres/`, the `control-plane/` directory is the repository home for the reviewed AegisOps-owned control-plane schema baseline and migration assets. It does not authorize live deployment, production data migration, or credentials.'
require_fixed_string "${readme_path}" 'That schema boundary remains separate from n8n-owned PostgreSQL metadata and execution-state tables, and future rollout, access-control, and index-tuning work stays explicit.'
require_fixed_string "${structure_doc}" '| `postgres/` | PostgreSQL deployment assets such as compose definitions for the n8n metadata and execution-state store, plus the reviewed schema and migration baseline for the AegisOps-owned control-plane boundary. |'
require_fixed_string "${structure_doc}" 'Within `postgres/`, `control-plane/schema.sql` and `control-plane/migrations/` define the reviewed control-plane schema baseline while staying separate from runtime application code, live deployment approval, credentials, and production migration execution.'
require_fixed_string "${state_model_doc}" 'The repository may materialize a version-controlled schema baseline for that future boundary under `postgres/control-plane/`, including reviewed schema manifests and migration files that keep the approved record-family boundary explicit without authorizing live deployment, credentials, or production migration execution in this phase.'
require_fixed_string "${control_plane_readme}" 'The schema remains separate from n8n-owned PostgreSQL metadata and execution-state tables even when both live on the same engine class.'
require_fixed_string "${control_plane_readme}" 'These repository assets do not authorize live deployment, production data migration, or credentials.'
require_fixed_string "${control_plane_readme}" 'Future work remains explicit: online rollout sequencing, environment-specific access controls, stricter foreign-key enforcement across cyclic record families, and additional index tuning stay out of scope for this baseline.'

record_families=(
  "alert"
  "case"
  "evidence"
  "observation"
  "lead"
  "recommendation"
  "approval_decision"
  "action_request"
  "hunt"
  "hunt_run"
  "ai_trace"
  "reconciliation"
)

for family in "${record_families[@]}"; do
  require_fixed_string "${control_plane_readme}" "- \`${family}_records\`"
  require_fixed_string "${schema_path}" "create table if not exists aegisops_control.${family}_records ("
  require_fixed_string "${migration_path}" "create table if not exists aegisops_control.${family}_records ("
done

echo "Phase 8 control-plane foundation validation remains aligned with the materialized schema v1 baseline."
