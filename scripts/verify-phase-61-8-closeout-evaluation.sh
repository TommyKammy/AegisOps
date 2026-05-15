#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-61-closeout-evaluation.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${file}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

if [[ ! -s "${absolute_doc_path}" ]]; then
  echo "Missing Phase 61 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 61 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "- [Phase 61.8 closeout evaluation](docs/phase-61-closeout-evaluation.md)" "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 61.8 closeout evaluation is defined by the [Phase 61.8 closeout evaluation](docs/phase-61-closeout-evaluation.md)." "README Product positioning reference"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF_PHRASE'
# Phase 61 Closeout Evaluation
**Status**: Accepted as Minimum SIEM Replacement Breadth before Phase 62 SOAR breadth, Phase 66 RC proof, Beta, RC, GA, and commercial replacement-readiness claims.
**Related Issues**: #1288, #1289, #1290, #1291, #1292, #1293, #1294, #1295, #1296
Phase 61 is accepted as the Minimum SIEM Replacement Breadth slice for reviewed source catalog, detector lifecycle, detector activation review, false-positive review, suppression proposal, source-health dashboard, and AegisOps record search/filter workflows.
AegisOps control-plane records remain authoritative for alert, case, evidence, detector lifecycle, false-positive review, suppression proposal, source-health record, search-result navigation, approval, action request, execution receipt, reconciliation, audit event, limitation, release, gate, and closeout truth.
Wazuh state, source-native alert state, parser output, detector display state, source-health display state, operator UI state, browser state, AI output, optional evidence, verifier output, issue-lint output, and record-search result ordering remain subordinate context and cannot close, reconcile, approve, activate, disable, suppress, release, gate, or claim readiness without reviewed AegisOps workflow records.
Phase 61 must reject missing child evidence, missing verifier output, raw Wazuh or source-native status as AegisOps truth, detector lifecycle skips, silent suppression, uncited or ownerless suppression, false-positive silent deletion, raw SIEM replacement claims, custom rule authoring expansion, network-heavy strategy shift, production secrets, workstation-local paths, and Phase 62/66/Beta/RC/GA/commercial-readiness claims.
This closeout does not claim Phase 62 SOAR breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability.
| #1288 | Epic: Phase 61 Minimum SIEM Replacement Breadth | Open until #1296 lands; accepted when this closeout, focused verifiers, focused backend/UI tests, authority-boundary checks, publishable path hygiene, and issue-lint pass. |
| #1296 | Phase 61.8 Phase 61 closeout evaluation | Open until this document and focused closeout verifier land. |
`apps/operator-ui/src/app/OperatorRoutes.detectorActivationReview.testSuite.tsx`
`apps/operator-ui/src/app/OperatorRoutes.sourceHealthDashboard.testSuite.tsx`
`apps/operator-ui/src/app/OperatorRoutes.recordSearch.testSuite.tsx`
`control-plane/tests/test_phase61_detector_lifecycle_record_contract.py`
`control-plane/tests/test_phase61_7_record_search_filter.py`
`bash scripts/verify-phase-61-1-source-catalog-contract.sh`
`bash scripts/verify-phase-61-2-detector-lifecycle-record-contract.sh`
`bash scripts/verify-phase-61-4-false-positive-review-records.sh`
`bash scripts/verify-phase-61-5-suppression-proposal-workflow.sh`
`bash scripts/verify-phase-61-6-source-health-dashboard.sh`
`bash scripts/verify-phase-61-7-record-search-filter.sh`
`bash scripts/verify-phase-61-8-closeout-evaluation.sh`
`bash scripts/test-verify-phase-61-8-closeout-evaluation.sh`
`bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`
`bash scripts/verify-publishable-path-hygiene.sh`
`node <codex-supervisor-root>/dist/index.js issue-lint 1288 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1289 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1290 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1291 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1292 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1293 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1294 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1295 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1296 --config <supervisor-config-path>`
Source catalog validation rejects missing owner, missing source-health boundary, source-native truth promotion, broad marketplace expansion, raw SIEM replacement claims, and unsupported family drift.
Detector lifecycle validation rejects unsupported source families, source-catalog mismatches, candidate-to-active skips, missing state-specific reason fields, source-native active-state shortcuts, and missing owners.
False-positive review validation rejects silent source-signal deletion, source-history mutation, case closure from labels alone, missing review linkage, missing owner, and source-native false-positive truth.
Suppression proposal validation rejects active suppression authority, missing citations, missing owner, unbounded scope, missing finite expiry, source-history mutation, silent signal hiding, and case closure shortcuts.
Source-health validation and UI tests reject stale-cache source health, raw-source authority, display-state authority, unreviewed state, unreviewed catalog linkage, lifecycle mismatch, and dashboard-driven workflow truth.
Record search/filter tests reject malformed queries, raw-source queries, unsupported search families, stale-cache search results, authority-leaking results, and workflow mutation through search.
Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output.
Phase 61 does not implement Phase 62 SOAR breadth, Phase 66 RC proof, Beta readiness, RC readiness, GA readiness, self-service commercial readiness, or commercial replacement readiness.
Phase 62 can consume Phase 61 reviewed source catalog, detector lifecycle, false-positive review, suppression proposal, source-health dashboard, and record search/filter evidence as SIEM-breadth input only.
Phase 66 can consume Phase 61 as one RC evidence input for minimum SIEM replacement breadth.
Phase 61 closeout is release and planning evidence only.
EOF_PHRASE

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 61 closeout term in ${doc_path}"
done

absolute_path_boundary='(^|[[:space:](){}<>;,!?`"'\''])'
macos_home_pattern="/""users/"
linux_home_pattern="/""home/"
windows_backslash_home_pattern='[a-z]:\\+users\\+'
windows_slash_home_pattern='[a-z]:/'"users"'/'
absolute_path_pattern="(${absolute_path_boundary}(${macos_home_pattern}|${linux_home_pattern}|${windows_backslash_home_pattern}|${windows_slash_home_pattern})|file:///?(${macos_home_pattern}|${linux_home_pattern}|${windows_backslash_home_pattern}|${windows_slash_home_pattern}))[^[:space:]]+"
if tr '[:upper:]' '[:lower:]' < "${absolute_doc_path}" | grep -Eq -- "${absolute_path_pattern}" || \
   tr '[:upper:]' '[:lower:]' < "${readme_path}" | grep -Eq -- "${absolute_path_pattern}"; then
  echo "Forbidden Phase 61 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="This closeout does not claim Phase 62 SOAR breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."
allowed_non_claim_line_lower="$(printf '%s' "${allowed_non_claim_line}" | tr '[:upper:]' '[:lower:]')"

forbidden_claims=(
  "phase 62 soar breadth is complete"
  "phase 66 rc proof is complete"
  "aegisops is beta"
  "aegisops is rc"
  "aegisops is ga"
  "aegisops is self-service commercially ready"
  "aegisops is a commercial replacement for every siem/soar capability"
  "phase 61 proves rc readiness"
  "phase 61 proves ga readiness"
  "phase 61 proves commercial replacement readiness"
  "raw siem search replacement is complete"
  "raw wazuh console replacement is complete"
  "custom rule authoring workbench is complete"
  "multi-site source management is complete"
  "wazuh status closes aegisops cases"
  "source-native alert state closes aegisops records"
  "source-native status is aegisops truth"
  "detector display state activates detectors"
  "source-health display state is workflow truth"
  "source-health dashboard closes cases"
  "record search result ordering is workflow truth"
  "false-positive review silently deletes source signals"
  "suppression proposal actively suppresses source signals"
  "silent suppression is allowed"
  "ownerless suppression is allowed"
  "uncited suppression is allowed"
)

for forbidden in "${forbidden_claims[@]}"; do
  if tr '[:upper:]' '[:lower:]' < "${absolute_doc_path}" | \
    grep -Fxv -- "${allowed_non_claim_line_lower}" | \
    grep -Fq -- "${forbidden}"; then
    echo "Forbidden Phase 61 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 61 closeout evaluation records minimum SIEM breadth outcomes, bounded authority posture, verifier evidence, accepted limitations, and Phase 62/66 handoff."
