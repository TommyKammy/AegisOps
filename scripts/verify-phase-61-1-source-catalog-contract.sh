#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-61-minimum-source-catalog-contract.md"
validation_path="${repo_root}/docs/phase-61-1-source-catalog-contract-validation.md"
policy_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
test_path="${repo_root}/control-plane/tests/test_phase61_source_catalog_contract.py"

for path in "${doc_path}" "${validation_path}" "${policy_path}" "${test_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 61 source catalog artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 61 source catalog statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

required_catalog_phrases=(
  '# AegisOps Phase 61.1 Minimum Source Catalog Contract'
  '## 2. Approved Source Catalog Entries'
  '## 5. Validation'
  '`wazuh_detection` (Wazuh manager and agent origin telemetry)'
  '`github_audit`'
  '`microsoft_365_audit`'
  '`entra_id`'
  '`windows_security_endpoint` (Windows endpoint detection-ready path)'
  'Reviewed owner'
  'Authority posture'
  'Evidence linkage'
  'Source-health requirements'
  'Explicit limitations'
  'This catalog must stay bounded to the five families above.'
  'The catalog must reject claims that broaden into marketplace'
  'No broad endpoint market'
  'No raw SIEM replacement'
  'Phase 62 automation breadth'
)

for phrase in "${required_catalog_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}"
done

required_validation_phrases=(
  '# Phase 61.1 Source Catalog Contract Validation'
  'Validation date:'
  'Phase 61.1 minimum source catalog contract'
  'Verification commands:'
  'Run `bash scripts/verify-phase-61-1-source-catalog-contract.sh`.'
  '- Validation status: PASS'
  '## Deviations'
  '- No deviations.'
)

for phrase in "${required_validation_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

(cd "${repo_root}" && python3 -m unittest control-plane.tests.test_phase61_source_catalog_contract) >/tmp/phase61_source_catalog_tests.out

path_hygiene_stderr="${repo_root}/.tmp-phase61-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 61 source catalog absolute path usage detected" >&2
  exit 1
fi

echo "Phase 61.1 source catalog contract and focused catalog tests pass."
