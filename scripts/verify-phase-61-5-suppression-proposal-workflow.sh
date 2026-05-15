#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
validation_path="${repo_root}/docs/phase-61-5-suppression-proposal-workflow-validation.md"
test_path="${repo_root}/control-plane/tests/test_phase61_detector_lifecycle_record_contract.py"
model_path="${repo_root}/control-plane/aegisops/control_plane/models.py"
validation_code_path="${repo_root}/control-plane/aegisops/control_plane/record_validation.py"
migration_path="${repo_root}/postgres/control-plane/migrations/0013_phase_61_detector_lifecycle_records.sql"

for path in \
  "${validation_path}" \
  "${test_path}" \
  "${model_path}" \
  "${validation_code_path}" \
  "${migration_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 61.5 suppression proposal artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 61.5 statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

required_validation_phrases=(
  '# Phase 61.5 Suppression Proposal Workflow Validation'
  'Validation status: PASS'
  'proposal-only AegisOps record'
  'finite expiry'
  'must not silently delete, hide, or suppress source signals'
  'Run `python3 -m unittest control-plane.tests.test_phase61_detector_lifecycle_record_contract`.'
)

for phrase in "${required_validation_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

required_test_names=(
  'test_suppression_proposal_record_is_proposal_only_and_reviewable'
  'test_suppression_proposal_rejects_uncited_ownerless_or_silent_suppression'
  'test_suppression_proposal_rejects_overbroad_permanent_or_applied_suppression'
  'test_restore_validation_rejects_suppression_proposal_without_detector_anchor'
)

for test_name in "${required_test_names[@]}"; do
  require_phrase "${test_path}" "${test_name}"
done

for phrase in \
  'class SuppressionProposalRecord' \
  'record_family: ClassVar[str] = "suppression_proposal"' \
  'expected_signal_impact' \
  'expires_at'; do
  require_phrase "${model_path}" "${phrase}"
done

for phrase in \
  '_validate_suppression_proposal_record' \
  '_SUPPRESSION_PROPOSAL_SCOPES' \
  'must set a finite expires_at' \
  'silently suppress'; do
  require_phrase "${validation_code_path}" "${phrase}"
done

for phrase in \
  'create table if not exists aegisops_control.suppression_proposal_records' \
  'preserve_source_signal' \
  'suppression_proposal'; do
  require_phrase "${migration_path}" "${phrase}"
done

(cd "${repo_root}" && python3 -m unittest control-plane.tests.test_phase61_detector_lifecycle_record_contract)

path_hygiene_stderr="${repo_root}/.tmp-phase61-5-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden absolute workstation-local path usage detected" >&2
  exit 1
fi

echo "Phase 61.5 suppression proposal workflow and focused tests pass."
