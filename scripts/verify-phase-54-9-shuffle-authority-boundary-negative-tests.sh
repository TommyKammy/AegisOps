#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/shuffle-authority-boundary-negative-tests.md"
test_path="${repo_root}/control-plane/tests/test_cross_boundary_negative_e2e_validation.py"
readme_path="${repo_root}/README.md"

required_doc_phrases=(
  "# Phase 54.9 Shuffle Authority-Boundary Negative Tests"
  "- **Status**: Accepted negative-test slice"
  "- **Related Issues**: #1154, #1160, #1161, #1163"
  "This slice makes the Shuffle authority-boundary negative tests directly runnable for the Phase 54 Shuffle product profile MVP."
  "Shuffle executes delegated routine work only after AegisOps records the action request, approval posture, delegation, execution receipt, and reconciliation records required by policy."
  "This slice cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "Direct ad-hoc Shuffle launch bypassing AegisOps approval."
  "Shuffle workflow success is presented as reconciliation truth without AegisOps delegation."
  "Ticket state, callback payload, workflow canvas state, or logs are presented as AegisOps case truth."
  "Run \`bash scripts/verify-phase-54-9-shuffle-authority-boundary-negative-tests.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1163 --config <supervisor-config-path>\`."
)

required_test_phrases=(
  "def test_direct_ad_hoc_shuffle_launch_without_aegisops_approval_fails_closed"
  "Missing action request 'shuffle-ad-hoc-launch-001'"
  "def test_shuffle_success_without_aegisops_delegation_is_mismatched_not_truth"
  "observed shuffle execution lacks an authoritative AegisOps delegation record"
  "def test_ticket_callback_canvas_and_logs_do_not_close_case_after_shuffle_success"
  "\"ticket_state\": \"closed\""
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 54.9 Shuffle authority-boundary negative-test doc: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${test_path}" ]]; then
  echo "Missing Phase 54.9 Shuffle authority-boundary negative-test module: ${test_path}" >&2
  exit 1
fi

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 54.9 Shuffle authority-boundary statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${required_test_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${test_path}"; then
    echo "Missing Phase 54.9 Shuffle authority-boundary test reference: ${phrase}" >&2
    exit 1
  fi
done

mac_user_home="$(printf '/%s/' 'Users')"
unix_user_home="$(printf '/%s/' 'home')"
windows_user_home="$(printf '[A-Za-z]:[\\\\/]%s[\\\\/]' 'Users')"
path_boundary="(^|[[:space:]\`\"'(<{=])"

if grep -Eq "(${path_boundary})(file://)?(${mac_user_home}|${unix_user_home}|${windows_user_home})" "${doc_path}"; then
  echo "Forbidden Phase 54.9 Shuffle authority-boundary doc: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 54.9 Shuffle authority-boundary link check: ${readme_path}" >&2
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

if ! grep -Eq '\[[^]]+\]\(docs/deployment/shuffle-authority-boundary-negative-tests\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 54.9 Shuffle authority-boundary negative tests." >&2
  exit 1
fi

PYTHONPATH="${repo_root}/control-plane:${repo_root}/control-plane/tests" \
  python3 -m unittest \
  test_cross_boundary_negative_e2e_validation.CrossBoundaryNegativeE2EValidationTests.test_direct_ad_hoc_shuffle_launch_without_aegisops_approval_fails_closed \
  test_cross_boundary_negative_e2e_validation.CrossBoundaryNegativeE2EValidationTests.test_shuffle_success_without_aegisops_delegation_is_mismatched_not_truth \
  test_cross_boundary_negative_e2e_validation.CrossBoundaryNegativeE2EValidationTests.test_ticket_callback_canvas_and_logs_do_not_close_case_after_shuffle_success

echo "Phase 54.9 Shuffle authority-boundary negative tests reject direct launch, Shuffle success shortcut reconciliation, and ticket/callback/canvas/log case-truth shortcuts."
