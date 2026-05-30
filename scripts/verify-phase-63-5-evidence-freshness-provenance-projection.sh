#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

projection_path="${repo_root}/control-plane/aegisops/control_plane/evidence/evidence_freshness_provenance_projection.py"
test_path="${repo_root}/control-plane/tests/test_phase63_5_evidence_freshness_provenance_projection.py"
doc_path="${repo_root}/docs/phase-63-5-evidence-freshness-provenance-projection.md"
validation_path="${repo_root}/docs/phase-63-5-evidence-freshness-provenance-projection-validation.md"
policy_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
fixture_path="${repo_root}/control-plane/tests/fixtures/phase59/stale-conflicting-evidence-ai-fixtures.json"

for path in "${projection_path}" "${test_path}" "${doc_path}" "${validation_path}" "${policy_path}" "${fixture_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 63.5 evidence freshness/provenance projection artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 63.5 evidence freshness/provenance projection statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

required_projection_phrases=(
  'EvidenceFreshnessProvenanceProjectionInput'
  'EvidenceFreshnessProvenanceProjection'
  'project_evidence_freshness_provenance'
  '"case_workbench"'
  '"ai_grounding"'
  '"missing_projection_custody"'
  '"missing_projection_confidence"'
  '"missing_projection_provenance"'
  '"missing_projection_uncertainty"'
  '"custody_binding_mismatch"'
  '"provenance_binding_mismatch"'
  '"response_digest_mismatch"'
  '"confidence_posture_mismatch"'
  '"confidence_ambiguity_badge_mismatch"'
  '"unexpected_projection_status"'
  '"projection_status_requires_reason"'
  '"unexpected_projection_reason"'
  '"unexpected_projection_metadata"'
  '"unsupported_projection_source"'
  '"unexpected_source_status"'
  '"source_denied"'
  '"source_stale"'
  '"source_mismatch"'
  '"case_mismatch"'
  '"projection cannot drive workflow authority"'
  '"stale_review_required"'
  '"unresolved_conflict"'
  '"source_unavailable"'
  '"related_entity_not_authoritative"'
  '"subordinate_evidence_context_only"'
)

for phrase in "${required_projection_phrases[@]}"; do
  require_phrase "${projection_path}" "${phrase}"
done

required_test_phrases=(
  'test_fresh_projection_for_case_workbench_is_subordinate'
  'test_projection_returns_normalized_consumer_name'
  'test_stale_projection_preserves_uncertainty_without_truth_promotion'
  'test_projection_recomputes_freshness_for_aged_persisted_pack'
  'test_conflicting_projection_is_unresolved_not_case_truth'
  'test_unavailable_source_projects_prerequisite_failure'
  'test_missing_custody_confidence_provenance_or_uncertainty_fails_closed'
  'test_provenance_bindings_must_match_pack_authority_fields'
  'test_custody_bindings_must_match_pack_hash_and_lookup_time'
  'test_response_digest_must_match_packed_reputation_response'
  'test_packed_reputation_hash_must_match_reviewed_hash'
  'test_confidence_posture_must_match_source_registry'
  'test_conflicting_projection_requires_unresolved_confidence_badge'
  'test_unexpected_pack_status_fails_closed'
  'test_projection_status_requires_matching_reason'
  'test_unknown_projection_reason_codes_fail_closed'
  'test_projection_metadata_maps_cannot_claim_authority'
  'test_projection_rejects_non_bounded_enrichment_sources'
  'test_projection_rechecks_current_source_registry_status'
  'test_source_or_case_mismatch_fails_closed'
  'test_projection_cannot_drive_case_closure_reconciliation_or_approval'
)

for phrase in "${required_test_phrases[@]}"; do
  require_phrase "${test_path}" "${phrase}"
done

required_doc_phrases=(
  '# AegisOps Phase 63.5 Evidence Freshness and Provenance Projection'
  'Phase 63.5 projects evidence freshness, custody, confidence, provenance, conflict, source mismatch, unavailable-source, and uncertainty posture for case workbench and AI-grounding consumers.'
  'The projection starts from a directly linked `BoundedEnrichmentEvidencePack` and does not redefine AegisOps workflow truth.'
  'Stale evidence projects `stale_review_required`; conflicting evidence projects `unresolved_conflict`; unavailable sources project `source_unavailable`; fresh related evidence projects `related_entity_not_authoritative`.'
  'Missing custody, missing confidence, missing provenance, missing uncertainty, source mismatch, case mismatch, non-bounded-enrichment source, custody binding mismatch, provenance binding mismatch, response digest mismatch, confidence posture mismatch, confidence ambiguity badge mismatch, unexpected pack status, status without a matching reason, unexpected reason code, unexpected metadata field, unexpected source status, hidden metadata authority claim, or requested projection-driven workflow authority fails closed.'
  'Projection freshness is recalculated from the pack lookup time and the authoritative source registry freshness window each time the surface is projected.'
  'Projection source status is recalculated from the current authoritative source registry status each time the surface is projected.'
  '`custody_state=complete` is returned only when the pack custody reviewed file hash, collection timestamp, response hash, and response digest remain bound to the pack file hash, lookup time, and canonical packed reputation response.'
  '`provenance_state=bound` is returned only when the pack provenance values remain bound to the pack'
  'Returned custody, provenance, and confidence maps must exactly match the bounded enrichment projection contract and cannot contain extra authority-bearing fields or authority-bearing values.'
  'Projection state cannot approve, execute, reconcile, close, activate detectors, create source truth, gate release, claim readiness, remediate endpoints, contain hosts, quarantine files, kill processes, mutate protected targets, or issue direct command authority.'
  'This slice does not add endpoint remediation, broad evidence-source breadth, autonomous AI authority, source-native truth, Controlled Write, Hard Write, Beta, RC, GA, commercial replacement readiness, or Phase 64/65/66/67 work.'
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}"
done

required_validation_phrases=(
  '# Phase 63.5 Evidence Freshness and Provenance Projection Validation'
  'Validation status: PASS'
  'Focused projection tests cover fresh, normalized consumers, stale, projection-time aging, conflicting, unavailable source, missing custody, missing confidence, missing provenance, missing uncertainty, source mismatch, case mismatch, non-bounded-enrichment source rejection, custody binding mismatch, provenance binding mismatch, response digest mismatch, response hash mismatch, confidence posture mismatch, confidence ambiguity badge mismatch, unexpected pack status, status without a matching reason, unexpected reason codes, unexpected metadata fields, hidden metadata authority claims, unexpected source status, projection-time source registry status changes, and no-authority-promotion paths.'
  'The projection remains subordinate context for case workbench and AI-grounding consumers only.'
  'No projection field becomes alert, case, evidence request, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, or closeout truth.'
)

for phrase in "${required_validation_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

(cd "${repo_root}" && PYTHONPATH="${repo_root}/control-plane" python3 -m unittest control-plane.tests.test_phase63_5_evidence_freshness_provenance_projection)

path_hygiene_stderr="${repo_root}/.tmp-phase63-5-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 63.5 evidence freshness/provenance projection absolute path usage detected" >&2
  exit 1
fi

echo "Phase 63.5 evidence freshness/provenance projection contract and focused tests pass."
