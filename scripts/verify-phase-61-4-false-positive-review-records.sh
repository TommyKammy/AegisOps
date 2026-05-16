#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
validation_path="${repo_root}/docs/phase-61-4-false-positive-review-records-validation.md"
test_path="${repo_root}/control-plane/tests/test_phase61_detector_lifecycle_record_contract.py"
model_path="${repo_root}/control-plane/aegisops/control_plane/models.py"
validation_code_path="${repo_root}/control-plane/aegisops/control_plane/phase61_record_validators.py"
migration_path="${repo_root}/postgres/control-plane/migrations/0013_phase_61_detector_lifecycle_records.sql"

for path in \
  "${validation_path}" \
  "${test_path}" \
  "${model_path}" \
  "${validation_code_path}" \
  "${migration_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 61.4 false-positive review artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 61.4 statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

required_validation_phrases=(
  '# Phase 61.4 False-Positive Review Records Validation'
  'Validation status: PASS'
  'False-positive review records may inform detector review and triage.'
  'must not silently delete or hide source signals'
  'Run `python3 -m unittest control-plane.tests.test_phase61_detector_lifecycle_record_contract`.'
)

for phrase in "${required_validation_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

required_test_names=(
  'test_false_positive_review_records_cover_normal_disputed_and_repeated_cases'
  'test_false_positive_review_rejects_missing_authoritative_links'
  'test_false_positive_review_rejects_uncited_or_silent_source_suppression'
  'test_false_positive_review_rejects_disputed_or_repeated_as_final_truth'
  'test_false_positive_review_record_is_registered_in_service_registries'
)

for test_name in "${required_test_names[@]}"; do
  require_phrase "${test_path}" "${test_name}"
done

for phrase in \
  'class FalsePositiveReviewRecord' \
  'record_family: ClassVar[str] = "false_positive_review"' \
  'source_signal_handling'; do
  require_phrase "${model_path}" "${phrase}"
done

for phrase in \
  '_validate_false_positive_review_record' \
  'may not delete, hide, or silently suppress source-native truth' \
  'repeated false positives'; do
  require_phrase "${validation_code_path}" "${phrase}"
done

for phrase in \
  'create table if not exists aegisops_control.false_positive_review_records' \
  'preserve_source_signal' \
  'false_positive_review'; do
  require_phrase "${migration_path}" "${phrase}"
done

(cd "${repo_root}" && python3 -m unittest control-plane.tests.test_phase61_detector_lifecycle_record_contract)

path_hygiene_stderr="${repo_root}/.tmp-phase61-4-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden absolute workstation-local path usage detected" >&2
  exit 1
fi

echo "Phase 61.4 false-positive review records and focused tests pass."
