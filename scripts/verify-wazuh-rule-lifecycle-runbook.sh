#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/wazuh-rule-lifecycle-runbook.md"

required_headings=(
  "# Wazuh Rule Lifecycle and Validation Runbook"
  "## 1. Purpose"
  "## 2. Scope and Non-Goals"
  "## 3. Rule Lifecycle Within AegisOps"
  "## 4. Custom-Rule Onboarding Path for Phase 12"
  '## 5. `wazuh-logtest` Validation Runbook'
  "## 6. Phase 40 Detector Activation Gate"
  "## 7. Rollout, Disable, and Rollback"
  "## 8. False-Positive Handling"
  "## 9. Detector Evidence Handoff"
  "## 10. Authority Boundary"
)

required_phrases=(
  "This runbook defines the reviewed lifecycle for Wazuh rules that AegisOps relies on during the current Phase 12 design and implementation slice."
  'It supplements `docs/detection-lifecycle-and-rule-qa-framework.md`, `docs/source-onboarding-contract.md`, `docs/wazuh-alert-ingest-contract.md`, and `docs/secops-business-hours-operating-model.md`.'
  "A Wazuh rule change must not be treated as an isolated substrate tweak."
  'For AegisOps, a custom-rule change is admissible only when the resulting Wazuh alert shape still satisfies the reviewed Wazuh ingest contract, especially `id`, `timestamp`, `rule.id`, `rule.level`, `rule.description`, accountable source identity, and full raw payload preservation.'
  'Phase 12 implementers must update or add fixture coverage under `control-plane/tests/fixtures/wazuh/` whenever a custom rule introduces a new reviewed alert shape, source-identity branch, or provenance expectation.'
  'At minimum, the fixture-backed review path must keep `control-plane/tests/test_wazuh_adapter.py`, `control-plane/tests/test_service_persistence_assistant_advisory.py`, and `control-plane/tests/test_service_persistence_ingest_case_lifecycle.py` aligned with the reviewed rule behavior before downstream workflow logic can rely on it.'
  'Use `wazuh-logtest` before staging or downstream workflow review so rule authors can confirm that the candidate event produces the expected Wazuh rule metadata and alert shape.'
  'The local validation sequence is: prepare representative input logs, run `wazuh-logtest`, compare the resulting alert fields against `docs/wazuh-alert-ingest-contract.md`, then refresh Phase 12 fixtures and adapter tests before treating the rule as onboarding-ready.'
  'If `wazuh-logtest` output does not preserve the reviewed rule metadata or accountable source identity needed by AegisOps, the rule must return to `draft` or `candidate` rather than moving forward on analyst workflow assumptions.'
  "Rollback means disabling or reverting the custom rule, restoring the last reviewed rule revision, and withdrawing any dependent fixture or workflow assumptions until validation is rerun."
  "This runbook does not authorize live Wazuh automation changes, broad source-family rollout, or destructive response actions."
  "Phase 40 detector activation must remain a reviewed AegisOps release-gate decision, not a Wazuh-owned workflow transition."
  "Staging activation is allowed only after rule review, fixture review, expected-volume review, false-positive review, rollback owner, disable owner, and next-review date are recorded."
  "Activation evidence must identify the candidate rule, reviewed fixture set, staging validation result, reviewer, activation window, expected alert volume, and release-gate evidence record."
  "Disable evidence must identify the disabled rule or candidate, disable owner, disable reason, affected fixture or parser evidence, operator notification path, and follow-up review."
  "Rollback evidence must identify the last reviewed rule revision, restored fixture set, rollback owner, rollback reason, validation rerun result, and AegisOps release-gate evidence record."
  "False-positive handling must keep benign, suspicious, deferred, and ambiguous outcomes tied to AegisOps-owned alert, case, approval, action, execution, or reconciliation records."
  "Detector evidence handoff must land in AegisOps-owned records and the retained release-gate evidence package before activation is treated as complete."
  "Wazuh remains detection substrate only and is not the authority for AegisOps alert lifecycle, case state, approval state, action state, execution state, reconciliation outcome, or release-gate truth."
  "The gate must fail closed when provenance, scope, reviewer, owner, fixture, validation, false-positive, disable, rollback, or release-gate evidence is missing, malformed, placeholder, or inferred."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Wazuh rule lifecycle runbook: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing Wazuh rule lifecycle runbook heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Wazuh rule lifecycle runbook statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Wazuh rule lifecycle runbook is present and preserves the reviewed Phase 12 onboarding and validation boundary."
