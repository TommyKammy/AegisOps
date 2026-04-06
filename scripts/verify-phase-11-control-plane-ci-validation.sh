#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/phase-11-control-plane-ci-validation.md"
state_model_doc="${repo_root}/docs/control-plane-state-model.md"
control_plane_readme="${repo_root}/control-plane/README.md"
service_tests="${repo_root}/control-plane/tests/test_service_persistence.py"
store_tests="${repo_root}/control-plane/tests/test_postgres_store.py"
cli_tests="${repo_root}/control-plane/tests/test_cli_inspection.py"
workflow_path="${repo_root}/.github/workflows/ci.yml"

bash "${script_dir}/verify-control-plane-state-model-doc.sh" "${repo_root}"

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

require_test_name() {
  local file_path="$1"
  local test_name="$2"

  if ! grep -Fq -- "def ${test_name}" "${file_path}" >/dev/null; then
    echo "Missing required Phase 11 test in ${file_path}: ${test_name}" >&2
    exit 1
  fi
}

require_file "${state_model_doc}" "Missing control-plane state model document"
require_file "${control_plane_readme}" "Missing control-plane runtime README"
require_file "${service_tests}" "Missing control-plane service persistence tests"
require_file "${store_tests}" "Missing control-plane PostgreSQL store tests"
require_file "${cli_tests}" "Missing control-plane CLI inspection tests"
require_file "${workflow_path}" "Missing CI workflow"
require_file "${validation_doc}" "Missing Phase 11 control-plane CI validation record"

validation_required_phrases=(
  "# Phase 11 Control-Plane Persistence and Vendor-Neutral CI Validation"
  "- Validation date: 2026-04-06"
  "- Validation scope: Phase 11 review of PostgreSQL-authoritative control-plane persistence, vendor-neutral analytic-signal and execution-surface coverage, and CI wiring for the reviewed local runtime and inspection paths"
  "- Baseline references: \`docs/control-plane-state-model.md\`, \`control-plane/README.md\`, \`control-plane/tests/test_service_persistence.py\`, \`control-plane/tests/test_postgres_store.py\`, \`control-plane/tests/test_cli_inspection.py\`, \`.github/workflows/ci.yml\`"
  "- Verification commands: \`bash scripts/verify-control-plane-state-model-doc.sh\`, \`python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_postgres_store control-plane.tests.test_cli_inspection\`, \`bash scripts/test-verify-ci-phase-11-workflow-coverage.sh\`, \`bash scripts/verify-phase-11-control-plane-ci-validation.sh\`"
  "- Validation status: PASS"
  "## Required Boundary Artifacts"
  "## Review Outcome"
  "## Cross-Link Review"
  "## Deviations"
  'Confirmed the reviewed runtime and inspection paths report `persistence_mode="postgresql"` and treat the PostgreSQL-backed control-plane store as the authoritative local persistence path.'
  'Confirmed analytic signals remain first-class control-plane records with durable `analytic_signal_id` and `substrate_detection_record_id` linkage instead of collapsing into alert-only state.'
  "Confirmed native detection intake remains constrained by explicit substrate-adapter boundaries and non-empty substrate-origin identifiers."
  'Confirmed reconciliation coverage preserves vendor-neutral `execution_surface_type`, `execution_surface_id`, and `execution_run_id` assumptions so the reviewed tests do not hard-code one automation substrate implementation.'
  "Confirmed CI now runs a dedicated Phase 11 validation step and a workflow coverage guard so failures point to this reviewed boundary instead of only surfacing through broad unit-test discovery."
  '`docs/control-plane-state-model.md` must continue to describe the reviewed local runtime as `persistence_mode="postgresql"` and the PostgreSQL-backed control-plane store as the authoritative local persistence path.'
  '`control-plane/README.md` must continue to describe the reviewed runtime and inspection commands as the authoritative local operator flow while keeping injected in-memory stores limited to tests and local doubles.'
  '`control-plane/tests/test_postgres_store.py` must continue to guard authoritative PostgreSQL persistence mode reporting.'
  '`control-plane/tests/test_service_persistence.py` must continue to guard substrate-adapter intake boundaries, first-class analytic-signal handling, and vendor-neutral execution-surface reconciliation.'
  '`control-plane/tests/test_cli_inspection.py` must continue to guard the reviewed runtime and inspection paths against PostgreSQL-backed read-only control-plane views.'
  '`.github/workflows/ci.yml` must continue to run the dedicated Phase 11 validation step, the focused Phase 11 unit-test command, and the workflow coverage guard.'
  "No deviations found."
)

for phrase in "${validation_required_phrases[@]}"; do
  require_fixed_string "${validation_doc}" "${phrase}"
done

required_artifacts=(
  "docs/control-plane-state-model.md"
  "control-plane/README.md"
  "control-plane/tests/test_service_persistence.py"
  "control-plane/tests/test_postgres_store.py"
  "control-plane/tests/test_cli_inspection.py"
  ".github/workflows/ci.yml"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 11 artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 11 validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

require_fixed_string "${state_model_doc}" 'The reviewed local control-plane runtime now reports `persistence_mode="postgresql"` and treats the PostgreSQL-backed control-plane store as the authoritative persistence path for local runtime and inspection flows, while `postgres/control-plane/` remains the reviewed schema and migration home and OpenSearch remains the analytics-plane store for telemetry and detection outputs.'
require_fixed_string "${control_plane_readme}" '- The runtime snapshot now reports `persistence_mode="postgresql"` so the reviewed control-plane runtime makes its authoritative store explicit.'
require_fixed_string "${control_plane_readme}" '- Those runtime and inspection commands now construct the same reviewed control-plane service path, so PostgreSQL-backed runtime configuration remains the authoritative local operator flow while injected in-memory stores stay limited to tests and local doubles.'

require_test_name "${store_tests}" "test_store_reports_postgresql_authoritative_persistence_mode"
require_test_name "${service_tests}" "test_service_admits_native_detection_records_via_substrate_adapter_boundary"
require_test_name "${service_tests}" "test_service_inspects_analytic_signal_records_as_first_class_records"
require_test_name "${service_tests}" "test_service_reconcile_action_execution_supports_generic_execution_surfaces"
require_test_name "${cli_tests}" "test_cli_renders_read_only_record_and_reconciliation_views"

require_fixed_string "${workflow_path}" "      - name: Run Phase 11 workflow coverage guard"
require_fixed_string "${workflow_path}" "      - name: Run Phase 11 control-plane validation"

echo "Phase 11 control-plane persistence and vendor-neutral CI validation remains reviewable and fail closed."
