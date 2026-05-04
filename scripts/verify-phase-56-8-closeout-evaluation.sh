#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-56-closeout-evaluation.md"
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
  echo "Missing Phase 56 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 56 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "- [Phase 56.8 closeout evaluation](docs/phase-56-closeout-evaluation.md)" "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 56.8 closeout evaluation is defined by the [Phase 56.8 closeout evaluation](docs/phase-56-closeout-evaluation.md)." "README Product positioning reference"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
# Phase 56 Closeout Evaluation
**Status**: Accepted as Daily SOC Workbench MVP evidence and handoff baseline; Phase 57, Phase 58, Phase 59, Phase 60, and Phase 66 can consume the bounded Phase 56 operator workflow evidence with explicit retained blockers.
**Related Issues**: #1190, #1191, #1192, #1193, #1194, #1195, #1196, #1197, #1198
Phase 56 is accepted as the Daily SOC Workbench MVP for the `smb-single-node` profile before admin, supportability, reporting breadth, SOAR breadth, RC, Beta, GA, or commercial replacement expansion.
AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.
Today cards, task cards, case timeline display state, business-hours handoff copy, health summary, navigation state, stale UI cache, browser state, AI-suggested focus, Wazuh state, Shuffle state, tickets, reports, verifier output, and issue-lint output remain subordinate context or validation evidence.
The Phase 56 operator surfaces must reject stale UI cache, unsupported role navigation, malformed projections, inferred timeline linkage, task-card completion shortcuts, handoff copy as closeout truth, health summary as gate truth, and authority confusion.
This closeout does not claim Phase 57 admin/RBAC/source/action policy is complete, Phase 58 supportability is complete, Phase 59 AI daily operations is complete, Phase 60 audit or reporting breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability.
| #1190 | Epic: Phase 56 Daily SOC Workbench MVP | Open until #1198 lands; accepted when this closeout, focused verifier, Phase 56 verifiers, backend projection tests, operator UI workflow tests, path hygiene, and issue-lint pass. |
| #1191 | Phase 56.1 Today view backend projection contract | Closed.
| #1192 | Phase 56.2 Today view UI | Closed.
| #1193 | Phase 56.3 case timeline authority/subordinate projection | Closed.
| #1194 | Phase 56.4 case timeline UI | Closed.
| #1195 | Phase 56.5 operator task cards | Closed.
| #1196 | Phase 56.6 business-hours handoff view | Closed.
| #1197 | Phase 56.7 workbench navigation and health summary | Closed.
| #1198 | Phase 56.8 Phase 56 closeout evaluation | Open until this document and focused closeout verifier land. |
| Today backend projection | Phase 55 had a guided first-user journey but no Daily SOC Workbench projection contract. | Phase 56.1 defines Today lanes for priority, stale work, pending approvals, degraded sources, reconciliation mismatches, evidence gaps, and advisory-only AI focus. |
| Today UI | Operators had first-login guidance and case/action surfaces, but no Today starting point for repeated daily review. | Phase 56.2 renders Today work focus, empty state, degraded/stale badges, pending approvals, mismatches, evidence gaps, advisory AI focus, and stale-cache refusal. |
| Case timeline projection | Case detail records existed, but the required authority/subordinate timeline projection was not the Phase 56 reviewed contract. | Phase 56.3 projects Wazuh signal, AegisOps alert, evidence, AI summary, recommendation, action request, approval, Shuffle receipt, and reconciliation with authority posture and direct backend record binding. |
| Case timeline UI | Case detail views did not show the reviewed Phase 56 chain with visual authority distinction. | Phase 56.4 renders the reviewed chain order, authority labels, missing/degraded states, and refuses malformed or cache-sourced timeline truth. |
| Operator task cards | Repeated daily work required operators to discover existing routes manually. | Phase 56.5 adds guidance cards for stale work, pending approvals, evidence gaps, degraded sources, mismatches, and handoff while preserving backend reread and existing authority surfaces. |
| Business-hours handoff | Phase 55 provided first-user journey evidence but no bounded handoff view for part-time operators. | Phase 56.6 renders changed, blocked, owner, evidence-gap, and AI-summary accepted/rejected handoff context without making handoff copy closeout truth. |
| Navigation and health summary | The operator shell did not expose the full Daily SOC Workbench route set and health summary in the Phase 56 shape. | Phase 56.7 exposes Today, Queue, Cases, Actions, Sources, Automations, Reports, Admin, and Health navigation with role visibility and backend-bound health summary. |
`docs/deployment/today-view-backend-projection-contract.md`
`docs/deployment/profiles/smb-single-node/today-view-projection.yaml`
`control-plane/tests/test_phase56_1_today_projection_contract.py`
`control-plane/tests/test_phase56_3_case_timeline_projection.py`
`control-plane/tests/test_phase56_3_case_timeline_projection_contract.py`
`apps/operator-ui/src/app/OperatorRoutes.today.testSuite.tsx`
`apps/operator-ui/src/app/OperatorRoutes.casework.detail.testSuite.tsx`
`apps/operator-ui/src/app/OperatorRoutes.businessHoursHandoff.testSuite.tsx`
`apps/operator-ui/src/app/OperatorRoutes.authAndShell.testSuite.tsx`
`apps/operator-ui/src/app/operatorConsolePages/todayPages.tsx`
`apps/operator-ui/src/app/operatorConsolePages/caseDetailSurfaces.tsx`
`apps/operator-ui/src/app/operatorConsolePages/handoffPages.tsx`
`docs/phase-56-closeout-evaluation.md`
`scripts/verify-phase-56-8-closeout-evaluation.sh`
`scripts/test-verify-phase-56-8-closeout-evaluation.sh`
`bash scripts/verify-phase-56-1-today-view-projection-contract.sh`
`bash scripts/test-verify-phase-56-1-today-view-projection-contract.sh`
`python -m unittest control-plane/tests/test_phase56_1_today_projection_contract.py`
`python -m unittest control-plane/tests/test_phase56_3_case_timeline_projection.py control-plane/tests/test_phase56_3_case_timeline_projection_contract.py`
`npm run test --workspace @aegisops/operator-ui -- OperatorRoutes.test.tsx`
`npm run test --workspace @aegisops/operator-ui -- caseworkActionCards`
`bash scripts/verify-publishable-path-hygiene.sh`
`bash scripts/verify-phase-56-8-closeout-evaluation.sh`
`bash scripts/test-verify-phase-56-8-closeout-evaluation.sh`
Today backend projection tests cover stale projection output, AI focus as authority, Wazuh/Shuffle/ticket closeout shortcuts, and Today summary state as approval/execution/reconciliation truth.
Today UI tests reject stale cache or malformed backend data and fail closed when a reread fails after cached data exists.
Case timeline projection tests reject inferred sibling linkage and keep missing/degraded segments visible.
Case timeline UI tests reject cache-sourced timeline truth, unsupported segments, wrong authority posture, and UI display state as approval/execution/reconciliation truth.
Operator task-card tests reject task-card state as authority and optimistic completion without backend reread.
Business-hours handoff tests reject handoff copy as closeout truth, AI summary as authority, ticket state as case truth, stale cache as current handoff, and unresolved failed paths as completed.
Navigation and health summary tests reject unsupported role access, hidden protected-surface bypass, health summary as gate truth, and stale UI state as current health authority.
node <codex-supervisor-root>/dist/index.js issue-lint 1190 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1191 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1192 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1193 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1194 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1195 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1196 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1197 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1198 --config <supervisor-config-path>
execution_ready=yes
missing_required=none
missing_recommended=none
metadata_errors=none
high_risk_blocking_ambiguity=none
Phase 56 does not implement Phase 57 admin/RBAC/source/action policy UI MVP, installer packaging, or customer-ready distribution.
Phase 56 does not implement Phase 58 supportability, doctor completeness, backup/restore support operations, support bundles, support diagnostics, break-glass support workflows, or customer support operations.
Phase 56 does not implement Phase 59 AI governance expansion, AI daily-operations breadth, AI approval authority, AI execution authority, or AI reconciliation authority.
Phase 56 does not implement Phase 60 audit export administration, commercial reporting breadth, executive reporting completeness, compliance reporting completeness, report custody, retention, or production report templates.
Phase 56 does not implement broad SOAR workflow catalog coverage, marketplace breadth, every action-family expectation, or standalone Shuffle replacement.
Phase 56 does not implement Phase 66 RC proof, RC readiness, GA readiness, Beta readiness, self-service commercial readiness, or commercial replacement readiness.
Phase 57 can consume the Phase 56 workbench navigation, Today cards, and reviewed route set as operator-entry context.
Phase 56 does not complete Phase 57 admin/RBAC or packaging.
Phase 58 can consume the Phase 56 health summary and degraded-source copy as supportability inputs.
Phase 56 does not complete Phase 58 supportability.
Phase 59 can consume the Phase 56 advisory-only AI focus and accepted/rejected AI summary handling as bounded operator-context evidence.
Phase 56 does not complete Phase 59 AI daily operations.
Phase 60 can consume the Phase 56 case timeline, reconciliation mismatch, evidence-gap, and handoff surfaces as workflow context for reporting design.
Phase 56 does not complete Phase 60 audit or reporting breadth.
Phase 66 can consume the Phase 56 Daily SOC Workbench MVP as one prerequisite evidence packet for RC proof.
Phase 56 does not complete Phase 66 RC proof.
This closeout is release and planning evidence only.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 56 closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_pattern="(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 56 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="This closeout does not claim Phase 57 admin/RBAC/source/action policy is complete, Phase 58 supportability is complete, Phase 59 AI daily operations is complete, Phase 60 audit or reporting breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."

for forbidden in \
  "Phase 57 admin/RBAC/source/action policy is complete" \
  "Phase 58 supportability is complete" \
  "Phase 59 AI daily operations is complete" \
  "Phase 60 audit or reporting breadth is complete" \
  "Phase 66 RC proof is complete" \
  "AegisOps is Beta" \
  "AegisOps is RC" \
  "AegisOps is GA" \
  "AegisOps is self-service commercially ready" \
  "AegisOps is a commercial replacement for every SIEM/SOAR capability" \
  "Phase 56 proves Beta readiness" \
  "Phase 56 proves RC readiness" \
  "Phase 56 proves GA readiness" \
  "Phase 56 proves commercial replacement readiness" \
  "Today cards are workflow truth" \
  "Task cards are workflow truth" \
  "Case timeline display state is workflow truth" \
  "Business-hours handoff copy is closeout truth" \
  "Health summary is release gate truth" \
  "Navigation state is access authority" \
  "Stale UI cache is current workflow truth" \
  "AI-suggested focus is authority" \
  "Wazuh state is AegisOps workflow truth" \
  "Shuffle state is AegisOps workflow truth" \
  "Ticket state is case truth" \
  "Report state is audit truth"; do
  if grep -Fxv -- "${allowed_non_claim_line}" "${absolute_doc_path}" | grep -Fq -- "${forbidden}"; then
    echo "Forbidden Phase 56 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 56 closeout evaluation records Daily SOC Workbench outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 57/58/59/60/66 handoff."
