#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-64-1-known-limitation-ownership-record-contract.md"
validation_path="${repo_root}/docs/phase-64-1-known-limitation-ownership-record-contract-validation.md"
policy_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
gate_path="${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
closeout_path="${repo_root}/docs/phase-63-closeout-evaluation.md"
model_path="${repo_root}/control-plane/aegisops/control_plane/models.py"
postgres_path="${repo_root}/control-plane/aegisops/control_plane/adapters/postgres.py"
validator_path="${repo_root}/control-plane/aegisops/control_plane/validation/phase64_record_validators.py"
test_path="${repo_root}/control-plane/tests/test_phase64_known_limitation_ownership_contract.py"
schema_path="${repo_root}/postgres/control-plane/schema.sql"
migration_path="${repo_root}/postgres/control-plane/migrations/0015_phase_64_known_limitation_ownership_records.sql"

for path in \
  "${doc_path}" \
  "${validation_path}" \
  "${policy_path}" \
  "${gate_path}" \
  "${closeout_path}" \
  "${model_path}" \
  "${postgres_path}" \
  "${validator_path}" \
  "${test_path}" \
  "${schema_path}" \
  "${migration_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 64.1 known limitation ownership artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 64.1 statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

required_model_phrases=(
  'class KnownLimitationOwnershipRecord'
  'record_family: ClassVar[str] = "known_limitation_ownership"'
  'identifier_field: ClassVar[str] = "limitation_id"'
  'phase66_handoff_posture: str'
  'readiness_claim: str | None = None'
)

for phrase in "${required_model_phrases[@]}"; do
  require_phrase "${model_path}" "${phrase}"
done

required_postgres_phrases=(
  'KnownLimitationOwnershipRecord: TableConfig'
  '"known_limitation_ownership_records"'
  'array_fields=frozenset({"evidence_references"})'
)

for phrase in "${required_postgres_phrases[@]}"; do
  require_phrase "${postgres_path}" "${phrase}"
done

required_validator_phrases=(
  '_KNOWN_LIMITATION_REVIEW_STATES'
  '_KNOWN_LIMITATION_HANDOFF_POSTURES'
  '_KNOWN_LIMITATION_AUTHORITY_BOUNDARY = "reviewed_evidence_input_only"'
  'validate_phase64_record'
  'readiness or release claims'
)

for phrase in "${required_validator_phrases[@]}"; do
  require_phrase "${validator_path}" "${phrase}"
done

required_test_phrases=(
  'test_known_limitation_ownership_record_is_registered_reviewed_contract_family'
  'test_known_limitation_ownership_persists_and_inspects_with_lifecycle_history'
  'test_known_limitation_ownership_default_lifecycle_state_follows_review_state'
  'test_known_limitation_ownership_requires_explicit_owner_mitigation_evidence_surface_review_and_handoff'
  'test_known_limitation_ownership_rejects_unsupported_review_and_handoff_states'
  'test_known_limitation_ownership_rejects_readiness_and_release_overclaims'
  'Support-bundle completion is achieved'
  'gate truth'
  'SIEM/SOAR replacement readiness'
  'Verifier output is readiness truth'
  'Issue-lint output is readiness truth'
)

for phrase in "${required_test_phrases[@]}"; do
  require_phrase "${test_path}" "${phrase}"
done

required_doc_phrases=(
  '# AegisOps Phase 64.1 Known Limitation Ownership Record Contract'
  'Every `known_limitation_ownership` record requires:'
  '`owner`'
  '`mitigation`'
  '`evidence_references`'
  '`affected_surface`'
  '`review_state`'
  '`phase66_handoff_posture`'
  '`authority_boundary` must be `reviewed_evidence_input_only`.'
  'They cannot claim Beta readiness, RC readiness, GA readiness, self-service commercial readiness, broad SIEM/SOAR replacement readiness, support-bundle completion, verifier readiness truth, issue-lint readiness truth, release truth, gate truth, case closure, approval, execution, or reconciliation.'
  'No Beta, RC, GA, self-service commercial, or commercial replacement readiness claim is made.'
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}"
done

required_validation_phrases=(
  '# Phase 64.1 Known Limitation Ownership Record Contract Validation'
  'Validation status: PASS'
  'missing owner, missing mitigation, missing evidence reference, missing affected surface, missing review state, missing Phase 66 handoff posture, unsupported review state, unsupported Phase 66 handoff posture, and forbidden readiness or release overclaims'
  'Verifier output and issue-lint output remain validation and metadata evidence only.'
  'No Beta, RC, GA, self-service commercial, or commercial replacement readiness claim is made.'
)

for phrase in "${required_validation_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

for phrase in \
  'create table if not exists aegisops_control.known_limitation_ownership_records' \
  "subject_record_family = 'known_limitation_ownership'" \
  "'mitigation_in_progress'"; do
  require_phrase "${schema_path}" "${phrase}"
  require_phrase "${migration_path}" "${phrase}"
done

(cd "${repo_root}" && PYTHONPATH="${repo_root}/control-plane" python3 -m unittest control-plane.tests.test_phase64_known_limitation_ownership_contract)

path_hygiene_stderr="${repo_root}/.tmp-phase64-1-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 64.1 known limitation ownership absolute path usage detected" >&2
  exit 1
fi

echo "Phase 64.1 known limitation ownership record contract and focused tests pass."
