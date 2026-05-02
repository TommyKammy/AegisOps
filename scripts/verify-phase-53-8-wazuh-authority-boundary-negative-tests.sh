#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/wazuh-authority-boundary-negative-tests.md"
test_path="${repo_root}/control-plane/tests/test_cross_boundary_negative_e2e_validation.py"
readme_path="${repo_root}/README.md"

required_doc_phrases=(
  "# Phase 53.8 Wazuh Authority-Boundary Negative Tests"
  "- **Status**: Accepted negative-test slice"
  "- **Related Issues**: #1135, #1138, #1141, #1143"
  "This slice makes the Wazuh authority-boundary negative tests directly runnable for the Phase 53 Wazuh product profile MVP."
  "Wazuh detections are analytic signals until admitted and linked by AegisOps."
  "This slice cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "Raw Wazuh alert status closes an AegisOps case."
  "Wazuh-triggered Shuffle execution appears without AegisOps delegation."
  "Wazuh Active Response is presented as AegisOps authority."
  "Wazuh dashboard state is presented as workflow truth."
  "Run \`bash scripts/verify-phase-53-8-wazuh-authority-boundary-negative-tests.sh\`."
  "Run Wazuh source-health tests with \`bash scripts/verify-phase-53-6-wazuh-source-health-projection.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1143 --config <supervisor-config-path>\`."
)

required_test_phrases=(
  "def test_raw_wazuh_status_cannot_close_aegisops_case"
  "Wazuh status is subordinate detection context"
  "def test_wazuh_triggered_shuffle_run_without_aegisops_delegation_is_mismatched"
  "observed shuffle execution lacks an authoritative AegisOps delegation record"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 53.8 Wazuh authority-boundary negative-test doc: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${test_path}" ]]; then
  echo "Missing Phase 53.8 Wazuh authority-boundary negative-test module: ${test_path}" >&2
  exit 1
fi

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 53.8 Wazuh authority-boundary statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${required_test_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${test_path}"; then
    echo "Missing Phase 53.8 Wazuh authority-boundary test reference: ${phrase}" >&2
    exit 1
  fi
done

mac_user_home="$(printf '/%s/' 'Users')"
unix_user_home="$(printf '/%s/' 'home')"
windows_user_home="$(printf '[A-Za-z]:[\\\\/]%s[\\\\/]' 'Users')"
path_boundary="(^|[[:space:]\`\"'(<{=])"

if grep -Eq "(${path_boundary})(file://)?(${mac_user_home}|${unix_user_home}|${windows_user_home})" "${doc_path}"; then
  echo "Forbidden Phase 53.8 Wazuh authority-boundary doc: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 53.8 Wazuh authority-boundary link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  awk '
    /^[[:space:]]*(```|~~~)/ {
      in_fenced_block = !in_fenced_block
      next
    }
    !in_fenced_block { print }
  ' "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/wazuh-authority-boundary-negative-tests\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 53.8 Wazuh authority-boundary negative tests." >&2
  exit 1
fi

python3 -m unittest \
  control-plane.tests.test_cross_boundary_negative_e2e_validation.CrossBoundaryNegativeE2EValidationTests.test_raw_wazuh_status_cannot_close_aegisops_case \
  control-plane.tests.test_cross_boundary_negative_e2e_validation.CrossBoundaryNegativeE2EValidationTests.test_wazuh_triggered_shuffle_run_without_aegisops_delegation_is_mismatched

echo "Phase 53.8 Wazuh authority-boundary negative tests reject raw Wazuh case closure and direct Wazuh-to-Shuffle shortcut reconciliation."
