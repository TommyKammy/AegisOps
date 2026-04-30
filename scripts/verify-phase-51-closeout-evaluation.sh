#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-51-closeout-evaluation.md"
absolute_doc_path="${repo_root}/${doc_path}"

require_phrase() {
  local phrase="$1"
  local description="$2"

  if ! grep -Fq -- "${phrase}" "${absolute_doc_path}"; then
    echo "Missing ${description} in ${doc_path}: ${phrase}" >&2
    exit 1
  fi
}

if [[ ! -s "${absolute_doc_path}" ]]; then
  echo "Missing Phase 51 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

required_phrases=(
  "# Phase 51 Closeout Evaluation"
  "**Status**: Accepted with lifecycle closeout pending"
  "**Related Issues**: #1041, #1042, #1043, #1044, #1045, #1046, #1047, #1048, #1049"
  "Phase 51 is accepted as a repo-owned replacement-readiness contract."
  "Phase 52 is the next materialization target after this closeout is made authoritative by closing or explicitly owner-accepting the Phase 51 Epic and closeout issue."
  'phase_classification["51"] = "materialized_open"'
  "| #1042 | Phase 51.1 replacement boundary ADR | Closed."
  "| #1043 | Phase 51.2 README product positioning | Closed."
  "| #1044 | Phase 51.3 Pilot, Beta, RC, and GA gate contract | Closed."
  "| #1045 | Phase 51.4 SMB personas and jobs-to-be-done | Closed."
  "| #1046 | Phase 51.5 competitive gap matrix | Closed."
  "| #1047 | Phase 51.6 authority-boundary negative-test policy | Closed."
  "| #1048 | Phase 51.7 roadmap materialization guard | Closed."
  "| #1049 | Phase 51.8 closeout evaluation | Open while this evaluation is under review."
  "bash scripts/verify-phase-51-1-replacement-boundary-adr.sh"
  "bash scripts/test-verify-phase-51-1-replacement-boundary-adr.sh"
  "bash scripts/verify-readme-product-positioning.sh"
  "bash scripts/test-verify-readme-product-positioning.sh"
  "bash scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh"
  "bash scripts/test-verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh"
  "bash scripts/verify-phase-51-4-smb-personas-jtbd.sh"
  "bash scripts/test-verify-phase-51-4-smb-personas-jtbd.sh"
  "bash scripts/verify-phase-51-5-competitive-gap-matrix.sh"
  "bash scripts/test-verify-phase-51-5-competitive-gap-matrix.sh"
  "bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh"
  "bash scripts/test-verify-phase-51-6-authority-boundary-negative-test-policy.sh"
  "bash scripts/verify-roadmap-materialization-preflight-contract.sh"
  "bash scripts/test-verify-roadmap-materialization-preflight-contract.sh"
  "bash scripts/test-verify-roadmap-materialization-preflight.sh"
  "execution_ready=yes"
  "missing_required=none"
  "missing_recommended=none"
  "metadata_errors=none"
  "high_risk_blocking_ambiguity=none"
  "CODEX_SUPERVISOR_ROOT=<codex-supervisor-root>"
  "CODEX_SUPERVISOR_CONFIG=<supervisor-config-path>"
  "bash scripts/roadmap-materialization-preflight.sh --graph docs/automation/roadmap-materialization-phase-graph.json --target-phase 52 --issue-source github"
  'invalid_phase_id="51"'
  'invalid_field="issue_state"'
  'invalid_issue_number=1041'
  'phase_classification["51"]="materialized_open"'
  "Replacement boundary ADR exists and is cited from README."
  "Authority-boundary policy requires later breadth issues to cite fail-closed negative-test expectations"
  "Phase 51 does not implement Phase 52 setup"
  "Phase 51 does not prove GA replacement readiness."
  'Do not materialize Phase 52 while the live preflight reports Phase 51 as `materialized_open`.'
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${phrase}" "required closeout term"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_pattern="(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}"; then
  echo "Forbidden Phase 51 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

for forbidden in \
  "Phase 51 proves GA replacement readiness" \
  "Phase 52 may be materialized while Phase 51 is open" \
  "AegisOps is already GA" \
  "AI is authoritative" \
  "Wazuh is authoritative for AegisOps records" \
  "Shuffle workflow success is AegisOps reconciliation truth"; do
  if grep -Fq -- "${forbidden}" "${absolute_doc_path}"; then
    echo "Forbidden Phase 51 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 51 closeout evaluation records verifier evidence, lifecycle limitation, authority boundary, and Phase 52 materialization recommendation."
