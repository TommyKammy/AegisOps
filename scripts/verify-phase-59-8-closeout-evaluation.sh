#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-59-closeout-evaluation.md"
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
  echo "Missing Phase 59 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 59 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "- [Phase 59.8 closeout evaluation](docs/phase-59-closeout-evaluation.md)" "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 59.8 closeout evaluation is defined by the [Phase 59.8 closeout evaluation](docs/phase-59-closeout-evaluation.md)." "README Product positioning reference"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
# Phase 59 Closeout Evaluation
**Status**: Accepted as AI governance foundation evidence and handoff baseline; Phase 60 can consume the bounded Phase 59 agent registry, tool registry, trace lifecycle, disabled/degraded mode, prompt-pressure, stale/conflicting evidence, and trace review queue evidence with explicit retained blockers.
**Related Issues**: #1252, #1253, #1254, #1255, #1256, #1257, #1258, #1259, #1260
Phase 59 is accepted as the AI Governance Foundation before Phase 60 daily AI operations, model/provider expansion, reporting breadth, SOAR breadth, RC, Beta, GA, or commercial replacement expansion.
The accepted governance foundation consists of the AI agent registry contract, AI tool registry contract, AI trace lifecycle contract, AI disabled and degraded mode contract, prompt-pressure negative fixtures, stale and conflicting evidence fixtures, and AI trace review queue skeleton.
AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit event, limitation, release, gate, workflow, and closeout truth.
AI output, agent registry rows, tool registry rows, trace lifecycle rows, trace review state, prompt text, model output, citations, doctor explanations, suggested focus, UI state, browser state, demo data, Wazuh state, Shuffle state, ticket state, optional evidence, verifier output, and issue-lint output remain subordinate governance or validation evidence.
The Phase 59 governance surfaces must reject missing authority ceilings, missing citation requirements, unregistered AI tools, prompt pressure to approve, execute, reconcile, close cases, activate detectors, create source truth, hide citations, suppress uncertainty, widen tool scope, treat stale evidence as current truth, silently resolve conflicting evidence, treat trace state as workflow truth, break non-AI workflows when AI is disabled or degraded, leak secrets, leak workstation-local paths, and Phase 60/RC/GA/commercial replacement claims.
This closeout does not claim Phase 60 daily AI operations are complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability.
| #1252 | Epic: Phase 59 AI Governance Foundation | Open until #1260 lands; accepted when this closeout, focused verifier, Phase 59 policy/trace/prompt/degraded-mode tests, authority-boundary verifier, path hygiene, and issue-lint pass. |
| #1253 | Phase 59.1 Add agent registry contract | Closed.
| #1254 | Phase 59.2 Add tool registry contract | Closed.
| #1255 | Phase 59.3 Add AI trace lifecycle contract | Closed.
| #1256 | Phase 59.4 Add AI disabled / degraded mode contract | Closed.
| #1257 | Phase 59.5 Add prompt-injection and prompt-pressure fixtures | Closed.
| #1258 | Phase 59.6 Add stale/conflicting evidence AI fixtures | Closed.
| #1259 | Phase 59.7 Add AI trace review queue skeleton | Closed.
| #1260 | Phase 59.8 Phase 59 governance closeout evaluation | Open until this document and focused closeout verifier land. |
| Agent registry | AI advisory behavior existed across assistant surfaces, but agent identity and authority ceilings were not captured in one executable governance artifact. | Phase 59.1 defines registered agents, allowed tools, disallowed tools, record families, citations, and advisory-only authority ceilings. |
| Tool registry | Tool use was bounded by surrounding workflows, but registered tool policy was not materialized as a structured artifact. | Phase 59.2 defines safe query, evidence lookup, source-health lookup, runbook lookup, recommendation draft, action-request draft, and doctor explanation as cited audited advisory tools. |
| Trace lifecycle | AI trace records existed, but the governance lifecycle needed explicit created, reviewed, accepted, corrected, rejected, and expired contract coverage. | Phase 59.3 defines state linkage, review metadata, expiration handling, allowed transitions, and trace review queue inputs without workflow-truth authority. |
| Disabled and degraded AI | Admin enablement and doctor posture existed, but disabled/degraded mode behavior needed an explicit AI governance contract. | Phase 59.4 blocks AI generation, recommendations, action drafts, and trace creation when disabled or degraded while queue, case, evidence review, action review, reconciliation, supportability, and admin posture continue from authoritative records. |
| Prompt pressure | Existing assistant guards handled authority overreach, but Phase 59 needed fixture coverage for direct prompt pressure. | Phase 59.5 fixtures reject approval, execution, reconciliation, closure, detector activation, source-truth, citation suppression, disallowed-tool, policy-bypass, scope, and record-family expansion attempts. |
| Stale and conflicting evidence | Missing and ambiguous evidence posture existed in earlier advisory surfaces, but stale/conflicting evidence needed dedicated AI governance fixtures. | Phase 59.6 fixtures require unresolved status, review-needed posture, citation handling, explicit evidence gaps, and refusal to choose authoritative truth. |
| Trace review queue | Phase 59.3 reserved queue inputs but no minimal projection and UI skeleton had landed. | Phase 59.7 renders AI trace review queue records with trace state, registered agent/tool, reviewed record, citations, reviewer note, and expiration posture as subordinate review context only. |
`docs/phase-59-1-agent-registry-contract.md`
`docs/automation/ai-agent-registry.json`
`docs/phase-59-2-tool-registry-contract.md`
`docs/automation/ai-tool-registry.json`
`docs/phase-59-3-ai-trace-lifecycle-contract.md`
`docs/automation/ai-trace-lifecycle.json`
`docs/phase-59-4-ai-disabled-degraded-mode-contract.md`
`docs/automation/ai-disabled-degraded-mode-contract.json`
`control-plane/tests/fixtures/phase59/prompt-pressure-negative-fixtures.json`
`control-plane/tests/fixtures/phase59/stale-conflicting-evidence-ai-fixtures.json`
`control-plane/tests/test_phase59_5_prompt_pressure_fixtures.py`
`control-plane/tests/test_phase59_6_stale_conflicting_evidence_fixtures.py`
`control-plane/aegisops/control_plane/operator_inspection.py`
`control-plane/tests/test_cli_inspection_workflow_family.py`
`apps/operator-ui/src/app/operatorConsolePages/assistantPages.tsx`
`apps/operator-ui/src/app/OperatorRoutes.assistant.testSuite.tsx`
`apps/operator-ui/src/app/OperatorRoutes.casework.queue.testSuite.tsx`
`docs/phase-59-closeout-evaluation.md`
`scripts/verify-phase-59-8-closeout-evaluation.sh`
`scripts/test-verify-phase-59-8-closeout-evaluation.sh`
`bash scripts/verify-phase-59-1-agent-registry-contract.sh`
`bash scripts/test-verify-phase-59-1-agent-registry-contract.sh`
`bash scripts/verify-phase-59-2-tool-registry-contract.sh`
`bash scripts/test-verify-phase-59-2-tool-registry-contract.sh`
`bash scripts/verify-phase-59-3-ai-trace-lifecycle-contract.sh`
`bash scripts/test-verify-phase-59-3-ai-trace-lifecycle-contract.sh`
`bash scripts/verify-phase-59-4-ai-disabled-degraded-mode-contract.sh`
`bash scripts/test-verify-phase-59-4-ai-disabled-degraded-mode-contract.sh`
`python3 -m unittest control-plane.tests.test_phase59_5_prompt_pressure_fixtures`
`python3 -m unittest control-plane.tests.test_phase59_6_stale_conflicting_evidence_fixtures`
`python3 -m unittest control-plane.tests.test_cli_inspection_workflow_family.CliInspectionWorkflowFamilyTests.test_cli_renders_ai_trace_review_queue_skeleton`
`npm test --workspace apps/operator-ui -- --run src/app/OperatorRoutes.test.tsx`
`bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`
`bash scripts/verify-publishable-path-hygiene.sh`
`bash scripts/verify-phase-59-8-closeout-evaluation.sh`
`bash scripts/test-verify-phase-59-8-closeout-evaluation.sh`
Agent registry verifiers reject missing agent fields, missing citation requirements, missing authority ceilings, unregistered/disallowed authority, and local path leakage.
Tool registry verifiers reject missing tool fields, missing audit fields, missing required citations, unregistered tools, disallowed authority, and local path leakage.
Trace lifecycle verifiers reject missing lifecycle states, unregistered agent/tool linkage, missing citations, invalid transitions, expired-to-accepted shortcuts, authority expansion, workflow-truth claims, and local path leakage.
Disabled/degraded mode verifiers and tests reject AI generation, recommendation generation, action-draft generation, trace creation, workflow dependency on AI, authority-expanding copy, automatic repair claims, and local path leakage.
Prompt-pressure fixtures reject approval, execution, reconciliation, closure, detector activation, source-truth creation, citation suppression, uncertainty suppression, disallowed tool access, unregistered tool access, policy bypass, scope expansion, record-family expansion, secrets, and workstation-local path leakage.
Stale/conflicting evidence fixtures reject stale evidence as current truth, conflicting evidence silently resolved by AI, missing citations hidden as sufficient, outdated source health as truth, mismatched record-family linkage, AI-created evidence truth, AI-created case truth, AI-created reconciliation truth, secrets, and workstation-local path leakage.
Trace review queue tests reject missing registered agent/tool/citation anchors, keep `read_only` true, keep `authoritative_workflow_truth` false, surface accepted/rejected/corrected states as review context only, and keep trace links subordinate to reviewed records.
Operator UI route tests render the trace review queue skeleton with accepted, rejected, and corrected states while displaying the explicit subordinate-workflow-truth boundary.
Publishable path hygiene rejects workstation-local absolute paths in publishable tracked Markdown, scripts, docs, and tests.
node <codex-supervisor-root>/dist/index.js issue-lint 1252 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1253 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1254 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1255 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1256 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1257 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1258 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1259 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1260 --config <supervisor-config-path>
execution_ready=yes
missing_required=none
missing_recommended=none
metadata_errors=none
high_risk_blocking_ambiguity=none
Phase 59 does not implement Phase 60 daily AI operations, queue digest expansion, case summary expansion, evidence-gap workflow breadth, runbook guidance workflow breadth, reporting support, or production AI operating breadth.
Phase 59 does not implement autonomous approval, autonomous execution, autonomous reconciliation, case closure, detector activation, source-truth creation, policy bypass, production write authority, or default Controlled Write / Hard Write enablement.
Phase 59 does not implement model/provider selection, billing, prompt marketplace, tool marketplace, agent ecosystem breadth, production prompt marketplace, or agent marketplace.
Phase 59 does not implement broad SIEM source marketplace breadth, broad SOAR workflow catalog coverage, broad evidence-source expansion, standalone Wazuh replacement, standalone Shuffle replacement, or commercial replacement readiness.
Phase 59 does not implement Phase 66 RC proof, RC readiness, GA readiness, Beta readiness, self-service commercial readiness, or commercial replacement readiness.
Phase 59 does not make AI output, registry rows, trace lifecycle rows, trace review state, prompt text, model output, citations, doctor explanations, suggested focus, UI state, browser state, demo data, Wazuh state, Shuffle state, ticket state, optional evidence, verifier output, issue-lint output, CLI output, HTTP output, or operator-facing summaries authoritative AegisOps truth.
Phase 60 can consume the Phase 59 governance foundation as a prerequisite for daily AI operations.
Phase 59 does not complete Phase 60 daily AI operations.
Phase 66 can consume the Phase 59 AI governance foundation as one prerequisite evidence packet for RC proof.
Phase 59 does not complete Phase 66 RC proof.
This closeout is release and planning evidence only.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 59 closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_boundary='(^|[[:space:]`"'\''(<[{=])'
absolute_path_pattern="${absolute_path_boundary}(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 59 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="This closeout does not claim Phase 60 daily AI operations are complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."

for forbidden in \
  "Phase 60 daily AI operations are complete" \
  "Phase 66 RC proof is complete" \
  "AegisOps is Beta" \
  "AegisOps is RC" \
  "AegisOps is GA" \
  "AegisOps is self-service commercially ready" \
  "AegisOps is a commercial replacement for every SIEM/SOAR capability" \
  "Phase 59 proves Beta readiness" \
  "Phase 59 proves RC readiness" \
  "Phase 59 proves GA readiness" \
  "Phase 59 proves commercial replacement readiness" \
  "AI may approve actions" \
  "AI may execute actions" \
  "AI may reconcile outcomes" \
  "AI may close cases" \
  "AI may activate detectors" \
  "AI may create source truth" \
  "AI output is workflow truth" \
  "Trace state is workflow truth" \
  "Trace review state is closeout truth" \
  "Agent registry row is workflow truth" \
  "Tool registry row is workflow truth" \
  "Stale evidence is current truth" \
  "Conflicting evidence can be silently resolved by AI" \
  "Missing citations may be hidden" \
  "Prompt pressure may widen tool scope" \
  "Disabled AI may block case review" \
  "Degraded AI may block reconciliation"; do
  if grep -Fxv -- "${allowed_non_claim_line}" "${absolute_doc_path}" | grep -Fq -- "${forbidden}"; then
    echo "Forbidden Phase 59 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 59 closeout evaluation records AI governance foundation outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 60/66 handoff."
