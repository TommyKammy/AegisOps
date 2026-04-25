#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
runbook_path="${repo_root}/docs/wazuh-rule-lifecycle-runbook.md"

require_contains() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Wazuh rollback evidence gate text in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

if [[ ! -f "${runbook_path}" ]]; then
  echo "Missing Wazuh rule lifecycle runbook: ${runbook_path}" >&2
  exit 1
fi

required_evidence_text=(
  "Activation evidence must identify the candidate rule, reviewed fixture set, staging validation result, reviewer, activation window, expected alert volume, and release-gate evidence record."
  "Disable evidence must identify the disabled rule or candidate, disable owner, disable reason, affected fixture or parser evidence, operator notification path, and follow-up review."
  "Rollback evidence must identify the last reviewed rule revision, restored fixture set, rollback owner, rollback reason, validation rerun result, and AegisOps release-gate evidence record."
  "Detector evidence handoff must land in AegisOps-owned records and the retained release-gate evidence package before activation is treated as complete."
  "the release-gate evidence record that binds activation, disable, and rollback evidence to the current repository revision."
  "The gate must fail closed when provenance, scope, reviewer, owner, fixture, validation, false-positive, disable, rollback, or release-gate evidence is missing, malformed, placeholder, or inferred."
  "Operators must not infer activation success, disable completion, rollback completion, case closure, approval state, or reconciliation outcome from Wazuh rule state, alert count, source names, manager labels, or detector status alone."
)

for expected in "${required_evidence_text[@]}"; do
  require_contains "${runbook_path}" "${expected}"
done

echo "Wazuh rollback evidence gate preserves activation, disable, rollback, handoff, and authority-boundary evidence."
