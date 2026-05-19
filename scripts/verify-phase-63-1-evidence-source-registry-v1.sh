#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

registry_path="${repo_root}/control-plane/aegisops/control_plane/evidence/evidence_source_registry.py"
test_path="${repo_root}/control-plane/tests/test_phase63_evidence_source_registry.py"
doc_path="${repo_root}/docs/phase-63-1-evidence-source-registry-v1.md"
validation_path="${repo_root}/docs/phase-63-1-evidence-source-registry-v1-validation.md"
policy_path="${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md"

for path in "${registry_path}" "${test_path}" "${doc_path}" "${validation_path}" "${policy_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 63.1 evidence source registry artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 63.1 evidence source registry statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

required_registry_phrases=(
  'PHASE63_EVIDENCE_SOURCE_REGISTRY'
  '"osquery_host_state"'
  '"malwarebazaar_hash_reputation"'
  '"subordinate_evidence_context_only"'
  '"unsupported_source_type"'
  '"missing_owner"'
  '"missing_freshness_window"'
  '"missing_custody_requirements"'
  '"source_disabled"'
  '"source_degraded"'
  '"authority_posture_not_subordinate"'
  '"registry_key_source_type_mismatch"'
)

for phrase in "${required_registry_phrases[@]}"; do
  require_phrase "${registry_path}" "${phrase}"
done

required_doc_phrases=(
  '# AegisOps Phase 63.1 Evidence Source Registry v1'
  'The registry permits osquery plus one bounded intel/enrichment source only.'
  '`osquery_host_state`'
  '`malwarebazaar_hash_reputation`'
  'Selected Bounded Enrichment Rationale'
  'Broad or default evidence source lists are rejected.'
  'Unsupported broad sources are rejected, including Velociraptor, YARA, capa, MISP breadth, Suricata, and IntelOwl breadth.'
  'Registry entries that claim workflow authority are rejected.'
  'This registry cannot let osquery output, hash-reputation output, source-native state, evidence packs, freshness or confidence projections, UI state, browser state, AI output, verifier output, or issue-lint output approve, execute, reconcile, close, activate detectors, create source truth, gate release, or claim readiness.'
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}"
done

required_validation_phrases=(
  '# Phase 63.1 Evidence Source Registry v1 Validation'
  'Validation status: PASS'
  'The registry now covers exactly two entries: `osquery_host_state` and `malwarebazaar_hash_reputation`.'
  'The focused test suite rejects unsupported broad sources, missing owner, missing freshness window, malformed freshness windows, missing custody requirements, missing allowed target class, disabled source use, degraded source use, target-class mismatch, swapped source identity/type/target/freshness pairings, source types outside the reviewed pair, and registry entries that claim workflow authority or workflow-truth ownership.'
  'The registry validator accepts the exported `PHASE63_EVIDENCE_SOURCE_REGISTRY` mapping directly and rejects mapping-key drift from the embedded `source_id`, including same-set key/value swaps and key/profile mismatches between the two bounded entries.'
  'No Velociraptor, YARA, capa, MISP breadth, Suricata, or IntelOwl breadth is implemented.'
)

for phrase in "${required_validation_phrases[@]}"; do
  require_phrase "${validation_path}" "${phrase}"
done

(cd "${repo_root}" && PYTHONPATH="${repo_root}/control-plane" python3 -m unittest control-plane.tests.test_phase63_evidence_source_registry)

path_hygiene_stderr="${repo_root}/.tmp-phase63-1-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 63.1 evidence source registry absolute path usage detected" >&2
  exit 1
fi

echo "Phase 63.1 evidence source registry v1 contract and focused registry tests pass."
