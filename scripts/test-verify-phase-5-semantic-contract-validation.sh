#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-5-semantic-contract-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/scripts"
}

write_file() {
  local target="$1"
  local path="$2"
  local content="$3"

  printf '%s\n' "${content}" >"${target}/${path}"
}

write_stub_verifiers() {
  local target="$1"

  for script_name in \
    verify-canonical-telemetry-schema-doc.sh \
    verify-secops-domain-model-doc.sh \
    verify-detection-lifecycle-and-rule-qa-framework.sh \
    verify-response-action-safety-model-doc.sh \
    verify-automation-substrate-contract-doc.sh \
    verify-control-plane-state-model-doc.sh \
    verify-secops-business-hours-operating-model-doc.sh \
    verify-auth-baseline-doc.sh \
    verify-retention-baseline-doc.sh \
    verify-source-onboarding-contract-doc.sh \
    verify-sigma-to-opensearch-translation-strategy-doc.sh
  do
    write_file "${target}" "scripts/${script_name}" "#!/usr/bin/env bash
set -euo pipefail
echo \"${script_name} ok\""
  done
}

write_valid_report() {
  local target="$1"

  write_file "${target}" "docs/phase-5-semantic-contract-validation.md" "# Phase 5 Semantic Contract Validation

- Validation date: 2026-04-07
- Validation scope: Telemetry schema, SecOps domain semantics, detection lifecycle, approval binding, approved automation delegation, control-plane state, operating model, identity boundaries, retention and replay readiness, source onboarding, and Sigma translation boundary
- Baseline references: \`docs/requirements-baseline.md\`, \`docs/architecture.md\`, \`docs/runbook.md\`
- Reviewed Phase 5 artifacts:
  - \`docs/canonical-telemetry-schema-baseline.md\`
  - \`docs/secops-domain-model.md\`
  - \`docs/detection-lifecycle-and-rule-qa-framework.md\`
  - \`docs/response-action-safety-model.md\`
  - \`docs/automation-substrate-contract.md\`
  - \`docs/control-plane-state-model.md\`
  - \`docs/secops-business-hours-operating-model.md\`
  - \`docs/auth-baseline.md\`
  - \`docs/retention-evidence-and-replay-readiness-baseline.md\`
  - \`docs/source-onboarding-contract.md\`
  - \`docs/sigma-to-opensearch-translation-strategy.md\`
- Verification commands: \`bash scripts/verify-canonical-telemetry-schema-doc.sh\`, \`bash scripts/verify-secops-domain-model-doc.sh\`, \`bash scripts/verify-detection-lifecycle-and-rule-qa-framework.sh\`, \`bash scripts/verify-response-action-safety-model-doc.sh\`, \`bash scripts/verify-automation-substrate-contract-doc.sh\`, \`bash scripts/verify-control-plane-state-model-doc.sh\`, \`bash scripts/verify-secops-business-hours-operating-model-doc.sh\`, \`bash scripts/verify-auth-baseline-doc.sh\`, \`bash scripts/verify-retention-baseline-doc.sh\`, \`bash scripts/verify-source-onboarding-contract-doc.sh\`, \`bash scripts/verify-sigma-to-opensearch-translation-strategy-doc.sh\`, \`bash scripts/verify-phase-5-semantic-contract-validation.sh\`
- Validation status: PASS

## Checks Performed

- Confirmed the telemetry contract stays schema-only and ECS-aligned rather than implying live mappings, ingest transforms, or new retention behavior.
- Confirmed detection content remains review- and evidence-bound and does not silently authorize production activation, staging bypass, or response execution.
- Confirmed approval, action request, and action execution remain separate first-class records with approval-bound write safeguards.
- Confirmed the approved automation delegation contract binds payload, provenance, idempotency, expiry, and execution-surface identity without turning substrates or executors into approval or reconciliation authorities.
- Confirmed control-plane ownership remains distinct from OpenSearch analytics outputs and n8n execution history and does not introduce a new live datastore or exposed service boundary.
- Confirmed the operating model remains business-hours-oriented, preserves explicit human escalation and approval decisions, and does not imply 24x7 staffing or autonomous destructive response.
- Confirmed identity boundaries keep human, approver, executor, and service-account responsibilities separate and do not treat shared credentials or workflow convenience roles as sufficient authorization.
- Confirmed retention and replay expectations remain policy-level, preserve evidence and approval lineage, and do not imply live ILM, snapshot-based recovery, or production storage settings.
- Confirmed source onboarding and Sigma translation remain evidence-bound review contracts and do not imply live ingestion approval, automatic detector generation, or unsupported multi-event translation semantics.

## Result

The reviewed Phase 5 semantic-contract documents and verifier set remain aligned with the approved requirements baseline, architecture overview, and runbook skeleton.

Telemetry, detection, approval, delegation, control-plane, operating-model, identity, retention, source-onboarding, and Sigma-translation terminology remain consistent about record boundaries, evidence expectations, and the separation between analytics, approval, and execution.

The reviewed artifacts do not silently authorize live detection rollout, uncontrolled write behavior, new exposed service boundaries, or runtime implementation beyond the approved baseline.

## Deviations

No deviations found."
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

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_stub_verifiers "${valid_repo}"
write_valid_report "${valid_repo}"
assert_passes "${valid_repo}"

missing_report_repo="${workdir}/missing-report"
create_repo "${missing_report_repo}"
write_stub_verifiers "${missing_report_repo}"
assert_fails_with "${missing_report_repo}" "Missing Phase 5 semantic contract validation result document"

missing_phrase_repo="${workdir}/missing-phrase"
create_repo "${missing_phrase_repo}"
write_stub_verifiers "${missing_phrase_repo}"
write_file "${missing_phrase_repo}" "docs/phase-5-semantic-contract-validation.md" "# Phase 5 Semantic Contract Validation

- Validation date: 2026-04-07
- Validation scope: Telemetry schema, SecOps domain semantics, detection lifecycle, approval binding, approved automation delegation, control-plane state, operating model, identity boundaries, retention and replay readiness, source onboarding, and Sigma translation boundary
- Baseline references: \`docs/requirements-baseline.md\`, \`docs/architecture.md\`, \`docs/runbook.md\`
- Reviewed Phase 5 artifacts:
  - \`docs/canonical-telemetry-schema-baseline.md\`
  - \`docs/secops-domain-model.md\`
  - \`docs/detection-lifecycle-and-rule-qa-framework.md\`
  - \`docs/response-action-safety-model.md\`
  - \`docs/automation-substrate-contract.md\`
  - \`docs/control-plane-state-model.md\`
  - \`docs/secops-business-hours-operating-model.md\`
  - \`docs/auth-baseline.md\`
  - \`docs/retention-evidence-and-replay-readiness-baseline.md\`
  - \`docs/source-onboarding-contract.md\`
  - \`docs/sigma-to-opensearch-translation-strategy.md\`
- Verification commands: \`bash scripts/verify-canonical-telemetry-schema-doc.sh\`, \`bash scripts/verify-secops-domain-model-doc.sh\`, \`bash scripts/verify-detection-lifecycle-and-rule-qa-framework.sh\`, \`bash scripts/verify-response-action-safety-model-doc.sh\`, \`bash scripts/verify-automation-substrate-contract-doc.sh\`, \`bash scripts/verify-control-plane-state-model-doc.sh\`, \`bash scripts/verify-secops-business-hours-operating-model-doc.sh\`, \`bash scripts/verify-auth-baseline-doc.sh\`, \`bash scripts/verify-retention-baseline-doc.sh\`, \`bash scripts/verify-source-onboarding-contract-doc.sh\`, \`bash scripts/verify-sigma-to-opensearch-translation-strategy-doc.sh\`, \`bash scripts/verify-phase-5-semantic-contract-validation.sh\`
- Validation status: PASS

## Checks Performed

- Confirmed the telemetry contract stays schema-only and ECS-aligned rather than implying live mappings, ingest transforms, or new retention behavior.

## Result

Incomplete record.

## Deviations

No deviations found."
assert_fails_with "${missing_phrase_repo}" "Confirmed detection content remains review- and evidence-bound and does not silently authorize production activation, staging bypass, or response execution."

missing_phase_5_artifact_repo="${workdir}/missing-phase-5-artifact"
create_repo "${missing_phase_5_artifact_repo}"
write_stub_verifiers "${missing_phase_5_artifact_repo}"
write_file "${missing_phase_5_artifact_repo}" "docs/phase-5-semantic-contract-validation.md" "# Phase 5 Semantic Contract Validation

- Validation date: 2026-04-07
- Validation scope: Telemetry schema, SecOps domain semantics, detection lifecycle, approval binding, approved automation delegation, control-plane state, operating model, identity boundaries, retention and replay readiness, source onboarding, and Sigma translation boundary
- Baseline references: \`docs/requirements-baseline.md\`, \`docs/architecture.md\`, \`docs/runbook.md\`
- Reviewed Phase 5 artifacts:
  - \`docs/canonical-telemetry-schema-baseline.md\`
  - \`docs/secops-domain-model.md\`
  - \`docs/detection-lifecycle-and-rule-qa-framework.md\`
  - \`docs/response-action-safety-model.md\`
  - \`docs/automation-substrate-contract.md\`
  - \`docs/control-plane-state-model.md\`
  - \`docs/secops-business-hours-operating-model.md\`
- Verification commands: \`bash scripts/verify-canonical-telemetry-schema-doc.sh\`, \`bash scripts/verify-secops-domain-model-doc.sh\`, \`bash scripts/verify-detection-lifecycle-and-rule-qa-framework.sh\`, \`bash scripts/verify-response-action-safety-model-doc.sh\`, \`bash scripts/verify-automation-substrate-contract-doc.sh\`, \`bash scripts/verify-control-plane-state-model-doc.sh\`, \`bash scripts/verify-secops-business-hours-operating-model-doc.sh\`, \`bash scripts/verify-phase-5-semantic-contract-validation.sh\`
- Validation status: PASS

## Checks Performed

- Confirmed the telemetry contract stays schema-only and ECS-aligned rather than implying live mappings, ingest transforms, or new retention behavior.
- Confirmed detection content remains review- and evidence-bound and does not silently authorize production activation, staging bypass, or response execution.
- Confirmed approval, action request, and action execution remain separate first-class records with approval-bound write safeguards.
- Confirmed control-plane ownership remains distinct from OpenSearch analytics outputs and n8n execution history and does not introduce a new live datastore or exposed service boundary.
- Confirmed the operating model remains business-hours-oriented, preserves explicit human escalation and approval decisions, and does not imply 24x7 staffing or autonomous destructive response.
- Confirmed identity boundaries keep human, approver, executor, and service-account responsibilities separate and do not treat shared credentials or workflow convenience roles as sufficient authorization.
- Confirmed retention and replay expectations remain policy-level, preserve evidence and approval lineage, and do not imply live ILM, snapshot-based recovery, or production storage settings.
- Confirmed source onboarding and Sigma translation remain evidence-bound review contracts and do not imply live ingestion approval, automatic detector generation, or unsupported multi-event translation semantics.

## Result

The reviewed Phase 5 semantic-contract documents and verifier set remain aligned with the approved requirements baseline, architecture overview, and runbook skeleton.

Telemetry, detection, approval, control-plane, operating-model, identity, retention, source-onboarding, and Sigma-translation terminology remain consistent about record boundaries, evidence expectations, and the separation between analytics, approval, and execution.

The reviewed artifacts do not silently authorize live detection rollout, uncontrolled write behavior, new exposed service boundaries, or runtime implementation beyond the approved baseline.

## Deviations

No deviations found."
assert_fails_with "${missing_phase_5_artifact_repo}" 'Missing validation statement in '"${missing_phase_5_artifact_repo}"'/docs/phase-5-semantic-contract-validation.md: - `docs/auth-baseline.md`'

echo "verify-phase-5-semantic-contract-validation tests passed"
