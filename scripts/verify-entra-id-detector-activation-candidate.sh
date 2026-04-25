#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
candidate_dir="${repo_root}/docs/source-families/entra-id/detector-activation-candidates"
candidate_doc="${candidate_dir}/privileged-role-assignment.md"
fixture_path="${repo_root}/control-plane/tests/fixtures/wazuh/entra-id-alert.json"
profile_test="${repo_root}/control-plane/tests/test_entra_id_detector_activation_candidate_docs.py"
microsoft_onboarding_doc="${repo_root}/docs/source-families/microsoft-365-audit/onboarding-package.md"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_contains() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing required text in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

require_single_candidate() {
  local count

  count="$(find "${candidate_dir}" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d '[:space:]')"
  if [[ "${count}" != "1" ]]; then
    echo "Expected exactly one Entra ID detector activation candidate, found ${count}." >&2
    exit 1
  fi
}

require_json_value() {
  local json_path="$1"
  local dotted_path="$2"
  local expected="$3"

  if ! python3 - "${json_path}" "${dotted_path}" "${expected}" <<'PY'
from __future__ import annotations

import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
current = payload
for part in sys.argv[2].split("."):
    current = current[part]

if str(current) != sys.argv[3]:
    raise SystemExit(1)
PY
  then
    echo "Fixture ${json_path} does not preserve ${dotted_path}=${expected}" >&2
    exit 1
  fi
}

require_file "${candidate_doc}" "Missing Entra ID detector activation candidate"
require_file "${fixture_path}" "Missing Entra ID fixture evidence"
require_file "${profile_test}" "Missing Entra ID detector activation candidate unittest"
require_file "${microsoft_onboarding_doc}" "Missing Microsoft 365 audit onboarding package"
require_single_candidate

required_candidate_text=(
  'Lifecycle state: `candidate`'
  "Candidate scope: Entra ID privileged directory role assignments."
  "Candidate Rule Review Criteria"
  "Fixture And Parser Evidence"
  '`control-plane/tests/fixtures/wazuh/entra-id-alert.json`'
  '`decoder.name` is `entra_id`'
  '`data.audit_action` is `Add member to role`'
  '`data.privilege.scope` is `directory_role`'
  '`data.privilege.permission` is `Global Administrator`'
  "Staging Activation Expectations"
  "False-Positive Review Expectations"
  "Rollback And Disable Procedure"
  "Entra ID remains source evidence only."
  "does not authorize direct Entra ID actioning"
  "does not make Entra ID the authority for AegisOps case state, approval state, action state, execution state, or reconciliation outcomes"
)

for expected in "${required_candidate_text[@]}"; do
  require_contains "${candidate_doc}" "${expected}"
done

require_contains "${microsoft_onboarding_doc}" 'Readiness state: `schema-reviewed`'
if grep -Fqx -- 'Readiness state: `detection-ready`' "${microsoft_onboarding_doc}" >/dev/null; then
  echo "Microsoft 365 audit must not be silently uplifted by the Entra ID detector candidate." >&2
  exit 1
fi

require_json_value "${fixture_path}" "decoder.name" "entra_id"
require_json_value "${fixture_path}" "rule.id" "entra-id-role-assignment"
require_json_value "${fixture_path}" "rule.description" "Entra ID privileged role assignment"
require_json_value "${fixture_path}" "data.source_family" "entra_id"
require_json_value "${fixture_path}" "data.audit_action" "Add member to role"
require_json_value "${fixture_path}" "data.operation" "Add member to role"
require_json_value "${fixture_path}" "data.record_type" "Entra ID audit"
require_json_value "${fixture_path}" "data.privilege.change_type" "role_assignment"
require_json_value "${fixture_path}" "data.privilege.scope" "directory_role"
require_json_value "${fixture_path}" "data.privilege.permission" "Global Administrator"
require_json_value "${fixture_path}" "data.privilege.role" "Privileged Role Administrator"
require_json_value "${fixture_path}" "data.tenant.id" "tenant-001"
require_json_value "${fixture_path}" "data.actor.id" "spn-operations"
require_json_value "${fixture_path}" "data.target.id" "role-global-admin"
require_json_value "${fixture_path}" "manager.name" "wazuh-manager-entra-1"
require_json_value "${fixture_path}" "data.correlation_id" "entra-corr-0001"
require_json_value "${fixture_path}" "data.request_id" "ENTRA-REQ-0001"

echo "Entra ID detector activation candidate remains fixture-backed, bounded, and source-evidence only."
