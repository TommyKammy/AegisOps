#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-60-closeout-evaluation.md"
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
  echo "Missing Phase 60 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 60 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "- [Phase 60.9 closeout evaluation](docs/phase-60-closeout-evaluation.md)" "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 60.9 closeout evaluation is defined by the [Phase 60.9 closeout evaluation](docs/phase-60-closeout-evaluation.md)." "README Product positioning reference"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF_PHRASE'
# Phase 60 Closeout Evaluation
**Status**: Accepted as AI Daily Operations MVP before Phase 61 SIEM breadth, Phase 62 SOAR breadth, Phase 66 RC proof, and commercial replacement-readiness claims.
**Related Issues**: #1269, #1270, #1271, #1272, #1273, #1274, #1275, #1276, #1277, #1278
Phase 60 is accepted as the AI Daily Operations MVP for advisory-only operational context before AI breadth expansion, Phase 61/62 planning, RC proof, Beta, RC, GA, or commercial replacement-readiness claims.
AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action request, approval, action review, execution receipt, reconciliation, audit event, limitation, source health, and closeout truth.
AI output, setup doctor explanation, queue digest output, case timeline summary output, evidence-gap detector output, runbook guidance output, recommendation draft output, action-request draft guardrail output, quality metrics report output, operator UI surfaces, browser state, Wazuh state, Shuffle state, ticket state, optional evidence, verifier output, issue-lint output, and model output remain subordinate advisory evidence.
AI daily operations must reject missing authority ceilings, missing citations, disallowed authority, authority-expansion prompt pressure, stale evidence overclaims, conflicting evidence auto-resolution, treatment of advisory output as workflow truth, disabled/degraded AI workflow blocking, workspace-local path leakage, and Phase 61/62/66/Beta/RC/GA/commercial replacement overclaims.
AI can be disabled or degraded without blocking non-AI workflow progression.
Conflicting evidence requires explicit operator resolution and is not auto-resolved.
This closeout does not claim Phase 61 SIEM breadth is complete, Phase 62 SOAR breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability.
| #1278 | Phase 60.9 Phase 60 closeout evaluation | Open until this document and focused closeout verifier land. |
Phase 60 does not implement autonomous approval, autonomous execution, autonomous reconciliation, case closure, detector activation, source-truth creation, policy bypass, or production write authority.
Phase 61 can consume the Phase 60 queue digest, timeline summary, evidence-gap, runbook guidance, recommendation draft, action-request guardrail, and quality metrics projections as bounded design context. Phase 61 must still implement explicit SIEM breadth, coverage growth, and breadth-bound authority decisions.
Phase 62 can consume Phase 60 reviewer-facing, advisory-only daily AI workflows as input only. Phase 62 must still implement SOAR breadth and action-family expansion under its own evidence and quality thresholds.
Phase 66 can consume Phase 60 quality metrics and authority-boundary evidence as part of RC readiness design inputs. Phase 66 must still prove RC gates, first-user RC readiness, rollout operational hygiene, and production rollout readiness outside this closeout.
`node <codex-supervisor-root>/dist/index.js issue-lint 1269 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1270 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1271 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1272 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1273 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1274 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1275 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1276 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1277 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1278 --config <supervisor-config-path>`
EOF_PHRASE

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 60 closeout term in ${doc_path}"
done

absolute_path_boundary='(^|[[:space:](){}<>;,!?.])'
macos_home_pattern="/""users/"
linux_home_pattern="/""home/"
windows_backslash_home_pattern='[a-z]:\\+users\\+'
windows_slash_home_pattern='[a-z]:/'"users"'/'
absolute_path_pattern="${absolute_path_boundary}(${macos_home_pattern}|${linux_home_pattern}|${windows_backslash_home_pattern}|${windows_slash_home_pattern})[^ ]+"
if tr '[:upper:]' '[:lower:]' < "${absolute_doc_path}" | grep -Eq -- "${absolute_path_pattern}" || \
   tr '[:upper:]' '[:lower:]' < "${readme_path}" | grep -Eq -- "${absolute_path_pattern}"; then
  echo "Forbidden Phase 60 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="This closeout does not claim Phase 61 SIEM breadth is complete, Phase 62 SOAR breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."
allowed_non_claim_line_lower="$(printf '%s' "${allowed_non_claim_line}" | tr '[:upper:]' '[:lower:]')"

forbidden_claims=(
  "phase 61 siem breadth is complete"
  "phase 62 soar breadth is complete"
  "phase 66 rc proof is complete"
  "aegisops is beta"
  "aegisops is rc"
  "aegisops is ga"
  "aegisops is self-service commercially ready"
  "aegisops is a commercial replacement for every siem/soar capability"
  "ai output is workflow truth"
  "ai output is closeout truth"
  "ai output is recommendation truth"
  "ai output approves actions"
  "ai output may approve actions"
  "ai output can approve actions"
  "ai output could approve actions"
  "ai output might approve actions"
  "ai may approve actions"
  "ai can approve actions"
  "ai could approve actions"
  "ai might approve actions"
  "ai output may execute actions"
  "ai output can execute actions"
  "ai output could execute actions"
  "ai output might execute actions"
  "ai may execute actions"
  "ai can execute actions"
  "ai could execute actions"
  "ai might execute actions"
  "degraded ai may block case review"
  "degraded ai could block case review"
  "degraded ai might block case review"
  "degraded ai can block case review"
  "ai output can block case review"
  "ai can be disabled or degraded to block case review"
  "ai may be disabled or degraded to block case review"
  "ai could be disabled or degraded to block case review"
  "ai might be disabled or degraded to block case review"
  "disabled ai may block case review"
  "disabled ai can block case review"
  "disabled ai could block case review"
  "disabled ai might block case review"
  "degraded ai workflow may block case review"
  "degraded ai can block case review"
  "degraded ai workflow could block case review"
  "degraded ai workflow might block case review"
  "conflicting evidence may be automatically resolved"
  "conflicting evidence can be automatically resolved"
  "conflicting evidence may be auto-resolved"
  "conflicting evidence can be auto-resolved"
  "conflicting evidence is automatically resolved"
  "conflicting evidence can be silently resolved"
  "stale evidence is current truth"
  "missing citations may be hidden"
  "stale evidence may be hidden"
  "stale evidence can be hidden"
)

for forbidden in "${forbidden_claims[@]}"; do
  if tr '[:upper:]' '[:lower:]' < "${absolute_doc_path}" | \
    grep -Fxv -- "${allowed_non_claim_line_lower}" | \
    grep -Fq -- "${forbidden}"; then
    echo "Forbidden Phase 60 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi

done

echo "Phase 60 closeout evaluation records AI daily operations outcomes, bounded authority posture, verifier evidence, accepted limitations, and Phase 61/62/66 handoff."
