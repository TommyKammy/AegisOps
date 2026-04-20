#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
validation_doc="${repo_root}/docs/phase-29-reviewed-ml-shadow-mode-and-optional-network-evidence-pack-validation.md"
docs_test="${repo_root}/control-plane/tests/test_phase29_no_authority_ml_and_optional_network_validation.py"
suricata_doc="${repo_root}/docs/phase-29-optional-suricata-evidence-pack-boundary.md"
ml_doc="${repo_root}/docs/phase-29-reviewed-ml-shadow-mode-boundary.md"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_fixed_line() {
  local path="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" "${path}" >/dev/null; then
    echo "Missing required line in ${path}: ${expected}" >&2
    exit 1
  fi
}

require_file "${validation_doc}" "Missing Phase 29 combined validation doc"
require_file "${docs_test}" "Missing Phase 29 combined validation unittest"
require_file "${suricata_doc}" "Missing Phase 29 optional network boundary doc"
require_file "${ml_doc}" "Missing Phase 29 ML shadow-mode boundary doc"

validation_required_lines=(
  '# Phase 29 Reviewed ML Shadow-Mode and Optional Network Evidence-Pack Validation'
  '- Validation status: PASS'
  '- Reviewed on: 2026-04-20'
  '## Validation Summary'
  '## Authority Boundary Review'
  '## ML Shadow-Mode Review'
  '## Optional Network Evidence-Pack Review'
  '## Review Outcome'
  '## Verification'
  'ML scores, drift surfaces, and shadow recommendations remain advisory-only and non-authoritative.'
  'Optional network evidence remains disabled by default, subordinate, and unable to become alert, case, approval, execution, or reconciliation truth.'
  'Missing provenance, missing labels, stale features, drift alarms, disabled optional-network paths, and optional-network outage paths all fail closed or degrade explicitly.'
  '- `python3 -m unittest control-plane.tests.test_phase29_no_authority_ml_and_optional_network_validation`'
  '- `bash scripts/verify-phase-29-reviewed-ml-shadow-mode-and-optional-network-evidence-pack.sh`'
)

for line in "${validation_required_lines[@]}"; do
  require_fixed_line "${validation_doc}" "${line}"
done

docs_test_required_lines=(
  'class Phase29NoAuthorityMlAndOptionalNetworkValidationTests(ServicePersistenceTestBase):'
  '    def test_shadow_outputs_and_optional_network_context_stay_non_authoritative(self) -> None:'
  '    def test_shadow_scoring_fails_closed_when_label_provenance_is_missing(self) -> None:'
  '    def test_optional_network_boundary_docs_and_validation_artifacts_exist(self) -> None:'
)

for line in "${docs_test_required_lines[@]}"; do
  require_fixed_line "${docs_test}" "${line}"
done

require_fixed_line "${suricata_doc}" 'Suricata integration is optional, disabled by default, and subordinate to the AegisOps-owned control-plane record chain.'
require_fixed_line "${ml_doc}" 'The reviewed ML shadow-mode boundary must keep ML advisory-only and must remain outside the authority path for alert admission, approval grant or reject, delegation, execution policy, reconciliation truth, and case truth promotion.'

echo "Phase 29 ML shadow-mode and optional network validation artifacts are present and aligned."
