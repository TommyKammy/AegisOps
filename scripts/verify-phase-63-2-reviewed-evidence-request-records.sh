#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

record_path="${repo_root}/control-plane/aegisops/control_plane/evidence/reviewed_evidence_requests.py"
test_path="${repo_root}/control-plane/tests/test_phase63_2_reviewed_evidence_request_records.py"
doc_path="${repo_root}/docs/phase-63-2-reviewed-evidence-request-records.md"
validation_path="${repo_root}/docs/phase-63-2-reviewed-evidence-request-records-validation.md"
source_registry_path="${repo_root}/docs/phase-63-1-evidence-source-registry-v1.md"
policy_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"

for path in "${record_path}" "${test_path}" "${doc_path}" "${validation_path}" "${source_registry_path}" "${policy_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 63.2 reviewed evidence request artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 63.2 reviewed evidence request statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

required_record_phrases=(
  'ReviewedEvidenceRequestRecord'
  'record_family: ClassVar[str] = "reviewed_evidence_request"'
  'validate_phase63_reviewed_evidence_request'
  '"missing_reviewed_scope"'
  '"request_expired"'
  '"unauthorized_requester_role"'
  '"target_source_not_compatible"'
  '"missing_custody"'
  '"missing_case_link"'
  '"source_stale"'
  '"source_denied"'
  '"duplicate_request_ambiguity"'
  '"evidence_request_id_subject_mismatch"'
  '"authority_posture_promotes_workflow_truth"'
  '"requested_scope_promotes_workflow_truth"'
  '"authorization_scope_promotes_workflow_truth"'
  '"source_status_promotes_workflow_truth"'
  'PHASE63_EVIDENCE_SOURCE_REGISTRY'
)

for phrase in "${required_record_phrases[@]}"; do
  require_phrase "${record_path}" "${phrase}"
done

required_test_phrases=(
  'test_required_acceptance_criteria_fail_closed'
  'missing_scope'
  'expired_request'
  'unauthorized_requester'
  'invalid_target_source_pairing'
  'missing_custody'
  'missing_case_link'
  'stale_source'
  'denied_source'
  'test_authority_boundary_rejects_evidence_output_as_truth'
  'test_authority_boundary_rejects_documented_verbs'
  'test_authority_boundary_rejects_authorization_posture_claims'
  'test_reviewed_scope_rejects_authority_claims'
  'test_source_status_truth_claims_are_normalized'
  'test_source_freshness_beyond_registry_window_is_stale'
  'test_source_registry_degraded_and_disabled_state_names_fail_closed'
  'test_duplicate_request_ambiguity_is_rejected'
  'test_duplicate_request_check_only_applies_to_active_candidate'
  'test_evidence_request_id_reuse_for_different_subject_is_rejected'
)

for phrase in "${required_test_phrases[@]}"; do
  require_phrase "${test_path}" "${phrase}"
done

required_doc_phrases=(
  '# AegisOps Phase 63.2 Reviewed Evidence Request Records'
  'The request is AegisOps-owned workflow context.'
  'Evidence output, source-native state, freshness projections, AI output, verifier output, issue-lint output, browser state, and UI cache remain subordinate context only.'
  '`osquery_host_state`'
  '`malwarebazaar_hash_reputation`'
  'The validator rejects missing scope, expired request use, unauthorized requester roles, invalid target/source pairing, missing custody, missing case linkage, stale source use, denied source use, and duplicate active request ambiguity.'
  'Source freshness that exceeds the Phase 63.1 registry window is stale, registry degraded or disabled state names stay binding, duplicate subject checks apply only to active candidate requests, and evidence request identifiers cannot be reused for a different request subject.'
  'Requested scope, authorization reviewed scope, source status, state, registry_state, and source_state fields cannot claim workflow truth, case truth, approval truth, execution authority, or readiness authority.'
  'Reviewed evidence request records cannot let osquery output, hash-reputation output, evidence output, source-native state, freshness or confidence projections, AI output, verifier output, issue-lint output, browser state, UI cache, or evidence packs approve, execute, reconcile, close, activate detectors, create source truth, gate release, or claim readiness.'
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}"
done

required_validation_phrases=(
  '# Phase 63.2 Reviewed Evidence Request Records Validation'
  'Validation status: PASS'
  'The focused test suite accepts a valid reviewed request and rejects missing scope, expired request use, unauthorized requester, invalid target/source pairing, missing custody, missing case link, stale source, denied source, duplicate request ambiguity, and evidence output that tries to become workflow truth.'
  'Review-thread regressions cover documented authority verbs, requested-scope authority claims, normalized source-status truth claims, freshness beyond the registry window, registry degraded or disabled state names, inactive candidate duplicate handling, and same-id reuse for a different request subject.'
  'No Velociraptor, YARA, capa, MISP breadth, Suricata, IntelOwl breadth, endpoint remediation, containment, destructive response, Controlled Write, Hard Write, Beta, RC, GA, commercial replacement readiness, or Phase 64/65/66/67 work is implemented.'
)

for phrase in "${required_validation_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

(cd "${repo_root}" && PYTHONPATH="${repo_root}/control-plane" python3 -m unittest control-plane.tests.test_phase63_2_reviewed_evidence_request_records)

path_hygiene_stderr="${repo_root}/.tmp-phase63-2-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 63.2 reviewed evidence request absolute path usage detected" >&2
  exit 1
fi

echo "Phase 63.2 reviewed evidence request records contract and focused tests pass."
