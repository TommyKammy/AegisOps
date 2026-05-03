#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-54-closeout-evaluation.md"
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
  echo "Missing Phase 54 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 54 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "[Phase 54.10 closeout evaluation](docs/phase-54-closeout-evaluation.md)" "README Phase 54.10 closeout link"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
# Phase 54 Closeout Evaluation
**Status**: Accepted as Shuffle product profile MVP evidence and handoff baseline; Phase 55, Phase 58, Phase 62, and Phase 66 can consume the bounded Shuffle profile MVP with explicit retained blockers.
**Related Issues**: #1154, #1155, #1156, #1157, #1158, #1159, #1160, #1161, #1162, #1163, #1164
Phase 54 is accepted as the Shuffle product profile MVP evidence baseline for the `smb-single-node` profile.
Shuffle remains a subordinate routine automation substrate.
Shuffle executes delegated routine work only after AegisOps records the action request, approval posture, delegation, execution receipt, and reconciliation records required by policy.
AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, delegation intent, release, gate, and closeout truth.
Canonical implementation namespace remains `aegisops.control_plane`; `aegisops_control_plane` is retained for compatibility only.
This closeout does not claim Phase 55 guided first-user journey work is complete, Phase 58 supportability work is complete, Phase 62 SOAR breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a replacement for every SIEM/SOAR capability.
| #1154 | Epic: Phase 54 Shuffle Product Profile MVP | Open until #1164 lands; accepted when this closeout, focused verifier, Phase 54 verifiers, focused Shuffle tests, path hygiene, and issue-lint pass. |
| #1155 | Phase 54.1 Shuffle profile contract and version matrix | Closed.
| #1156 | Phase 54.2 reviewed workflow template contract | Closed.
| #1157 | Phase 54.3 notify_identity_owner template import contract | Closed.
| #1158 | Phase 54.4 create_tracking_ticket template import contract | Closed.
| #1159 | Phase 54.5 Read/Notify template contracts | Closed.
| #1160 | Phase 54.6 AegisOps-to-Shuffle delegation binding | Closed.
| #1161 | Phase 54.7 execution receipt normalization contract | Closed.
| #1162 | Phase 54.8 manual fallback contract | Closed.
| #1163 | Phase 54.9 Shuffle authority-boundary negative tests | Closed.
| #1164 | Phase 54.10 Phase 54 closeout evaluation | Open until this closeout lands; accepted when this document and focused negative verifier pass. |
| Shuffle product profile | Deferred placeholder from Phase 52 first-user stack contracts and Phase 53 Wazuh-side handoff. | Repo-owned `smb-single-node` Shuffle profile contract with frontend, backend, orborus, worker, OpenSearch, exact `2.2.0` Shuffle pins, exact `3.2.0` OpenSearch pin, resource, port, volume, API, callback, and credential expectations. |
| Workflow template contract | Generic delegated-execution expectations from earlier action policy work. | Reviewed workflow template metadata requires correlation, action request, approval decision, execution receipt, version, owner, reviewed status, callback URL, and trusted callback secret reference before import. |
| Template import coverage | No Phase 54 reviewed template import catalog. | `notify_identity_owner`, `create_tracking_ticket`, `enrichment_only_lookup`, `operator_notification`, and `manual_escalation_request` are represented by repo-owned reviewed artifacts with low-risk or Read/Notify boundaries. |
| Delegation binding | Shuffle dispatch could rely on generic approved action request routing. | AegisOps-to-Shuffle dispatch requires explicit `shuffle_delegation_binding` fields, reviewed workflow version, correlation id, expected execution receipt id, and requested-scope match before adapter dispatch. |
| Receipt normalization | Downstream receipt handling was not pinned to the Phase 54 profile contract. | Shuffle receipts are normalized into AegisOps execution receipt context only when the observed run, delegation id, expected receipt id, approval id, payload hash, idempotency key, and coordination binding match the authoritative action execution. |
| Manual fallback | Unavailable or rejected Shuffle paths did not have a Phase 54 manual fallback artifact. | Manual fallback requires owner, operator note, affected template/action, expected evidence, and blocked, unavailable, rejected, missing receipt, stale receipt, or mismatched receipt reason. |
| Authority boundary | Shuffle subordinate posture inherited from Phase 51.6, Phase 52, and Phase 53 contracts. | Focused negative tests prove direct ad-hoc Shuffle launch fails closed, Shuffle-success shortcut reconciliation remains mismatched, and ticket/callback/canvas/log state cannot close cases. |
`docs/deployment/shuffle-smb-single-node-profile-contract.md`
`docs/deployment/shuffle-reviewed-workflow-template-contract.md`
`docs/deployment/shuffle-notify-identity-owner-template-import-contract.md`
`docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md`
`docs/deployment/shuffle-read-notify-template-contracts.md`
`docs/deployment/shuffle-manual-fallback-contract.md`
`docs/deployment/shuffle-authority-boundary-negative-tests.md`
`docs/deployment/profiles/smb-single-node/shuffle/profile.yaml`
`docs/deployment/profiles/smb-single-node/shuffle/reviewed-workflow-template-contract.yaml`
`docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml`
`docs/deployment/profiles/smb-single-node/shuffle/templates/notify_identity_owner-import-contract.yaml`
`docs/deployment/profiles/smb-single-node/shuffle/templates/create_tracking_ticket-import-contract.yaml`
`docs/deployment/profiles/smb-single-node/shuffle/templates/enrichment_only_lookup-import-contract.yaml`
`docs/deployment/profiles/smb-single-node/shuffle/templates/operator_notification-import-contract.yaml`
`docs/deployment/profiles/smb-single-node/shuffle/templates/manual_escalation_request-import-contract.yaml`
`control-plane/aegisops/control_plane/actions/execution_coordinator_delegation.py`
`control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py`
`control-plane/tests/test_service_persistence_action_reconciliation_create_tracking_ticket.py`
`control-plane/tests/test_service_persistence_action_reconciliation_reconciliation.py`
`control-plane/tests/test_cross_boundary_negative_e2e_validation.py`
`docs/phase-54-closeout-evaluation.md`
`scripts/verify-phase-54-10-closeout-evaluation.sh`
`scripts/test-verify-phase-54-10-closeout-evaluation.sh`
`bash scripts/verify-phase-54-1-shuffle-profile-contract.sh`
`bash scripts/test-verify-phase-54-1-shuffle-profile-contract.sh`
`bash scripts/verify-phase-54-2-reviewed-workflow-template-contract.sh`
`bash scripts/test-verify-phase-54-2-reviewed-workflow-template-contract.sh`
`bash scripts/verify-phase-54-3-notify-identity-owner-template-import-contract.sh`
`bash scripts/test-verify-phase-54-3-notify-identity-owner-template-import-contract.sh`
`bash scripts/verify-phase-54-4-create-tracking-ticket-template-import-contract.sh`
`bash scripts/test-verify-phase-54-4-create-tracking-ticket-template-import-contract.sh`
`bash scripts/verify-phase-54-5-read-notify-template-contracts.sh`
`bash scripts/test-verify-phase-54-5-read-notify-template-contracts.sh`
`PYTHONPATH="${PWD}/control-plane:${PWD}/control-plane/tests" python3 -m unittest test_service_persistence_action_reconciliation_create_tracking_ticket`
`PYTHONPATH="${PWD}/control-plane:${PWD}/control-plane/tests" python3 -m unittest test_service_persistence_action_reconciliation_reconciliation`
`bash scripts/verify-phase-54-8-manual-fallback-contract.sh`
`bash scripts/test-verify-phase-54-8-manual-fallback-contract.sh`
`bash scripts/verify-phase-54-9-shuffle-authority-boundary-negative-tests.sh`
`bash scripts/verify-publishable-path-hygiene.sh`
`bash scripts/verify-phase-54-10-closeout-evaluation.sh`
`bash scripts/test-verify-phase-54-10-closeout-evaluation.sh`
`PYTHONPATH="${PWD}/control-plane:${PWD}/control-plane/tests" python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
node <codex-supervisor-root>/dist/index.js issue-lint 1154 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1155 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1156 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1157 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1158 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1159 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1160 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1161 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1162 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1163 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1164 --config <supervisor-config-path>
execution_ready=yes
missing_required=none
missing_recommended=none
metadata_errors=none
high_risk_blocking_ambiguity=none
Phase 54 does not implement Phase 55 guided first-user UI journey work.
Phase 54 does not implement Phase 58 supportability, production runbook completeness, support workflows, or customer support operations.
Phase 54 does not complete Phase 62 SOAR breadth, broad workflow catalog coverage, marketplace work, or every action-family expectation.
Phase 54 does not complete Phase 66 RC proof, RC readiness, GA readiness, Beta readiness, or self-service commercial readiness.
Phase 54 does not enable Controlled Write or Hard Write by default.
Phase 54 does not approve direct ad-hoc Shuffle launch, direct Wazuh-to-Shuffle shortcut execution, Shuffle workflow status case closure, Shuffle success as reconciliation truth, ticket status as case truth, or Shuffle logs as audit truth.
Phase 55 can consume the Shuffle profile MVP as one setup, template, delegation, receipt, and fallback evidence surface for the guided first-user journey.
Phase 55 must still implement the guided journey, user-facing validation flow, runtime custody choices, setup error handling, and first-user ergonomics.
Phase 58 can consume the Shuffle profile MVP as the reviewed automation-substrate support boundary for supportability work.
Phase 58 must still implement support playbooks, customer-safe diagnostics, escalation paths, backup/restore rehearsals, and operator support evidence.
Phase 62 can consume the Shuffle profile MVP as the first reviewed routine-automation substrate profile and evidence pattern.
Phase 62 must still implement SOAR breadth, action-family prioritization, workflow catalog custody expansion, write-capable action gating, and any additional automation profile contracts explicitly.
Phase 54 does not complete Phase 62 SOAR breadth.
Phase 66 can consume the Shuffle profile MVP as one prerequisite evidence packet for RC proof.
Phase 66 must still prove RC gate criteria, production-readiness evidence, upgrade/rollback posture, supportability, security review, and end-to-end first-user journey behavior.
Phase 54 does not complete Phase 66 RC proof.
This closeout is evidence recording only.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 54 closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_pattern="(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 54 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="This closeout does not claim Phase 55 guided first-user journey work is complete, Phase 58 supportability work is complete, Phase 62 SOAR breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a replacement for every SIEM/SOAR capability."

for forbidden in \
  "Phase 55 guided first-user journey work is complete" \
  "Phase 58 supportability work is complete" \
  "Phase 62 SOAR breadth is complete" \
  "Phase 66 RC proof is complete" \
  "Phase 54 proves Beta readiness" \
  "Phase 54 proves RC readiness" \
  "Phase 54 proves GA readiness" \
  "Phase 54 proves self-service commercial readiness" \
  "Phase 54 proves commercial replacement readiness" \
  "AegisOps replaces every SIEM/SOAR capability" \
  "Controlled Write is enabled by default" \
  "Hard Write is enabled by default" \
  "Direct ad-hoc Shuffle launch is approved" \
  "Direct Wazuh-to-Shuffle shortcuts are approved" \
  "Shuffle workflow status closes AegisOps cases" \
  "Shuffle success is AegisOps reconciliation truth" \
  "Ticket status is AegisOps case truth" \
  "Shuffle logs are AegisOps audit truth" \
  "Shuffle workflow success is AegisOps workflow truth" \
  "Shuffle callback payload is AegisOps execution receipt truth"; do
  if grep -Fv -- "${allowed_non_claim_line}" "${absolute_doc_path}" | grep -Fq -- "${forbidden}"; then
    echo "Forbidden Phase 54 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 54 closeout evaluation records Shuffle profile MVP outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 55/58/62/66 handoff."
