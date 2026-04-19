#!/usr/bin/env bash

phase_contract_all_verifier_commands() {
  cat <<'EOF'
bash scripts/verify-phase-5-semantic-contract-validation.sh
bash scripts/verify-phase-7-ai-hunt-design-validation.sh
bash scripts/verify-phase-8-control-plane-foundation-validation.sh
bash scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh
bash scripts/verify-phase-10-thesis-consistency.sh
bash scripts/verify-phase-6-initial-telemetry-slice-doc.sh
bash scripts/verify-phase-6-opensearch-detector-artifacts.sh
bash scripts/verify-phase-6-replay-to-notify-validation.sh
bash scripts/verify-phase-25-multi-source-case-review-runbook.sh
EOF
}

phase_contract_all_shell_test_commands() {
  cat <<'EOF'
bash scripts/test-verify-ci-phase-7-workflow-coverage.sh
bash scripts/test-verify-ci-phase-5-workflow-coverage.sh
bash scripts/test-verify-ci-phase-6-workflow-coverage.sh
bash scripts/test-verify-ci-phase-8-workflow-coverage.sh
bash scripts/test-verify-ci-phase-9-workflow-coverage.sh
bash scripts/test-verify-ci-phase-10-workflow-coverage.sh
bash scripts/test-verify-ci-phase-11-workflow-coverage.sh
bash scripts/test-verify-ci-phase-12-workflow-coverage.sh
bash scripts/test-verify-ci-phase-13-workflow-coverage.sh
bash scripts/test-verify-phase-5-semantic-contract-validation.sh
bash scripts/test-verify-phase-7-ai-hunt-design-validation.sh
bash scripts/test-verify-phase-8-control-plane-foundation-validation.sh
bash scripts/test-verify-phase-9-control-plane-runtime-boundary-validation.sh
bash scripts/test-verify-phase-10-thesis-consistency.sh
bash scripts/test-verify-phase-11-control-plane-ci-validation.sh
bash scripts/test-verify-phase-12-wazuh-ci-validation.sh
bash scripts/test-verify-phase-13-guarded-automation-ci-validation.sh
bash scripts/test-verify-phase-14-identity-rich-source-family-design.sh
bash scripts/test-verify-phase-14-identity-rich-source-expansion-ci-validation.sh
bash scripts/test-verify-phase-15-identity-grounded-analyst-assistant-boundary.sh
bash scripts/test-verify-ci-phase-16-workflow-coverage.sh
bash scripts/test-verify-phase-19-thin-operator-surface.sh
bash scripts/test-verify-phase-20-low-risk-action-boundary.sh
bash scripts/test-verify-phase-21-production-like-hardening-boundary.sh
bash scripts/test-verify-phase-22-operator-trust-boundary.sh
bash scripts/test-verify-phase-23-authority-closure.sh
bash scripts/test-verify-phase-24-live-assistant-workflow-contract.sh
bash scripts/test-verify-phase-25-multi-source-case-review-runbook.sh
bash scripts/test-verify-phase-26-ticket-coordination-validation.sh
bash scripts/test-verify-phase-27-day-2-hardening-validation.sh
bash scripts/test-verify-ci-phase-28-workflow-coverage.sh
bash scripts/test-verify-ci-phase-14-workflow-coverage.sh
bash scripts/test-verify-ci-phase-15-workflow-coverage.sh
bash scripts/test-verify-ci-phase-19-workflow-coverage.sh
bash scripts/test-verify-ci-phase-20-workflow-coverage.sh
bash scripts/test-verify-ci-phase-21-workflow-coverage.sh
bash scripts/test-verify-ci-phase-22-workflow-coverage.sh
bash scripts/test-verify-ci-phase-23-workflow-coverage.sh
bash scripts/test-verify-ci-phase-24-workflow-coverage.sh
bash scripts/test-verify-ci-phase-25-workflow-coverage.sh
bash scripts/test-verify-ci-phase-26-workflow-coverage.sh
bash scripts/test-verify-ci-phase-27-workflow-coverage.sh
bash scripts/test-verify-phase-6-initial-telemetry-slice-doc.sh
bash scripts/test-verify-phase-6-opensearch-detector-artifacts.sh
bash scripts/test-verify-phase-6-replay-to-notify-validation.sh
EOF
}
