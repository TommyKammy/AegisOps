#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/phase-12-wazuh-ci-validation.md"
contract_doc="${repo_root}/docs/wazuh-alert-ingest-contract.md"
runbook_doc="${repo_root}/docs/wazuh-rule-lifecycle-runbook.md"
contract_doc_tests="${repo_root}/control-plane/tests/test_wazuh_alert_ingest_contract_docs.py"
adapter_tests="${repo_root}/control-plane/tests/test_wazuh_adapter.py"
service_tests="${repo_root}/control-plane/tests/test_service_persistence.py"
cli_tests="${repo_root}/control-plane/tests/test_cli_inspection.py"
workflow_path="${repo_root}/.github/workflows/ci.yml"

bash "${script_dir}/verify-wazuh-rule-lifecycle-runbook.sh" "${repo_root}"

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
    echo "Missing required Phase 12 test in ${file_path}: ${test_name}" >&2
    exit 1
  fi
}

require_file "${validation_doc}" "Missing Phase 12 Wazuh CI validation record"
require_file "${contract_doc}" "Missing Wazuh alert ingest contract document"
require_file "${runbook_doc}" "Missing Wazuh rule lifecycle runbook"
require_file "${contract_doc_tests}" "Missing Wazuh contract documentation tests"
require_file "${adapter_tests}" "Missing Wazuh adapter tests"
require_file "${service_tests}" "Missing control-plane service persistence tests"
require_file "${cli_tests}" "Missing control-plane CLI inspection tests"
require_file "${workflow_path}" "Missing CI workflow"

validation_required_phrases=(
  "# Phase 12 Wazuh Ingest and Workflow CI Validation"
  "- Validation date: 2026-04-07"
  "- Validation scope: Phase 12 review of Wazuh ingest contract coverage, fixture-backed admissions, alert and case lifecycle behavior, analyst queue invariants, and CI wiring for the reviewed Wazuh control-plane path"
  "- Baseline references: \`docs/wazuh-alert-ingest-contract.md\`, \`docs/wazuh-rule-lifecycle-runbook.md\`, \`control-plane/tests/test_wazuh_alert_ingest_contract_docs.py\`, \`control-plane/tests/test_wazuh_adapter.py\`, \`control-plane/tests/test_service_persistence.py\`, \`control-plane/tests/test_cli_inspection.py\`, \`.github/workflows/ci.yml\`"
  "- Verification commands: \`bash scripts/verify-wazuh-rule-lifecycle-runbook.sh\`, \`python3 -m unittest control-plane.tests.test_wazuh_alert_ingest_contract_docs control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection\`, \`bash scripts/test-verify-ci-phase-12-workflow-coverage.sh\`, \`bash scripts/verify-phase-12-wazuh-ci-validation.sh\`"
  "- Validation status: PASS"
  "## Required Boundary Artifacts"
  "## Review Outcome"
  "## Cross-Link Review"
  "## Deviations"
  'Confirmed the reviewed Wazuh ingest contract remains explicit about native identifier preservation, namespaced `substrate_detection_record_id` linkage, native timing preservation, and accountable source provenance.'
  "Confirmed fixture-backed Wazuh adapter coverage still admits both agent-origin and manager-origin alerts through the reviewed substrate-adapter boundary."
  "Confirmed the reviewed service persistence path still admits Wazuh-origin analytic signals, preserves restated case linkage, and exposes analyst queue records with Wazuh-native rule and accountable source context."
  "Confirmed analyst queue review keeps Wazuh-specific source precedence when multi-source linkage is present so queue routing does not drift away from the reviewed Phase 12 ingest path."
  "Confirmed the CLI inspection path still renders the read-only Wazuh business-hours analyst queue view from the same reviewed control-plane state."
  "Confirmed CI now runs a dedicated Phase 12 validation step and a workflow coverage guard so failures point to the reviewed Wazuh ingest and workflow boundary instead of only surfacing through broad suite discovery."
  '`docs/wazuh-alert-ingest-contract.md` must continue to define the reviewed Wazuh-native required fields, provenance set, and identifier mapping that the Phase 12 intake path preserves.'
  '`docs/wazuh-rule-lifecycle-runbook.md` must continue to require fixture refresh and aligned adapter and persistence tests before downstream workflow logic relies on a Wazuh rule change.'
  '`control-plane/tests/test_wazuh_alert_ingest_contract_docs.py` must continue to guard the reviewed Wazuh contract document and its required cross-links.'
  '`control-plane/tests/test_wazuh_adapter.py` must continue to guard fixture-backed Wazuh native-record and source-identity admission behavior.'
  '`control-plane/tests/test_service_persistence.py` must continue to guard Wazuh ingest admission, alert and case lifecycle linkage, and analyst queue invariants.'
  '`control-plane/tests/test_cli_inspection.py` must continue to guard the read-only Wazuh analyst queue inspection path.'
  '`.github/workflows/ci.yml` must continue to run the dedicated Phase 12 validation step, the focused Wazuh unit-test command, and the workflow coverage guard.'
  "No deviations found."
)

for phrase in "${validation_required_phrases[@]}"; do
  require_fixed_string "${validation_doc}" "${phrase}"
done

required_artifacts=(
  "docs/wazuh-alert-ingest-contract.md"
  "docs/wazuh-rule-lifecycle-runbook.md"
  "control-plane/tests/test_wazuh_alert_ingest_contract_docs.py"
  "control-plane/tests/test_wazuh_adapter.py"
  "control-plane/tests/test_service_persistence.py"
  "control-plane/tests/test_cli_inspection.py"
  ".github/workflows/ci.yml"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 12 artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 12 validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

require_fixed_string "${contract_doc}" '| `substrate_detection_record_id` | Set to `wazuh:<id>` unless the input is already namespaced as `wazuh:<id>`. This matches the shipped control-plane rule that substrate detection identifiers are namespaced by substrate key. |'
require_fixed_string "${runbook_doc}" 'At minimum, the fixture-backed review path must keep `control-plane/tests/test_wazuh_adapter.py` and `control-plane/tests/test_service_persistence.py` aligned with the reviewed rule behavior before downstream workflow logic can rely on it.'

require_test_name "${contract_doc_tests}" "test_wazuh_contract_doc_defines_required_mapping_and_ownership_terms"
require_test_name "${adapter_tests}" "test_adapter_builds_native_detection_record_from_agent_origin_fixture"
require_test_name "${adapter_tests}" "test_adapter_accepts_manager_origin_fixture_when_agent_identity_is_absent"
require_test_name "${service_tests}" "test_service_admits_wazuh_fixture_through_substrate_adapter_boundary"
require_test_name "${service_tests}" "test_service_extends_promoted_wazuh_alert_with_existing_case_linkage"
require_test_name "${service_tests}" "test_service_exposes_wazuh_origin_alerts_in_business_hours_analyst_queue"
require_test_name "${service_tests}" "test_service_analyst_queue_prefers_explicit_wazuh_source_for_multi_source_linkage"
require_test_name "${cli_tests}" "test_cli_renders_wazuh_business_hours_analyst_queue_view"

require_fixed_string "${workflow_path}" "      - name: Run Phase 12 workflow coverage guard"
require_fixed_string "${workflow_path}" "      - name: Run Phase 12 Wazuh validation"

echo "Phase 12 Wazuh ingest and workflow CI validation remains reviewable and fail closed."
