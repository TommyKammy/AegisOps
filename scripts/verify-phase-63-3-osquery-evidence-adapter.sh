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
)

for phrase in "${required_adapter_phrases[@]}"; do
  require_phrase "${adapter_path}" "${phrase}"
done

required_test_phrases=(
  'test_normal_osquery_result_builds_subordinate_evidence_pack'
  'test_stale_osquery_output_is_degraded_not_truth'
  'test_unavailable_adapter_returns_unavailable_pack'
  'test_malformed_output_is_rejected'
  'test_unauthorized_request_fails_closed'
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
  'Malformed rows, unsupported result kinds, unauthorized or expired reviewed requests, target mismatch, missing custody, custody host mismatch, naive timestamps, and non-read-only operations fail closed.'
  'Osquery output, evidence packs, source-native state, freshness projections, AI output, verifier output, issue-lint output, browser state, UI cache, and adapter state remain subordinate context only.'
  'The adapter cannot approve, execute, reconcile, close, activate detectors, create source truth, gate release, claim readiness, remediate endpoints, contain hosts, quarantine files, kill processes, mutate protected targets, or issue direct command authority.'
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}"
done

required_validation_phrases=(
  '# Phase 63.3 Osquery Evidence Adapter Validation'
  'Validation status: PASS'
  'The focused adapter test suite accepts a normal reviewed osquery host-state result and rejects or degrades the requested boundary cases: stale output, unavailable adapter state, malformed rows, unauthorized reviewed request, mismatched target host, missing custody, and no-remediation attempts.'
  'The adapter is bound to Phase 63.1 source registry freshness and Phase 63.2 reviewed evidence request validation.'
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
