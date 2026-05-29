#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

adapter_path="${repo_root}/control-plane/aegisops/control_plane/evidence/osquery_evidence_adapter.py"
test_path="${repo_root}/control-plane/tests/test_phase63_3_osquery_evidence_adapter.py"
doc_path="${repo_root}/docs/phase-63-3-osquery-evidence-adapter.md"
validation_path="${repo_root}/docs/phase-63-3-osquery-evidence-adapter-validation.md"
request_path="${repo_root}/docs/phase-63-2-reviewed-evidence-request-records.md"
registry_path="${repo_root}/docs/phase-63-1-evidence-source-registry-v1.md"
policy_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"

for path in "${adapter_path}" "${test_path}" "${doc_path}" "${validation_path}" "${request_path}" "${registry_path}" "${policy_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 63.3 osquery evidence adapter artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 63.3 osquery evidence adapter statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

required_adapter_phrases=(
  'OsqueryEvidenceAdapter'
  'OsqueryEvidenceAdapterInput'
  'OsqueryEvidencePack'
  'validate_phase63_reviewed_evidence_request'
  'PHASE63_EVIDENCE_SOURCE_REGISTRY'
  '"osquery_host_state"'
  '"subordinate_evidence_context_only"'
  '"adapter_unavailable"'
  '"stale_collection"'
  '"osquery adapter is read-only"'
  '"host_identifier must match reviewed request target"'
  '"missing_osquery_custody"'
  '_ACTIVE_REVIEWED_REQUEST_STATES = frozenset({"reviewed", "approved", "active"})'
  '"reviewed evidence request lifecycle_state must be active"'
  'max_rows: int = 500'
  'max_columns: int = 128'
  'max_column_name_bytes: int = 256'
  'max_cell_bytes: int = 4096'
  '"query_id must match osquery custody reviewed_query_id"'
  '"osquery custody collection_timestamp must match collected_at"'
  '"osquery evidence pack must contain JSON-serializable finite values"'
)

for phrase in "${required_adapter_phrases[@]}"; do
  require_phrase "${adapter_path}" "${phrase}"
done

required_test_phrases=(
  'test_normal_osquery_result_builds_subordinate_evidence_pack'
  'test_stale_osquery_output_is_degraded_not_truth'
  'test_unavailable_adapter_returns_unavailable_pack'
  'test_malformed_output_is_rejected'
  'test_query_id_must_match_reviewed_custody'
  'test_custody_collection_timestamp_must_match_collected_at'
  'test_large_result_sets_are_rejected_before_pack_serialization'
  'test_large_column_sets_are_rejected_before_pack_serialization'
  'test_large_column_names_are_rejected_before_pack_serialization'
  'test_large_cell_values_are_rejected_before_pack_serialization'
  'test_non_finite_row_values_are_rejected_before_pack_return'
  'test_malformed_custody_extras_are_rejected_before_pack_return'
  'test_unauthorized_request_fails_closed'
  'test_terminal_evidence_request_states_fail_closed'
  'test_target_mismatch_fails_closed'
  'test_missing_custody_fails_closed'
  'test_no_remediation_or_direct_command_authority'
)

for phrase in "${required_test_phrases[@]}"; do
  require_phrase "${test_path}" "${phrase}"
done

required_doc_phrases=(
  '# AegisOps Phase 63.3 Osquery Evidence Adapter MVP'
  'The adapter turns reviewed osquery host-state, process-context, and state-context output into subordinate evidence packs only after a reviewed Phase 63 evidence request record binds the case, target host, source, scope, custody, authorization, and expiry.'
  'The MVP result kinds are `host_state`, `process`, and `state_context`.'
  'Osquery output older than the registry freshness window returns a `degraded` pack with `stale_collection`.'
  'Unavailable adapter state returns an `unavailable` pack with `adapter_unavailable` and no rows.'
  'The adapter rejects osquery output whose `query_id` does not match the reviewed query id in custody. It also requires custody `collection_timestamp` to parse as a timezone-aware timestamp and match `collected_at`.'
  'Osquery rows are bounded before whole-pack serialization: at most 500 rows, 128 distinct columns, 256 bytes per serialized column name, and 4096 bytes per serialized cell value.'
  'Malformed rows, oversized rows, oversized column names, non-finite row values, malformed custody extras, unsupported result kinds, unauthorized, terminal, or expired reviewed requests, target mismatch, missing custody, custody query mismatch, custody host mismatch, custody timestamp mismatch, naive timestamps, and non-read-only operations fail closed.'
  'Osquery output, evidence packs, source-native state, freshness projections, AI output, verifier output, issue-lint output, browser state, UI cache, and adapter state remain subordinate context only.'
  'The adapter cannot approve, execute, reconcile, close, activate detectors, create source truth, gate release, claim readiness, remediate endpoints, contain hosts, quarantine files, kill processes, mutate protected targets, or issue direct command authority.'
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}"
done

required_validation_phrases=(
  '# Phase 63.3 Osquery Evidence Adapter Validation'
  'Validation status: PASS'
  'The focused adapter test suite accepts a normal reviewed osquery host-state result and rejects or degrades the requested boundary cases: stale output, unavailable adapter state without rows, malformed rows, oversized rows, oversized column sets, oversized column names, oversized cell values, non-finite row values, unauthorized reviewed request, terminal reviewed request states, mismatched target host, query id custody mismatch, collection timestamp custody mismatch, missing custody, malformed custody extras, and no-remediation attempts.'
  'The adapter is bound to Phase 63.1 source registry freshness and Phase 63.2 reviewed evidence request validation. It binds query id and collection timestamp to osquery custody before pack construction.'
  'No Velociraptor, YARA, capa, MISP breadth, Suricata, IntelOwl breadth, endpoint remediation, containment, destructive response, Controlled Write, Hard Write, Beta, RC, GA, commercial replacement readiness, or Phase 64/65/66/67 work is implemented.'
)

for phrase in "${required_validation_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

(cd "${repo_root}" && PYTHONPATH="${repo_root}/control-plane" python3 -m unittest control-plane.tests.test_phase63_3_osquery_evidence_adapter)

path_hygiene_stderr="${repo_root}/.tmp-phase63-3-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 63.3 osquery evidence adapter absolute path usage detected" >&2
  exit 1
fi

echo "Phase 63.3 osquery evidence adapter contract and focused tests pass."
