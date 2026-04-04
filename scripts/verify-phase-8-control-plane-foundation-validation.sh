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

require_substring() {
  local file_path="$1"
  local expected="$2"
  local message="$3"

  if ! grep -Fq -- "${expected}" "${file_path}" >/dev/null; then
    echo "${message} in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

require_file "${readme_path}" "Missing repository overview"
require_file "${structure_doc}" "Missing repository structure baseline"
require_file "${state_model_doc}" "Missing control-plane state model document"
require_file "${control_plane_readme}" "Missing control-plane schema skeleton README"
require_file "${schema_path}" "Missing control-plane schema skeleton manifest"
require_file "${migration_path}" "Missing control-plane schema skeleton migration"
require_file "${validation_doc}" "Missing Phase 8 control-plane foundation validation record"

validation_required_phrases=(
  "# Phase 8 Control-Plane MVP Foundation Validation"
  "- Validation date: 2026-04-04"
  "- Validation scope: Phase 8 control-plane MVP foundation review covering the baseline state model, placeholder PostgreSQL boundary, repository placement, and reviewer-facing cross-links for the future AegisOps-owned control-plane foundation"
  "- Baseline references: \`README.md\`, \`docs/control-plane-state-model.md\`, \`docs/repository-structure-baseline.md\`, \`postgres/control-plane/README.md\`, \`postgres/control-plane/schema.sql\`, \`postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql\`"
  "- Verification commands: \`bash scripts/verify-control-plane-state-model-doc.sh\`, \`bash scripts/verify-control-plane-schema-skeleton.sh\`, \`bash scripts/verify-phase-8-control-plane-foundation-validation.sh\`"
  "- Validation status: PASS"
  "## Required Foundation Artifacts"
  "## Review Outcome"
  "## Cross-Link Review"
  "## Deviations"
  "Confirmed the control-plane state model remains the normative source for ownership, source-of-truth boundaries, and future reconciliation duties before any live control-plane service or datastore exists."
  "Confirmed the repository reserves \`postgres/control-plane/\` as the reviewed placeholder home for future AegisOps-owned schema and migration assets without approving live deployment, credentials, or runtime migration execution."
  "Confirmed the placeholder PostgreSQL boundary stays explicitly separate from n8n-owned metadata and execution-state tables through the \`aegisops_control\` schema boundary and mirrored record-family placeholders, including reconciliation state."
  "Confirmed the placeholder schema contract now fails closed if executable live-ish DDL or seed data appears in \`postgres/control-plane/\`, while placeholder comments about future reviewed DDL remain allowed."
  "Confirmed the foundation artifact set keeps reviewer-facing alignment between the top-level repository description, the repository-structure baseline, the control-plane state model, and the placeholder PostgreSQL assets."
  "\`README.md\` must continue to describe the \`postgres/control-plane/\` directory as the repository home for placeholder control-plane schema assets so contributor-facing orientation stays aligned with the approved repository layout."
  "\`docs/repository-structure-baseline.md\` must continue to describe \`postgres/\` as the home for placeholder control-plane schema and migration assets and must keep the explicit \`control-plane/schema.sql\` and \`control-plane/migrations/\` reservation statement reviewable."
  "\`docs/control-plane-state-model.md\` must continue to cite \`postgres/control-plane/\` as the version-controlled placeholder home for the future boundary so the state-model baseline and repository skeleton stay cross-linked."
  "\`postgres/control-plane/README.md\`, \`postgres/control-plane/schema.sql\`, and \`postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql\` must continue to agree on the \`aegisops_control\` boundary and the placeholder homes for \`alert\`, \`case\`, \`evidence\`, \`observation\`, \`lead\`, \`recommendation\`, \`approval_decision\`, \`action_request\`, \`hunt\`, \`hunt_run\`, \`ai_trace\`, and \`reconciliation\` records."
  "\`postgres/control-plane/README.md\` and the schema-skeleton verifier must continue to make the fail-closed placeholder boundary reviewable by forbidding executable live-ish DDL while allowing placeholder comments that describe future reviewed DDL intent."
  "This validation record must remain aligned with the reviewed foundation artifacts above and fail closed if any required artifact, required cross-link, schema-boundary statement, or record-family placeholder alignment is removed."
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

require_fixed_string "${readme_path}" 'Within `postgres/`, the `control-plane/` directory reserves the repository home for placeholder AegisOps-owned control-plane schema and migration assets. It does not introduce a live datastore or runtime migration flow.'
require_fixed_string "${readme_path}" 'That placeholder boundary fails closed if executable live-ish control-plane DDL or seed data appears before explicit persistence approval.'
require_fixed_string "${structure_doc}" '| `postgres/` | PostgreSQL deployment assets such as compose definitions for the n8n metadata and execution-state store, plus placeholder schema and migration assets for the future AegisOps-owned control-plane boundary. |'
require_fixed_string "${structure_doc}" 'Within `postgres/`, placeholder files may reserve approved homes such as `control-plane/schema.sql` and `control-plane/migrations/` before any live control-plane service, credentials, or runtime migration execution is approved.'
require_fixed_string "${state_model_doc}" 'The repository may reserve a version-controlled placeholder home for that future boundary under `postgres/control-plane/`, including schema manifests and migration skeleton files that document reviewed record-family intent without claiming live readiness.'
require_fixed_string "${control_plane_readme}" 'The reserved schema boundary is `aegisops_control`, kept separate from n8n-owned PostgreSQL metadata and execution-state tables.'
require_fixed_string "${control_plane_readme}" 'Executable runtime-oriented SQL such as `CREATE TABLE`, `ALTER TABLE`, index creation, constraint DDL, and seed data is out of bounds for this placeholder-only directory until control-plane persistence implementation is explicitly approved.'
require_fixed_string "${control_plane_readme}" 'Placeholder comments may describe future reviewed DDL intent, but executable live-ish SQL must fail closed during validation.'

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
  require_fixed_string "${schema_path}" "-- table: ${family}_records"
  require_fixed_string "${migration_path}" "-- reserve table home: ${family}_records"
done

echo "Phase 8 control-plane foundation validation record and CI-facing artifact contract remain reviewable and fail closed."
