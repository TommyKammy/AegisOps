#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_verifier="${repo_root}/scripts/verify-phase-6-replay-to-notify-validation.sh"

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

write_stub_verifier() {
  local target="$1"
  local path="$2"

  write_file "${target}" "${path}" "#!/usr/bin/env bash
set -euo pipefail
echo stub ok"
}

install_verifier_under_test() {
  local target="$1"

  cp "${source_verifier}" "${target}/scripts/verify-phase-6-replay-to-notify-validation.sh"
}

write_all_stub_verifiers() {
  local target="$1"

  local stub_paths=(
    "scripts/verify-phase-5-semantic-contract-validation.sh"
    "scripts/verify-phase-6-initial-telemetry-slice-doc.sh"
    "scripts/verify-windows-source-onboarding-assets.sh"
    "scripts/verify-phase-6-opensearch-detector-artifacts.sh"
    "scripts/verify-sigma-n8n-skeleton-validation.sh"
    "scripts/verify-runbook-doc.sh"
    "scripts/verify-canonical-telemetry-schema-doc.sh"
    "scripts/verify-secops-domain-model-doc.sh"
    "scripts/verify-detection-lifecycle-and-rule-qa-framework.sh"
    "scripts/verify-response-action-safety-model-doc.sh"
    "scripts/verify-control-plane-state-model-doc.sh"
    "scripts/verify-secops-business-hours-operating-model-doc.sh"
    "scripts/verify-auth-baseline-doc.sh"
    "scripts/verify-retention-baseline-doc.sh"
    "scripts/verify-source-onboarding-contract-doc.sh"
    "scripts/verify-sigma-to-opensearch-translation-strategy-doc.sh"
    "scripts/verify-sigma-guidance-doc.sh"
    "scripts/verify-sigma-curated-skeleton.sh"
    "scripts/verify-sigma-suppressed-skeleton.sh"
    "scripts/verify-n8n-workflow-category-guidance.sh"
    "scripts/verify-n8n-workflow-skeleton.sh"
  )

  local path
  for path in "${stub_paths[@]}"; do
    write_stub_verifier "${target}" "${path}"
  done
}

write_valid_report() {
  local target="$1"

  write_file "${target}" "docs/phase-6-replay-to-notify-validation.md" "# Phase 6 Replay-to-Notify Validation

- Validation date: 2026-04-03
- Validation scope: Selected Windows security and endpoint replay-to-notify slice from normalized replay input through notify-only analyst routing
- Baseline references: \`docs/phase-5-semantic-contract-validation.md\`, \`docs/phase-6-initial-telemetry-slice.md\`, \`docs/runbook.md\`
- Verification commands: \`bash scripts/verify-phase-5-semantic-contract-validation.sh\`, \`bash scripts/verify-phase-6-initial-telemetry-slice-doc.sh\`, \`bash scripts/verify-windows-source-onboarding-assets.sh\`, \`bash scripts/verify-phase-6-opensearch-detector-artifacts.sh\`, \`bash scripts/verify-sigma-n8n-skeleton-validation.sh\`, \`bash scripts/verify-runbook-doc.sh\`, \`bash scripts/verify-phase-6-replay-to-notify-validation.sh\`
- Validation status: PASS

## Reviewed Artifacts

- \`docs/phase-6-initial-telemetry-slice.md\`
- \`docs/source-families/windows-security-and-endpoint/onboarding-package.md\`
- \`ingest/replay/windows-security-and-endpoint/normalized/success.ndjson\`
- \`sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml\`
- \`sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml\`
- \`sigma/curated/windows-security-and-endpoint/new-local-user-created.yml\`
- \`opensearch/detectors/windows-security-and-endpoint/privileged-group-membership-change-staging.yaml\`
- \`opensearch/detectors/windows-security-and-endpoint/audit-log-cleared-staging.yaml\`
- \`opensearch/detectors/windows-security-and-endpoint/new-local-user-created-staging.yaml\`
- \`n8n/workflows/aegisops_enrich/aegisops_enrich_windows_selected_detector_outputs.json\`
- \`n8n/workflows/aegisops_notify/aegisops_notify_windows_selected_detector_outputs.json\`
- \`docs/runbook.md\`

## Commands Executed

- \`bash scripts/verify-phase-5-semantic-contract-validation.sh\`
- \`bash scripts/verify-phase-6-initial-telemetry-slice-doc.sh\`
- \`bash scripts/verify-windows-source-onboarding-assets.sh\`
- \`bash scripts/verify-phase-6-opensearch-detector-artifacts.sh\`
- \`bash scripts/verify-sigma-n8n-skeleton-validation.sh\`
- \`bash scripts/verify-runbook-doc.sh\`
- \`bash scripts/verify-phase-6-replay-to-notify-validation.sh\`

## Evidence Reviewed

Validated the success replay corpus only for the three selected Windows use cases: privileged group membership change, audit log cleared, and new local user created.

Confirmed the normalized replay input remains limited to synthetic or redacted review fixtures and preserves the Phase 5 evidence, provenance, and replay-readiness semantics.

Confirmed the selected Sigma rules remain reviewable single-event detections and match the staging-only OpenSearch detector artifacts without introducing unsupported translation behavior.

## Result

Confirmed the enrich workflow remains read-only, the notify workflow remains notify-only, and the reviewed path stops at analyst routing without approval bypass, write-capable connectors, or response execution.

Confirmed the reviewed slice remains business-hours oriented, staging-only, and suitable for analyst queue handling rather than production activation or autonomous action.

## Guardrail Review

No unresolved hidden write behavior, uncontrolled activation path, or silent architecture drift was identified in the reviewed replay-to-notify slice.

## Deviations

No deviations found."
}

assert_passes() {
  local target="$1"

  if ! bash "${target}/scripts/verify-phase-6-replay-to-notify-validation.sh" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${target}/scripts/verify-phase-6-replay-to-notify-validation.sh" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
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
install_verifier_under_test "${valid_repo}"
write_all_stub_verifiers "${valid_repo}"
write_valid_report "${valid_repo}"
assert_passes "${valid_repo}"

missing_report_repo="${workdir}/missing-report"
create_repo "${missing_report_repo}"
install_verifier_under_test "${missing_report_repo}"
write_all_stub_verifiers "${missing_report_repo}"
assert_fails_with "${missing_report_repo}" "Missing Phase 6 replay-to-notify validation record"

missing_phrase_repo="${workdir}/missing-phrase"
create_repo "${missing_phrase_repo}"
install_verifier_under_test "${missing_phrase_repo}"
write_all_stub_verifiers "${missing_phrase_repo}"
write_file "${missing_phrase_repo}" "docs/phase-6-replay-to-notify-validation.md" "# Phase 6 Replay-to-Notify Validation

- Validation date: 2026-04-03
- Validation scope: Selected Windows security and endpoint replay-to-notify slice from normalized replay input through notify-only analyst routing
- Baseline references: \`docs/phase-5-semantic-contract-validation.md\`, \`docs/phase-6-initial-telemetry-slice.md\`, \`docs/runbook.md\`
- Verification commands: \`bash scripts/verify-phase-5-semantic-contract-validation.sh\`, \`bash scripts/verify-phase-6-initial-telemetry-slice-doc.sh\`, \`bash scripts/verify-windows-source-onboarding-assets.sh\`, \`bash scripts/verify-phase-6-opensearch-detector-artifacts.sh\`, \`bash scripts/verify-sigma-n8n-skeleton-validation.sh\`, \`bash scripts/verify-runbook-doc.sh\`, \`bash scripts/verify-phase-6-replay-to-notify-validation.sh\`
- Validation status: PASS

## Reviewed Artifacts

- \`docs/phase-6-initial-telemetry-slice.md\`
- \`docs/source-families/windows-security-and-endpoint/onboarding-package.md\`
- \`ingest/replay/windows-security-and-endpoint/normalized/success.ndjson\`
- \`sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml\`
- \`sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml\`
- \`sigma/curated/windows-security-and-endpoint/new-local-user-created.yml\`
- \`opensearch/detectors/windows-security-and-endpoint/privileged-group-membership-change-staging.yaml\`
- \`opensearch/detectors/windows-security-and-endpoint/audit-log-cleared-staging.yaml\`
- \`opensearch/detectors/windows-security-and-endpoint/new-local-user-created-staging.yaml\`
- \`n8n/workflows/aegisops_enrich/aegisops_enrich_windows_selected_detector_outputs.json\`
- \`n8n/workflows/aegisops_notify/aegisops_notify_windows_selected_detector_outputs.json\`
- \`docs/runbook.md\`

## Commands Executed

- \`bash scripts/verify-phase-5-semantic-contract-validation.sh\`

## Evidence Reviewed

Validated the success replay corpus only for the three selected Windows use cases: privileged group membership change, audit log cleared, and new local user created.

## Result

Confirmed the reviewed slice remains business-hours oriented, staging-only, and suitable for analyst queue handling rather than production activation or autonomous action.

## Guardrail Review

No unresolved hidden write behavior, uncontrolled activation path, or silent architecture drift was identified in the reviewed replay-to-notify slice.

## Deviations

No deviations found."
assert_fails_with "${missing_phrase_repo}" "Missing validation statement in ${missing_phrase_repo}/docs/phase-6-replay-to-notify-validation.md: Confirmed the normalized replay input remains limited to synthetic or redacted review fixtures and preserves the Phase 5 evidence, provenance, and replay-readiness semantics."
echo "verify-phase-6-replay-to-notify-validation tests passed"
