#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

adapter_path="${repo_root}/control-plane/aegisops/control_plane/evidence/bounded_enrichment_adapter.py"
test_path="${repo_root}/control-plane/tests/test_phase63_4_bounded_enrichment_adapter.py"
doc_path="${repo_root}/docs/phase-63-4-bounded-enrichment-adapter.md"
validation_path="${repo_root}/docs/phase-63-4-bounded-enrichment-adapter-validation.md"
request_path="${repo_root}/docs/phase-63-2-reviewed-evidence-request-records.md"
registry_path="${repo_root}/docs/phase-63-1-evidence-source-registry-v1.md"
policy_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"

for path in "${adapter_path}" "${test_path}" "${doc_path}" "${validation_path}" "${request_path}" "${registry_path}" "${policy_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 63.4 bounded enrichment adapter artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 63.4 bounded enrichment adapter statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

required_adapter_phrases=(
  'BoundedEnrichmentAdapter'
  'BoundedEnrichmentAdapterInput'
  'BoundedEnrichmentEvidencePack'
  'validate_phase63_reviewed_evidence_request'
  'PHASE63_EVIDENCE_SOURCE_REGISTRY'
  '"malwarebazaar_hash_reputation"'
  '_BOUNDED_ENRICHMENT_SOURCE_ID = "malwarebazaar_hash_reputation"'
  '"subordinate_evidence_context_only"'
  '"source_unavailable"'
  '"stale_reputation"'
  '"conflicting_enrichment"'
  '"bounded enrichment adapter source_id must be malwarebazaar_hash_reputation"'
  '"reviewed request source_id must be malwarebazaar_hash_reputation"'
  '"bounded enrichment adapter is read-only"'
  '"file_hash must match reviewed request target"'
  '"response hash must match reviewed file hash"'
  '"missing_enrichment_custody"'
  '"enrichment response cannot claim workflow authority"'
  '_ACTIVE_REVIEWED_REQUEST_STATES = frozenset({"reviewed", "approved", "active"})'
  '"reviewed evidence request lifecycle_state must be active"'
  '"bounded enrichment custody collection_timestamp must match looked_up_at"'
  '"looked_up_at must not predate reviewed evidence request"'
  '"looked_up_at must not be in the future"'
  '"bounded enrichment evidence pack must contain JSON-serializable finite values"'
)

for phrase in "${required_adapter_phrases[@]}"; do
  require_phrase "${adapter_path}" "${phrase}"
done

required_test_phrases=(
  'test_available_hash_reputation_builds_subordinate_evidence_pack'
  'test_stale_hash_reputation_is_degraded_not_truth'
  'test_unavailable_source_returns_unavailable_pack'
  'test_conflicting_enrichment_is_degraded_and_visible'
  'test_missing_custody_fails_closed'
  'test_source_mismatch_fails_closed'
  'test_hash_mismatch_fails_closed'
  'test_no_authority_promotion_from_operation_or_response'
)

for phrase in "${required_test_phrases[@]}"; do
  require_phrase "${test_path}" "${phrase}"
done

required_doc_phrases=(
  '# AegisOps Phase 63.4 Bounded Intel Enrichment Adapter MVP'
  'The selected source is `malwarebazaar_hash_reputation`, matching the Phase 63.1 source registry.'
  'The selection is intentionally limited to reviewed file-hash reputation context.'
  'The adapter entry point is `BoundedEnrichmentAdapter.build_evidence_pack`.'
  'The MVP output is a subordinate evidence pack with source provenance, confidence posture, freshness state, unavailable state, degraded reasons, and an explicit no-authority boundary.'
  'Hash reputation output older than the registry freshness window returns a `degraded` pack with `stale_reputation`.'
  'Conflicting enrichment returns a `degraded` pack with `conflicting_enrichment` and an unresolved confidence ambiguity badge.'
  'Unavailable source state returns an `unavailable` pack with `source_unavailable` and no response body.'
  'The adapter is fixed to the `malwarebazaar_hash_reputation` source and rejects attempts to rebind the adapter or reviewed request to another evidence source.'
  'It rejects responses whose hash does not match the reviewed file hash.'
  'Missing custody, source mismatch, hash mismatch, collection before request review, future lookup timestamps, unavailable malformed states, non-read-only operations, and enrichment responses that claim workflow authority fail closed.'
  'MalwareBazaar output, enrichment output, confidence scores, freshness projections, evidence packs, source-native state, AI output, verifier output, issue-lint output, browser state, UI cache, and adapter state remain subordinate context only.'
  'The adapter cannot approve, execute, reconcile, close, activate detectors, create source truth, gate release, claim readiness, remediate endpoints, contain hosts, quarantine files, kill processes, mutate protected targets, or issue direct command authority.'
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}"
done

required_validation_phrases=(
  '# Phase 63.4 Bounded Intel Enrichment Adapter Validation'
  'Validation status: PASS'
  'The focused adapter test suite accepts a normal reviewed MalwareBazaar hash reputation result and rejects or degrades the requested boundary cases: stale reputation, unavailable source state without a response body, conflicting enrichment, missing custody, source mismatch, response hash mismatch, and enrichment-driven approval or workflow-authority claims.'
  'The adapter is bound to the Phase 63.1 `malwarebazaar_hash_reputation` source registry freshness and Phase 63.2 reviewed evidence request validation.'
  'It binds reviewed file hash, enrichment request id, collection timestamp, response digest, source provenance, confidence posture, and freshness before pack construction.'
  'No Velociraptor, YARA, capa, MISP breadth, Suricata, IntelOwl breadth, endpoint remediation, containment, destructive response, Controlled Write, Hard Write, Beta, RC, GA, commercial replacement readiness, or Phase 64/65/66/67 work is implemented.'
)

for phrase in "${required_validation_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

(cd "${repo_root}" && PYTHONPATH="${repo_root}/control-plane" python3 -m unittest control-plane.tests.test_phase63_4_bounded_enrichment_adapter)

path_hygiene_stderr="${repo_root}/.tmp-phase63-4-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 63.4 bounded enrichment adapter absolute path usage detected" >&2
  exit 1
fi

echo "Phase 63.4 bounded enrichment adapter contract and focused tests pass."
