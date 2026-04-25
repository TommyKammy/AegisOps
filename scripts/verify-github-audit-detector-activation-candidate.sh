#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
candidate_dir="${repo_root}/docs/source-families/github-audit/detector-activation-candidates"
candidate_doc="${candidate_dir}/repository-admin-membership-change.md"
fixture_path="${repo_root}/control-plane/tests/fixtures/wazuh/github-audit-alert.json"
profile_test="${repo_root}/control-plane/tests/test_github_audit_detector_activation_candidate_docs.py"

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
    echo "Expected exactly one GitHub audit detector activation candidate, found ${count}." >&2
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

require_file "${candidate_doc}" "Missing GitHub audit detector activation candidate"
require_file "${fixture_path}" "Missing GitHub audit fixture evidence"
require_file "${profile_test}" "Missing GitHub audit detector activation candidate unittest"
require_single_candidate

required_candidate_text=(
  'Lifecycle state: `candidate`'
  "Candidate scope: GitHub audit repository administrator membership changes."
  "Candidate Rule Review Criteria"
  "Fixture And Parser Evidence"
  '`control-plane/tests/fixtures/wazuh/github-audit-alert.json`'
  '`decoder.name` is `github_audit`'
  '`data.audit_action` is `member.added`'
  '`data.privilege.permission` is `admin`'
  "Staging Activation Expectations"
  "False-Positive Review Expectations"
  "Rollback Expectations"
  "GitHub audit remains source evidence only."
  "does not authorize direct GitHub API actioning"
  "does not make GitHub the authority for AegisOps case state, approval state, action state, execution state, or reconciliation outcomes"
)

for expected in "${required_candidate_text[@]}"; do
  require_contains "${candidate_doc}" "${expected}"
done

require_json_value "${fixture_path}" "decoder.name" "github_audit"
require_json_value "${fixture_path}" "rule.id" "github-audit-privilege-change"
require_json_value "${fixture_path}" "rule.description" "GitHub audit repository privilege change"
require_json_value "${fixture_path}" "data.source_family" "github_audit"
require_json_value "${fixture_path}" "data.audit_action" "member.added"
require_json_value "${fixture_path}" "data.privilege.change_type" "membership_change"
require_json_value "${fixture_path}" "data.privilege.scope" "repository_admin"
require_json_value "${fixture_path}" "data.privilege.permission" "admin"
require_json_value "${fixture_path}" "data.privilege.role" "maintainer"
require_json_value "${fixture_path}" "manager.name" "wazuh-manager-github-1"
require_json_value "${fixture_path}" "data.request_id" "GH-REQ-0001"

echo "GitHub audit detector activation candidate remains fixture-backed, bounded, and source-evidence only."
