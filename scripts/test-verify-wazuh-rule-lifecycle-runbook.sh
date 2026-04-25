#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-wazuh-rule-lifecycle-runbook.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/docs/wazuh-rule-lifecycle-runbook.md"
  git -C "${target}" add docs/wazuh-rule-lifecycle-runbook.md
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_doc "${valid_repo}" '# Wazuh Rule Lifecycle and Validation Runbook

## 1. Purpose

This runbook defines the reviewed lifecycle for Wazuh rules that AegisOps relies on during the current Phase 12 design and implementation slice.

It supplements `docs/detection-lifecycle-and-rule-qa-framework.md`, `docs/source-onboarding-contract.md`, `docs/wazuh-alert-ingest-contract.md`, and `docs/secops-business-hours-operating-model.md`.

## 2. Scope and Non-Goals

This runbook does not authorize live Wazuh automation changes, broad source-family rollout, or destructive response actions.

## 3. Rule Lifecycle Within AegisOps

A Wazuh rule change must not be treated as an isolated substrate tweak.

## 4. Custom-Rule Onboarding Path for Phase 12

For AegisOps, a custom-rule change is admissible only when the resulting Wazuh alert shape still satisfies the reviewed Wazuh ingest contract, especially `id`, `timestamp`, `rule.id`, `rule.level`, `rule.description`, accountable source identity, and full raw payload preservation.

Phase 12 implementers must update or add fixture coverage under `control-plane/tests/fixtures/wazuh/` whenever a custom rule introduces a new reviewed alert shape, source-identity branch, or provenance expectation.

At minimum, the fixture-backed review path must keep `control-plane/tests/test_wazuh_adapter.py`, `control-plane/tests/test_service_persistence_assistant_advisory.py`, and `control-plane/tests/test_service_persistence_ingest_case_lifecycle.py` aligned with the reviewed rule behavior before downstream workflow logic can rely on it.

## 5. `wazuh-logtest` Validation Runbook

Use `wazuh-logtest` before staging or downstream workflow review so rule authors can confirm that the candidate event produces the expected Wazuh rule metadata and alert shape.

The local validation sequence is: prepare representative input logs, run `wazuh-logtest`, compare the resulting alert fields against `docs/wazuh-alert-ingest-contract.md`, then refresh Phase 12 fixtures and adapter tests before treating the rule as onboarding-ready.

If `wazuh-logtest` output does not preserve the reviewed rule metadata or accountable source identity needed by AegisOps, the rule must return to `draft` or `candidate` rather than moving forward on analyst workflow assumptions.

## 6. Phase 40 Detector Activation Gate

Phase 40 detector activation must remain a reviewed AegisOps release-gate decision, not a Wazuh-owned workflow transition.

Staging activation is allowed only after rule review, fixture review, expected-volume review, false-positive review, rollback owner, disable owner, and next-review date are recorded.

Activation evidence must identify the candidate rule, reviewed fixture set, staging validation result, reviewer, activation window, expected alert volume, and release-gate evidence record.

The gate must fail closed when provenance, scope, reviewer, owner, fixture, validation, false-positive, disable, rollback, or release-gate evidence is missing, malformed, placeholder, or inferred.

## 7. Rollout, Disable, and Rollback

Rollback means disabling or reverting the custom rule, restoring the last reviewed rule revision, and withdrawing any dependent fixture or workflow assumptions until validation is rerun.

Disable evidence must identify the disabled rule or candidate, disable owner, disable reason, affected fixture or parser evidence, operator notification path, and follow-up review.

Rollback evidence must identify the last reviewed rule revision, restored fixture set, rollback owner, rollback reason, validation rerun result, and AegisOps release-gate evidence record.

## 8. False-Positive Handling

False-positive handling must keep benign, suspicious, deferred, and ambiguous outcomes tied to AegisOps-owned alert, case, approval, action, execution, or reconciliation records.

## 9. Detector Evidence Handoff

Detector evidence handoff must land in AegisOps-owned records and the retained release-gate evidence package before activation is treated as complete.

## 10. Authority Boundary

Wazuh remains detection substrate only and is not the authority for AegisOps alert lifecycle, case state, approval state, action state, execution state, reconciliation outcome, or release-gate truth.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing Wazuh rule lifecycle runbook:"

missing_logtest_repo="${workdir}/missing-logtest"
create_repo "${missing_logtest_repo}"
write_doc "${missing_logtest_repo}" '# Wazuh Rule Lifecycle and Validation Runbook

## 1. Purpose

This runbook defines the reviewed lifecycle for Wazuh rules that AegisOps relies on during the current Phase 12 design and implementation slice.

It supplements `docs/detection-lifecycle-and-rule-qa-framework.md`, `docs/source-onboarding-contract.md`, `docs/wazuh-alert-ingest-contract.md`, and `docs/secops-business-hours-operating-model.md`.

## 2. Scope and Non-Goals

This runbook does not authorize live Wazuh automation changes, broad source-family rollout, or destructive response actions.

## 3. Rule Lifecycle Within AegisOps

A Wazuh rule change must not be treated as an isolated substrate tweak.

## 4. Custom-Rule Onboarding Path for Phase 12

For AegisOps, a custom-rule change is admissible only when the resulting Wazuh alert shape still satisfies the reviewed Wazuh ingest contract, especially `id`, `timestamp`, `rule.id`, `rule.level`, `rule.description`, accountable source identity, and full raw payload preservation.

Phase 12 implementers must update or add fixture coverage under `control-plane/tests/fixtures/wazuh/` whenever a custom rule introduces a new reviewed alert shape, source-identity branch, or provenance expectation.

At minimum, the fixture-backed review path must keep `control-plane/tests/test_wazuh_adapter.py`, `control-plane/tests/test_service_persistence_assistant_advisory.py`, and `control-plane/tests/test_service_persistence_ingest_case_lifecycle.py` aligned with the reviewed rule behavior before downstream workflow logic can rely on it.

## 5. `wazuh-logtest` Validation Runbook

## 6. Phase 40 Detector Activation Gate

Phase 40 detector activation must remain a reviewed AegisOps release-gate decision, not a Wazuh-owned workflow transition.

Staging activation is allowed only after rule review, fixture review, expected-volume review, false-positive review, rollback owner, disable owner, and next-review date are recorded.

Activation evidence must identify the candidate rule, reviewed fixture set, staging validation result, reviewer, activation window, expected alert volume, and release-gate evidence record.

The gate must fail closed when provenance, scope, reviewer, owner, fixture, validation, false-positive, disable, rollback, or release-gate evidence is missing, malformed, placeholder, or inferred.

## 7. Rollout, Disable, and Rollback

Rollback means disabling or reverting the custom rule, restoring the last reviewed rule revision, and withdrawing any dependent fixture or workflow assumptions until validation is rerun.

Disable evidence must identify the disabled rule or candidate, disable owner, disable reason, affected fixture or parser evidence, operator notification path, and follow-up review.

Rollback evidence must identify the last reviewed rule revision, restored fixture set, rollback owner, rollback reason, validation rerun result, and AegisOps release-gate evidence record.

## 8. False-Positive Handling

False-positive handling must keep benign, suspicious, deferred, and ambiguous outcomes tied to AegisOps-owned alert, case, approval, action, execution, or reconciliation records.

## 9. Detector Evidence Handoff

Detector evidence handoff must land in AegisOps-owned records and the retained release-gate evidence package before activation is treated as complete.

## 10. Authority Boundary

Wazuh remains detection substrate only and is not the authority for AegisOps alert lifecycle, case state, approval state, action state, execution state, reconciliation outcome, or release-gate truth.'
commit_fixture "${missing_logtest_repo}"
assert_fails_with "${missing_logtest_repo}" 'Missing Wazuh rule lifecycle runbook statement: Use `wazuh-logtest` before staging or downstream workflow review so rule authors can confirm that the candidate event produces the expected Wazuh rule metadata and alert shape.'

missing_phase40_repo="${workdir}/missing-phase40"
create_repo "${missing_phase40_repo}"
write_doc "${missing_phase40_repo}" '# Wazuh Rule Lifecycle and Validation Runbook

## 1. Purpose

This runbook defines the reviewed lifecycle for Wazuh rules that AegisOps relies on during the current Phase 12 design and implementation slice.

It supplements `docs/detection-lifecycle-and-rule-qa-framework.md`, `docs/source-onboarding-contract.md`, `docs/wazuh-alert-ingest-contract.md`, and `docs/secops-business-hours-operating-model.md`.

## 2. Scope and Non-Goals

This runbook does not authorize live Wazuh automation changes, broad source-family rollout, or destructive response actions.

## 3. Rule Lifecycle Within AegisOps

A Wazuh rule change must not be treated as an isolated substrate tweak.

## 4. Custom-Rule Onboarding Path for Phase 12

For AegisOps, a custom-rule change is admissible only when the resulting Wazuh alert shape still satisfies the reviewed Wazuh ingest contract, especially `id`, `timestamp`, `rule.id`, `rule.level`, `rule.description`, accountable source identity, and full raw payload preservation.

Phase 12 implementers must update or add fixture coverage under `control-plane/tests/fixtures/wazuh/` whenever a custom rule introduces a new reviewed alert shape, source-identity branch, or provenance expectation.

At minimum, the fixture-backed review path must keep `control-plane/tests/test_wazuh_adapter.py`, `control-plane/tests/test_service_persistence_assistant_advisory.py`, and `control-plane/tests/test_service_persistence_ingest_case_lifecycle.py` aligned with the reviewed rule behavior before downstream workflow logic can rely on it.

## 5. `wazuh-logtest` Validation Runbook

Use `wazuh-logtest` before staging or downstream workflow review so rule authors can confirm that the candidate event produces the expected Wazuh rule metadata and alert shape.

The local validation sequence is: prepare representative input logs, run `wazuh-logtest`, compare the resulting alert fields against `docs/wazuh-alert-ingest-contract.md`, then refresh Phase 12 fixtures and adapter tests before treating the rule as onboarding-ready.

If `wazuh-logtest` output does not preserve the reviewed rule metadata or accountable source identity needed by AegisOps, the rule must return to `draft` or `candidate` rather than moving forward on analyst workflow assumptions.

## 6. Rollout, Fixture Review, and Rollback

Rollback means disabling or reverting the custom rule, restoring the last reviewed rule revision, and withdrawing any dependent fixture or workflow assumptions until validation is rerun.'
commit_fixture "${missing_phase40_repo}"
assert_fails_with "${missing_phase40_repo}" "Missing Wazuh rule lifecycle runbook heading: ## 6. Phase 40 Detector Activation Gate"

echo "verify-wazuh-rule-lifecycle-runbook tests passed"
