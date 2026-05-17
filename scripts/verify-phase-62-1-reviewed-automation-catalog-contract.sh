#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
catalog_path="${repo_root}/docs/phase-62-reviewed-automation-catalog-contract.md"
validation_path="${repo_root}/docs/phase-62-1-reviewed-automation-catalog-validation.md"
policy_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
test_path="${repo_root}/control-plane/tests/test_phase62_reviewed_automation_catalog_contract.py"

for path in "${catalog_path}" "${validation_path}" "${policy_path}" "${test_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 62.1 reviewed automation catalog artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 62.1 reviewed automation catalog statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

catalog_required_phrases=(
  '# AegisOps Phase 62.1 Reviewed Automation Catalog Contract'
  '## 3. Approved Default Catalog Entries'
  '| Catalog action | Family | Owner | Substrate mapping need | Required approval posture | Expected receipt shape | Reconciliation expectation | Allowed roles | Idempotency posture | Explicit limitations |'
  '| `enrichment_only_lookup` | Read |'
  '| `operator_notification` | Notify |'
  '| `manual_escalation_request` | Notify |'
  '| `create_tracking_ticket` | Soft Write |'
  'AegisOps execution receipt'
  'Idempotency key'
  'No direct ad-hoc Shuffle launch.'
  'This catalog must stay bounded to the four default entries above for Phase 62.1.'
  'The default catalog families are exactly Read, Notify, and Soft Write.'
  'Controlled Write and Hard Write are not default catalog families and must be rejected when marked as default entries.'
  'Unreviewed integrations, arbitrary SOAR connectors, broad SOAR marketplace language, template marketplace import, and broad Shuffle replacement claims are rejected.'
  'Run `python3 -m unittest control-plane.tests.test_phase62_reviewed_automation_catalog_contract`.'
)

for phrase in "${catalog_required_phrases[@]}"; do
  require_phrase "${catalog_path}" "${phrase}"
done

validation_required_phrases=(
  '# Phase 62.1 Reviewed Automation Catalog Contract Validation'
  'Validation date:'
  'Phase 62.1 reviewed automation catalog contract'
  '- Validation status: PASS'
  'Read: `enrichment_only_lookup`'
  'Notify: `operator_notification`, `manual_escalation_request`'
  'Soft Write: `create_tracking_ticket`'
  'Controlled Write and Hard Write default entries'
  '## Deviations'
  '- No deviations.'
)

for phrase in "${validation_required_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

catalog_table="$(
  awk '
    /^## 3\. Approved Default Catalog Entries$/ { in_section = 1; next }
    /^## 4\. Catalog Boundedness Rules$/ { in_section = 0 }
    in_section { print }
  ' "${catalog_path}"
)"

while IFS= read -r catalog_line; do
  if [[ ! "${catalog_line}" =~ ^\|[[:space:]]+\` ]]; then
    continue
  fi
  family="$(
    awk -F'|' '{ gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3 }' \
      <<<"${catalog_line}"
  )"
  if [[ "${family}" == "Controlled Write" || "${family}" == "Hard Write" ]]; then
    echo "Disallowed default Phase 62.1 catalog family for row: ${catalog_line}" >&2
    exit 1
  fi
done <<<"${catalog_table}"

require_catalog_row_field() {
  local action="$1"
  local expected="$2"
  if ! grep -F -- "| \`${action}\` |" <<<"${catalog_table}" | grep -Fq -- "${expected}"; then
    echo "Missing Phase 62.1 catalog row field for ${action}: ${expected}" >&2
    exit 1
  fi
}

for action in enrichment_only_lookup operator_notification manual_escalation_request create_tracking_ticket; do
  require_catalog_row_field "${action}" 'AegisOps execution receipt'
  require_catalog_row_field "${action}" 'Idempotency key'
  require_catalog_row_field "${action}" '`analyst`'
  require_catalog_row_field "${action}" '`approver`'
  require_catalog_row_field "${action}" 'No '
done

(cd "${repo_root}" && python3 -m unittest control-plane.tests.test_phase62_reviewed_automation_catalog_contract)

path_hygiene_stderr="${repo_root}/.tmp-phase62-automation-catalog-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 62.1 reviewed automation catalog absolute path usage detected" >&2
  exit 1
fi

echo "Phase 62.1 reviewed automation catalog contract and focused catalog tests pass."
