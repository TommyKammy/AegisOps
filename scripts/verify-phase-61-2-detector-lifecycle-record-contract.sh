#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-61-2-detector-lifecycle-record-contract.md"
validation_path="${repo_root}/docs/phase-61-2-detector-lifecycle-record-contract-validation.md"
policy_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
catalog_path="${repo_root}/docs/phase-61-minimum-source-catalog-contract.md"
test_path="${repo_root}/control-plane/tests/test_phase61_detector_lifecycle_record_contract.py"

for path in "${doc_path}" "${validation_path}" "${policy_path}" "${catalog_path}" "${test_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 61.2 artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 61.2 statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

required_doc_phrases=(
  '# AegisOps Phase 61.2 Detector Lifecycle Record Contract'
  '## 2. Approved Detector Lifecycle States'
  '## 4. Family and Catalog Binding'
  '## 5. Authoritative and Boundary Rules'
  '`candidate`'
  '`review-overdue`'
  'candidate → active'
  'No raw Wazuh replacement'
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}"
done

required_validation_phrases=(
  '# Phase 61.2 Detector Lifecycle Record Contract Validation'
  'Validation status: PASS'
  '## Non-goals kept in scope boundaries'
  'Verification commands:'
)

for phrase in "${required_validation_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

python3 -m unittest control-plane.tests.test_phase61_detector_lifecycle_record_contract

path_hygiene_stderr="${repo_root}/.tmp-phase61-2-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden absolute workstation-local path usage detected" >&2
  exit 1
fi

echo "Phase 61.2 detector lifecycle contract and focused tests pass."
