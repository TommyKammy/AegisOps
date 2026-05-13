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

absolute_path_boundary='(^|[[:space:]([{\=])'
absolute_path_pattern="${absolute_path_boundary}(/Users/|/home/|[A-Za-z]:\\\\Users\\\\|[A-Za-z]:/Users/)[^ ]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 60 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="This closeout does not claim Phase 61 SIEM breadth is complete, Phase 62 SOAR breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."

for forbidden in \
  "Phase 61 SIEM breadth is complete" \
  "Phase 62 SOAR breadth is complete" \
  "Phase 66 RC proof is complete" \
  "AegisOps is Beta" \
  "AegisOps is RC" \
  "AegisOps is GA" \
  "AegisOps is self-service commercially ready" \
  "AegisOps is a commercial replacement for every SIEM/SOAR capability" \
  "AI output is workflow truth" \
  "AI output is closeout truth" \
  "AI output is recommendation truth" \
  "AI output approves actions" \
  "AI output may approve actions" \
  "AI output may execute actions" \
  "AI output can block case review" \
  "Stale evidence is current truth" \
  "Missing citations may be hidden" \
  "Disabled AI may block case review"; do
  if grep -Fxv -- "${allowed_non_claim_line}" "${absolute_doc_path}" | grep -Fq -- "${forbidden}"; then
    echo "Forbidden Phase 60 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi

done

echo "Phase 60 closeout evaluation records AI daily operations outcomes, bounded authority posture, verifier evidence, accepted limitations, and Phase 61/62/66 handoff."
