#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-57-closeout-evaluation.md"
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
  echo "Missing Phase 57 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 57 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "- [Phase 57.8 closeout evaluation](docs/phase-57-closeout-evaluation.md)" "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 57.8 closeout evaluation is defined by the [Phase 57.8 closeout evaluation](docs/phase-57-closeout-evaluation.md)." "README Product positioning reference"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
# Phase 57 Closeout Evaluation
**Status**: Accepted as commercial administration MVP evidence and handoff baseline; Phase 58, Phase 59, Phase 60, and Phase 66 can consume the bounded Phase 57 admin evidence with explicit retained blockers.
**Related Issues**: #1207, #1208, #1209, #1210, #1211, #1212, #1213, #1214, #1215
Phase 57 is accepted as the Admin / RBAC / Source / Action Policy UI MVP before supportability, AI daily operations, reporting breadth, SOAR breadth, RC, Beta, GA, or commercial replacement expansion.
AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit event truth, limitation, release, gate, and closeout truth.
RBAC docs, admin configuration, user and role state, source profile state, action policy state, retention policy state, audit export configuration, AI enablement posture, UI cache, browser state, verifier output, and issue-lint output remain subordinate configuration, policy posture, or validation evidence.
The Phase 57 admin surfaces must reject support operator workflow authority, external collaborator workflow authority, role UI cache as authority, admin config rewriting historical records, Controlled / Hard Write default enablement, unsafe retention deletion, audit export authority confusion, AI scope creep, and historical workflow rewrite.
This closeout does not claim Phase 58 supportability is complete, Phase 59 AI daily operations is complete, Phase 60 audit or reporting breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability.
| #1207 | Epic: Phase 57 Admin / RBAC / Source / Action Policy UI MVP | Open until #1215 lands; accepted when this closeout, focused verifier, RBAC/admin/export/retention/AI tests, path hygiene, and issue-lint pass. |
| #1208 | Phase 57.1 Add RBAC role matrix contract | Closed.
| #1209 | Phase 57.2 Add user and role admin surface | Closed.
| #1210 | Phase 57.3 Add source profile admin surface | Closed.
| #1211 | Phase 57.4 Add action policy admin surface | Closed.
| #1212 | Phase 57.5 Add retention policy admin surface | Closed.
| #1213 | Phase 57.6 Add audit export admin surface | Closed.
| #1214 | Phase 57.7 Add AI enablement admin toggle | Closed.
| #1215 | Phase 57.8 Phase 57 closeout evaluation | Open until this document and focused closeout verifier land. |
| RBAC role matrix | Phase 56 had operator route sets and backend-bound health context, but no commercial admin role matrix. | Phase 57.1 defines platform admin, analyst, approver, read-only auditor, support operator, and external collaborator roles with support/external workflow authority denied. |
| User and role admin | Commercial user and role posture still depended on low-level or implicit configuration. | Phase 57.2 renders minimum user and role administration for platform admins without tenant-model expansion or historical truth rewrite authority. |
| Source profile admin | Source posture was represented by reviewed Wazuh contracts, but no bounded admin surface. | Phase 57.3 renders Wazuh and future reviewed source profile posture for create, update, disable, degraded, and audit-trail states without source marketplace claims. |
| Action policy admin | Default action policy posture was not visible in the commercial admin surface. | Phase 57.4 renders Read, Notify, and Soft Write posture while rejecting Controlled and Hard Write default enablement. |
| Retention policy admin | Retention families existed as baseline policy, but not as commercial admin posture. | Phase 57.5 renders alerts, cases, evidence, AI traces, audit exports, execution receipts, and reconciliation retention posture with locked, export-pending, expired, active, and denied states. |
| Audit export admin | Audit export posture was not visible in the admin MVP. | Phase 57.6 renders minimum audit export configuration and access posture for normal, empty, degraded, denied, and export-pending states. |
| AI enablement admin | AI posture was advisory but not explicitly controlled by admin enablement state. | Phase 57.7 adds enabled, disabled, and degraded AI enablement posture without new AI features, approval authority, execution authority, or reconciliation authority. |
`docs/phase-57-1-rbac-role-matrix-contract.md`
`apps/operator-ui/src/auth/roleMatrix.ts`
`apps/operator-ui/src/auth/roleMatrix.test.ts`
`apps/operator-ui/src/auth/session.test.ts`
`apps/operator-ui/src/app/operatorConsolePages/adminPages.tsx`
`apps/operator-ui/src/app/OperatorRoutes.authAndShell.testSuite.tsx`
`apps/operator-ui/src/app/OperatorRoutes.tsx`
`apps/operator-ui/src/app/OperatorShell.tsx`
`apps/operator-ui/src/app/optionalExtensionVisibility.tsx`
`apps/operator-ui/src/app/optionalExtensionVisibility.test.tsx`
`control-plane/aegisops/control_plane/config.py`
`control-plane/aegisops/control_plane/assistant/assistant_context.py`
`control-plane/aegisops/control_plane/runtime/readiness_operability.py`
`control-plane/tests/test_phase57_7_ai_enablement_admin_toggle.py`
`docs/phase-57-closeout-evaluation.md`
`scripts/verify-phase-57-8-closeout-evaluation.sh`
`scripts/test-verify-phase-57-8-closeout-evaluation.sh`
`bash scripts/verify-phase-57-1-rbac-role-matrix-contract.sh`
`bash scripts/test-verify-phase-57-1-rbac-role-matrix-contract.sh`
`npm test --workspace apps/operator-ui -- --run src/auth/roleMatrix.test.ts src/auth/session.test.ts`
`npm test --workspace apps/operator-ui -- --run src/app/OperatorRoutes.test.tsx`
`python -m unittest control-plane/tests/test_phase57_7_ai_enablement_admin_toggle.py`
`npm test --workspace apps/operator-ui -- --run src/app/optionalExtensionVisibility.test.tsx`
`bash scripts/verify-control-plane-runtime-skeleton.sh`
`bash scripts/test-verify-control-plane-runtime-skeleton.sh`
`bash scripts/verify-publishable-path-hygiene.sh`
`bash scripts/verify-phase-57-8-closeout-evaluation.sh`
`bash scripts/test-verify-phase-57-8-closeout-evaluation.sh`
RBAC tests cover every Phase 57 commercial role and keep workflowAuthority false for platform admin, analyst, approver, read-only auditor, support operator, and external collaborator role matrix entries.
User and role admin tests reject stale platform-admin browser state when backend reread returns an analyst session.
Source profile admin tests reject source profile state as signal, alert, case, evidence, workflow, release, gate, or closeout truth and keep broad source marketplace claims absent.
Action policy admin tests reject Controlled and Hard Write default enablement and reject action policy config as approval, execution, reconciliation, substrate mutation, or historical receipt truth.
Retention policy admin tests reject locked or export-pending deletion, active workflow closure, audit erasure, historical record-chain rewrite, policy-as-closeout, and stale retention cache authority.
Audit export admin tests reject export config as audit truth, generated export output as workflow truth, denied role access, stale export cache authority, and compliance reporting breadth claims.
AI enablement tests reject feature expansion values, disabled or degraded trace reads, AI approval authority, AI execution authority, AI reconciliation authority, and workflow loss when AI is disabled.
node <codex-supervisor-root>/dist/index.js issue-lint 1207 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1208 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1209 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1210 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1211 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1212 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1213 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1214 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1215 --config <supervisor-config-path>
execution_ready=yes
missing_required=none
missing_recommended=none
metadata_errors=none
high_risk_blocking_ambiguity=none
Phase 57 does not implement Phase 58 supportability, doctor completeness, backup/restore support operations, support bundles, support diagnostics, break-glass support workflows, or customer support operations.
Phase 57 does not implement Phase 59 AI governance expansion, AI daily-operations breadth, AI approval authority, AI execution authority, or AI reconciliation authority.
Phase 57 does not implement Phase 60 audit export administration breadth, commercial reporting breadth, executive reporting completeness, compliance reporting completeness, report custody, or production report templates.
Phase 57 does not implement broad SIEM source marketplace breadth, broad SOAR workflow catalog coverage, marketplace breadth, every action-family expectation, or standalone Wazuh or Shuffle replacement.
Phase 57 does not implement Phase 66 RC proof, RC readiness, GA readiness, Beta readiness, self-service commercial readiness, or commercial replacement readiness.
Phase 58 can consume the Phase 57 admin route, AI disabled/degraded posture, source profile posture, audit export posture, and role matrix as supportability inputs.
Phase 57 does not complete Phase 58 supportability.
Phase 59 can consume the Phase 57 AI enablement posture as bounded enablement evidence.
Phase 57 does not complete Phase 59 AI daily operations.
Phase 60 can consume the Phase 57 retention and audit export administration posture as reporting design input.
Phase 57 does not complete Phase 60 audit or reporting breadth.
Phase 66 can consume the Phase 57 commercial administration MVP as one prerequisite evidence packet for RC proof.
Phase 57 does not complete Phase 66 RC proof.
This closeout is release and planning evidence only.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 57 closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_boundary='(^|[[:space:]`"'\''(<[{=])'
absolute_path_pattern="${absolute_path_boundary}(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 57 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="This closeout does not claim Phase 58 supportability is complete, Phase 59 AI daily operations is complete, Phase 60 audit or reporting breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."

for forbidden in \
  "Phase 58 supportability is complete" \
  "Phase 59 AI daily operations is complete" \
  "Phase 60 audit or reporting breadth is complete" \
  "Phase 66 RC proof is complete" \
  "AegisOps is Beta" \
  "AegisOps is RC" \
  "AegisOps is GA" \
  "AegisOps is self-service commercially ready" \
  "AegisOps is a commercial replacement for every SIEM/SOAR capability" \
  "Phase 57 proves Beta readiness" \
  "Phase 57 proves RC readiness" \
  "Phase 57 proves GA readiness" \
  "Phase 57 proves commercial replacement readiness" \
  "Support operator workflow authority is enabled" \
  "External collaborator workflow authority is enabled" \
  "Controlled default enablement is allowed" \
  "Hard Write default enablement is allowed" \
  "Retention policy deletes locked records" \
  "Retention policy deletes export-pending records" \
  "Audit export config is audit truth" \
  "AI enablement toggle adds new AI features" \
  "Admin config rewrites historical workflow truth" \
  "Admin UI state is workflow truth" \
  "RBAC docs are workflow truth" \
  "User role state is workflow truth" \
  "Source profile state is signal truth" \
  "Action policy config is execution truth" \
  "AI enablement state is AI approval authority"; do
  if grep -Fxv -- "${allowed_non_claim_line}" "${absolute_doc_path}" | grep -Fq -- "${forbidden}"; then
    echo "Forbidden Phase 57 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 57 closeout evaluation records commercial admin MVP outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 58/59/60/66 handoff."
